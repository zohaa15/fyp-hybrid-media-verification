import numpy as np
from src.clip_image_similarity import extract_clip_image_features, cosine_similarity
from src.database_mac import verify_database_mac


INDEX_PATH = "trusted_assets/clip_image_features.npz"


def load_clip_feature_index(index_path):
    data = np.load(index_path, allow_pickle=True)

    return {
        "asset_ids": data["asset_ids"],
        "filenames": data["filenames"],
        "original_paths": data["original_paths"],
        "provenance_statuses": data["provenance_statuses"],
        "feature_vectors": data["feature_vectors"]
    }


def find_best_clip_match_from_index(query_image_path, index_path):
    print("Verifying database integrity before indexed CLIP matching...")

    if not verify_database_mac():
        print("Aborting indexed CLIP matching because database integrity verification failed.")
        return None, []

    index_data = load_clip_feature_index(index_path)
    query_features = extract_clip_image_features(query_image_path)

    best_match = None
    best_score = -1.0
    all_results = []

    for i in range(len(index_data["asset_ids"])):
        asset_id = index_data["asset_ids"][i]
        filename = index_data["filenames"][i]
        original_path = index_data["original_paths"][i]
        provenance_status = index_data["provenance_statuses"][i]
        trusted_features = index_data["feature_vectors"][i]

        score = cosine_similarity(query_features, trusted_features)

        result = {
            "asset_id": asset_id,
            "filename": filename,
            "original_path": original_path,
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

    best_match, all_results = find_best_clip_match_from_index(query_image, INDEX_PATH)

    print("\nQuery image:", query_image)

    if best_match is not None:
        print("Best match asset ID:", best_match["asset_id"])
        print("Best match filename:", best_match["filename"])
        print("Best match original path:", best_match["original_path"])
        print("Best cosine similarity:", best_match["score"])
        print("Provenance status:", best_match["provenance_status"])
    else:
        print("No valid indexed image matches found.")

    if all_results:
        print("\nAll similarity scores:")
        for result in sorted(all_results, key=lambda x: x["score"], reverse=True):
            print(f'{result["asset_id"]} | {result["filename"]}: {result["score"]:.6f}')