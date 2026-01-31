"""Shared fixtures for game module tests."""

import pytest

from app.game.dictionary import Dictionary, TrieNode
from app.game.generator import generate_puzzle
from app.game.types import Puzzle, Tile


@pytest.fixture(scope="session")
def sample_dictionary() -> Dictionary:
    """Create a small dictionary for testing.

    Returns:
        A Dictionary instance with sample words.
    """
    root = TrieNode()

    # Build simple trie structure
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

    # Add "TEST"
    te_node = TrieNode()
    st_node = TrieNode(is_word=True, definition="A trial")
    root.children["T"] = te_node
    te_node.children["E"] = st_node

    # Add "TESTING"
    ing_node = TrieNode(is_word=True, definition="The act of testing")
    i_node = TrieNode()
    st_node.children["I"] = i_node
    i_node.children["N"] = TrieNode()
    i_node.children["N"].children["G"] = ing_node

    # Add "QUARTILE"
    q_node = TrieNode()
    u_node = TrieNode()
    root.children["Q"] = q_node
    q_node.children["U"] = u_node
    u_node.children["A"] = TrieNode()
    u_node.children["A"].children["R"] = TrieNode()
    u_node.children["A"].children["R"].children["T"] = TrieNode()
    u_node.children["A"].children["R"].children["T"].children["I"] = TrieNode()
    u_node.children["A"].children["R"].children["T"].children["I"].children["L"] = TrieNode()
    u_node.children["A"].children["R"].children["T"].children["I"].children["L"].children["E"] = TrieNode(
        is_word=True, definition="One of four equal parts"
    )

    return Dictionary(root)


@pytest.fixture(scope="session")
def sample_tiles() -> tuple[Tile, ...]:
    """Create sample tiles for testing.

    Returns:
        A tuple of 4 Tile objects.
    """
    return (
        Tile(id=0, letters="TE"),
        Tile(id=1, letters="ST"),
        Tile(id=2, letters="IN"),
        Tile(id=3, letters="G"),
    )


@pytest.fixture(scope="session")
def sample_puzzle(_sample_tiles: tuple[Tile, ...]) -> Puzzle:
    """Create a sample puzzle for testing.

    Args:
        _sample_tiles: Sample tiles fixture (unused).

    Returns:
        A Puzzle with sample data.
    """
    # Create 20 tiles (repeating sample tiles for simplicity)
    tiles = tuple(Tile(id=i, letters="AB") for i in range(20))
    return Puzzle(
        tiles=tiles,
        quartile_words=("WORDONE", "WORDTWO", "WORDTHREE", "WORDFOUR", "WORDFIVE"),
        valid_words=frozenset({"TEST", "TESTING", "BEST", "REST"}),
        total_points=150,
    )


@pytest.fixture(scope="session")
def real_dictionary() -> Dictionary:
    """Load the real dictionary for integration tests.

    Returns:
        The actual Dictionary instance from dictionary.bin.
    """
    return Dictionary.load()


@pytest.fixture(scope="session")
def generated_puzzle(real_dictionary: Dictionary) -> Puzzle:
    """Generate a puzzle once per test session for integration tests.

    This fixture generates a puzzle using the real dictionary and caches it
    for the entire test session, significantly speeding up tests that need
    a generated puzzle.

    Args:
        real_dictionary: The real dictionary fixture.

    Returns:
        A Puzzle instance generated from the real dictionary.
    """
    puzzle = generate_puzzle(real_dictionary, excluded_quartiles=set())
    assert puzzle is not None, "Failed to generate puzzle"
    return puzzle
