import os
import sqlite3
import numpy as np

from image_similarity import extract_image_features


DB_PATH = "trusted_assets/metadata.db"
FEATURES_DIR = "trusted_features"
IMAGE_FEATURES_FILE = os.path.join(FEATURES_DIR, "image_features.npz")


def build_image_feature_index():
    os.makedirs(FEATURES_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT asset_id, original_path
        FROM trusted_assets
        WHERE media_type = 'image'
    """)
    rows = cursor.fetchall()
    conn.close()

    feature_data = {}

    for asset_id, image_path in rows:
        if not image_path or not os.path.exists(image_path):
            print(f"Skipping missing file: {image_path}")
            continue

        try:
            features = extract_image_features(image_path)
            feature_data[asset_id] = features
            print(f"Processed {asset_id}: {image_path}")
        except Exception as e:
            print(f"Failed to process {image_path}: {e}")

    np.savez_compressed(IMAGE_FEATURES_FILE, **feature_data)
    print(f"\nSaved image features to: {IMAGE_FEATURES_FILE}")


if __name__ == "__main__":
    build_image_feature_index()