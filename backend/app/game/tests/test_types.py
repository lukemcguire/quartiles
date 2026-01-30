"""Tests for game domain types."""

import pytest

from app.game.types import GameState, Puzzle, Tile, Word


class TestTile:
    """Tests for Tile dataclass."""

    def test_valid_tile_creation(self) -> None:
        """Tile can be created with valid input."""
        tile = Tile(id=0, letters="TE")
        assert tile.id == 0
        assert tile.letters == "TE"

    def test_tile_auto_uppercases(self) -> None:
        """Tile converts letters to uppercase."""
        tile = Tile(id=0, letters="te")
        assert tile.letters == "TE"

    def test_tile_two_letters_valid(self) -> None:
        """Tile accepts 2-letter strings."""
        tile = Tile(id=0, letters="TE")
        assert tile.letters == "TE"

    def test_tile_three_letters_valid(self) -> None:
        """Tile accepts 3-letter strings."""
        tile = Tile(id=0, letters="TES")
        assert tile.letters == "TES"

    def test_tile_four_letters_valid(self) -> None:
        """Tile accepts 4-letter strings."""
        tile = Tile(id=0, letters="TEST")
        assert tile.letters == "TEST"

    def test_tile_one_letter_invalid(self) -> None:
        """Tile rejects 1-letter strings."""
        with pytest.raises(ValueError, match="Tile must have 2-4 letters"):
            Tile(id=0, letters="A")

    def test_tile_five_letters_invalid(self) -> None:
        """Tile rejects 5-letter strings."""
        with pytest.raises(ValueError, match="Tile must have 2-4 letters"):
            Tile(id=0, letters="ABCDE")

    def test_tile_non_alpha_invalid(self) -> None:
        """Tile rejects non-alphabetic characters."""
        with pytest.raises(ValueError, match="Tile letters must be alphabetic"):
            Tile(id=0, letters="T1")

    def test_tile_empty_invalid(self) -> None:
        """Tile rejects empty strings."""
        with pytest.raises(ValueError, match="Tile must have 2-4 letters"):
            Tile(id=0, letters="")

    def test_tile_is_frozen(self) -> None:
        """Tile is immutable (frozen dataclass)."""
        tile = Tile(id=0, letters="TE")
        with pytest.raises(AttributeError):
            tile.letters = "ST"  # type: ignore[misc]

    def test_tile_equality(self) -> None:
        """Tiles with same values are equal."""
        tile1 = Tile(id=0, letters="TE")
        tile2 = Tile(id=0, letters="TE")
        assert tile1 == tile2

    def test_tile_inequality(self) -> None:
        """Tiles with different values are not equal."""
        tile1 = Tile(id=0, letters="TE")
        tile2 = Tile(id=1, letters="TE")
        assert tile1 != tile2


class TestWord:
    """Tests for Word dataclass."""

    def test_word_creation(self) -> None:
        """Word can be created with valid input."""
        word = Word(text="TEST", tile_ids=(0, 1), points=4)
        assert word.text == "TEST"
        assert word.tile_ids == (0, 1)
        assert word.points == 4

    def test_tile_count_property(self) -> None:
        """tile_count returns correct number of tiles."""
        word = Word(text="TEST", tile_ids=(0, 1, 2, 3), points=10)
        assert word.tile_count == 4

        word2 = Word(text="TE", tile_ids=(0,), points=2)
        assert word2.tile_count == 1


class TestPuzzle:
    """Tests for Puzzle dataclass."""

    def test_puzzle_creation(self) -> None:
        """Puzzle can be created with valid input."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset({"TEST"}),
            total_points=150,
        )
        assert len(puzzle.tiles) == 20
        assert len(puzzle.quartile_words) == 5
        assert puzzle.total_points == 150

    def test_puzzle_requires_20_tiles(self) -> None:
        """Puzzle validation fails with wrong number of tiles."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(19))
        with pytest.raises(ValueError, match="Puzzle must have 20 tiles"):
            Puzzle(
                tiles=tiles,
                quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
                valid_words=frozenset(),
                total_points=0,
            )

    def test_puzzle_requires_5_quartiles(self) -> None:
        """Puzzle validation fails with wrong number of quartile words."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        with pytest.raises(ValueError, match="Puzzle must have 5 quartile words"):
            Puzzle(
                tiles=tiles,
                quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR"),
                valid_words=frozenset(),
                total_points=0,
            )

    def test_get_tile_by_id_found(self) -> None:
        """get_tile_by_id returns correct tile."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=0,
        )
        tile = puzzle.get_tile_by_id(5)
        assert tile is not None
        assert tile.id == 5

    def test_get_tile_by_id_not_found(self) -> None:
        """get_tile_by_id returns None for non-existent tile."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=0,
        )
        tile = puzzle.get_tile_by_id(25)
        assert tile is None

    def test_iter_tiles_by_ids_valid(self) -> None:
        """iter_tiles_by_ids yields tiles in correct order."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=0,
        )
        result = list(puzzle.iter_tiles_by_ids((5, 3, 7)))
        assert len(result) == 3
        assert result[0].id == 5
        assert result[1].id == 3
        assert result[2].id == 7

    def test_iter_tiles_by_ids_invalid_id(self) -> None:
        """iter_tiles_by_ids raises ValueError for non-existent tile."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=0,
        )
        with pytest.raises(ValueError, match="Tile ID 25 not found"):
            list(puzzle.iter_tiles_by_ids((0, 25)))


class TestGameState:
    """Tests for GameState dataclass."""

    def test_game_state_creation(self) -> None:
        """GameState can be created with valid input."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=150,
        )
        state = GameState(
            puzzle=puzzle,
            found_words=set(),
            current_score=0,
            hints_used=0,
        )
        assert state.current_score == 0
        assert state.hints_used == 0

    def test_is_solved_threshold(self) -> None:
        """is_solved returns True when score >= 100."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=150,
        )
        state = GameState(
            puzzle=puzzle,
            found_words=set(),
            current_score=100,
            hints_used=0,
        )
        assert state.is_solved is True

    def test_is_solved_below_threshold(self) -> None:
        """is_solved returns False when score < 100."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=150,
        )
        state = GameState(
            puzzle=puzzle,
            found_words=set(),
            current_score=99,
            hints_used=0,
        )
        assert state.is_solved is False

    def test_unfound_quartiles(self) -> None:
        """unfound_quartiles returns quartiles not yet found."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=150,
        )
        state = GameState(
            puzzle=puzzle,
            found_words={"WORDONE", "WORDTWO"},
            current_score=20,
            hints_used=0,
        )
        assert state.unfound_quartiles == {"WORDTHREE", "WORDFOUR", "WORDFIVE"}

    def test_unfound_quartiles_all_found(self) -> None:
        """unfound_quartiles returns empty set when all found."""
        tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
        puzzle = Puzzle(
            tiles=tiles,
            quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
            valid_words=frozenset(),
            total_points=150,
        )
        state = GameState(
            puzzle=puzzle,
            found_words={"WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"},
            current_score=50,
            hints_used=0,
        )
        assert state.unfound_quartiles == set()
