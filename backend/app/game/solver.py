"""Word finding and scoring for Quartiles puzzles.

Uses cursor-based state exploration with prefix pruning for efficient search.
"""

from __future__ import annotations

from itertools import permutations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .dictionary import Dictionary
    from .types import Tile


# Scoring table
POINTS = {1: 2, 2: 4, 3: 7, 4: 10}

# Hint penalties (milliseconds)
HINT_PENALTIES = {1: 30_000, 2: 60_000, 3: 120_000, 4: 240_000, 5: 480_000}


def find_all_valid_words(tiles: Sequence[Tile], dictionary: Dictionary) -> set[str]:
    """Find all valid words using state space exploration with prefix pruning.

    For each 1-4 tile permutation:
    - Check if concatenated letters form a valid prefix
    - If not, skip all extensions of this permutation
    - If valid word, add to results

    Args:
        tiles: Available tiles to form words from.
        dictionary: Word dictionary for validation.

    Returns:
        Set of all valid words that can be formed from the tiles.
    """
    valid_words: set[str] = set()

    for num_tiles in range(1, 5):
        for perm in permutations(tiles, num_tiles):
            word = "".join(tile.letters for tile in perm)

            # Early pruning: check prefix validity
            if not dictionary.contains_prefix(word):
                continue

            if dictionary.contains(word):
                valid_words.add(word)

    return valid_words


def score_word(tile_count: int) -> int:
    """Calculate points for a word based on tile count.

    Args:
        tile_count: Number of tiles used to form the word (1-4).

    Returns:
        Points awarded for the word.
    """
    return POINTS.get(tile_count, 0)


def get_tile_count(word: str, tiles: Sequence[Tile]) -> int:
    """Determine how many tiles form this word.

    Finds the minimal number of tiles that can form the given word
    by searching through tile combinations.

    Args:
        word: The word to analyze.
        tiles: Available tiles.

    Returns:
        Number of tiles (1-4) that form the word, or 0 if impossible.

    Raises:
        ValueError: If the word cannot be formed from the tiles.
    """
    for num_tiles in range(1, 5):
        for perm in permutations(tiles, num_tiles):
            formed = "".join(tile.letters for tile in perm)
            if formed == word:
                return num_tiles

    msg = f"Word '{word}' cannot be formed from the given tiles"
    raise ValueError(msg)


def calculate_total_points(words: set[str], tiles: Sequence[Tile]) -> int:
    """Calculate total available points for a puzzle.

    Args:
        words: Set of valid words in the puzzle.
        tiles: Tiles in the puzzle.

    Returns:
        Sum of points for all words.
    """
    total = 0
    for word in words:
        tile_count = get_tile_count(word, tiles)
        total += score_word(tile_count)
    return total


def calculate_hint_penalty(hint_number: int) -> int:
    """Calculate time penalty (ms) for nth hint (1-indexed).

    Args:
        hint_number: The hint number (1-indexed).

    Returns:
        Time penalty in milliseconds.
    """
    return HINT_PENALTIES.get(hint_number, HINT_PENALTIES[5])


def get_unfound_quartile_hint(
    quartile_words: tuple[str, ...],
    found_words: set[str],
    dictionary: Dictionary,
) -> tuple[str, str] | None:
    """Get word and definition for an unfound quartile.

    Args:
        quartile_words: Tuple of all quartile words in the puzzle.
        found_words: Set of words the player has already found.
        dictionary: Word dictionary for definitions.

    Returns:
        Tuple of (word, definition) or None if all quartiles found.
    """
    unfound = set(quartile_words) - found_words
    if not unfound:
        return None
    word = next(iter(unfound))
    definition = dictionary.get_definition(word)
    return (word, definition or "No definition available")


def is_quartile_word(word: str, tiles: Sequence[Tile]) -> bool:
    """Check if word uses exactly 4 tiles.

    Args:
        word: The word to check.
        tiles: Available tiles.

    Returns:
        True if the word can be formed using exactly 4 tiles.
    """
    try:
        return get_tile_count(word, tiles) == 4
    except ValueError:
        return False
