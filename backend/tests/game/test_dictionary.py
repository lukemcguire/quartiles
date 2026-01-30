"""Tests for the Dictionary class."""

import pytest

from app.game.dictionary import Dictionary, TrieNode


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
        """Create a small dictionary for testing.

        Returns:
            A Dictionary instance with sample words.
        """
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
