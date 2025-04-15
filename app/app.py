import logging

from cassandra import InvalidRequest
from cassandra.cluster import Cluster

# --- CONFIG --- #

STAGE = "init_cassandra"

KEYSPACE = "search_index"
TABLES = {
    "inverted_index": """
        CREATE TABLE inverted_index (
            term TEXT,
            doc_id INT,
            tf INT,
            PRIMARY KEY (term, doc_id)
        )
    """,
    "documents": """
        CREATE TABLE documents (
            doc_id INT PRIMARY KEY,
            doc_length INT,
            title TEXT
        )
    """,
    "stats": """
        CREATE TABLE stats (
            key TEXT PRIMARY KEY,
            value DOUBLE
        )
    """,
    "vocabulary": """
        CREATE TABLE vocabulary (
            term TEXT PRIMARY KEY,
            df INT,
            idf DOUBLE
        )
    """,
}

# --- LOGGER --- #

logging.basicConfig(level=logging.INFO, format=f"[{STAGE}] %(message)s")
log = logging.getLogger(__name__)

# --- CONNECTION --- #

log.info("👋 Connecting to Cassandra...")

try:
    cluster = Cluster(["cassandra-server"])
    session = cluster.connect()
    log.info("🫱 Connected successfully")
except Exception as e:
    log.error(f"❌ Connection failed: {e}")
    exit(1)

# --- KEYSPACE --- #

try:
    log.info(f"📦 Creating keyspace '{KEYSPACE}' (if not exists)...")
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': 1 }}
    """)
    session.set_keyspace(KEYSPACE)
    log.info("🫱 Keyspace ready")
except Exception as e:
    log.error(f"❌ Failed to create/use keyspace: {e}")
    exit(1)

# --- TABLES (DROP + CREATE) --- #

for name, ddl in TABLES.items():
    try:
        log.info(f"🧹 Dropping table '{name}' if exists...")
        session.execute(f"DROP TABLE IF EXISTS {name}")
        log.info("🫱 Table dropped")

        log.info(f"🛠️ Creating table '{name}'...")
        session.execute(ddl)
        log.info(f"🫱 Table '{name}' created")
    except InvalidRequest as e:
        log.error(f"❌ Error with table '{name}': {e}")
        exit(1)

# --- DONE --- #

log.info("🤝 All Cassandra structures are initialized successfully")
