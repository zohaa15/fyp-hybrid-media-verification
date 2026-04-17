import os
import subprocess
import tempfile
from config import TMK_QUERY_EXE


def create_needle_file(query_tmk_path):
    """
    Create a temporary needle file containing only the uploaded query TMK path.
    Returns the temporary file path.
    """
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8")
    temp_file.write(query_tmk_path + "\n")
    temp_file.close()
    return temp_file.name


def create_haystack_file(trusted_tmk_dir):
    """
    Create a temporary haystack file containing all trusted TMK paths.
    Returns the temporary file path.
    """
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8")

    for filename in os.listdir(trusted_tmk_dir):
        if filename.lower().endswith(".tmk"):
            trusted_tmk_path = os.path.join(trusted_tmk_dir, filename)
            temp_file.write(trusted_tmk_path + "\n")

    temp_file.close()
    return temp_file.name


def parse_tmk_query_output(output_text):
    """
    Parse tmk-query output lines in the format:
    <level_1_score> <level_2_score> <query_tmk> <trusted_tmk>

    Returns a list of result dictionaries sorted by highest Level-2 score.
    """
    results = []

    for line in output_text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split(maxsplit=3)

        if len(parts) < 4:
            continue

        try:
            level_1_score = float(parts[0])
            level_2_score = float(parts[1])
            query_tmk = parts[2]
            trusted_tmk = parts[3]

            results.append({
                "level_1_score": level_1_score,
                "level_2_score": level_2_score,
                "query_tmk": query_tmk,
                "trusted_tmk": trusted_tmk,
                "matched": True,
                "raw_output": line
            })
        except ValueError:
            continue

    results.sort(key=lambda x: x["level_2_score"], reverse=True)
    return results


def run_tmk_query(query_tmk_path, trusted_tmk_dir):
    """
    Run needle-in-a-haystack TMK retrieval using tmk-query.exe.
    """
    needle_file = create_needle_file(query_tmk_path)
    haystack_file = create_haystack_file(trusted_tmk_dir)

    try:
        result = subprocess.run(
            [
                TMK_QUERY_EXE,
                "--c1", "-1",
                "--c2", "0",
                needle_file,
                haystack_file
            ],
            capture_output=True,
            text=True,
            check=False
        )

        output_text = result.stdout.strip()
        results = parse_tmk_query_output(output_text)

        return results

    finally:
        if os.path.exists(needle_file):
            os.remove(needle_file)
        if os.path.exists(haystack_file):
            os.remove(haystack_file)


def get_best_level_2_match(results):
    """
    Return the highest-scoring TMK query result based on Level-2 score.
    """
    if not results:
        return None

    return max(results, key=lambda x: x["level_2_score"])


def find_best_tmk_match(query_tmk_path, trusted_tmk_dir):
    """
    Run TMK needle-in-a-haystack retrieval and return:
    1. the best match
    2. the full ranked results list
    """
    results = run_tmk_query(query_tmk_path, trusted_tmk_dir)
    best_match = get_best_level_2_match(results)
    return best_match, results


def make_tmk_match_decision(best_match, level_2_threshold=0.7):
    """
    Convert the best TMK query result into a final match / no-match decision.
    """
    if best_match is None:
        return {
            "decision": "No match",
            "reason": "No trusted TMK candidates were returned by the query process."
        }

    if best_match["level_2_score"] >= level_2_threshold:
        return {
            "decision": "Match found",
            "reason": f"Level-2 score {best_match['level_2_score']:.6f} exceeded threshold {level_2_threshold:.2f}."
        }

    return {
        "decision": "No reliable match",
        "reason": f"Best Level-2 score {best_match['level_2_score']:.6f} did not exceed threshold {level_2_threshold:.2f}."
    }