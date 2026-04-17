import os
import sqlite3

DB_FOLDER = "trusted_assets"
DB_PATH = os.path.join(DB_FOLDER, "metadata.db")

os.makedirs(DB_FOLDER, exist_ok=True)


def initialise_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trusted_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT UNIQUE,
            filename TEXT,
            media_type TEXT,
            original_path TEXT,
            signed_path TEXT,
            provenance_status TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_trusted_asset(asset_id, filename, media_type, original_path, signed_path, provenance_status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO trusted_assets (
            asset_id,
            filename,
            media_type,
            original_path,
            signed_path,
            provenance_status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        asset_id,
        filename,
        media_type,
        original_path,
        signed_path,
        provenance_status
    ))

    conn.commit()
    conn.close()