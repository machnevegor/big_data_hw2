#!/bin/bash

set -e

# --- CONFIG --- #

STAGE=query

CASSANDRA_DIR=cassandra_lib
CASSANDRA_ZIP=$CASSANDRA_DIR.zip

# --- LOGGER --- #

log() {
  echo "[$STAGE] $1"
}

# --- PREPARE CASSANDRA LIB --- #

if [[ ! -f $CASSANDRA_ZIP ]]; then
  log "✋ Preparing Cassandra driver..."
  mkdir -p $CASSANDRA_DIR
  pip install cassandra-driver -t $CASSANDRA_DIR
  (cd $CASSANDRA_DIR && zip -qr ../$CASSANDRA_ZIP .)
  rm -rf $CASSANDRA_DIR
  log "🫱 $CASSANDRA_ZIP created"
else
  log "🫱 $CASSANDRA_ZIP already exists"
fi

# --- RUN SPARK JOB --- #

log "✋ Exiting safemode if active..."
hdfs dfsadmin -safemode leave
log "🫱 Safemode exited or was not active"

log "✋ Running Spark job with query: $1..."
spark-submit \
  --master yarn \
  --files $CASSANDRA_ZIP \
  query.py "$1"
log "🤝 Query completed successfully"
