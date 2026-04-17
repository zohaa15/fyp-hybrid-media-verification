import os
import sqlite3

DB_PATH = "trusted_assets/metadata.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT asset_id, original_path, signed_path FROM trusted_assets")
rows = cursor.fetchall()

print("Checking trusted asset file paths...\n")

all_valid = True

for row in rows:
    asset_id, original_path, signed_path = row

    original_exists = os.path.exists(original_path)
    signed_exists = os.path.exists(signed_path)

    print(f"Asset: {asset_id}")
    print(f"  Original exists: {original_exists} -> {original_path}")
    print(f"  Signed exists:   {signed_exists} -> {signed_path}")
    print()

    if not original_exists or not signed_exists:
        all_valid = False

if all_valid:
    print("✅ All trusted asset paths are valid.")
else:
    print("❌ Some paths are missing or incorrect.")

conn.close()