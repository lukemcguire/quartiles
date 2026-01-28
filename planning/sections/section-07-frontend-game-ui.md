# Section 07: Frontend Game UI Components

## Background

The Quartiles frontend provides the interactive game experience: a 4x5 tile grid, word formation zone, score/timer display, and found words list. This section implements all game UI components using daisyUI (replacing shadcn/ui) and integrates with the game API.

Key requirements:
1. **Responsive design** - Works on desktop and mobile
2. **Keyboard support** - Arrow keys + vim-style (hjkl) navigation
3. **State persistence** - Game survives page refresh via localStorage
4. **Server-authoritative** - Timer is display-only; server calculates actual time

## Dependencies

| Type | Section | Description |
|------|---------|-------------|
| **requires** | 02 | Design foundation provides daisyUI theme and mockups |
| **requires** | 06 | Game API provides endpoints for word validation |
| **blocks** | 08 | Daily system needs frontend components |
| **blocks** | 09 | Testing requires components to test |

## Requirements

When this section is complete:
1. shadcn/ui components replaced with daisyUI
2. All game components render correctly
3. Tile selection with toggle behavior works
4. Keyboard navigation (arrows + hjkl) works
5. Game state persists across page refresh
6. Word validation calls API and shows feedback
7. Found words grouped by tile count

---

## Implementation Details

### 7.1 Remove shadcn/ui, Install daisyUI

**Remove shadcn dependencies:**
```bash
cd frontend
npm uninstall @radix-ui/react-* cmdk lucide-react class-variance-authority clsx tailwind-merge
rm -rf src/components/ui/
```

**Install daisyUI:**
```bash
npm install daisyui@^4
```

**Update tailwind.config.js:** (See Section 02 for theme configuration)

### 7.2 Game Route

**File:** `frontend/src/routes/_layout/game.tsx`

```typescript
import { createFileRoute } from '@tanstack/react-router';
import { GameBoard } from '@/components/Game/GameBoard';

export const Route = createFileRoute('/_layout/game')({
  component: GamePage,
});

function GamePage() {
  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Quartiles</h1>
      <GameBoard />
    </div>
  );
}
```

### 7.3 Game State Hook

**File:** `frontend/src/hooks/useGame.ts`

```typescript
import { useReducer, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

// Types
interface Tile {
  id: number;
  letters: string;
}

interface GameState {
  // Session
  sessionId: string | null;
  playerId: string | null;
  displayName: string | null;

  // Puzzle
  tiles: Tile[];
  selectedTileIds: number[];
  foundWords: string[];
  currentScore: number;

  // Timer (display only - server is authoritative)
  timerMs: number;
  isTimerRunning: boolean;

  // Progress
  isSolved: boolean;
  hintsUsed: number;
  phase: 'loading' | 'playing' | 'solved' | 'completed' | 'already_played';

  // UI state
  error: string | null;
  isSubmitting: boolean;
}

type GameAction =
  | { type: 'INIT_GAME'; payload: { sessionId: string; playerId: string; displayName: string; tiles: Tile[] } }
  | { type: 'ALREADY_PLAYED'; payload: { previousResult: any } }
  | { type: 'TOGGLE_TILE'; payload: { tileId: number } }
  | { type: 'CLEAR_SELECTION' }
  | { type: 'WORD_VALID'; payload: { word: string; points: number; isQuartile: boolean; currentScore: number; isSolved: boolean } }
  | { type: 'WORD_INVALID'; payload: { reason: string } }
  | { type: 'HINT_RECEIVED'; payload: { definition: string; hintsUsed: number } }
  | { type: 'TICK_TIMER' }
  | { type: 'STOP_TIMER' }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'SET_SUBMITTING'; payload: boolean }
  | { type: 'RESTORE_STATE'; payload: Partial<GameState> };

const STORAGE_KEY = 'quartiles_game_state';

const initialState: GameState = {
  sessionId: null,
  playerId: null,
  displayName: null,
  tiles: [],
  selectedTileIds: [],
  foundWords: [],
  currentScore: 0,
  timerMs: 0,
  isTimerRunning: false,
  isSolved: false,
  hintsUsed: 0,
  phase: 'loading',
  error: null,
  isSubmitting: false,
};

function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'INIT_GAME':
      return {
        ...state,
        ...action.payload,
        phase: 'playing',
        isTimerRunning: true,
      };

    case 'ALREADY_PLAYED':
      return {
        ...state,
        phase: 'already_played',
      };

    case 'TOGGLE_TILE': {
      const { tileId } = action.payload;
      const isSelected = state.selectedTileIds.includes(tileId);
      return {
        ...state,
        selectedTileIds: isSelected
          ? state.selectedTileIds.filter(id => id !== tileId)
          : [...state.selectedTileIds, tileId],
      };
    }

    case 'CLEAR_SELECTION':
      return { ...state, selectedTileIds: [] };

    case 'WORD_VALID':
      return {
        ...state,
        foundWords: [...state.foundWords, action.payload.word],
        currentScore: action.payload.currentScore,
        isSolved: action.payload.isSolved,
        selectedTileIds: [],
        phase: action.payload.isSolved ? 'solved' : state.phase,
        isTimerRunning: action.payload.isSolved ? false : state.isTimerRunning,
      };

    case 'WORD_INVALID':
      return { ...state, selectedTileIds: [] };

    case 'HINT_RECEIVED':
      return { ...state, hintsUsed: action.payload.hintsUsed };

    case 'TICK_TIMER':
      return { ...state, timerMs: state.timerMs + 100 };

    case 'STOP_TIMER':
      return { ...state, isTimerRunning: false };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'SET_SUBMITTING':
      return { ...state, isSubmitting: action.payload };

    case 'RESTORE_STATE':
      return { ...state, ...action.payload };

    default:
      return state;
  }
}

export function useGame() {
  const [state, dispatch] = useReducer(gameReducer, initialState, (initial) => {
    // Try to restore from localStorage
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // TODO: Validate session is still for today
        return { ...initial, ...parsed, phase: 'playing', isTimerRunning: !parsed.isSolved };
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    return initial;
  });

  // Persist to localStorage
  useEffect(() => {
    if (state.sessionId && state.phase !== 'loading') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        sessionId: state.sessionId,
        playerId: state.playerId,
        displayName: state.displayName,
        tiles: state.tiles,
        foundWords: state.foundWords,
        currentScore: state.currentScore,
        timerMs: state.timerMs,
        isSolved: state.isSolved,
        hintsUsed: state.hintsUsed,
      }));
    }
  }, [state]);

  // Timer
  useEffect(() => {
    if (!state.isTimerRunning) return;
    const interval = setInterval(() => {
      dispatch({ type: 'TICK_TIMER' });
    }, 100);
    return () => clearInterval(interval);
  }, [state.isTimerRunning]);

  // Actions
  const selectTile = useCallback((tileId: number) => {
    dispatch({ type: 'TOGGLE_TILE', payload: { tileId } });
  }, []);

  const clearSelection = useCallback(() => {
    dispatch({ type: 'CLEAR_SELECTION' });
  }, []);

  const submitWord = useCallback(async () => {
    if (state.selectedTileIds.length === 0 || !state.sessionId) return;

    const word = state.selectedTileIds
      .map(id => state.tiles.find(t => t.id === id)?.letters)
      .join('');

    dispatch({ type: 'SET_SUBMITTING', payload: true });

    try {
      const response = await fetch(`/api/v1/game/sessions/${state.sessionId}/word`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word }),
      });

      const data = await response.json();

      if (data.is_valid) {
        dispatch({
          type: 'WORD_VALID',
          payload: {
            word,
            points: data.points,
            isQuartile: data.is_quartile,
            currentScore: data.current_score,
            isSolved: data.is_solved,
          },
        });
        if (data.is_quartile) {
          toast.success(`Quartile! +${data.points} points`);
        } else {
          toast.success(`+${data.points} points`);
        }
      } else {
        dispatch({ type: 'WORD_INVALID', payload: { reason: data.reason } });
        // Trigger shake animation via CSS class
      }
    } catch (error) {
      toast.error('Failed to validate word');
    } finally {
      dispatch({ type: 'SET_SUBMITTING', payload: false });
    }
  }, [state.selectedTileIds, state.sessionId, state.tiles]);

  const requestHint = useCallback(async () => {
    if (!state.sessionId || state.hintsUsed >= 5) return;

    try {
      const response = await fetch(`/api/v1/game/sessions/${state.sessionId}/hint`, {
        method: 'POST',
      });
      const data = await response.json();

      dispatch({
        type: 'HINT_RECEIVED',
        payload: { definition: data.definition, hintsUsed: data.hints_used },
      });

      toast.info(`Hint: ${data.definition}`, { duration: 10000 });
    } catch {
      toast.error('Failed to get hint');
    }
  }, [state.sessionId, state.hintsUsed]);

  return {
    state,
    selectTile,
    clearSelection,
    submitWord,
    requestHint,
    dispatch,
  };
}
```

### 7.4 Keyboard Navigation Hook

**File:** `frontend/src/hooks/useKeyboardNavigation.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';

interface Tile {
  id: number;
  letters: string;
}

export function useKeyboardNavigation(
  tiles: Tile[],
  onSelect: (id: number) => void,
  onSubmit: () => void,
  onClear: () => void,
) {
  const [focusIndex, setFocusIndex] = useState(0);
  const COLS = 5;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Ignore if typing in an input
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return;
    }

    switch (e.key) {
      // Arrow keys
      case 'ArrowUp':
      case 'k': // vim
        e.preventDefault();
        setFocusIndex(i => Math.max(0, i - COLS));
        break;
      case 'ArrowDown':
      case 'j': // vim
        e.preventDefault();
        setFocusIndex(i => Math.min(tiles.length - 1, i + COLS));
        break;
      case 'ArrowLeft':
      case 'h': // vim
        e.preventDefault();
        setFocusIndex(i => Math.max(0, i - 1));
        break;
      case 'ArrowRight':
      case 'l': // vim
        e.preventDefault();
        setFocusIndex(i => Math.min(tiles.length - 1, i + 1));
        break;

      // Selection
      case 'Enter':
        e.preventDefault();
        if (e.shiftKey) {
          onSubmit();
        } else {
          onSelect(tiles[focusIndex]?.id);
        }
        break;
      case ' ':
        e.preventDefault();
        onSelect(tiles[focusIndex]?.id);
        break;

      // Clear
      case 'Escape':
        e.preventDefault();
        onClear();
        break;
    }
  }, [tiles, focusIndex, onSelect, onSubmit, onClear]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return focusIndex;
}
```

### 7.5 Game Board Component

**File:** `frontend/src/components/Game/GameBoard.tsx`

```typescript
import { useEffect } from 'react';
import { useGame } from '@/hooks/useGame';
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation';
import { TileGrid } from './TileGrid';
import { WordFormation } from './WordFormation';
import { ScoreDisplay } from './ScoreDisplay';
import { FoundWordsList } from './FoundWordsList';

export function GameBoard() {
  const { state, selectTile, clearSelection, submitWord, requestHint, dispatch } = useGame();

  const focusIndex = useKeyboardNavigation(
    state.tiles,
    selectTile,
    submitWord,
    clearSelection,
  );

  // Initialize game on mount
  useEffect(() => {
    async function initGame() {
      // Get or create player ID from localStorage
      let playerId = localStorage.getItem('quartiles_player_id');

      try {
        const response = await fetch('/api/v1/game/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            device_fingerprint: navigator.userAgent, // Simple fingerprint
            player_id: playerId,
          }),
        });

        const data = await response.json();

        // Store player ID for future sessions
        localStorage.setItem('quartiles_player_id', data.player_id);

        if (data.already_played) {
          dispatch({ type: 'ALREADY_PLAYED', payload: { previousResult: data.previous_result } });
        } else {
          dispatch({
            type: 'INIT_GAME',
            payload: {
              sessionId: data.session_id,
              playerId: data.player_id,
              displayName: data.display_name,
              tiles: data.tiles,
            },
          });
        }
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: 'Failed to start game' });
      }
    }

    if (state.phase === 'loading' && !state.sessionId) {
      initGame();
    }
  }, [state.phase, state.sessionId, dispatch]);

  if (state.phase === 'loading') {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (state.phase === 'already_played') {
    return (
      <div className="alert alert-info">
        <span>You already completed today's puzzle!</span>
      </div>
    );
  }

  const selectedTiles = state.selectedTileIds.map(
    id => state.tiles.find(t => t.id === id)!
  );

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Main game area */}
      <div className="flex-1 space-y-4">
        <ScoreDisplay
          currentScore={state.currentScore}
          solveThreshold={100}
          timerMs={state.timerMs}
          isSolved={state.isSolved}
          hintsUsed={state.hintsUsed}
        />

        <TileGrid
          tiles={state.tiles}
          selectedIds={state.selectedTileIds}
          foundQuartileIds={[]} // TODO: track which tiles formed quartiles
          focusIndex={focusIndex}
          onTileClick={selectTile}
        />

        <WordFormation
          selectedTiles={selectedTiles}
          onSubmit={submitWord}
          onClear={clearSelection}
          isSubmitting={state.isSubmitting}
        />

        <button
          className="btn btn-secondary"
          onClick={requestHint}
          disabled={state.hintsUsed >= 5 || state.isSolved}
        >
          Get Hint (+{getHintPenalty(state.hintsUsed + 1)}s)
        </button>
      </div>

      {/* Sidebar */}
      <div className="w-full lg:w-64">
        <FoundWordsList
          words={state.foundWords}
          tiles={state.tiles}
        />
      </div>
    </div>
  );
}

function getHintPenalty(hintNumber: number): number {
  const penalties: Record<number, number> = { 1: 30, 2: 60, 3: 120, 4: 240, 5: 480 };
  return penalties[hintNumber] || 480;
}
```

### 7.6 Tile Components

**File:** `frontend/src/components/Game/TileGrid.tsx`

```typescript
import { TileButton } from './TileButton';

interface Tile {
  id: number;
  letters: string;
}

interface TileGridProps {
  tiles: Tile[];
  selectedIds: number[];
  foundQuartileIds: number[];
  focusIndex: number;
  onTileClick: (id: number) => void;
}

export function TileGrid({
  tiles,
  selectedIds,
  foundQuartileIds,
  focusIndex,
  onTileClick,
}: TileGridProps) {
  return (
    <div className="grid grid-cols-5 gap-2 max-w-md">
      {tiles.map((tile, index) => (
        <TileButton
          key={tile.id}
          tile={tile}
          isSelected={selectedIds.includes(tile.id)}
          isQuartileFound={foundQuartileIds.includes(tile.id)}
          isFocused={index === focusIndex}
          onClick={() => onTileClick(tile.id)}
        />
      ))}
    </div>
  );
}
```

**File:** `frontend/src/components/Game/TileButton.tsx`

```typescript
interface Tile {
  id: number;
  letters: string;
}

interface TileButtonProps {
  tile: Tile;
  isSelected: boolean;
  isQuartileFound: boolean;
  isFocused: boolean;
  onClick: () => void;
}

export function TileButton({
  tile,
  isSelected,
  isQuartileFound,
  isFocused,
  onClick,
}: TileButtonProps) {
  return (
    <button
      className={`
        btn btn-lg aspect-square font-bold text-lg
        transition-all duration-200
        animate-float
        ${isSelected ? 'btn-primary ring-2 ring-primary ring-offset-2' : 'btn-neutral'}
        ${isQuartileFound ? 'bg-success/20' : ''}
        ${isFocused ? 'ring-2 ring-accent' : ''}
        hover:scale-105
      `}
      onClick={onClick}
      data-tile-id={tile.id}
    >
      {tile.letters}
    </button>
  );
}
```

### 7.7 Other Components

**File:** `frontend/src/components/Game/WordFormation.tsx`

```typescript
interface Tile {
  id: number;
  letters: string;
}

interface WordFormationProps {
  selectedTiles: Tile[];
  onSubmit: () => void;
  onClear: () => void;
  isSubmitting: boolean;
}

export function WordFormation({
  selectedTiles,
  onSubmit,
  onClear,
  isSubmitting,
}: WordFormationProps) {
  const word = selectedTiles.map(t => t.letters).join('');

  return (
    <div className="flex items-center gap-4 p-4 bg-base-200 rounded-lg">
      <div className="text-2xl font-bold min-w-[200px] font-mono">
        {word || <span className="text-base-content/50">Select tiles...</span>}
      </div>
      <button
        className="btn btn-primary"
        onClick={onSubmit}
        disabled={selectedTiles.length === 0 || isSubmitting}
      >
        {isSubmitting ? <span className="loading loading-spinner"></span> : 'Submit'}
      </button>
      <button
        className="btn btn-ghost"
        onClick={onClear}
        disabled={selectedTiles.length === 0}
      >
        Clear
      </button>
    </div>
  );
}
```

**File:** `frontend/src/components/Game/ScoreDisplay.tsx`

```typescript
interface ScoreDisplayProps {
  currentScore: number;
  solveThreshold: number;
  timerMs: number;
  isSolved: boolean;
  hintsUsed: number;
}

export function ScoreDisplay({
  currentScore,
  solveThreshold,
  timerMs,
  isSolved,
  hintsUsed,
}: ScoreDisplayProps) {
  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="stats shadow w-full">
      <div className="stat">
        <div className="stat-title">Score</div>
        <div className={`stat-value ${isSolved ? 'text-success' : ''}`}>
          {currentScore} / {solveThreshold}
        </div>
      </div>
      <div className="stat">
        <div className="stat-title">Time</div>
        <div className="stat-value font-mono">{formatTime(timerMs)}</div>
      </div>
      {hintsUsed > 0 && (
        <div className="stat">
          <div className="stat-title">Hints</div>
          <div className="stat-value">{hintsUsed}</div>
        </div>
      )}
    </div>
  );
}
```

**File:** `frontend/src/components/Game/FoundWordsList.tsx`

```typescript
import { useMemo } from 'react';

interface Tile {
  id: number;
  letters: string;
}

interface FoundWordsListProps {
  words: string[];
  tiles: Tile[];
}

export function FoundWordsList({ words, tiles }: FoundWordsListProps) {
  const grouped = useMemo(() => {
    const groups: Record<number, string[]> = { 1: [], 2: [], 3: [], 4: [] };

    for (const word of words) {
      // Estimate tile count from word length (simplified)
      const tileCount = Math.min(4, Math.ceil(word.length / 3));
      groups[tileCount].push(word);
    }

    return groups;
  }, [words]);

  return (
    <div className="card bg-base-200">
      <div className="card-body">
        <h2 className="card-title">Found Words</h2>

        {[4, 3, 2, 1].map(count => (
          grouped[count].length > 0 && (
            <div key={count} className="mb-2">
              <h3 className="font-semibold text-sm text-base-content/70">
                {count}-tile ({grouped[count].length})
              </h3>
              <div className="flex flex-wrap gap-1">
                {grouped[count].map(word => (
                  <span key={word} className="badge badge-outline badge-sm">
                    {word}
                  </span>
                ))}
              </div>
            </div>
          )
        ))}

        {words.length === 0 && (
          <p className="text-base-content/50 text-sm">No words found yet</p>
        )}
      </div>
    </div>
  );
}
```

### 7.8 CSS Animations

**File:** `frontend/src/styles/animations.css`

```css
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-2px); }
}

@keyframes wobble {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-2deg); }
  75% { transform: rotate(2deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

.animate-wobble {
  animation: wobble 0.3s ease-in-out;
}

.animate-shake {
  animation: shake 0.5s ease-in-out;
}
```

---

## Acceptance Criteria

- [ ] shadcn/ui components removed from codebase
- [ ] daisyUI installed and configured
- [ ] `/game` route renders GameBoard component
- [ ] TileGrid displays 4x5 grid of tiles
- [ ] Clicking tile toggles selection (toggle behavior)
- [ ] Keyboard navigation works (arrows + hjkl)
- [ ] Word formation zone shows selected letters
- [ ] Submit button validates word via API
- [ ] Invalid word triggers shake animation
- [ ] Valid word shows toast and updates score
- [ ] Timer increments while playing
- [ ] Timer stops when solved (100 points)
- [ ] Found words grouped by tile count
- [ ] Game state persists across page refresh (localStorage)
- [ ] Hint button calls API and shows definition toast
- [ ] Responsive design works on mobile

## Files Summary

### Create
- `frontend/src/routes/_layout/game.tsx`
- `frontend/src/components/Game/GameBoard.tsx`
- `frontend/src/components/Game/TileGrid.tsx`
- `frontend/src/components/Game/TileButton.tsx`
- `frontend/src/components/Game/WordFormation.tsx`
- `frontend/src/components/Game/ScoreDisplay.tsx`
- `frontend/src/components/Game/FoundWordsList.tsx`
- `frontend/src/hooks/useGame.ts`
- `frontend/src/hooks/useKeyboardNavigation.ts`
- `frontend/src/styles/animations.css`

### Delete
- `frontend/src/components/ui/` (entire shadcn directory)
- `frontend/src/components/Items/` (scaffolding)

### Modify
- `frontend/package.json` (remove shadcn deps, add daisyui)
- `frontend/tailwind.config.js` (add daisyui plugin)
- `frontend/src/index.css` (import animations.css)
