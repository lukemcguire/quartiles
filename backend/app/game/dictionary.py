"""Trie-based dictionary for word validation.

This module is part of the pure Python game logic layer.
It has NO dependencies on FastAPI, SQLModel, or Pydantic.
"""

from __future__ import annotations

import pickle  # noqa: S403 - trusted data only
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
            message = f"Dictionary not found at {path}. Run 'python backend/scripts/build_dictionary.py' first."
            raise FileNotFoundError(message)

        with Path(path).open("rb") as f:
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
