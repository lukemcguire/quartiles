"""Puzzle generation using constraint satisfaction.

Algorithm (Generate-First with CSP):
1. Select 5 quartile words (8-16 letters, not in cooldown)
2. Decompose each into 4 tiles (2-4 letters each)
3. Verify no duplicate tiles across words
4. Validate: solver finds exactly these 5 quartiles
5. Check total points >= 130
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .dictionary import Dictionary
    from .types import Puzzle, Tile

from .solver import (
    calculate_total_points,
    find_all_valid_words,
    is_quartile_word,
)

MAX_ATTEMPTS = 1000
MIN_TOTAL_POINTS = 130
MIN_QUARTILE_LENGTH = 8
MAX_QUARTILE_LENGTH = 16


def generate_puzzle(
    dictionary: Dictionary,
    excluded_quartiles: set[str],
) -> Puzzle | None:
    """Generate a valid puzzle with exactly 5 quartile words.

    Args:
        dictionary: Word dictionary for validation.
        excluded_quartiles: Words in cooldown (can't be used as quartiles).

    Returns:
        Valid Puzzle or None if generation fails after MAX_ATTEMPTS.
    """
    # Get candidate quartile words (8-16 letters, has definition)
    quartile_candidates = [word for word in _get_quartile_words(dictionary) if word not in excluded_quartiles]

    if len(quartile_candidates) < 5:
        return None

    for _attempt in range(MAX_ATTEMPTS):
        # Step 1: Select 5 random quartile words
        selected_words = random.sample(quartile_candidates, 5)

        # Step 2: Decompose into tiles
        tiles = _decompose_words_to_tiles(selected_words)
        if tiles is None:
            continue  # Couldn't find valid decomposition

        # Step 3: Find all valid words
        valid_words = find_all_valid_words(tuple(tiles), dictionary)

        # Step 4: Verify our quartiles are found
        found_quartiles = {w for w in valid_words if is_quartile_word(w, tuple(tiles))}
        if found_quartiles != set(selected_words):
            continue

        # Step 5: Check minimum points
        total_points = calculate_total_points(valid_words, tuple(tiles))
        if total_points < MIN_TOTAL_POINTS:
            continue

        from .types import Puzzle

        return Puzzle(
            tiles=tuple(tiles),
            quartile_words=tuple(selected_words),
            valid_words=frozenset(valid_words),
            total_points=total_points,
        )

    return None


def _get_quartile_words(dictionary: Dictionary) -> list[str]:
    """Get all words suitable for quartiles (8-16 letters with definitions).

    Args:
        dictionary: Word dictionary.

    Returns:
        List of words that meet quartile criteria.
    """
    # We need to iterate through the dictionary to find suitable words
    # Since we don't have a direct iteration method, we use words_with_prefix
    # with single letter prefixes to traverse the dictionary
    words: list[str] = []

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        matching = [
            word
            for word in dictionary.words_with_prefix(letter)
            if MIN_QUARTILE_LENGTH <= len(word) <= MAX_QUARTILE_LENGTH and dictionary.get_definition(word) is not None
        ]
        words.extend(matching)

    return words


def _decompose_words_to_tiles(words: list[str]) -> list[Tile] | None:
    """Decompose 5 words into exactly 20 unique tiles.

    Each word must split into exactly 4 tiles of 2-4 letters.
    No duplicate tiles across words.

    Args:
        words: List of 5 words to decompose.

    Returns:
        List of 20 Tile objects, or None if decomposition fails.
    """
    all_tiles: list[Tile] = []
    used_tile_letters: set[str] = set()
    tile_id = 0

    for word in words:
        tiles = _decompose_single_word(word, used_tile_letters, tile_id)
        if tiles is None:
            return None
        all_tiles.extend(tiles)
        for tile in tiles:
            used_tile_letters.add(tile.letters)
        tile_id += len(tiles)

    if len(all_tiles) != 20:
        return None

    return all_tiles


def _decompose_single_word(
    word: str,
    forbidden_tiles: set[str],
    start_id: int,
) -> list[Tile] | None:
    """Split word into exactly 4 tiles of 2-4 letters using backtracking.

    Args:
        word: The word to decompose.
        forbidden_tiles: Tile strings that cannot be used.
        start_id: Starting tile ID.

    Returns:
        List of 4 Tile objects, or None if decomposition fails.
    """
    from .types import Tile

    word_upper = word.upper()

    def backtrack(remaining: str, tiles: list[str]) -> list[str] | None:
        if not remaining:
            return tiles if len(tiles) == 4 else None
        if len(tiles) >= 4:
            return None

        # Try tile sizes 2, 3, 4
        for size in (2, 3, 4):
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

            result = backtrack(remaining_after, [*tiles, tile_letters])
            if result is not None:
                return result

        return None

    result = backtrack(word_upper, [])
    if result is None:
        return None

    return [Tile(id=start_id + i, letters=letters) for i, letters in enumerate(result)]


def iterate_quartile_candidates(
    dictionary: Dictionary,
    min_length: int = MIN_QUARTILE_LENGTH,
    max_length: int = MAX_QUARTILE_LENGTH,
) -> Iterator[str]:
    """Iterate over words suitable for quartiles.

    Args:
        dictionary: Word dictionary.
        min_length: Minimum word length (default 8).
        max_length: Maximum word length (default 16).

    Yields:
        Words that have definitions and are within the length range.
    """
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for word in dictionary.words_with_prefix(letter):
            if min_length <= len(word) <= max_length and dictionary.get_definition(word) is not None:
                yield word
