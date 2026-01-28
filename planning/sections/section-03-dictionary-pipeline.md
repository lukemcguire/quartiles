# Section 03: Dictionary Building Pipeline

## Background

Quartiles requires a high-quality word dictionary for two purposes:

1. **Word validation** - Determining if a player's tile combination forms a valid English word
2. **Hint definitions** - Providing WordNet definitions as hints for unfound quartile words

The dictionary must be curated carefully. Using a raw word list (like SOWPODS) would include obscure "Scrabble words" that frustrate players (e.g., "qi", "xu", "qat"). Instead, we use SCOWL (Spell Checker Oriented Word Lists) filtered by COCA (Corpus of Contemporary American English) frequency data to ensure words are recognizable to the average player.

The dictionary is built at development time (not runtime) and serialized as a binary trie structure for fast loading (<50ms) and efficient prefix lookups.

## Dependencies

| Type | Section | Description |
|------|---------|-------------|
| **requires** | 01 | Codebase cleanup ensures pre-commit hooks pass |
| **blocks** | 04 | Game logic depends on the Dictionary class and data |

## Requirements

When this section is complete:

1. A reproducible pipeline downloads, filters, and enriches word data
2. The dictionary contains 15,000-35,000 common English words
3. Each word has an associated WordNet definition (where available)
4. The dictionary is serialized as a binary trie for fast loading
5. The `Dictionary` class provides efficient validation and prefix checking
6. Profanity and offensive words are explicitly excluded
7. All words are 3+ letters (no 1-2 letter words)
8. All scripts pass pre-commit checks

## Data Sources

### SCOWL (Primary Word List)

**URL:** https://github.com/en-wl/wordlist or http://wordlist.aspell.net/

**Recommended Size:** 60 (produces ~35,000 words)

| Size | Approximate Words | Description |
|------|-------------------|-------------|
| 35 | ~15,000 | Compact, very common words only |
| 50 | ~25,000 | Balanced for most uses |
| **60** | ~35,000 | **Recommended** - good coverage without obscurity |
| 70 | ~80,000 | Includes less common words |
| 80 | ~280,000 | Includes rare/archaic words |

**Download command:**
```bash
# Download SCOWL final word list (size 60, American English)
curl -L "https://raw.githubusercontent.com/en-wl/wordlist/master/alt12dicts/2of12inf.txt" \
  -o backend/data/raw/scowl-2of12.txt

# Alternative: Full SCOWL archive for more control
curl -L "http://downloads.sourceforge.net/wordlist/scowl-2020.12.07.tar.gz" \
  -o backend/data/raw/scowl.tar.gz
```

### COCA Frequency Data

**Purpose:** Filter out obscure words by keeping only those in the top 30,000 most frequently used words.

**Source:** Corpus of Contemporary American English word frequency list

**Format:** CSV or TSV with columns: `rank, word, frequency`

**Filtering threshold:** Words with frequency rank > 30,000 are excluded

### WordNet (Definitions)

**Library:** NLTK's WordNet corpus (or `wn` package for SQLite-backed performance)

**Installation:**
```bash
uv add nltk
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

**Usage:**
```python
from nltk.corpus import wordnet as wn

def get_definition(word: str) -> str | None:
    """Get the primary definition for a word."""
    synsets = wn.synsets(word)
    if synsets:
        return synsets[0].definition()
    return None
```

### Profanity Blocklist

**Purpose:** Explicitly exclude offensive words that may appear in SCOWL

**Strategy:** Maintain a curated blocklist file that is never committed (use `.gitignore`), or embed a minimal list in the build script.

**Recommended approach:** Use a community-maintained blocklist like `better-profanity` or create a minimal list of ~100-200 words.

## Implementation Details

### Directory Structure

```
backend/
├── data/
│   ├── raw/                    # Downloaded source files (gitignored)
│   │   ├── scowl-2of12.txt
│   │   └── coca-frequencies.csv
│   ├── dictionary.bin          # Serialized trie (committed)
│   └── blocklist.txt           # Profanity blocklist (gitignored)
├── scripts/
│   ├── download_sources.py     # Download SCOWL, COCA data
│   └── build_dictionary.py     # Main build pipeline
└── app/
    └── game/
        └── dictionary.py       # Dictionary class (load and query)
```

### Pipeline Steps

```
1. DOWNLOAD        2. FILTER           3. ENRICH           4. SERIALIZE
   SCOWL   ────►   Length >= 3  ────►  WordNet      ────►  Binary Trie
   COCA            COCA rank           definitions          dictionary.bin
                   < 30000
                   Not in blocklist
```

### Script: download_sources.py

```python
#!/usr/bin/env python3
"""Download word list sources for dictionary building.

Usage:
    python backend/scripts/download_sources.py
"""

import urllib.request
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

SOURCES = {
    "scowl": "https://raw.githubusercontent.com/en-wl/wordlist/master/alt12dicts/2of12inf.txt",
    # COCA requires academic access; use a freely available alternative
    # or manually download and place in raw/
}


def download_scowl() -> None:
    """Download SCOWL 2of12inf word list."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / "scowl-2of12.txt"

    if output_path.exists():
        print(f"SCOWL already exists at {output_path}")
        return

    print(f"Downloading SCOWL to {output_path}...")
    urllib.request.urlretrieve(SOURCES["scowl"], output_path)
    print("Done.")


def main() -> None:
    """Download all dictionary sources."""
    download_scowl()
    print("\nNote: COCA frequency data requires manual download.")
    print("Place coca-frequencies.csv in backend/data/raw/")


if __name__ == "__main__":
    main()
```

### Script: build_dictionary.py

```python
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

import nltk
from nltk.corpus import wordnet as wn

# Ensure WordNet is downloaded
try:
    wn.synsets("test")
except LookupError:
    nltk.download("wordnet")
    nltk.download("omw-1.4")

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
        with open(path, "wb") as f:
            pickle.dump(self.root, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"Serialized {self.word_count} words to {path}")


def load_scowl_words(path: Path) -> set[str]:
    """Load words from SCOWL 2of12inf format."""
    words = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            # 2of12inf format: word or word% (% indicates inflection)
            word = line.strip().rstrip("%").lower()
            if word and re.match(r"^[a-z]+$", word):
                words.add(word)
    return words


def load_coca_frequencies(path: Path) -> dict[str, int]:
    """Load COCA word frequency ranks."""
    frequencies: dict[str, int] = {}
    if not path.exists():
        print(f"Warning: COCA file not found at {path}")
        print("Proceeding without frequency filtering...")
        return frequencies

    with open(path, encoding="utf-8") as f:
        for rank, line in enumerate(f, start=1):
            parts = line.strip().split(",")
            if parts:
                word = parts[0].lower().strip()
                if word:
                    frequencies[word] = rank
    return frequencies


def load_blocklist(path: Path) -> set[str]:
    """Load profanity blocklist."""
    if not path.exists():
        print(f"Warning: Blocklist not found at {path}")
        return set()

    with open(path, encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def get_wordnet_definition(word: str) -> str | None:
    """Get the primary WordNet definition for a word."""
    synsets = wn.synsets(word)
    if synsets:
        return synsets[0].definition()
    return None


def build_dictionary() -> None:
    """Execute the full dictionary build pipeline."""
    print("=== Dictionary Build Pipeline ===\n")

    # Step 1: Load SCOWL words
    scowl_path = RAW_DIR / "scowl-2of12.txt"
    if not scowl_path.exists():
        raise FileNotFoundError(
            f"SCOWL file not found at {scowl_path}. "
            "Run download_sources.py first."
        )

    print("Step 1: Loading SCOWL words...")
    scowl_words = load_scowl_words(scowl_path)
    print(f"  Loaded {len(scowl_words)} raw words")

    # Step 2: Filter by length
    print(f"\nStep 2: Filtering words < {MIN_WORD_LENGTH} letters...")
    words = {w for w in scowl_words if len(w) >= MIN_WORD_LENGTH}
    print(f"  Remaining: {len(words)} words")

    # Step 3: Filter by COCA frequency (if available)
    print("\nStep 3: Filtering by COCA frequency...")
    coca_path = RAW_DIR / "coca-frequencies.csv"
    coca_freqs = load_coca_frequencies(coca_path)

    if coca_freqs:
        words = {
            w for w in words
            if coca_freqs.get(w, MAX_COCA_RANK + 1) <= MAX_COCA_RANK
        }
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

    print(f"\n=== Build Complete ===")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total words: {builder.word_count}")


if __name__ == "__main__":
    build_dictionary()
```

### Dictionary Class: dictionary.py

This file belongs in `backend/app/game/dictionary.py` and provides the runtime interface for word validation.

```python
"""Trie-based dictionary for word validation.

This module is part of the pure Python game logic layer.
It has NO dependencies on FastAPI, SQLModel, or Pydantic.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Default dictionary location (relative to this file)
DEFAULT_DICTIONARY_PATH = Path(__file__).parent.parent.parent / "data" / "dictionary.bin"


@dataclass
class TrieNode:
    """Node in the dictionary prefix tree."""

    children: dict[str, TrieNode] = field(default_factory=dict)
    is_word: bool = False
    definition: str | None = None


class Dictionary:
    """Trie-backed dictionary for efficient word validation.

    Supports:
    - O(k) word lookup where k = word length
    - O(k) prefix checking for early pruning
    - Definition retrieval for hints

    Example:
        dictionary = Dictionary.load()
        if dictionary.contains("QUARTER"):
            print(dictionary.get_definition("QUARTER"))
    """

    def __init__(self, root: TrieNode) -> None:
        """Initialize with a trie root node.

        Args:
            root: The root TrieNode of the dictionary trie.
        """
        self._root = root

    @classmethod
    def load(cls, path: Path | None = None) -> Dictionary:
        """Load dictionary from serialized binary file.

        Args:
            path: Path to dictionary.bin. Uses default if None.

        Returns:
            Loaded Dictionary instance.

        Raises:
            FileNotFoundError: If dictionary file doesn't exist.
        """
        path = path or DEFAULT_DICTIONARY_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"Dictionary not found at {path}. "
                "Run 'python backend/scripts/build_dictionary.py' first."
            )

        with open(path, "rb") as f:
            root = pickle.load(f)  # noqa: S301 - trusted data

        return cls(root)

    def _traverse(self, text: str) -> TrieNode | None:
        """Traverse the trie for a given text.

        Args:
            text: The text to traverse (will be uppercased).

        Returns:
            The TrieNode at the end of the path, or None if path doesn't exist.
        """
        node = self._root
        for char in text.upper():
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def contains(self, word: str) -> bool:
        """Check if word exists in dictionary.

        Args:
            word: The word to check (case-insensitive).

        Returns:
            True if word is a valid dictionary word.
        """
        node = self._traverse(word)
        return node is not None and node.is_word

    def contains_prefix(self, prefix: str) -> bool:
        """Check if any words start with the given prefix.

        This is crucial for pruning the search space during word finding.
        If a prefix doesn't exist, no extensions need to be explored.

        Args:
            prefix: The prefix to check (case-insensitive).

        Returns:
            True if at least one word starts with this prefix.
        """
        return self._traverse(prefix) is not None

    def get_definition(self, word: str) -> str | None:
        """Get the WordNet definition for a word.

        Args:
            word: The word to look up (case-insensitive).

        Returns:
            The definition string, or None if word not found or has no definition.
        """
        node = self._traverse(word)
        if node is not None and node.is_word:
            return node.definition
        return None

    def words_with_prefix(self, prefix: str) -> Iterator[str]:
        """Yield all words starting with the given prefix.

        Args:
            prefix: The prefix to match (case-insensitive).

        Yields:
            Words that start with the prefix.
        """
        node = self._traverse(prefix)
        if node is None:
            return

        prefix_upper = prefix.upper()

        def _collect(current_node: TrieNode, current_prefix: str) -> Iterator[str]:
            if current_node.is_word:
                yield current_prefix
            for char, child in current_node.children.items():
                yield from _collect(child, current_prefix + char)

        yield from _collect(node, prefix_upper)

    def __len__(self) -> int:
        """Return the total number of words in the dictionary."""
        count = 0

        def _count(node: TrieNode) -> int:
            nonlocal count
            if node.is_word:
                count += 1
            for child in node.children.values():
                _count(child)
            return count

        _count(self._root)
        return count
```

### Makefile Target

Add to the project Makefile:

```makefile
# Dictionary pipeline
.PHONY: download-sources build-dictionary

download-sources:
	python backend/scripts/download_sources.py

build-dictionary: download-sources
	python backend/scripts/build_dictionary.py
```

## Acceptance Criteria

- [ ] `backend/scripts/download_sources.py` exists and downloads SCOWL word list
- [ ] `backend/scripts/build_dictionary.py` exists and executes the full pipeline
- [ ] Pipeline filters words to 3+ letters only
- [ ] Pipeline integrates COCA frequency filtering (when data available)
- [ ] Pipeline excludes words from blocklist
- [ ] Pipeline enriches words with WordNet definitions
- [ ] `backend/data/dictionary.bin` is generated and committed
- [ ] `backend/app/game/dictionary.py` implements the `Dictionary` class
- [ ] `Dictionary.contains()` returns correct results
- [ ] `Dictionary.contains_prefix()` returns correct results
- [ ] `Dictionary.get_definition()` returns WordNet definitions
- [ ] Dictionary loads in <100ms
- [ ] All scripts pass `pre-commit run --all-files`
- [ ] Dictionary contains 15,000-35,000 words
- [ ] Unit tests exist for Dictionary class

## Files to Create

| File | Purpose |
|------|---------|
| `backend/data/raw/.gitkeep` | Placeholder for raw data directory |
| `backend/data/.gitignore` | Ignore raw/ directory contents |
| `backend/scripts/download_sources.py` | Download SCOWL and COCA data |
| `backend/scripts/build_dictionary.py` | Main build pipeline |
| `backend/app/game/dictionary.py` | Dictionary class implementation |
| `backend/app/game/tests/test_dictionary.py` | Unit tests for Dictionary |

## Files to Modify

| File | Change |
|------|--------|
| `Makefile` | Add `download-sources` and `build-dictionary` targets |
| `.gitignore` | Ensure `backend/data/raw/` is ignored |

## Test Cases

```python
# backend/app/game/tests/test_dictionary.py
"""Tests for the Dictionary class."""

import pytest

from backend.app.game.dictionary import Dictionary, TrieNode


class TestTrieNode:
    """Tests for TrieNode dataclass."""

    def test_default_values(self) -> None:
        """TrieNode initializes with correct defaults."""
        node = TrieNode()
        assert node.children == {}
        assert node.is_word is False
        assert node.definition is None


class TestDictionary:
    """Tests for Dictionary class."""

    @pytest.fixture
    def sample_dictionary(self) -> Dictionary:
        """Create a small dictionary for testing."""
        root = TrieNode()

        # Add "CAT"
        c_node = TrieNode()
        a_node = TrieNode()
        t_node = TrieNode(is_word=True, definition="A small feline")
        root.children["C"] = c_node
        c_node.children["A"] = a_node
        a_node.children["T"] = t_node

        # Add "CAR"
        r_node = TrieNode(is_word=True, definition="A vehicle")
        a_node.children["R"] = r_node

        # Add "CART"
        cart_t = TrieNode(is_word=True, definition="A wheeled vehicle")
        r_node.children["T"] = cart_t

        return Dictionary(root)

    def test_contains_existing_word(self, sample_dictionary: Dictionary) -> None:
        """contains() returns True for existing words."""
        assert sample_dictionary.contains("CAT") is True
        assert sample_dictionary.contains("CAR") is True
        assert sample_dictionary.contains("CART") is True

    def test_contains_case_insensitive(self, sample_dictionary: Dictionary) -> None:
        """contains() is case-insensitive."""
        assert sample_dictionary.contains("cat") is True
        assert sample_dictionary.contains("Cat") is True
        assert sample_dictionary.contains("CAT") is True

    def test_contains_nonexistent_word(self, sample_dictionary: Dictionary) -> None:
        """contains() returns False for non-words."""
        assert sample_dictionary.contains("DOG") is False
        assert sample_dictionary.contains("CA") is False  # Prefix, not word

    def test_contains_prefix_valid(self, sample_dictionary: Dictionary) -> None:
        """contains_prefix() returns True for valid prefixes."""
        assert sample_dictionary.contains_prefix("C") is True
        assert sample_dictionary.contains_prefix("CA") is True
        assert sample_dictionary.contains_prefix("CAT") is True
        assert sample_dictionary.contains_prefix("CAR") is True

    def test_contains_prefix_invalid(self, sample_dictionary: Dictionary) -> None:
        """contains_prefix() returns False for invalid prefixes."""
        assert sample_dictionary.contains_prefix("D") is False
        assert sample_dictionary.contains_prefix("CATS") is False

    def test_get_definition(self, sample_dictionary: Dictionary) -> None:
        """get_definition() returns correct definitions."""
        assert sample_dictionary.get_definition("CAT") == "A small feline"
        assert sample_dictionary.get_definition("CAR") == "A vehicle"

    def test_get_definition_nonexistent(self, sample_dictionary: Dictionary) -> None:
        """get_definition() returns None for non-words."""
        assert sample_dictionary.get_definition("DOG") is None

    def test_words_with_prefix(self, sample_dictionary: Dictionary) -> None:
        """words_with_prefix() returns all matching words."""
        words = list(sample_dictionary.words_with_prefix("CA"))
        assert set(words) == {"CAT", "CAR", "CART"}

    def test_words_with_prefix_no_matches(self, sample_dictionary: Dictionary) -> None:
        """words_with_prefix() returns empty for no matches."""
        words = list(sample_dictionary.words_with_prefix("DOG"))
        assert words == []


class TestDictionaryLoad:
    """Tests for dictionary loading."""

    def test_load_nonexistent_raises(self, tmp_path) -> None:
        """load() raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            Dictionary.load(tmp_path / "nonexistent.bin")
```

## Notes

### COCA Data Availability

COCA frequency data requires academic access or purchase from corpus.byu.edu. Alternatives:

1. **Proceed without frequency filtering** - Use SCOWL size 50 or 60 directly
2. **Use free alternatives** - Google Books N-grams, SUBTLEXus
3. **Manual curation** - Review and remove obscure words manually

### Pickle Security

The `pickle.load()` call in Dictionary is safe because:
- The dictionary.bin file is generated by our own build script
- The file is committed to the repository (not user-provided)
- We use `# noqa: S301` to acknowledge this deliberate choice

### Performance Expectations

| Operation | Target | Method |
|-----------|--------|--------|
| Dictionary load | <100ms | Binary pickle + efficient trie |
| Word lookup | <1ms | O(k) trie traversal |
| Prefix check | <1ms | O(k) trie traversal |
| Definition lookup | <1ms | O(k) trie traversal |

### Future Enhancements (Post-MVP)

- Bloom filter for client-side quick rejection
- Compressed trie (DAWG) for smaller file size
- Multiple dictionaries (easy/hard mode)
- Custom word additions per puzzle
