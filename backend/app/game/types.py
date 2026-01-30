"""Domain types for the Quartiles game.

These are pure Python dataclasses with NO framework dependencies.
API routes convert between these types and Pydantic schemas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class Tile:
    """A single tile containing 2-4 letters."""

    id: int
    letters: str  # 2-4 uppercase letters

    def __post_init__(self) -> None:
        """Validate tile constraints.

        Raises:
            ValueError: If letters are not 2-4 characters or not alphabetic.
        """
        if not 2 <= len(self.letters) <= 4:
            msg = f"Tile must have 2-4 letters, got {len(self.letters)}"
            raise ValueError(msg)
        if not self.letters.isalpha():
            msg = "Tile letters must be alphabetic"
            raise ValueError(msg)
        # Ensure uppercase
        object.__setattr__(self, "letters", self.letters.upper())


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
        """Validate puzzle constraints.

        Raises:
            ValueError: If puzzle doesn't have exactly 20 tiles or 5 quartile words.
        """
        if len(self.tiles) != 20:
            msg = f"Puzzle must have 20 tiles, got {len(self.tiles)}"
            raise ValueError(msg)
        if len(self.quartile_words) != 5:
            msg = f"Puzzle must have 5 quartile words, got {len(self.quartile_words)}"
            raise ValueError(msg)

    def get_tile_by_id(self, tile_id: int) -> Tile | None:
        """Get a tile by its ID.

        Args:
            tile_id: The ID of the tile to retrieve.

        Returns:
            The Tile with the given ID, or None if not found.
        """
        for tile in self.tiles:
            if tile.id == tile_id:
                return tile
        return None

    def iter_tiles_by_ids(self, tile_ids: tuple[int, ...]) -> Iterator[Tile]:
        """Yield tiles in the order of the given tile IDs.

        Args:
            tile_ids: Tuple of tile IDs to iterate.

        Yields:
            Tiles corresponding to the given IDs.

        Raises:
            ValueError: If a tile ID is not found.
        """
        for tile_id in tile_ids:
            tile = self.get_tile_by_id(tile_id)
            if tile is None:
                msg = f"Tile ID {tile_id} not found in puzzle"
                raise ValueError(msg)
            yield tile


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

    @property
    def unfound_quartiles(self) -> set[str]:
        """Set of quartile words that haven't been found yet."""
        return set(self.puzzle.quartile_words) - self.found_words
