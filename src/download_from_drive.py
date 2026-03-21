import os
import shutil
import time
from pathlib import Path
from dotenv import load_dotenv


# ==================================================
# CONFIG
# ==================================================
load_dotenv()

EXPORT_FILENAME = "grand_sud_monthly_features_v2.csv"
PROJECT_DATA_DIR = Path("data/processed")
DEST_PATH = PROJECT_DATA_DIR / EXPORT_FILENAME

# Prefer .env for this path:
# GDRIVE_SYNC_DIR=C:\Users\YourName\My Drive\gee_exports
GDRIVE_SYNC_DIR = Path(os.getenv("GDRIVE_SYNC_DIR", r"C:\Users\YourName\My Drive\gee_exports"))

MAX_WAIT_SECONDS = 1800
CHECK_INTERVAL = 15


def find_export_file():
    candidate = GDRIVE_SYNC_DIR / EXPORT_FILENAME
    if candidate.exists():
        return candidate

    matches = sorted(
        GDRIVE_SYNC_DIR.glob("*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for file in matches:
        if EXPORT_FILENAME.replace(".csv", "") in file.name:
            return file

    return None


def wait_for_file():
    start = time.time()

    if not GDRIVE_SYNC_DIR.exists():
        raise FileNotFoundError(
            f"Google Drive sync folder not found: {GDRIVE_SYNC_DIR}\n"
            "Set GDRIVE_SYNC_DIR correctly in your .env file."
        )

    print(f"Waiting for exported file in: {GDRIVE_SYNC_DIR}")

    while True:
        found = find_export_file()
        if found is not None:
            print(f"Found export file: {found}")
            return found

        elapsed = time.time() - start
        if elapsed > MAX_WAIT_SECONDS:
            raise TimeoutError(
                f"Timeout after {MAX_WAIT_SECONDS} seconds waiting for {EXPORT_FILENAME}"
            )

        print("File not found yet. Waiting...")
        time.sleep(CHECK_INTERVAL)


def copy_to_project(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"Copied file to project: {destination}")


def main():
    source_file = wait_for_file()
    copy_to_project(source_file, DEST_PATH)
    print("Download/copy step complete.")


if __name__ == "__main__":
    main()