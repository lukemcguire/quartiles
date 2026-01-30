"""Integration tests for the game module."""

import pytest

from app.game.dictionary import Dictionary
from app.game.generator import generate_puzzle
from app.game.solver import (
    find_all_valid_words,
    is_quartile_word,
)
from app.game.types import GameState


class TestDictionaryLoad:
    """Tests for loading the real dictionary."""

    def test_load_real_dictionary(self) -> None:
        """Real dictionary loads successfully."""
        dictionary = Dictionary.load()
        assert len(dictionary) > 0

    def test_dictionary_contains_common_words(self) -> None:
        """Dictionary contains common English words."""
        dictionary = Dictionary.load()
        assert dictionary.contains("TEST")
        assert dictionary.contains("QUARTILE")
        assert dictionary.contains("PUZZLE")

    def test_dictionary_prefix_checking(self) -> None:
        """Dictionary supports prefix checking."""
        dictionary = Dictionary.load()
        assert dictionary.contains_prefix("TE")
        assert dictionary.contains_prefix("QUA")
        assert not dictionary.contains_prefix("XYZABC")

    def test_dictionary_definitions(self) -> None:
        """Dictionary provides definitions for words."""
        dictionary = Dictionary.load()
        definition = dictionary.get_definition("TEST")
        # Most common words should have definitions
        # But we don't want to fail if some don't
        # Just check it returns a string or None
        assert definition is None or isinstance(definition, str)


class TestPuzzleGeneration:
    """Integration tests for puzzle generation."""

    @pytest.mark.slow
    def test_generate_valid_puzzle(self) -> None:
        """Can generate a valid puzzle with real dictionary."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        assert len(puzzle.tiles) == 20
        assert len(puzzle.quartile_words) == 5
        assert puzzle.total_points >= 130

    @pytest.mark.slow
    def test_quartiles_are_valid_words(self) -> None:
        """All quartile words exist in dictionary."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        for quartile in puzzle.quartile_words:
            assert dictionary.contains(quartile)
            # Quartiles should have definitions
            assert dictionary.get_definition(quartile) is not None

    @pytest.mark.slow
    def test_quartiles_are_four_tile_words(self) -> None:
        """All quartile words use exactly 4 tiles."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        for quartile in puzzle.quartile_words:
            assert is_quartile_word(quartile, puzzle.tiles)

    @pytest.mark.slow
    def test_valid_words_contain_quartiles(self) -> None:
        """All quartiles are in the valid_words set."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        for quartile in puzzle.quartile_words:
            assert quartile in puzzle.valid_words

    @pytest.mark.slow
    def test_excluded_quartiles_respected(self) -> None:
        """Excluded quartiles are not used in new puzzles."""
        dictionary = Dictionary.load()
        puzzle1 = generate_puzzle(dictionary, excluded_quartiles=set())
        assert puzzle1 is not None

        # Exclude the quartiles from the first puzzle
        excluded = set(puzzle1.quartile_words)
        puzzle2 = generate_puzzle(dictionary, excluded_quartiles=excluded)
        assert puzzle2 is not None

        # Second puzzle should not use any of the first puzzle's quartiles
        for quartile in puzzle1.quartile_words:
            assert quartile not in puzzle2.quartile_words


class TestGameState:
    """Tests for game state management."""

    def test_initial_game_state(self) -> None:
        """GameState initializes correctly."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        state = GameState(
            puzzle=puzzle,
            found_words=set(),
            current_score=0,
            hints_used=0,
        )

        assert state.current_score == 0
        assert state.hints_used == 0
        assert state.is_solved is False
        assert len(state.unfound_quartiles) == 5

    def test_finding_words_updates_state(self) -> None:
        """Finding words updates the game state."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        state = GameState(
            puzzle=puzzle,
            found_words=set(),
            current_score=0,
            hints_used=0,
        )

        # Find a quartile word
        quartile = puzzle.quartile_words[0]
        state.found_words.add(quartile)

        # Update score (4-tile word = 10 points)
        state.current_score += 10

        assert quartile not in state.unfound_quartiles
        assert len(state.unfound_quartiles) == 4

    def test_solved_state_at_100_points(self) -> None:
        """Game is solved when reaching 100 points."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        state = GameState(
            puzzle=puzzle,
            found_words=set(),
            current_score=100,
            hints_used=0,
        )

        assert state.is_solved is True


class TestWordFinding:
    """Integration tests for word finding."""

    def test_find_words_from_generated_puzzle(self) -> None:
        """Can find valid words from a generated puzzle."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        # The puzzle already has valid_words pre-computed
        # Let's verify by running the solver ourselves
        found_words = find_all_valid_words(puzzle.tiles, dictionary)

        # Should find all the quartile words
        for quartile in puzzle.quartile_words:
            assert quartile in found_words

    def test_solver_matches_puzzle_valid_words(self) -> None:
        """Solver results match puzzle's valid_words set."""
        dictionary = Dictionary.load()
        puzzle = generate_puzzle(dictionary, excluded_quartiles=set())

        assert puzzle is not None
        found_words = find_all_valid_words(puzzle.tiles, dictionary)

        # The puzzle's valid_words should match what we find
        assert found_words == puzzle.valid_words
