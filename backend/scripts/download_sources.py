#!/usr/bin/env python3
"""Download word list sources for dictionary building.

Usage:
    python backend/scripts/download_sources.py
"""

import urllib.request
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Use the english-words repository which has a clean word list
WORD_LIST_URL = "https://github.com/dwyl/english-words/raw/master/words_alpha.txt"


def download_word_list() -> None:
    """Download english word list.

    Raises:
        FileNotFoundError: If download fails.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / "english-words.txt"

    if output_path.exists():
        print(f"Word list already exists at {output_path}")
        return

    print(f"Downloading English word list to {output_path}...")
    print(f"Source: {WORD_LIST_URL}")

    try:
        urllib.request.urlretrieve(WORD_LIST_URL, output_path)
        print("Done.")
    except Exception as e:
        print(f"Error downloading: {e}")
        message = "Failed to download word list. You can download manually from: https://github.com/dwyl/english-words"
        raise FileNotFoundError(message) from e


def main() -> None:
    """Download all dictionary sources."""
    try:
        download_word_list()
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nAlternative: You can download a word list manually from:")
        print("  https://github.com/dwyl/english-words")
        print("\nPlace the file at: backend/data/raw/english-words.txt")
        return

    print("\nNote: COCA frequency data requires manual download.")
    print("Place coca-frequencies.csv in backend/data/raw/")


if __name__ == "__main__":
    main()
