#!/usr/bin/env python3
"""Build the game dictionary from SCOWL, COCA, and WordNet.

Usage:
    python backend/scripts/build_dictionary.py

Output:
    backend/data/dictionary.bin
"""

import pickle
import re
from dataclasses import dataclass, field
from pathlib import Path

# Ensure WordNet is downloaded
try:
    import nltk
    from nltk.corpus import wordnet as wn

    wn.synsets("test")
except (ImportError, LookupError):
    import nltk

    nltk.download("wordnet")
    nltk.download("omw-1.4")
    from nltk.corpus import wordnet as wn

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_PATH = DATA_DIR / "dictionary.bin"

# Configuration
MIN_WORD_LENGTH = 3
MAX_COCA_RANK = 30_000  # Only include words in top 30K by frequency


@dataclass
class TrieNode:
    """Node in the dictionary trie."""

    children: dict[str, "TrieNode"] = field(default_factory=dict)
    is_word: bool = False
    definition: str | None = None


class DictionaryBuilder:
    """Build a trie-based dictionary from word sources."""

    def __init__(self) -> None:
        """Initialize the builder."""
        self.root = TrieNode()
        self.word_count = 0

    def add_word(self, word: str, definition: str | None = None) -> None:
        """Add a word to the trie."""
        node = self.root
        for char in word.upper():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True
        node.definition = definition
        self.word_count += 1

    def serialize(self, path: Path) -> None:
        """Serialize the trie to a binary file."""
        with Path(path).open("wb") as f:
            pickle.dump(self.root, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"Serialized {self.word_count} words to {path}")


def load_word_list(path: Path) -> set[str]:
    """Load words from a simple word list file (one word per line).

    Args:
        path: Path to the word list file.

    Returns:
        Set of lowercase words.
    """
    words = set()
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word and re.match(r"^[a-z]+$", word):
                words.add(word)
    return words


def load_coca_frequencies(path: Path) -> dict[str, int]:
    """Load COCA word frequency ranks.

    Args:
        path: Path to the COCA frequency file.

    Returns:
        Dictionary mapping words to their frequency rank.
    """
    frequencies: dict[str, int] = {}
    if not path.exists():
        print(f"Warning: COCA file not found at {path}")
        print("Proceeding without frequency filtering...")
        return frequencies

    with Path(path).open(encoding="utf-8") as f:
        for rank, line in enumerate(f, start=1):
            parts = line.strip().split(",")
            if parts:
                word = parts[0].lower().strip()
                if word:
                    frequencies[word] = rank
    return frequencies


def load_blocklist(path: Path) -> set[str]:
    """Load profanity blocklist.

    Args:
        path: Path to the blocklist file.

    Returns:
        Set of lowercase blocked words.
    """
    if not path.exists():
        print(f"Warning: Blocklist not found at {path}")
        return set()

    with Path(path).open(encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def get_wordnet_definition(word: str) -> str | None:
    """Get the primary WordNet definition for a word.

    Args:
        word: The word to look up.

    Returns:
        The definition string, or None if not found.
    """
    synsets = wn.synsets(word)
    if synsets:
        return synsets[0].definition()
    return None


def build_dictionary() -> None:
    """Execute the full dictionary build pipeline.

    Raises:
        FileNotFoundError: If word list file is not found.
    """
    print("=== Dictionary Build Pipeline ===\n")

    # Step 1: Load word list
    word_list_path = RAW_DIR / "english-words.txt"
    if not word_list_path.exists():
        message = f"Word list file not found at {word_list_path}. Run download_sources.py first."
        raise FileNotFoundError(message)

    print("Step 1: Loading word list...")
    source_words = load_word_list(word_list_path)
    print(f"  Loaded {len(source_words)} raw words")

    # Step 2: Filter by length
    print(f"\nStep 2: Filtering words < {MIN_WORD_LENGTH} letters...")
    words = {w for w in source_words if len(w) >= MIN_WORD_LENGTH}
    print(f"  Remaining: {len(words)} words")

    # Step 3: Filter by COCA frequency (if available)
    print("\nStep 3: Filtering by COCA frequency...")
    coca_path = RAW_DIR / "coca-frequencies.csv"
    coca_freqs = load_coca_frequencies(coca_path)

    if coca_freqs:
        words = {w for w in words if coca_freqs.get(w, MAX_COCA_RANK + 1) <= MAX_COCA_RANK}
        print(f"  Remaining: {len(words)} words (top {MAX_COCA_RANK} frequency)")
    else:
        print("  Skipped (no COCA data)")

    # Step 4: Remove blocklisted words
    print("\nStep 4: Removing blocklisted words...")
    blocklist_path = RAW_DIR / "blocklist.txt"
    blocklist = load_blocklist(blocklist_path)
    words -= blocklist
    print(f"  Remaining: {len(words)} words")

    # Step 5: Enrich with WordNet definitions
    print("\nStep 5: Enriching with WordNet definitions...")
    builder = DictionaryBuilder()
    words_with_defs = 0

    for word in sorted(words):
        definition = get_wordnet_definition(word)
        builder.add_word(word, definition)
        if definition:
            words_with_defs += 1

    print(f"  Words with definitions: {words_with_defs}/{len(words)}")

    # Step 6: Serialize
    print("\nStep 6: Serializing trie...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    builder.serialize(OUTPUT_PATH)

    print("\n=== Build Complete ===")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total words: {builder.word_count}")


if __name__ == "__main__":
    build_dictionary()
