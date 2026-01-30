"""Tests for word finding and scoring functions."""

import pytest

from app.game.dictionary import Dictionary, TrieNode
from app.game.solver import (
    calculate_hint_penalty,
    calculate_total_points,
    find_all_valid_words,
    get_tile_count,
    get_unfound_quartile_hint,
    is_quartile_word,
    score_word,
)
from app.game.types import Tile


class TestScoreWord:
    """Tests for score_word function."""

    def test_score_one_tile(self) -> None:
        """1-tile word scores 2 points."""
        assert score_word(1) == 2

    def test_score_two_tiles(self) -> None:
        """2-tile word scores 4 points."""
        assert score_word(2) == 4

    def test_score_three_tiles(self) -> None:
        """3-tile word scores 7 points."""
        assert score_word(3) == 7

    def test_score_four_tiles(self) -> None:
        """4-tile word scores 10 points."""
        assert score_word(4) == 10

    def test_score_invalid_tile_count(self) -> None:
        """Invalid tile count scores 0 points."""
        assert score_word(0) == 0
        assert score_word(5) == 0
        assert score_word(10) == 0


class TestGetTileCount:
    """Tests for get_tile_count function."""

    def test_one_tile_word(self) -> None:
        """Word formed by 1 tile returns 1."""
        tiles = (Tile(0, "TEST"),)
        assert get_tile_count("TEST", tiles) == 1

    def test_two_tile_word(self) -> None:
        """Word formed by 2 tiles returns 2."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"))
        assert get_tile_count("TEST", tiles) == 2

    def test_three_tile_word(self) -> None:
        """Word formed by 3 tiles returns 3."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"), Tile(2, "ING"))
        assert get_tile_count("TESTING", tiles) == 3

    def test_four_tile_word(self) -> None:
        """Word formed by 4 tiles returns 4."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"), Tile(2, "IN"), Tile(3, "GG"))
        assert get_tile_count("TESTINGG", tiles) == 4

    def test_word_not_formable(self) -> None:
        """Word that cannot be formed raises ValueError."""
        tiles = (Tile(0, "AB"), Tile(1, "CD"))
        with pytest.raises(ValueError, match="cannot be formed"):
            get_tile_count("TEST", tiles)

    def test_different_permutations(self) -> None:
        """Finds tile count regardless of tile order."""
        tiles = (Tile(0, "ST"), Tile(1, "TE"))
        assert get_tile_count("TEST", tiles) == 2


class TestFindAllValidWords:
    """Tests for find_all_valid_words function."""

    @pytest.fixture
    def solver_dictionary(self) -> Dictionary:
        """Create a dictionary for solver testing.

        Returns:
            A Dictionary with test words for solver validation.
        """
        root = TrieNode()

        # Add TEST
        t_node = TrieNode()
        e_node = TrieNode()
        s_node = TrieNode()
        test_node = TrieNode(is_word=True, definition="A trial")
        root.children["T"] = t_node
        t_node.children["E"] = e_node
        e_node.children["S"] = s_node
        s_node.children["T"] = test_node

        # Add TESTING (extends TEST)
        ing_node = TrieNode(is_word=True, definition="The act of testing")
        i_node = TrieNode()
        n_node = TrieNode()
        s_node.children["I"] = i_node
        i_node.children["N"] = n_node
        n_node.children["G"] = ing_node

        # Add BEST
        b_node = TrieNode()
        root.children["B"] = b_node
        b_node.children["E"] = e_node  # Share E node

        return Dictionary(root)

    def test_finds_single_tile_words(self, solver_dictionary: Dictionary) -> None:
        """Finds words using single tile."""
        tiles = (Tile(0, "TEST"),)
        words = find_all_valid_words(tiles, solver_dictionary)
        assert "TEST" in words

    def test_finds_multi_tile_words(self, solver_dictionary: Dictionary) -> None:
        """Finds words using multiple tiles."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"))
        words = find_all_valid_words(tiles, solver_dictionary)
        assert "TEST" in words

    def test_finds_all_valid_words(self, solver_dictionary: Dictionary) -> None:
        """Finds all valid words from tiles."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"), Tile(2, "IN"), Tile(3, "GG"))
        words = find_all_valid_words(tiles, solver_dictionary)
        assert "TEST" in words
        # Note: TESTINGG won't be found because it's not a real word

    def test_pruning_with_invalid_prefix(self, solver_dictionary: Dictionary) -> None:
        """Does not find words starting with invalid prefixes."""
        tiles = (Tile(0, "XX"), Tile(1, "YY"))
        words = find_all_valid_words(tiles, solver_dictionary)
        assert len(words) == 0

    def test_case_insensitive(self, solver_dictionary: Dictionary) -> None:
        """Tile letters are already uppercased by Tile class."""
        tiles = (Tile(0, "te"), Tile(1, "St"))
        # Tile auto-uppercases, so this should work
        words = find_all_valid_words(tiles, solver_dictionary)
        assert "TEST" in words


class TestCalculateTotalPoints:
    """Tests for calculate_total_points function."""

    def test_calculates_total_points(self) -> None:
        """Sum points for all words."""
        tiles = (Tile(0, "TEST"), Tile(1, "ST"), Tile(2, "ING"))
        words = {"TEST", "ST", "ING"}
        total = calculate_total_points(words, tiles)
        # TEST = 1 tile = 2 points
        # ST = 1 tile = 2 points
        # ING = 1 tile = 2 points
        assert total == 6

    def test_empty_word_set(self) -> None:
        """Empty word set returns 0 points."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"))
        total = calculate_total_points(set(), tiles)
        assert total == 0


class TestCalculateHintPenalty:
    """Tests for calculate_hint_penalty function."""

    def test_first_hint_penalty(self) -> None:
        """First hint has 30 second penalty."""
        assert calculate_hint_penalty(1) == 30_000

    def test_second_hint_penalty(self) -> None:
        """Second hint has 60 second penalty."""
        assert calculate_hint_penalty(2) == 60_000

    def test_third_hint_penalty(self) -> None:
        """Third hint has 120 second penalty."""
        assert calculate_hint_penalty(3) == 120_000

    def test_fourth_hint_penalty(self) -> None:
        """Fourth hint has 240 second penalty."""
        assert calculate_hint_penalty(4) == 240_000

    def test_fifth_hint_penalty(self) -> None:
        """Fifth hint has 480 second penalty."""
        assert calculate_hint_penalty(5) == 480_000

    def test_sixth_hint_penalty(self) -> None:
        """Sixth+ hint caps at fifth penalty level."""
        assert calculate_hint_penalty(6) == 480_000
        assert calculate_hint_penalty(10) == 480_000


class TestGetUnfoundQuartileHint:
    """Tests for get_unfound_quartile_hint function."""

    @pytest.fixture
    def hint_dictionary(self) -> Dictionary:
        """Create a dictionary with definitions.

        Returns:
            A Dictionary with test words and definitions.
        """
        root = TrieNode()
        word1 = TrieNode(is_word=True, definition="Definition for WORD1")
        word2 = TrieNode(is_word=True, definition="Definition for WORD2")
        root.children["W"] = TrieNode()
        root.children["W"].children["O"] = TrieNode()
        root.children["W"].children["O"].children["R"] = TrieNode()
        root.children["W"].children["O"].children["R"].children["D"] = TrieNode()
        root.children["W"].children["O"].children["R"].children["D"].children["1"] = word1
        root.children["W"].children["O"].children["R"].children["D"].children["2"] = word2
        return Dictionary(root)

    def test_returns_unfound_quartile(self, hint_dictionary: Dictionary) -> None:
        """Returns word and definition for unfound quartile."""
        quartiles = ("WORD1", "WORD2", "WORD3", "WORD4", "WORD5")
        found = {"WORD3", "WORD4", "WORD5"}
        result = get_unfound_quartile_hint(quartiles, found, hint_dictionary)
        assert result is not None
        word, definition = result
        assert word in {"WORD1", "WORD2"}
        # The exact word returned depends on set iteration order
        assert definition == f"Definition for {word}"

    def test_returns_none_when_all_found(self, hint_dictionary: Dictionary) -> None:
        """Returns None when all quartiles are found."""
        quartiles = ("WORD1", "WORD2", "WORD3", "WORD4", "WORD5")
        found = {"WORD1", "WORD2", "WORD3", "WORD4", "WORD5"}
        result = get_unfound_quartile_hint(quartiles, found, hint_dictionary)
        assert result is None

    def test_handles_missing_definition(self, hint_dictionary: Dictionary) -> None:
        """Returns default message when definition is missing."""
        # Add a word without definition
        quartiles = ("WORD1", "NOWORD", "WORD3", "WORD4", "WORD5")
        found = {"WORD3", "WORD4", "WORD5"}
        result = get_unfound_quartile_hint(quartiles, found, hint_dictionary)
        assert result is not None
        word, definition = result
        if word != "WORD1":
            assert definition == "No definition available"


class TestIsQuartileWord:
    """Tests for is_quartile_word function."""

    def test_four_tile_word_is_quartile(self) -> None:
        """Word using 4 tiles returns True."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"), Tile(2, "IN"), Tile(3, "GG"))
        assert is_quartile_word("TESTINGG", tiles) is True

    def test_three_tile_word_not_quartile(self) -> None:
        """Word using 3 tiles returns False."""
        tiles = (Tile(0, "TE"), Tile(1, "ST"), Tile(2, "ING"))
        assert is_quartile_word("TESTING", tiles) is False

    def test_non_formable_word_not_quartile(self) -> None:
        """Word that can't be formed returns False."""
        tiles = (Tile(0, "AB"), Tile(1, "CD"))
        assert is_quartile_word("TEST", tiles) is False
