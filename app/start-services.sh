#!/bin/bash

set -e

# --- CONFIG --- #

STAGE=start_services

# --- LOGGER --- #

log() {
    echo "[$STAGE] $1"
}

# --- START HADOOP SERVICES --- #

log "✋ Starting HDFS daemons..."
$HADOOP_HOME/sbin/start-dfs.sh
log "🫱 HDFS daemons started"

log "✋ Starting DataNode (explicitly)..."
$HADOOP_HOME/sbin/hadoop-daemon.sh start datanode
log "🫱 DataNode started"

log "✋ Starting YARN daemons..."
$HADOOP_HOME/sbin/start-yarn.sh
log "🫱 YARN daemons started"

log "✋ Starting MapReduce history server..."
mapred --daemon start historyserver
log "🫱 MapReduce history server started"

# --- SYSTEM CHECKS --- #

log "👇 Checking running JVM services"
jps -lm

log "👇 HDFS report:"
hdfs dfsadmin -report

log "✋ Exiting safemode if active..."
hdfs dfsadmin -safemode leave
log "🫱 Safemode exited or was not active"

# --- PREPARE SPARK JARS --- #

log "🫳 Creating HDFS directory for Spark JARs..."
hdfs dfs -mkdir -p /apps/spark/jars
hdfs dfs -chmod 744 /apps/spark/jars
log "🫱 Directory /apps/spark/jars ready"

log "🫳 Uploading Spark JARs to HDFS..."
hdfs dfs -put /usr/local/spark/jars/* /apps/spark/jars/
hdfs dfs -chmod +rx /apps/spark/jars/
log "🫱 Spark JARs uploaded to HDFS"

# --- FINAL CHECKS --- #

log "👇 Checking Scala version"
scala -version

log "👇 Final check of running JVM services"
jps -lm

# --- HDFS USER DIR --- #

log "🫳 Creating HDFS user directory: /user/root..."
hdfs dfs -mkdir -p /user/root
log "🫱 Directory /user/root created"

log "🤝 Cluster startup complete. All services are up!"
