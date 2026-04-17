import hmac
import hashlib
from pathlib import Path


SECRET_KEY = b"replace_this_with_a_long_random_secret_key"
DB_PATH = Path("trusted_assets/metadata.db")
MAC_PATH = Path("trusted_assets/metadata.db.mac")


def compute_file_hmac(file_path, secret_key):
    hmac_obj = hmac.new(secret_key, digestmod=hashlib.sha256)

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hmac_obj.update(chunk)

    return hmac_obj.hexdigest()


def generate_database_mac():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database file not found: {DB_PATH}")

    mac_value = compute_file_hmac(DB_PATH, SECRET_KEY)

    with open(MAC_PATH, "w") as f:
        f.write(mac_value)

    print("Database MAC generated successfully.")
    print("MAC value:", mac_value)


def verify_database_mac():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database file not found: {DB_PATH}")

    if not MAC_PATH.exists():
        raise FileNotFoundError(f"MAC file not found: {MAC_PATH}")

    current_mac = compute_file_hmac(DB_PATH, SECRET_KEY)

    with open(MAC_PATH, "r") as f:
        stored_mac = f.read().strip()

    if hmac.compare_digest(current_mac, stored_mac):
        print("Database integrity verified: MAC is valid.")
        return True
    else:
        print("WARNING: Database integrity check failed.")
        print("Stored MAC: ", stored_mac)
        print("Current MAC:", current_mac)
        return False


if __name__ == "__main__":
    print("1 = Generate MAC")
    print("2 = Verify MAC")
    choice = input("Choose an option: ").strip()

    if choice == "1":
        generate_database_mac()
    elif choice == "2":
        verify_database_mac()
    else:
        print("Invalid option.")