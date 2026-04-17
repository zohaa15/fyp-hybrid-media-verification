import os
import sqlite3
import numpy as np
from clip_image_similarity import extract_clip_image_features
from database_mac import verify_database_mac


DB_PATH = "trusted_assets/metadata.db"
OUTPUT_INDEX_PATH = "trusted_assets/clip_image_features.npz"


def get_registered_image_assets(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT asset_id, filename, original_path, signed_path, provenance_status
        FROM trusted_assets
        WHERE media_type = 'image'
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def build_clip_feature_index():
    print("Verifying database integrity before building CLIP feature index...")

    if not verify_database_mac():
        print("Aborting index build because database integrity verification failed.")
        return

    registered_images = get_registered_image_assets(DB_PATH)

    asset_ids = []
    filenames = []
    original_paths = []
    provenance_statuses = []
    feature_vectors = []

    for asset_id, filename, original_path, signed_path, provenance_status in registered_images:
        image_path = os.path.normpath(original_path)

        if not os.path.exists(image_path):
            print(f"Skipping missing file: {image_path}")
            continue

        print(f"Extracting CLIP features for: {filename}")

        features = extract_clip_image_features(image_path)

        asset_ids.append(asset_id)
        filenames.append(filename)
        original_paths.append(image_path)
        provenance_statuses.append(provenance_status)
        feature_vectors.append(features)

    if not feature_vectors:
        print("No valid image features were extracted.")
        return

    feature_vectors = np.array(feature_vectors)

    np.savez(
        OUTPUT_INDEX_PATH,
        asset_ids=np.array(asset_ids),
        filenames=np.array(filenames),
        original_paths=np.array(original_paths),
        provenance_statuses=np.array(provenance_statuses),
        feature_vectors=feature_vectors
    )

    print("\nCLIP feature index built successfully.")
    print("Saved to:", OUTPUT_INDEX_PATH)
    print("Number of indexed images:", len(asset_ids))
    print("Feature matrix shape:", feature_vectors.shape)


if __name__ == "__main__":
    build_clip_feature_index()