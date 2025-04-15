#!/usr/bin/env python3

import math
import sys

sys.path.insert(0, "cassandra_lib.zip")

from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, ConsistencyLevel

BATCH_SIZE = 100

cluster = Cluster(["cassandra-server"])
session = cluster.connect("search_index")

term_index = {}
doc_lengths = {}
titles = {}
doc_ids_set = set()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    parts = line.split("\t", 2)
    if len(parts) < 3:
        continue

    key, doc_id_str, value = parts

    try:
        doc_id = int(doc_id_str)
    except ValueError:
        continue

    if key == "__TITLE__":
        titles[doc_id] = value
    elif key == "__DOC_LEN__":
        doc_lengths[doc_id] = int(value)
    elif key == "__DOC_ID__":
        doc_ids_set.add(doc_id)
    else:
        term = key
        count = int(value)
        if term not in term_index:
            term_index[term] = {}
        term_index[term][doc_id] = term_index[term].get(doc_id, 0) + count

total_docs = len(doc_ids_set)
avg_doc_length = (
    sum(doc_lengths.get(d, 0) for d in doc_ids_set) / total_docs if total_docs else 0.0
)

session.execute(
    "INSERT INTO stats (key, value) VALUES (%s, %s)", ("totalDocs", float(total_docs))
)
session.execute(
    "INSERT INTO stats (key, value) VALUES (%s, %s)",
    ("avgDocLength", float(avg_doc_length)),
)

doc_stmt = session.prepare(
    "INSERT INTO documents (doc_id, doc_length, title) VALUES (?, ?, ?)"
)

batch = BatchStatement(consistency_level=ConsistencyLevel.ONE)
for i, doc_id in enumerate(doc_ids_set, 1):
    batch.add(doc_stmt, (doc_id, doc_lengths.get(doc_id, 0), titles.get(doc_id, "")))
    if i % BATCH_SIZE == 0:
        session.execute(batch)
        batch.clear()
if batch:
    session.execute(batch)

vocab_stmt = session.prepare("INSERT INTO vocabulary (term, df, idf) VALUES (?, ?, ?)")
index_stmt = session.prepare(
    "INSERT INTO inverted_index (term, doc_id, tf) VALUES (?, ?, ?)"
)

batch_vocab = BatchStatement(consistency_level=ConsistencyLevel.ONE)
batch_index = BatchStatement(consistency_level=ConsistencyLevel.ONE)

vocab_count = 0
index_count = 0

for term, doc_freqs in term_index.items():
    df = len(doc_freqs)
    idf = math.log((total_docs + 1.0) / (df + 1.0)) if df else 0.0

    batch_vocab.add(vocab_stmt, (term, df, idf))
    vocab_count += 1
    if vocab_count % BATCH_SIZE == 0:
        session.execute(batch_vocab)
        batch_vocab.clear()

    for doc_id, tf in doc_freqs.items():
        batch_index.add(index_stmt, (term, doc_id, tf))
        index_count += 1
        if index_count % BATCH_SIZE == 0:
            session.execute(batch_index)
            batch_index.clear()

if batch_vocab:
    session.execute(batch_vocab)
if batch_index:
    session.execute(batch_index)
