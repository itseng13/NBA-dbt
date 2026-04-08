"""
NBA Raw Ingestion: balldontlie API → Snowflake RAW schema
---------------------------------------------------------
Loads teams, players, games, and player stats into Snowflake
as VARIANT (JSON) columns in the RAW schema.

Usage:
    pip3 install requests snowflake-connector-python python-dotenv
    python3 load_raw.py

Environment variables (set in .env file):
    BDL_API_KEY         — balldontlie API key
    SF_ACCOUNT          — Snowflake account identifier (e.g. BUVOUSS-IZB53285)
    SF_USER             — Snowflake username
    SF_PASSWORD         — Snowflake password
    SF_WAREHOUSE        — e.g. COMPUTE_WH
    SF_ROLE             — e.g. ACCOUNTADMIN
"""

import os
import json
import time
import logging
from datetime import datetime, timezone

import requests
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

BDL_BASE_URL     = "https://api.balldontlie.io/v1"
BDL_HEADERS      = {"Authorization": os.environ["BDL_API_KEY"]}

SEASON           = 2024
PER_PAGE         = 100
RATE_LIMIT_DELAY = 5       # seconds between requests

SF_DATABASE = "NBA_DEV"
SF_SCHEMA   = "RAW"

SF_CONN_PARAMS = {
    "account":   os.environ["SF_ACCOUNT"],
    "user":      os.environ["SF_USER"],
    "password":  os.environ["SF_PASSWORD"],
    "warehouse": os.environ["SF_WAREHOUSE"],
    "role":      os.environ.get("SF_ROLE", "ACCOUNTADMIN"),
}


# ── API helpers ───────────────────────────────────────────────────────────────

def get_all_pages(endpoint: str, params: dict = None) -> list:
    params  = params or {}
    records = []
    cursor  = None

    while True:
        if cursor:
            params["cursor"] = cursor

        # Retry up to 5 times on 429 rate limit
        for attempt in range(5):
            response = requests.get(
                f"{BDL_BASE_URL}/{endpoint}",
                headers=BDL_HEADERS,
                params={**params, "per_page": PER_PAGE},
            )
            if response.status_code == 429:
                wait = 10 * (attempt + 1)
                log.warning(f"  Rate limited, waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                break

        response.raise_for_status()
        payload = response.json()

        batch = payload.get("data", [])
        records.extend(batch)
        log.info(f"  Fetched {len(batch)} records from /{endpoint} (total so far: {len(records)})")

        cursor = payload.get("meta", {}).get("next_cursor")
        if not cursor:
            break

        time.sleep(RATE_LIMIT_DELAY)

    return records


# ── Snowflake helpers ─────────────────────────────────────────────────────────

def get_snowflake_conn():
    return snowflake.connector.connect(**SF_CONN_PARAMS)


def use_context(cur):
    cur.execute(f"USE DATABASE {SF_DATABASE}")
    cur.execute(f"USE SCHEMA {SF_DATABASE}.{SF_SCHEMA}")


def setup_raw_tables(conn):
    tables = ["NBA_TEAMS", "NBA_PLAYERS", "NBA_GAMES", "NBA_PLAYER_STATS"]
    cur    = conn.cursor()
    use_context(cur)

    for table in tables:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                ID          NUMBER,
                RAW_DATA    VARIANT,
                _LOADED_AT  TIMESTAMP_NTZ DEFAULT SYSDATE()
            )
        """)
        log.info(f"Ensured table exists: {table}")

    cur.close()


def truncate_and_load(conn, table: str, records: list):
    cur       = conn.cursor()
    loaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    use_context(cur)
    cur.execute(f"TRUNCATE TABLE {table}")
    log.info(f"Truncated {table}")

    for rec in records:
        cur.execute(
            f"INSERT INTO {table} (ID, RAW_DATA, _LOADED_AT) "
            f"SELECT %s, PARSE_JSON(%s), %s",
            (rec["id"], json.dumps(rec), loaded_at)
        )

    conn.commit()
    log.info(f"Loaded {len(records)} rows into {table}")
    cur.close()


# ── Load functions ────────────────────────────────────────────────────────────

def load_teams(conn):
    log.info("Loading teams...")
    records = get_all_pages("teams")
    truncate_and_load(conn, "NBA_TEAMS", records)


def load_players(conn):
    log.info("Loading players...")
    records = get_all_pages("players")
    truncate_and_load(conn, "NBA_PLAYERS", records)


def load_games(conn):
    log.info(f"Loading games for season {SEASON}...")
    records = get_all_pages("games", params={"seasons[]": SEASON})
    truncate_and_load(conn, "NBA_GAMES", records)


def load_player_stats(conn):
    log.info(f"Loading player stats for season {SEASON}...")
    records = get_all_pages("stats", params={"seasons[]": SEASON})
    truncate_and_load(conn, "NBA_PLAYER_STATS", records)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("Starting NBA raw ingestion")
    conn = get_snowflake_conn()

    try:
        setup_raw_tables(conn)
        load_teams(conn)
        load_players(conn)
        load_games(conn)
        load_player_stats(conn)
        log.info("Raw ingestion complete ✓")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
