#!/usr/bin/env python3

import re
import sys

STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "while",
    "with",
    "without",
    "of",
    "at",
    "by",
    "for",
    "in",
    "on",
    "to",
    "from",
    "up",
    "down",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "can",
    "will",
    "just",
    "don",
    "should",
    "now",
}


def tokenize(text):
    """Split text into lowercase word tokens, ignoring non-word characters and stopwords."""
    tokens = re.split(r"\W+", text.lower())
    return [token for token in tokens if token and token not in STOPWORDS]


def process_line(line):
    """Process a single line of input and print formatted output."""
    line = line.strip()

    if not line:
        return

    parts = line.split("\t", 2)

    if len(parts) < 3:
        return

    doc_id_str, title, text = parts
    doc_id = int(doc_id_str)

    print(f"__TITLE__\t{doc_id}\t{title}")

    combined_text = f"{title} {text}"
    tokens = tokenize(combined_text)

    print(f"__DOC_LEN__\t{doc_id}\t{len(tokens)}")
    print(f"__DOC_ID__\t{doc_id}\t1")

    for token in tokens:
        print(f"{token}\t{doc_id}\t1")


for line in sys.stdin:
    process_line(line)
