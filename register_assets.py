import os
from src.database import initialise_database, insert_trusted_asset

initialise_database()

IMAGE_FOLDER = "trusted_assets/images"
VIDEO_FOLDER = "trusted_assets/videos"

print("Registering trusted assets...\n")

# -------- IMAGES --------
image_files = os.listdir(IMAGE_FOLDER)

asset_counter = 1

for file in image_files:
    if "_original." in file and "_signed" not in file:
        base_name = file.replace("_original", "")
        signed_name = file.replace("_original", "_original_signed")

        original_path = os.path.join(IMAGE_FOLDER, file)
        signed_path = os.path.join(IMAGE_FOLDER, signed_name)

        if os.path.exists(signed_path):
            asset_id = f"IMG_{asset_counter:03d}"

            insert_trusted_asset(
                asset_id=asset_id,
                filename=file,
                media_type="image",
                original_path=original_path,
                signed_path=signed_path,
                provenance_status="Provenance metadata found"
            )

            print(f"✔ Registered image: {asset_id} -> {file}")
            asset_counter += 1
        else:
            print(f"⚠ Missing signed version for: {file}")

# -------- VIDEOS --------
video_files = os.listdir(VIDEO_FOLDER)

video_counter = 1

for file in video_files:
    if "_original." in file and "_signed" not in file:
        signed_name = file.replace("_original", "_original_signed")

        original_path = os.path.join(VIDEO_FOLDER, file)
        signed_path = os.path.join(VIDEO_FOLDER, signed_name)

        if os.path.exists(signed_path):
            asset_id = f"VID_{video_counter:03d}"

            insert_trusted_asset(
                asset_id=asset_id,
                filename=file,
                media_type="video",
                original_path=original_path,
                signed_path=signed_path,
                provenance_status="Provenance metadata found"
            )

            print(f"✔ Registered video: {asset_id} -> {file}")
            video_counter += 1
        else:
            print(f"⚠ Missing signed version for: {file}")

print("\nRegistration complete.")