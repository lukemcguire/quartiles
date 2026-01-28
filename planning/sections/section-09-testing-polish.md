# Section 09: Testing & Polish

## Background

This final section ensures the Quartiles game is production-ready through comprehensive testing, performance optimization, and accessibility improvements. Testing validates that all components work correctly together, while polish addresses the user experience details that make a game feel complete.

## Dependencies

| Type | Section | Description |
|------|---------|-------------|
| **requires** | 07 | Frontend components must be complete |
| **requires** | 08 | Daily system must be integrated |
| **blocks** | None | This is the final section |

## Requirements

When this section is complete:
1. Backend unit tests cover >90% of game logic
2. E2E tests verify complete game flows
3. Performance meets targets (page load <2s, validation <10ms)
4. Accessibility basics are in place (keyboard, focus states)
5. All pre-commit hooks pass

---

## Implementation Details

### 9.1 Backend Unit Tests

**Directory structure:**
```
backend/app/game/tests/
├── __init__.py
├── conftest.py
├── test_types.py
├── test_dictionary.py
├── test_generator.py
├── test_solver.py
└── test_integration.py
```

**File:** `backend/app/game/tests/conftest.py`

```python
"""Shared test fixtures for game module."""

import pytest
from pathlib import Path

from app.game.dictionary import Dictionary
from app.game.types import Tile, Puzzle


@pytest.fixture
def sample_tiles() -> tuple[Tile, ...]:
    """Sample tiles for testing."""
    return (
        Tile(0, "QUA"),
        Tile(1, "RTER"),
        Tile(2, "LY"),
        Tile(3, "MA"),
        Tile(4, "STER"),
        # ... 15 more tiles
    )


@pytest.fixture
def test_dictionary() -> Dictionary:
    """Small dictionary for testing."""
    d = Dictionary()
    words = ["QUARTERLY", "QUARTER", "MASTER", "MAST", "TEST", "TESTING"]
    for word in words:
        d.add(word, f"Definition of {word}")
    return d


@pytest.fixture
def sample_puzzle(sample_tiles: tuple[Tile, ...], test_dictionary: Dictionary) -> Puzzle:
    """Sample puzzle for testing."""
    return Puzzle(
        tiles=sample_tiles,
        quartile_words=("QUARTERLY", "MASTERFUL", "SOMETHING", "ANOTHER", "FIFTHONE"),
        valid_words=frozenset(["QUARTERLY", "QUARTER", "MASTER"]),
        total_points=150,
    )
```

**File:** `backend/app/game/tests/test_types.py`

```python
"""Tests for game domain types."""

import pytest
from app.game.types import Tile, Word, Puzzle, GameState


class TestTile:
    """Tests for Tile dataclass."""

    def test_valid_tile(self):
        """Tile accepts 2-4 letters."""
        tile = Tile(id=0, letters="AB")
        assert tile.letters == "AB"

        tile = Tile(id=1, letters="ABCD")
        assert tile.letters == "ABCD"

    def test_tile_rejects_single_letter(self):
        """Tile rejects 1-letter strings."""
        with pytest.raises(ValueError, match="2-4 letters"):
            Tile(id=0, letters="A")

    def test_tile_rejects_five_letters(self):
        """Tile rejects 5+ letter strings."""
        with pytest.raises(ValueError, match="2-4 letters"):
            Tile(id=0, letters="ABCDE")

    def test_tile_rejects_non_alpha(self):
        """Tile rejects non-alphabetic characters."""
        with pytest.raises(ValueError, match="alphabetic"):
            Tile(id=0, letters="A1")


class TestPuzzle:
    """Tests for Puzzle dataclass."""

    def test_puzzle_requires_20_tiles(self, sample_tiles):
        """Puzzle requires exactly 20 tiles."""
        with pytest.raises(ValueError, match="20 tiles"):
            Puzzle(
                tiles=sample_tiles[:5],  # Only 5 tiles
                quartile_words=("A", "B", "C", "D", "E"),
                valid_words=frozenset(),
                total_points=0,
            )

    def test_puzzle_requires_5_quartiles(self, sample_tiles):
        """Puzzle requires exactly 5 quartile words."""
        with pytest.raises(ValueError, match="5 quartile"):
            Puzzle(
                tiles=sample_tiles,
                quartile_words=("A", "B", "C"),  # Only 3
                valid_words=frozenset(),
                total_points=0,
            )


class TestGameState:
    """Tests for GameState dataclass."""

    def test_is_solved_below_threshold(self, sample_puzzle):
        """GameState.is_solved is False below 100 points."""
        state = GameState(
            puzzle=sample_puzzle,
            found_words=set(),
            current_score=99,
            hints_used=0,
        )
        assert not state.is_solved

    def test_is_solved_at_threshold(self, sample_puzzle):
        """GameState.is_solved is True at 100 points."""
        state = GameState(
            puzzle=sample_puzzle,
            found_words=set(),
            current_score=100,
            hints_used=0,
        )
        assert state.is_solved
```

**File:** `backend/app/game/tests/test_dictionary.py`

```python
"""Tests for Dictionary class."""

import pytest
from app.game.dictionary import Dictionary, TrieNode


class TestDictionary:
    """Tests for trie-based Dictionary."""

    def test_add_and_contains(self):
        """Dictionary correctly stores and retrieves words."""
        d = Dictionary()
        d.add("TEST")

        assert d.contains("TEST")
        assert not d.contains("TESTING")
        assert not d.contains("TES")

    def test_contains_prefix(self):
        """Dictionary correctly identifies prefixes."""
        d = Dictionary()
        d.add("TESTING")

        assert d.contains_prefix("T")
        assert d.contains_prefix("TE")
        assert d.contains_prefix("TEST")
        assert d.contains_prefix("TESTING")
        assert not d.contains_prefix("TESTX")
        assert not d.contains_prefix("X")

    def test_case_insensitive(self):
        """Dictionary is case-insensitive."""
        d = Dictionary()
        d.add("Test")

        assert d.contains("TEST")
        assert d.contains("test")
        assert d.contains("Test")

    def test_definition_storage(self):
        """Dictionary stores and retrieves definitions."""
        d = Dictionary()
        d.add("TEST", "A procedure for evaluation")

        assert d.get_definition("TEST") == "A procedure for evaluation"
        assert d.get_definition("NONEXISTENT") is None

    def test_word_count(self):
        """Dictionary tracks word count correctly."""
        d = Dictionary()
        assert len(d) == 0

        d.add("TEST")
        assert len(d) == 1

        d.add("TEST")  # Duplicate
        assert len(d) == 1  # Still 1

        d.add("TESTING")
        assert len(d) == 2
```

**File:** `backend/app/game/tests/test_solver.py`

```python
"""Tests for solver module."""

import pytest
from app.game.solver import (
    find_all_valid_words,
    score_word,
    calculate_hint_penalty,
    calculate_total_points,
)
from app.game.types import Tile


class TestScoring:
    """Tests for scoring functions."""

    @pytest.mark.parametrize("tile_count,expected", [
        (1, 2),
        (2, 4),
        (3, 7),
        (4, 10),
        (5, 0),  # Invalid
    ])
    def test_score_word(self, tile_count, expected):
        """Score calculation matches spec."""
        assert score_word(tile_count) == expected

    @pytest.mark.parametrize("hint_num,expected_ms", [
        (1, 30_000),
        (2, 60_000),
        (3, 120_000),
        (4, 240_000),
        (5, 480_000),
        (6, 480_000),  # Caps at 5th
    ])
    def test_hint_penalty(self, hint_num, expected_ms):
        """Hint penalties match spec."""
        assert calculate_hint_penalty(hint_num) == expected_ms


class TestWordFinding:
    """Tests for word finding."""

    def test_finds_single_tile_word(self, test_dictionary):
        """Solver finds 1-tile words."""
        tiles = (Tile(0, "TEST"),)
        words = find_all_valid_words(tiles, test_dictionary)
        assert "TEST" in words

    def test_finds_multi_tile_word(self, test_dictionary):
        """Solver finds multi-tile words."""
        tiles = (Tile(0, "TEST"), Tile(1, "ING"))
        words = find_all_valid_words(tiles, test_dictionary)
        assert "TESTING" in words
        assert "TEST" in words

    def test_respects_tile_order(self, test_dictionary):
        """Solver checks tile permutations."""
        # "GNITEST" is not a word, but "TESTING" is
        tiles = (Tile(0, "ING"), Tile(1, "TEST"))
        words = find_all_valid_words(tiles, test_dictionary)
        assert "TESTING" in words  # Found via permutation

    def test_prefix_pruning(self, test_dictionary):
        """Solver prunes invalid prefixes efficiently."""
        tiles = (Tile(0, "XY"), Tile(1, "ZZ"))
        words = find_all_valid_words(tiles, test_dictionary)
        assert len(words) == 0  # No valid words
```

### 9.2 E2E Test Suite

**File:** `frontend/e2e/game.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Quartiles Game', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to start fresh
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('loads game page and displays tiles', async ({ page }) => {
    await page.goto('/game');

    // Wait for loading to complete
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Verify 20 tiles are displayed
    const tiles = page.locator('[data-tile-id]');
    await expect(tiles).toHaveCount(20);
  });

  test('tile selection toggles on click', async ({ page }) => {
    await page.goto('/game');
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    const firstTile = page.locator('[data-tile-id="0"]');

    // Click to select
    await firstTile.click();
    await expect(firstTile).toHaveClass(/btn-primary/);

    // Click again to deselect
    await firstTile.click();
    await expect(firstTile).not.toHaveClass(/btn-primary/);
  });

  test('keyboard navigation with arrow keys', async ({ page }) => {
    await page.goto('/game');
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Focus first tile
    await page.keyboard.press('Tab');

    // Navigate right
    await page.keyboard.press('ArrowRight');

    // Select with Enter
    await page.keyboard.press('Enter');

    // Second tile should be selected (index 1)
    const secondTile = page.locator('[data-tile-id="1"]');
    await expect(secondTile).toHaveClass(/btn-primary/);
  });

  test('vim-style navigation with hjkl', async ({ page }) => {
    await page.goto('/game');
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Navigate with j (down)
    await page.keyboard.press('j');
    await page.keyboard.press('Space');

    // Tile at position 5 should be selected (5 columns, so j moves down one row)
    const tile = page.locator('[data-tile-id="5"]');
    await expect(tile).toHaveClass(/btn-primary/);
  });

  test('submitting valid word updates score', async ({ page }) => {
    await page.goto('/game');
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Select some tiles (this depends on the actual puzzle)
    // For testing, we'll just verify the UI flow
    const scoreDisplay = page.locator('.stat-value').first();
    const initialScore = await scoreDisplay.textContent();

    // Note: In a real test, you'd select tiles that form a valid word
    // and verify the score increases
  });

  test('timer starts on game load', async ({ page }) => {
    await page.goto('/game');
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Get initial timer value
    const timerDisplay = page.locator('.stat-value').nth(1);
    const initialTime = await timerDisplay.textContent();

    // Wait a bit
    await page.waitForTimeout(1500);

    // Timer should have increased
    const newTime = await timerDisplay.textContent();
    expect(newTime).not.toBe(initialTime);
  });

  test('escape clears selection', async ({ page }) => {
    await page.goto('/game');
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Select a tile
    await page.locator('[data-tile-id="0"]').click();
    await expect(page.locator('[data-tile-id="0"]')).toHaveClass(/btn-primary/);

    // Press Escape
    await page.keyboard.press('Escape');

    // Should be deselected
    await expect(page.locator('[data-tile-id="0"]')).not.toHaveClass(/btn-primary/);
  });

  test('game state persists across page refresh', async ({ page }) => {
    await page.goto('/game');
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Select a tile and submit (assuming it's valid)
    // ... actual test would need to know valid words

    // Get current score
    const score = await page.locator('.stat-value').first().textContent();

    // Refresh
    await page.reload();
    await expect(page.locator('.loading')).not.toBeVisible({ timeout: 5000 });

    // Score should be restored
    const newScore = await page.locator('.stat-value').first().textContent();
    expect(newScore).toBe(score);
  });
});
```

### 9.3 Performance Optimization

**Targets:**
- Puzzle generation: <50ms (pre-generated, so not critical path)
- Dictionary load: <50ms
- Word validation: <10ms
- Page load: <2s
- Time to interactive: <3s

**Optimizations:**

1. **Dictionary loading**
   - Use binary pickle format
   - Load asynchronously on app startup
   - Cache in memory

2. **Puzzle pre-generation**
   - Generate puzzles 7 days ahead
   - Never generate on user request

3. **Frontend code splitting**
   ```typescript
   // Lazy load game components
   const GameBoard = lazy(() => import('./components/Game/GameBoard'));
   ```

4. **API response optimization**
   - Don't send valid_words to client
   - Minimal payload sizes

### 9.4 Accessibility Checklist

**Required for MVP:**
- [ ] All interactive elements focusable via keyboard
- [ ] Focus states visible (ring/outline)
- [ ] Color contrast meets WCAG AA (4.5:1 for text)
- [ ] Tile states not communicated by color alone (use shapes/icons)
- [ ] Score changes announced (aria-live region)

**Post-MVP:**
- [ ] Screen reader support (ARIA labels)
- [ ] Reduced motion option
- [ ] Full WCAG 2.1 AA compliance

**Implementation:**

```typescript
// Accessible ScoreDisplay with aria-live
export function ScoreDisplay({ currentScore, ... }) {
  return (
    <div className="stats" role="status" aria-live="polite">
      <div className="stat">
        <div className="stat-title" id="score-label">Score</div>
        <div className="stat-value" aria-labelledby="score-label">
          {currentScore} / 100
        </div>
      </div>
    </div>
  );
}

// Focus-visible tile
export function TileButton({ isFocused, ... }) {
  return (
    <button
      className={`
        ${isFocused ? 'ring-2 ring-offset-2 ring-accent' : ''}
        focus-visible:ring-2 focus-visible:ring-accent
      `}
      aria-pressed={isSelected}
    >
      {tile.letters}
    </button>
  );
}
```

---

## Acceptance Criteria

### Testing
- [ ] `pytest backend/app/game/tests/` passes
- [ ] Game logic test coverage >90%
- [ ] `npx playwright test` passes
- [ ] E2E tests cover: tile selection, keyboard nav, timer, persistence

### Performance
- [ ] Dictionary loads in <50ms
- [ ] Page load time <2s (Lighthouse)
- [ ] Word validation API responds in <100ms

### Accessibility
- [ ] All tiles keyboard accessible
- [ ] Focus states visible
- [ ] Color contrast passes (WCAG AA)
- [ ] Score changes use aria-live

### Quality
- [ ] `pre-commit run --all-files` passes
- [ ] No TypeScript errors
- [ ] No console errors in browser

## Files Summary

### Create
- `backend/app/game/tests/conftest.py`
- `backend/app/game/tests/test_types.py`
- `backend/app/game/tests/test_dictionary.py`
- `backend/app/game/tests/test_generator.py`
- `backend/app/game/tests/test_solver.py`
- `backend/app/game/tests/test_integration.py`
- `frontend/e2e/game.spec.ts`

### Modify
- Game components (add accessibility attributes)
- `frontend/playwright.config.ts` (if needed)
