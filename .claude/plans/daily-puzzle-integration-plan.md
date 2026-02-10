# Plan: Fix Section 08 Daily Puzzle System Integration Gaps

## Overview

The automated coding agent implemented solid backend infrastructure (puzzle scheduler, daily scheduler, `already_played` tracking) but left critical frontend features incomplete. This plan fixes those gaps.

## Current State

| Feature | Backend | Frontend |
|---------|---------|----------|
| Puzzle generation (lazy + scheduled) | ✅ Complete | - |
| First-play-wins enforcement | ✅ Complete | ⚠️ Data received, no UI |
| Session resume | ❌ Missing | ❌ Missing |
| Timezone handling | ⚠️ Server UTC only | ❌ No client date handling |
| Player identity persistence | ✅ Device fingerprint | ❌ No usePlayer hook |
| AlreadyPlayed UI component | - | ❌ Missing |
| Countdown timer | - | ❌ Missing |

## Implementation Steps

### Step 1: Create Timezone Utilities

**File:** `frontend/src/utils/timezone.ts` (new)

```typescript
/**
 * Get the local puzzle date as YYYY-MM-DD string.
 * Uses the client's local timezone to determine "today".
 */
export function getLocalPuzzleDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Get milliseconds until next local midnight.
 */
export function getTimeUntilNextPuzzle(): number {
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(0, 0, 0, 0);
  return tomorrow.getTime() - now.getTime();
}

/**
 * Format milliseconds into "Xh Ym Zs" format for countdown display.
 */
export function formatCountdown(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  const remainingSeconds = seconds % 60;
  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (remainingMinutes > 0) parts.push(`${remainingMinutes}m`);
  if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds}s`);
  return parts.join(' ');
}
```

---

### Step 2: Create usePlayer Hook

**File:** `frontend/src/hooks/usePlayer.ts` (new)

```typescript
import { useState, useEffect, useCallback } from 'react';

const PLAYER_STORAGE_KEY = 'quartiles_player';
const PLAYER_VALIDITY_MS = 30 * 24 * 60 * 60 * 1000; // 30 days

interface StoredPlayer {
  playerId: string;
  displayName: string;
  timestamp: number;
}

export function usePlayer() {
  const [playerId, setPlayerId] = useState<string | null>(() =>
    localStorage.getItem(PLAYER_STORAGE_KEY) ? JSON.parse(localStorage.getItem(PLAYER_STORAGE_KEY)!).playerId : null
  );
  const [displayName, setDisplayName] = useState<string | null>(() =>
    localStorage.getItem(PLAYER_STORAGE_KEY) ? JSON.parse(localStorage.getItem(PLAYER_STORAGE_KEY)!).displayName : null
  );

  const savePlayer = useCallback((id: string, name: string) => {
    const stored: StoredPlayer = { playerId: id, displayName: name, timestamp: Date.now() };
    localStorage.setItem(PLAYER_STORAGE_KEY, JSON.stringify(stored));
    setPlayerId(id);
    setDisplayName(name);
  }, []);

  const clearPlayer = useCallback(() => {
    localStorage.removeItem(PLAYER_STORAGE_KEY);
    setPlayerId(null);
    setDisplayName(null);
  }, []);

  return {
    playerId,
    displayName,
    savePlayer,
    clearPlayer,
    isReturningPlayer: playerId !== null,
  };
}
```

---

### Step 3: Create AlreadyPlayed Component

**File:** `frontend/src/components/Game/AlreadyPlayed.tsx` (new)

```typescript
import { useEffect, useState } from 'react';
import { Trophy, Clock, TrendingUp } from 'lucide-react';
import { formatCountdown, getTimeUntilNextPuzzle } from '@/utils/timezone';
import { cn } from '@/lib/utils';

export interface AlreadyPlayedProps {
  finalScore: number;
  solveTimeMs?: number | null;
  wordsFound: string[];
  leaderboardRank?: number | null;
  className?: string;
}

export function AlreadyPlayed({
  finalScore,
  solveTimeMs,
  wordsFound,
  leaderboardRank,
  className,
}: AlreadyPlayedProps) {
  const [timeRemaining, setTimeRemaining] = useState(getTimeUntilNextPuzzle());

  useEffect(() => {
    const interval = setInterval(() => setTimeRemaining(getTimeUntilNextPuzzle()), 1000);
    return () => clearInterval(interval);
  }, []);

  const formatSolveTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className={cn('flex flex-col items-center gap-6 w-full max-w-2xl mx-auto', className)}>
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">You've already played today!</h2>
        <p className="text-muted-foreground">Come back tomorrow for a new puzzle</p>
      </div>

      <div className="bg-base-100 rounded-xl p-6 card-organic w-full">
        <div className="flex items-center justify-center gap-3">
          <Clock className="h-5 w-5 text-primary" />
          <div className="text-center">
            <div className="text-sm text-muted-foreground">Next puzzle in</div>
            <div className="text-2xl font-bold text-primary" data-testid="countdown">
              {formatCountdown(timeRemaining)}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full">
        <div className="bg-base-100 rounded-xl p-4 card-organic text-center">
          <Trophy className="h-5 w-5 mx-auto mb-2 text-warning" />
          <div className="text-sm text-muted-foreground mb-1">Score</div>
          <div className="text-3xl font-bold" data-testid="final-score">{finalScore}</div>
        </div>

        {solveTimeMs != null && (
          <div className="bg-base-100 rounded-xl p-4 card-organic text-center">
            <Clock className="h-5 w-5 mx-auto mb-2 text-info" />
            <div className="text-sm text-muted-foreground mb-1">Time</div>
            <div className="text-2xl font-bold" data-testid="solve-time">{formatSolveTime(solveTimeMs)}</div>
          </div>
        )}

        {leaderboardRank != null && (
          <div className="bg-base-100 rounded-xl p-4 card-organic text-center">
            <TrendingUp className="h-5 w-5 mx-auto mb-2 text-success" />
            <div className="text-sm text-muted-foreground mb-1">Rank</div>
            <div className="text-2xl font-bold text-success" data-testid="leaderboard-rank">#{leaderboardRank}</div>
          </div>
        )}
      </div>

      <div className="bg-base-100 rounded-xl p-4 card-organic w-full">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Words Found</h3>
          <span className="text-sm text-muted-foreground">{wordsFound.length} words</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {wordsFound.map((word) => <span key={word} className="badge badge-lg badge-outline">{word}</span>)}
        </div>
      </div>

      <button type="button" className="btn btn-outline btn-lg btn-organic" onClick={() => window.location.href = '/leaderboard'}>
        <TrendingUp className="mr-2 h-4 w-4" />View Leaderboard
      </button>
    </div>
  );
}
```

---

### Step 4: Update Backend Game Route

**File:** `backend/app/api/routes/game.py`

**Change 1:** Add `puzzle_date` to `GameStartRequest` (around line 51):

```python
class GameStartRequest(BaseModel):
    """Request to start a new game session."""
    device_fingerprint: str
    player_id: str | None = None
    puzzle_date: str | None = None  # YYYY-MM-DD format, defaults to server UTC today
```

**Change 2:** Update `start_game` endpoint (around line 274) to use `puzzle_date`:

```python
# Parse puzzle_date or use server UTC today
if request.puzzle_date:
    try:
        target_date = datetime.strptime(request.puzzle_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="puzzle_date must be in YYYY-MM-DD format"
        )
else:
    target_date = datetime.now(UTC).date()

# Get or create puzzle for target date
puzzle = ensure_puzzle_exists_for_date(target_date, db)
```

**Change 3:** Add session resume logic (insert after line 277, before `_get_existing_session`):

```python
# Check for uncompleted session (resume logic)
uncompleted_session = db.exec(
    select(GameSession)
    .where(GameSession.player_id == player.id)
    .where(GameSession.puzzle_id == puzzle.id)
    .where(GameSession.completed_at.is_(None))
).first()

if uncompleted_session:
    # Resume existing session
    return GameStartResponse(
        session_id=str(uncompleted_session.id),
        player_id=str(player.id),
        display_name=player.display_name,
        tiles=_parse_tiles_json(puzzle.tiles_json),
        already_played=False,
    )
```

---

### Step 5: Update useGame Hook

**File:** `frontend/src/hooks/useGame.ts`

Add import at top:
```typescript
import { getLocalPuzzleDate } from "@/utils/timezone"
```

Update `useGameStart` mutation (around line 47):
```typescript
const response = await GameService.startGame({
  requestBody: {
    device_fingerprint: getDeviceFingerprint(),
    puzzle_date: getLocalPuzzleDate(),
  },
})
```

---

### Step 6: Update Game Component

**File:** `frontend/src/components/Game/Game.tsx`

**Change 1:** Add import:
```typescript
import { AlreadyPlayed } from './AlreadyPlayed'
```

**Change 2:** Add already-played state (after error state check, around line 275):

```typescript
// Already played state
if (gameSession?.alreadyPlayed && gameSession.previousResult) {
  return (
    <div className="flex flex-col items-center gap-6 w-full">
      <AlreadyPlayed
        finalScore={gameSession.previousResult.finalScore}
        solveTimeMs={gameSession.previousResult.solveTimeMs}
        wordsFound={gameSession.previousResult.wordsFound}
        leaderboardRank={gameSession.previousResult.leaderboardRank}
        className="w-full"
      />
    </div>
  )
}
```

---

### Step 7: Update Component Exports

**File:** `frontend/src/components/Game/index.ts`

Add export:
```typescript
export { AlreadyPlayed } from './AlreadyPlayed'
```

---

### Step 8: Generate API Client

After backend changes:
```bash
make generate-client
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/utils/timezone.ts` | Timezone/date utilities |
| `frontend/src/hooks/usePlayer.ts` | Player identity management |
| `frontend/src/components/Game/AlreadyPlayed.tsx` | Already-played UI with countdown |

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/api/routes/game.py` | Add `puzzle_date` param, session resume logic |
| `frontend/src/hooks/useGame.ts` | Send `puzzle_date` to API |
| `frontend/src/components/Game/Game.tsx` | Render AlreadyPlayed component |
| `frontend/src/components/Game/index.ts` | Export AlreadyPlayed |

## Verification

After implementation, test:

1. **Backend:**
   - `POST /api/v1/game/start` accepts optional `puzzle_date` parameter
   - Uncompleted sessions are resumed (new session not created)
   - Completed sessions return `already_played: true` with previous results

2. **Frontend:**
   - AlreadyPlayed component displays when user completed today's puzzle
   - Countdown timer updates every second
   - "View Leaderboard" button navigates correctly
   - Game board is hidden when already played
   - `getLocalPuzzleDate()` returns client's local date in YYYY-MM-DD format

3. **Integration:**
   - Complete a puzzle, refresh page → see AlreadyPlayed UI
   - Change system timezone → puzzle date reflects local date
   - Close browser mid-game, reopen → session resumes

## Implementation Order

1. `frontend/src/utils/timezone.ts` (foundation)
2. `frontend/src/hooks/usePlayer.ts` (independent)
3. `frontend/src/components/Game/AlreadyPlayed.tsx` (depends on timezone)
4. `backend/app/api/routes/game.py` (API changes)
5. `frontend/src/hooks/useGame.ts` (use timezone)
6. `frontend/src/components/Game/Game.tsx` (integrate AlreadyPlayed)
7. `frontend/src/components/Game/index.ts` (exports)
8. `make generate-client` (regenerate types)
