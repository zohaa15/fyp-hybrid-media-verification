import os
import json
import subprocess
import streamlit as st
from config import TMK_HASH_EXE, FFMPEG_EXE
from src.database import initialise_database
from src.clip_image_index_matcher import find_best_clip_match_from_index
from src.image_similarity import extract_image_features
from src.tmk_pdqf_video_similarity import find_best_tmk_match, make_tmk_match_decision

initialise_database()

st.title("Hybrid Media Verification System")
st.write("Drag and drop an image or video file below, or click to browse.")

UPLOAD_FOLDER = "uploads"
QUERY_VIDEO_HASH_FOLDER = "video_hashes/query"
CLIP_INDEX_PATH = "trusted_assets/clip_image_features.npz"


IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv"]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QUERY_VIDEO_HASH_FOLDER, exist_ok=True)


def detect_media_type(filename):
    ext = os.path.splitext(filename)[1].lower()

    if ext in IMAGE_EXTENSIONS:
        return "image"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    else:
        return "unsupported"


def run_c2pa_check(file_path):
    try:
        result = subprocess.run(
            ["c2patool", file_path],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "data": data,
                    "raw_output": result.stdout
                }
            except json.JSONDecodeError:
                return {
                    "status": "non_json_output",
                    "data": None,
                    "raw_output": result.stdout
                }

        error_text = result.stderr.strip()

        if "No claim found" in error_text:
            return {
                "status": "no_claim",
                "data": None,
                "raw_output": error_text
            }

        return {
            "status": "error",
            "data": None,
            "raw_output": error_text
        }

    except FileNotFoundError:
        return {
            "status": "not_installed",
            "data": None,
            "raw_output": "c2patool was not found in PATH."
        }


def classify_c2pa_result(c2pa_result):
    if c2pa_result["status"] == "success":
        data = c2pa_result["data"]

        if not data or "manifests" not in data or len(data["manifests"]) == 0:
            return "No provenance metadata found"

        validation_state = data.get("validation_state", "")

        if validation_state == "Valid":
            return "Provenance metadata found"
        elif validation_state == "Invalid":
            return "Provenance metadata found, but validation issues detected"
        else:
            return "Provenance metadata found"

    elif c2pa_result["status"] == "no_claim":
        return "No provenance metadata found"

    else:
        return "C2PA check failed"


def extract_c2pa_summary(c2pa_result):
    if c2pa_result["status"] != "success" or not c2pa_result["data"]:
        return None

    data = c2pa_result["data"]
    active_manifest = data.get("active_manifest", "Not available")
    validation_state = data.get("validation_state", "Not available")
    manifests = data.get("manifests", {})

    title = "Not available"
    issuer = "Not available"
    signer_name = "Not available"

    if active_manifest in manifests:
        manifest_data = manifests[active_manifest]
        title = manifest_data.get("title", "Not available")

        signature_info = manifest_data.get("signature_info", {})
        issuer = signature_info.get("issuer", "Not available")
        signer_name = signature_info.get("common_name", "Not available")

    return {
        "Active Manifest": active_manifest,
        "Title": title,
        "Validation State": validation_state,
        "Issuer": issuer,
        "Signer Common Name": signer_name
    }


def determine_next_action(provenance_status):
    if provenance_status == "Provenance metadata found":
        return "Proceed to similarity matching as part of hybrid verification"
    elif provenance_status == "No provenance metadata found":
        return "Proceed to similarity matching"
    elif provenance_status == "Provenance metadata found, but validation issues detected":
        return "Proceed to similarity matching"
    else:
        return "Provenance check unsuccessful - similarity matching will still be attempted"


def run_clip_image_match(query_image_path):
    best_match, all_results = find_best_clip_match_from_index(
        query_image_path,
        CLIP_INDEX_PATH
    )
    return best_match, all_results


def generate_query_video_tmk(video_path):
    try:
        result = subprocess.run(
            [
                TMK_HASH_EXE,
                "-f", FFMPEG_EXE,
                "-i", video_path,
                "-d", QUERY_VIDEO_HASH_FOLDER
            ],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return {
                "status": "error",
                "raw_output": result.stderr if result.stderr else result.stdout,
                "tmk_path": None
            }

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        tmk_path = os.path.join(QUERY_VIDEO_HASH_FOLDER, f"{video_name}.tmk")

        if os.path.exists(tmk_path):
            return {
                "status": "success",
                "raw_output": result.stdout,
                "tmk_path": tmk_path
            }

        return {
            "status": "error",
            "raw_output": "TMK file was not created.",
            "tmk_path": None
        }

    except Exception as e:
        return {
            "status": "error",
            "raw_output": str(e),
            "tmk_path": None
        }


def get_best_match_video_path(best_match):
    """
    Convert a matched trusted TMK path into the corresponding trusted video path.
    Example:
        video_hashes/trusted/street_original.tmk
        -> trusted_assets/videos/street_original.mp4
    """
    if best_match is None:
        return None

    trusted_tmk_path = best_match.get("trusted_tmk")
    if not trusted_tmk_path:
        return None

    tmk_filename = os.path.basename(trusted_tmk_path)
    video_filename = os.path.splitext(tmk_filename)[0] + ".mp4"
    video_path = os.path.join("trusted_assets", "videos", video_filename)

    if os.path.exists(video_path):
        return video_path

    return None


uploaded_file = st.file_uploader(
    "Upload an image or video",
    help="Accepted formats: JPG, JPEG, PNG, MP4, MOV, AVI, MKV."
)

if uploaded_file is not None:
    media_type = detect_media_type(uploaded_file.name)

    if media_type == "unsupported":
        st.error(
            "Error: Unsupported file type. Please upload a JPG, JPEG, PNG, MP4, MOV, AVI, or MKV file."
        )
        st.stop()

    save_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    file_size_kb = round(uploaded_file.size / 1024, 2)

    st.success(f"File uploaded successfully: {uploaded_file.name}")
    st.write(f"Saved to: {save_path}")
    st.write(f"Detected media type: **{media_type}**")

    st.subheader("File Metadata")
    st.write(f"**Filename:** {uploaded_file.name}")
    st.write(f"**Extension:** {file_extension}")
    st.write(f"**Size:** {file_size_kb} KB")

    if media_type == "image":
        st.image(save_path, caption="Uploaded image preview", use_container_width=True)

        st.subheader("Feature Extraction")
        features = extract_image_features(save_path)

        st.write(f"Feature vector length: {len(features)}")
        st.write(f"Feature vector shape: {features.shape}")
        st.write("Feature vector preview (first 10 values):")
        st.write(features[:10])

    elif media_type == "video":
        st.video(save_path)

    st.subheader("C2PA Inspection")

    if st.button("Run Hybrid Verification"):
        c2pa_result = run_c2pa_check(save_path)
        provenance_status = classify_c2pa_result(c2pa_result)
        c2pa_summary = extract_c2pa_summary(c2pa_result)
        next_action = determine_next_action(provenance_status)

        clip_best_match = None
        clip_all_results = []

        video_tmk_result = None
        best_match = None
        all_results = []
        video_decision = None

        # Always run similarity matching for hybrid verification
        if media_type == "image":
            clip_best_match, clip_all_results = run_clip_image_match(save_path)

        elif media_type == "video":
            video_tmk_result = generate_query_video_tmk(save_path)

            if video_tmk_result["status"] == "success":
                query_tmk_path = video_tmk_result["tmk_path"]
                trusted_tmk_dir = "video_hashes/trusted"

                best_match, all_results = find_best_tmk_match(
                    query_tmk_path,
                    trusted_tmk_dir
                )

                video_decision = make_tmk_match_decision(
                    best_match,
                    level_2_threshold=0.7
                )

        st.subheader("Provenance Status")
        if provenance_status == "Provenance metadata found":
            st.success(provenance_status)
        elif provenance_status == "No provenance metadata found":
            st.warning(provenance_status)
        elif provenance_status == "Provenance metadata found, but validation issues detected":
            st.warning(provenance_status)
        else:
            st.error(provenance_status)

        st.subheader("Next Action")
        st.write(next_action)

        if c2pa_summary:
            st.subheader("C2PA Summary")
            for key, value in c2pa_summary.items():
                st.write(f"**{key}:** {value}")

        st.subheader("C2PA Raw Output")
        if c2pa_result["status"] == "success":
            st.json(c2pa_result["data"])
        else:
            st.text(c2pa_result["raw_output"])

        if clip_best_match is not None:
            st.subheader("Similarity Matching Result (CLIP)")
            st.write(f"**Best Match Asset ID:** {clip_best_match['asset_id']}")
            st.write(f"**Filename:** {clip_best_match['filename']}")
            st.write(f"**Cosine Similarity:** {round(clip_best_match['score'], 6)}")
            st.write(f"**Provenance Status:** {clip_best_match['provenance_status']}")

            st.image(
                clip_best_match["original_path"],
                caption="Best matched trusted image",
                use_container_width=True
            )

            st.subheader("Top CLIP Candidates")
            for result in clip_all_results[:5]:
                st.write(
                    f"{result['filename']} | "
                    f"Score: {result['score']:.6f} | "
                    f"Asset ID: {result['asset_id']}"
                )

        if media_type == "video":
            st.subheader("Video Similarity Result (TMK + PDQF)")

            if video_tmk_result is not None and video_tmk_result["status"] == "success":
                st.success("Query video TMK features extracted successfully.")
                st.write(f"**Generated TMK file:** {video_tmk_result['tmk_path']}")

                if best_match is not None:
                    best_filename = os.path.basename(best_match["trusted_tmk"])
                    matched_video_path = get_best_match_video_path(best_match)

                    st.write(f"**Best Match:** {best_filename}")
                    st.write(f"**Level-1 Score:** {best_match['level_1_score']:.6f}")
                    st.write(f"**Level-2 Score:** {best_match['level_2_score']:.6f}")

                    if video_decision is not None:
                        st.write(f"**Decision:** {video_decision['decision']}")
                        st.write(f"**Reason:** {video_decision['reason']}")

                    st.subheader("Top TMK Query Candidates")
                    for result in all_results[:5]:
                        candidate_name = os.path.basename(result["trusted_tmk"])
                        st.write(
                            f"{candidate_name} | "
                            f"Level-1: {result['level_1_score']:.6f} | "
                            f"Level-2: {result['level_2_score']:.6f}"
                        )

                    if matched_video_path is not None:
                        st.video(matched_video_path)
                else:
                    st.warning("No trusted video candidates were returned by the TMK query process.")

            elif video_tmk_result is not None and video_tmk_result["status"] == "error":
                st.error("Failed to extract TMK features from uploaded video.")
                st.text(video_tmk_result["raw_output"])