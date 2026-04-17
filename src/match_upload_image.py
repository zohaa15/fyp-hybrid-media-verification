import os
import numpy as np

from image_similarity import extract_image_features


IMAGE_FEATURES_FILE = "trusted_features/image_features.npz"


def compute_euclidean_distance(vec1, vec2):
    return np.linalg.norm(vec1 - vec2)


def match_uploaded_image(uploaded_image_path):
    if not os.path.exists(IMAGE_FEATURES_FILE):
        raise FileNotFoundError(f"Feature index not found: {IMAGE_FEATURES_FILE}")

    feature_index = np.load(IMAGE_FEATURES_FILE)

    uploaded_features = extract_image_features(uploaded_image_path)

    results = []

    for asset_id in feature_index.files:
        trusted_features = feature_index[asset_id]
        distance = compute_euclidean_distance(uploaded_features, trusted_features)
        results.append((asset_id, distance))

    results.sort(key=lambda x: x[1])
    return results


if __name__ == "__main__":
    test_image = "test_images/human_compressed.jpg"   # replace this
    matches = match_uploaded_image(test_image)

    print("\nTop matches:")
    for asset_id, distance in matches[:5]:
        print(f"{asset_id}: distance={distance:.4f}")