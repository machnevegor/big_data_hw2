#!/bin/bash

set -e

# --- CONFIG --- #

STAGE=index

INPUT_PATH=${1:-/index/data}
HDFS_OUTPUT=/tmp/index

MAPPER=mapreduce/mapper1.py
REDUCER=mapreduce/reducer1.py

CASSANDRA_DIR=cassandra_lib
CASSANDRA_ZIP=$CASSANDRA_DIR.zip

# --- LOGGER --- #

log() {
  echo "[$STAGE] $1"
}

# --- ENV SETUP --- #

log "✋ Activating virtual environment..."
source .venv/bin/activate

# --- PREPARE CASSANDRA LIB --- #

log "✋ Preparing cassandra-driver package..."
if [[ ! -f $CASSANDRA_ZIP ]]; then
  mkdir -p $CASSANDRA_DIR
  pip install cassandra-driver -t $CASSANDRA_DIR
  (cd $CASSANDRA_DIR && zip -qr ../$CASSANDRA_ZIP .)
  rm -rf $CASSANDRA_DIR
  log "🫱 $CASSANDRA_ZIP created"
else
  log "🫱 $CASSANDRA_ZIP already exists"
fi

# --- LOCATE HADOOP STREAMING --- #

log "✋ Locating Hadoop Streaming JAR..."
HADOOP_STREAMING_JAR=$(find /usr/lib /opt /usr/local -name hadoop-streaming*.jar 2>/dev/null | head -n 1)
if [[ -z $HADOOP_STREAMING_JAR ]]; then
  log "❌ Hadoop Streaming JAR not found — aborting"
  exit 1
fi
log "🫱 Found: $HADOOP_STREAMING_JAR"

# --- RUN PYTHON APP --- #

log "✋ Running pre-index Python app..."
python app.py
log "🫱 app.py execution complete"

# --- MAPREDUCE --- #

log "🫳 Removing previous HDFS output (if any)..."
hdfs dfs -rm -r -f $HDFS_OUTPUT || true
log "🫱 Old HDFS output cleared"

log "✋ Starting Hadoop Streaming job..."
hadoop jar $HADOOP_STREAMING_JAR \
  -input $INPUT_PATH \
  -output $HDFS_OUTPUT \
  -mapper $MAPPER \
  -reducer $REDUCER \
  -file $MAPPER \
  -file $REDUCER \
  -file $CASSANDRA_ZIP
log "🤝 Hadoop job completed successfully"
