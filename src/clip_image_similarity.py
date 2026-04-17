import os
import sqlite3
import torch
import clip
import numpy as np
from PIL import Image
from src.database_mac import verify_database_mac


device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()


def extract_clip_image_features(image_path):
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)

    with torch.no_grad():
        features = model.encode_image(image)

    features = features.cpu().numpy().flatten()
    return features


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = np.dot(vec1, vec2) / (norm1 * norm2)
    return float(similarity)


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


def find_best_clip_match_from_db(query_image_path, db_path):
    print("Verifying database integrity before CLIP matching...")

    if not verify_database_mac():
        print("Aborting CLIP matching because database integrity verification failed.")
        return None, []

    query_features = extract_clip_image_features(query_image_path)
    registered_images = get_registered_image_assets(db_path)

    best_match = None
    best_score = -1.0
    all_results = []

    for asset_id, filename, original_path, signed_path, provenance_status in registered_images:
        trusted_image_path = os.path.normpath(original_path)

        if not os.path.exists(trusted_image_path):
            print(f"Warning: File not found for {filename}: {trusted_image_path}")
            continue

        trusted_features = extract_clip_image_features(trusted_image_path)
        score = cosine_similarity(query_features, trusted_features)

        result = {
            "asset_id": asset_id,
            "filename": filename,
            "original_path": trusted_image_path,
            "signed_path": signed_path,
            "provenance_status": provenance_status,
            "score": score
        }

        all_results.append(result)

        if score > best_score:
            best_score = score
            best_match = result

    return best_match, all_results


if __name__ == "__main__":
    query_image = "trusted_assets/images/cat_original_signed.jpg"
    db_path = "trusted_assets/metadata.db"

    best_match, all_results = find_best_clip_match_from_db(query_image, db_path)

    print("\nQuery image:", query_image)

    if best_match is not None:
        print("Best match asset ID:", best_match["asset_id"])
        print("Best match filename:", best_match["filename"])
        print("Best match original path:", best_match["original_path"])
        print("Best cosine similarity:", best_match["score"])
        print("Provenance status:", best_match["provenance_status"])
    else:
        print("No valid image matches found, or database integrity verification failed.")

    if all_results:
        print("\nAll similarity scores:")
        for result in sorted(all_results, key=lambda x: x["score"], reverse=True):
            print(f'{result["asset_id"]} | {result["filename"]}: {result["score"]:.6f}')