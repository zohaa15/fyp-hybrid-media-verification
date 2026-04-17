import cv2
import numpy as np


def extract_image_features(image_path, size=(128, 128)):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    image = cv2.resize(image, size)
    image = image.astype("float32") / 255.0

    features = image.flatten()
    return features