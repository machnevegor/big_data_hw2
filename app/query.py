#!/usr/bin/env python3

import sys

from pyspark import SparkConf, SparkContext

sys.path.insert(0, "cassandra_lib.zip")

from cassandra.cluster import Cluster

KEYSPACE = "search_index"
TOP_K = 10
CASSANDRA_HOST = "cassandra-server"

K1 = 1.5
B = 0.75

query = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
query_terms = query.lower().split()

conf = SparkConf().setAppName("BM25Query")
sc = SparkContext(conf=conf)

cluster = Cluster([CASSANDRA_HOST])
session = cluster.connect(KEYSPACE)

rows = session.execute("SELECT term, df, idf FROM vocabulary")
vocab = {row.term: (row.df, row.idf) for row in rows if row.term in query_terms}

stats = dict(session.execute("SELECT key, value FROM stats"))
total_docs = stats.get("totalDocs", 1.0)
avg_doc_length = stats.get("avgDocLength", 1.0)

index_data = []
for term in query_terms:
    if term not in vocab:
        continue
    rows = session.execute(
        "SELECT doc_id, tf FROM inverted_index WHERE term = %s", (term,)
    )
    for row in rows:
        index_data.append((row.doc_id, (term, row.tf)))

doc_lengths = dict(session.execute("SELECT doc_id, doc_length FROM documents"))
titles = dict(session.execute("SELECT doc_id, title FROM documents"))

rdd = sc.parallelize(index_data)


def compute_bm25(doc_id, term_tf_pairs):
    score = 0.0
    doc_len = doc_lengths.get(doc_id, avg_doc_length)
    for term, tf in term_tf_pairs:
        df, idf = vocab.get(term, (0, 0.0))
        numerator = tf * (K1 + 1)
        denominator = tf + K1 * (1 - B + B * (doc_len / avg_doc_length))
        score += idf * (numerator / denominator)
    return doc_id, score


bm25_scores = (
    rdd.groupByKey()
    .mapValues(list)
    .map(lambda x: compute_bm25(x[0], x[1]))
    .filter(lambda x: x[1] > 0)
    .sortBy(lambda x: -x[1])
    .take(TOP_K)
)

print("\nTop Documents by BM25 Score:")
print("=" * 60)
print(f"{'Doc ID':<10} {'Score':<10} {'Title'}")
print("-" * 60)

for doc_id, score in bm25_scores:
    title = titles.get(doc_id, "(no title)")
    print(f"{doc_id:<10} {score:<10.4f} {title}")

print("=" * 60)

sc.stop()
