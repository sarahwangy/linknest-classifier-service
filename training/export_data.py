"""
Exports labeled bookmarks straight from Linknest's Neon Postgres database —
no Linknest API involved, this connects to the same DATABASE_URL directly.

Usage:
    export DATABASE_URL=postgres://...   # same value as linknest/.env.local
    python export_data.py
"""

import json
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

OUTPUT_PATH = Path(__file__).parent / "training-data.jsonl"

QUERY = """
    SELECT title, "ogDescription", "aiCategory"
    FROM "Bookmark"
    WHERE "aiCategory" IS NOT NULL
      AND "deletedAt" IS NULL
      AND title IS NOT NULL
"""


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("DATABASE_URL is not set — copy the value from linknest/.env.local")

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(QUERY)
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        sys.exit("No labeled bookmarks found — nothing to export.")

    with open(OUTPUT_PATH, "w") as f:
        for row in rows:
            f.write(
                json.dumps(
                    {
                        "title": row["title"],
                        "description": row["ogDescription"] or "",
                        "aiCategory": row["aiCategory"],
                    }
                )
                + "\n"
            )

    print(f"Exported {len(rows)} labeled bookmarks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
