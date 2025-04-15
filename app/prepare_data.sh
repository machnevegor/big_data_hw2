#!/bin/bash

set -e

# --- CONFIG --- #

STAGE=prepare_data

PARQUET_FILE=a.parquet
PARQUET_ZIP=${PARQUET_FILE}.zip
PARQUET_URL=https://www.kaggle.com/api/v1/datasets/download/jjinho/wikipedia-20230701?fileName=${PARQUET_FILE}

# --- LOGGER --- #

log() {
    echo "[${STAGE}] $1"
}

# --- ENV SETUP --- #

log "✋ Activating virtual environment..."
source .venv/bin/activate

log "✋ Setting PySpark environment variables..."
export PYSPARK_DRIVER_PYTHON=$(which python)
unset PYSPARK_PYTHON

# --- DOWNLOAD PARQUET --- #

log "✋ Checking for $PARQUET_FILE..."
if [[ ! -f $PARQUET_FILE ]]; then
    log "✋ Downloading $PARQUET_FILE from Kaggle..."
    curl -L -o $PARQUET_ZIP $PARQUET_URL
    unzip $PARQUET_ZIP
    rm $PARQUET_ZIP
    log "🫱 $PARQUET_FILE downloaded and extracted"
else
    log "🫱 $PARQUET_FILE already exists"
fi

# --- UPLOAD RAW DATA TO HDFS --- #

log "🫳 Uploading $PARQUET_FILE to HDFS..."
hdfs dfs -put -f $PARQUET_FILE /
log "🫱 $PARQUET_FILE uploaded to HDFS"

# --- DATA PREPARATION --- #

log "✋ Preparing data using Spark..."
spark-submit prepare_data.py
log "🫱 Data preparation complete"

# --- UPLOAD PROCESSED DATA TO HDFS --- #

log "🫳 Uploading processed data to HDFS..."
hdfs dfs -put -f data /
log "🫱 Processed data uploaded to HDFS"

log "👇 Listing HDFS directory: /data"
hdfs dfs -ls /data

log "👇 Listing HDFS directory: /index/data"
hdfs dfs -ls /index/data

log "🤝 All operations completed successfully"
