# Section 04: Pure Python Game Logic

## Background

The Quartiles game logic is intentionally isolated in a pure Python module (`backend/app/game/`) with no dependencies on FastAPI, SQLModel, or Pydantic. This architectural decision provides:

1. **Testability** - Game logic can be unit tested without HTTP or database setup
2. **Reusability** - Logic could be used in CLI tools, batch processing, or other contexts
3. **Separation of Concerns** - API routes act as adapters, not logic containers
4. **Type Safety** - Pure Python dataclasses are simple and predictable

The game module implements:
- Domain types (Tile, Puzzle, Word, GameSession)
- Dictionary class (trie-based word validation)
- Puzzle generator (CSP algorithm)
- Solver (word finding with prefix pruning)

## Dependencies

| Type | Section | Description |
|------|---------|-------------|
| **requires** | 03 | Dictionary pipeline provides the word data |
| **blocks** | 05 | Database models need game types for schema design |

## Requirements

When this section is complete:
1. All game domain types are defined as dataclasses
2. Dictionary class loads and queries the trie efficiently
3. Puzzle generator creates valid puzzles with 5 quartiles
4. Solver finds all valid words from a tile configuration
5. Unit tests achieve >90% coverage of game logic

---

## Implementation Details

### 4.1 Domain Types

**File:** `backend/app/game/types.py`

```python
"""
Domain types for the Quartiles game.

These are pure Python dataclasses with NO framework dependencies.
API routes convert between these types and Pydantic schemas.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Tile:
    """A single tile containing 2-4 letters."""

    id: int
    letters: str  # 2-4 uppercase letters

    def __post_init__(self) -> None:
        """Validate tile constraints."""
        if not 2 <= len(self.letters) <= 4:
            raise ValueError(f"Tile must have 2-4 letters, got {len(self.letters)}")
        if not self.letters.isalpha():
            raise ValueError("Tile letters must be alphabetic")


@dataclass(frozen=True)
class Word:
    """A valid word formed from tiles."""

    text: str
    tile_ids: tuple[int, ...]  # Which tiles form this word
    points: int  # Calculated from tile count

    @property
    def tile_count(self) -> int:
        """Number of tiles used to form this word."""
        return len(self.tile_ids)


@dataclass
class Puzzle:
    """A complete puzzle configuration."""

    tiles: tuple[Tile, ...]  # Exactly 20 tiles
    quartile_words: tuple[str, ...]  # Exactly 5 target words (8-16 letters)
    valid_words: frozenset[str]  # All valid words findable in this puzzle
    total_points: int  # Sum of all valid word points

    def __post_init__(self) -> None:
        """Validate puzzle constraints."""
        if len(self.tiles) != 20:
            raise ValueError(f"Puzzle must have 20 tiles, got {len(self.tiles)}")
        if len(self.quartile_words) != 5:
            raise ValueError(f"Puzzle must have 5 quartile words, got {len(self.quartile_words)}")


@dataclass
class GameState:
    """Active game state for a player (in-memory representation)."""

    puzzle: Puzzle
    found_words: set[str]
    current_score: int
    hints_used: int

    @property
    def is_solved(self) -> bool:
        """Whether the player has reached the solve threshold (100 points)."""
        return self.current_score >= 100
```

### 4.2 Dictionary Class

**File:** `backend/app/game/dictionary.py`

```python
"""
Trie-based dictionary for efficient word validation and prefix checking.
"""

import pickle
from pathlib import Path
from typing import Optional


class TrieNode:
    """Node in the prefix tree."""

    __slots__ = ('children', 'is_word', 'definition')

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_word: bool = False
        self.definition: Optional[str] = None


class Dictionary:
    """
    Trie-backed word dictionary.

    Provides O(k) lookup where k is word length, and efficient prefix checking
    for early pruning during word search.
    """

    def __init__(self) -> None:
        self.root = TrieNode()
        self._word_count = 0

    def add(self, word: str, definition: Optional[str] = None) -> None:
        """Add a word to the dictionary."""
        node = self.root
        for char in word.upper():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if not node.is_word:
            self._word_count += 1
        node.is_word = True
        node.definition = definition

    def contains(self, word: str) -> bool:
        """Check if word exists in dictionary."""
        node = self._get_node(word.upper())
        return node is not None and node.is_word

    def contains_prefix(self, prefix: str) -> bool:
        """Check if any words start with prefix (for search pruning)."""
        return self._get_node(prefix.upper()) is not None

    def get_definition(self, word: str) -> Optional[str]:
        """Get WordNet definition for word."""
        node = self._get_node(word.upper())
        if node and node.is_word:
            return node.definition
        return None

    def _get_node(self, text: str) -> Optional[TrieNode]:
        """Traverse to node for given text."""
        node = self.root
        for char in text:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def __len__(self) -> int:
        return self._word_count

    @classmethod
    def load(cls, filepath: Path) -> "Dictionary":
        """Load dictionary from binary file."""
        with open(filepath, 'rb') as f:
            word_data = pickle.load(f)

        dictionary = cls()
        for word, data in word_data.items():
            dictionary.add(word, data.get('definition'))
        return dictionary
```

### 4.3 Puzzle Generator

**File:** `backend/app/game/generator.py`

```python
"""
Puzzle generation using constraint satisfaction.

Algorithm (Generate-First with CSP):
1. Select 5 quartile words (8-16 letters, not in cooldown)
2. Decompose each into 4 tiles (2-4 letters each)
3. Verify no duplicate tiles across words
4. Validate: solver finds exactly these 5 quartiles
5. Check total points >= 130
"""

import random
from typing import Optional

from .dictionary import Dictionary
from .types import Puzzle, Tile
from .solver import find_all_valid_words, calculate_total_points


MAX_ATTEMPTS = 1000
MIN_TOTAL_POINTS = 130


def generate_puzzle(
    dictionary: Dictionary,
    excluded_quartiles: set[str],
) -> Optional[Puzzle]:
    """
    Generate a valid puzzle with exactly 5 quartile words.

    Args:
        dictionary: Word dictionary for validation
        excluded_quartiles: Words in cooldown (can't be used as quartiles)

    Returns:
        Valid Puzzle or None if generation fails
    """
    # Get candidate quartile words (8-16 letters, has definition)
    quartile_candidates = [
        word for word in get_quartile_words(dictionary)
        if word not in excluded_quartiles
    ]

    for attempt in range(MAX_ATTEMPTS):
        # Step 1: Select 5 random quartile words
        if len(quartile_candidates) < 5:
            return None
        selected_words = random.sample(quartile_candidates, 5)

        # Step 2: Decompose into tiles
        tiles = decompose_words_to_tiles(selected_words)
        if tiles is None:
            continue  # Couldn't find valid decomposition

        # Step 3: Find all valid words
        valid_words = find_all_valid_words(tiles, dictionary)

        # Step 4: Verify our quartiles are found
        found_quartiles = {w for w in valid_words if is_quartile_word(w, tiles)}
        if found_quartiles != set(selected_words):
            continue

        # Step 5: Check minimum points
        total_points = calculate_total_points(valid_words, tiles)
        if total_points < MIN_TOTAL_POINTS:
            continue

        return Puzzle(
            tiles=tuple(tiles),
            quartile_words=tuple(selected_words),
            valid_words=frozenset(valid_words),
            total_points=total_points,
        )

    return None


def get_quartile_words(dictionary: Dictionary) -> list[str]:
    """Get all words suitable for quartiles (8-16 letters with definitions)."""
    # Implementation: iterate dictionary, filter by length and definition
    pass


def decompose_words_to_tiles(words: list[str]) -> Optional[list[Tile]]:
    """
    Decompose 5 words into exactly 20 unique tiles.

    Each word must split into exactly 4 tiles of 2-4 letters.
    No duplicate tiles across words.
    """
    all_tiles: list[Tile] = []
    used_tile_letters: set[str] = set()
    tile_id = 0

    for word in words:
        tiles = decompose_single_word(word, used_tile_letters, tile_id)
        if tiles is None:
            return None
        all_tiles.extend(tiles)
        for tile in tiles:
            used_tile_letters.add(tile.letters)
        tile_id += len(tiles)

    if len(all_tiles) != 20:
        return None

    return all_tiles


def decompose_single_word(
    word: str,
    forbidden_tiles: set[str],
    start_id: int,
) -> Optional[list[Tile]]:
    """
    Split word into exactly 4 tiles of 2-4 letters using backtracking.
    """
    def backtrack(remaining: str, tiles: list[str]) -> Optional[list[str]]:
        if not remaining:
            return tiles if len(tiles) == 4 else None
        if len(tiles) >= 4:
            return None

        # Try tile sizes 2, 3, 4
        for size in [2, 3, 4]:
            if size > len(remaining):
                continue
            tile_letters = remaining[:size]
            if tile_letters in forbidden_tiles:
                continue
            # Check remaining can still form valid tiles
            remaining_after = remaining[size:]
            remaining_tiles = 4 - len(tiles) - 1
            if remaining_after and not (2 * remaining_tiles <= len(remaining_after) <= 4 * remaining_tiles):
                continue

            result = backtrack(remaining_after, tiles + [tile_letters])
            if result is not None:
                return result

        return None

    result = backtrack(word.upper(), [])
    if result is None:
        return None

    return [Tile(id=start_id + i, letters=letters) for i, letters in enumerate(result)]


def is_quartile_word(word: str, tiles: list[Tile]) -> bool:
    """Check if word uses exactly 4 tiles."""
    # Implementation: find which tiles spell the word
    pass
```

### 4.4 Solver Module

**File:** `backend/app/game/solver.py`

```python
"""
Word finding and scoring for Quartiles puzzles.

Uses cursor-based state exploration with prefix pruning for efficient search.
"""

from itertools import permutations
from typing import Iterator

from .dictionary import Dictionary
from .types import Tile, Word


# Scoring table
POINTS = {1: 2, 2: 4, 3: 7, 4: 10}

# Hint penalties (milliseconds)
HINT_PENALTIES = {1: 30_000, 2: 60_000, 3: 120_000, 4: 240_000, 5: 480_000}


def find_all_valid_words(tiles: tuple[Tile, ...], dictionary: Dictionary) -> set[str]:
    """
    Find all valid words using state space exploration with prefix pruning.

    For each 1-4 tile permutation:
    - Check if concatenated letters form a valid prefix
    - If not, skip all extensions of this permutation
    - If valid word, add to results
    """
    valid_words: set[str] = set()

    for num_tiles in range(1, 5):
        for perm in permutations(tiles, num_tiles):
            word = ''.join(tile.letters for tile in perm)

            # Early pruning: check prefix validity
            if not dictionary.contains_prefix(word):
                continue

            if dictionary.contains(word):
                valid_words.add(word)

    return valid_words


def score_word(tile_count: int) -> int:
    """Calculate points for a word based on tile count."""
    return POINTS.get(tile_count, 0)


def calculate_total_points(words: set[str], tiles: tuple[Tile, ...]) -> int:
    """Calculate total available points for a puzzle."""
    total = 0
    for word in words:
        tile_count = get_tile_count(word, tiles)
        total += score_word(tile_count)
    return total


def get_tile_count(word: str, tiles: tuple[Tile, ...]) -> int:
    """Determine how many tiles form this word."""
    # Implementation: find minimal tile combination
    pass


def calculate_hint_penalty(hint_number: int) -> int:
    """Calculate time penalty (ms) for nth hint (1-indexed)."""
    return HINT_PENALTIES.get(hint_number, HINT_PENALTIES[5])


def get_unfound_quartile_hint(
    quartile_words: tuple[str, ...],
    found_words: set[str],
    dictionary: Dictionary,
) -> tuple[str, str] | None:
    """
    Get word and definition for an unfound quartile.

    Returns:
        Tuple of (word, definition) or None if all quartiles found
    """
    unfound = set(quartile_words) - found_words
    if not unfound:
        return None
    word = next(iter(unfound))
    definition = dictionary.get_definition(word)
    return (word, definition or "No definition available")
```

### 4.5 Unit Tests

**Directory:** `backend/app/game/tests/`

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_types.py        # Domain type tests
├── test_dictionary.py   # Trie tests
├── test_generator.py    # Puzzle generation tests
├── test_solver.py       # Word finding tests
└── test_integration.py  # End-to-end tests
```

**Key test cases:**

```python
# test_types.py
def test_tile_validates_length():
    """Tile rejects letters outside 2-4 range."""
    with pytest.raises(ValueError):
        Tile(id=0, letters="A")
    with pytest.raises(ValueError):
        Tile(id=0, letters="ABCDE")

# test_dictionary.py
def test_contains_and_prefix():
    """Dictionary correctly identifies words and prefixes."""
    d = Dictionary()
    d.add("TESTING")
    assert d.contains("TESTING")
    assert not d.contains("TEST")  # Prefix but not a word
    assert d.contains_prefix("TEST")
    assert not d.contains_prefix("TESTX")

# test_generator.py
def test_decompose_word():
    """Word decomposes into exactly 4 tiles."""
    tiles = decompose_single_word("QUARTERLY", set(), 0)
    assert tiles is not None
    assert len(tiles) == 4
    assert ''.join(t.letters for t in tiles) == "QUARTERLY"

# test_solver.py
def test_find_valid_words():
    """Solver finds expected words from tiles."""
    tiles = (Tile(0, "TE"), Tile(1, "ST"), Tile(2, "ING"), Tile(3, "ED"))
    dictionary = Dictionary()
    dictionary.add("TEST")
    dictionary.add("TESTING")

    words = find_all_valid_words(tiles, dictionary)
    assert "TEST" in words
    assert "TESTING" in words

# test_integration.py
def test_generate_and_solve():
    """Generated puzzle is solvable with 5 quartiles."""
    dictionary = Dictionary.load(Path("data/dictionary.bin"))
    puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

    assert puzzle is not None
    assert len(puzzle.quartile_words) == 5
    assert all(q in puzzle.valid_words for q in puzzle.quartile_words)
    assert puzzle.total_points >= 130
```

---

## Acceptance Criteria

- [ ] `backend/app/game/types.py` defines Tile, Word, Puzzle, GameState
- [ ] `backend/app/game/dictionary.py` implements Dictionary with trie
- [ ] `backend/app/game/generator.py` generates valid puzzles
- [ ] `backend/app/game/solver.py` finds all valid words
- [ ] No imports from FastAPI, SQLModel, or Pydantic in game module
- [ ] `Dictionary.load()` completes in <50ms
- [ ] `generate_puzzle()` succeeds within 1000 attempts
- [ ] `find_all_valid_words()` completes in <100ms
- [ ] Unit tests exist for all modules
- [ ] Test coverage >90% for game module
- [ ] `pytest backend/app/game/tests/` passes

## Files Summary

### Create
- `backend/app/game/__init__.py`
- `backend/app/game/types.py`
- `backend/app/game/dictionary.py`
- `backend/app/game/generator.py`
- `backend/app/game/solver.py`
- `backend/app/game/tests/__init__.py`
- `backend/app/game/tests/conftest.py`
- `backend/app/game/tests/test_types.py`
- `backend/app/game/tests/test_dictionary.py`
- `backend/app/game/tests/test_generator.py`
- `backend/app/game/tests/test_solver.py`
- `backend/app/game/tests/test_integration.py`
