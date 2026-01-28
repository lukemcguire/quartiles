# Section 08: Daily Puzzle System Integration

## Background

Quartiles is a daily word puzzle game where players compete for the fastest solve time on a shared daily puzzle. The core game mechanics (tile selection, word validation, scoring) are implemented in Sections 04-07, but the "daily" aspect requires additional infrastructure:

1. **One puzzle per day** - All players see the same puzzle on a given date
2. **First-play-wins** - Each player gets exactly one competitive attempt per puzzle
3. **Automatic generation** - New puzzles must be ready at midnight without manual intervention
4. **Global consistency** - Players in different timezones need a consistent experience

This section integrates the puzzle scheduler, player identity management, and timezone handling to create the complete daily puzzle experience.

## Requirements

When this section is complete:

1. A new puzzle is automatically available at midnight (server time) each day
2. Players can only submit one competitive result per puzzle
3. Returning players see their previous result instead of replaying
4. The system pre-generates puzzles 7 days ahead to ensure availability
5. Timezone handling allows players to play "today's puzzle" based on their local date
6. Player identity persists across sessions via localStorage and device fingerprint

## Dependencies

```yaml
requires:
  - "06"  # Game API Endpoints (provides /game/start, /game/sessions/{id}/submit)
  - "07"  # Frontend Game UI Components (provides useGame hook, GameBoard)

blocks:
  - "09"  # Testing & Polish (E2E tests depend on daily system)
```

## Implementation Details

### 8.1 First-Play-Wins Logic

The first-play-wins rule ensures competitive integrity: a player's first completed attempt is their official result for the leaderboard. Subsequent visits show their previous result.

#### Backend Implementation

**File:** `backend/app/services/first_play.py`

```python
from datetime import date
from uuid import UUID
from sqlmodel import Session, select
from app.models import GameSession, Player

async def check_already_played(
    player_id: UUID,
    puzzle_id: UUID,
    db: Session
) -> tuple[bool, GameSession | None]:
    """
    Check if player has already completed this puzzle.

    Returns:
        (already_played, previous_session) - previous_session is None if not played
    """
    existing = db.exec(
        select(GameSession)
        .where(GameSession.player_id == player_id)
        .where(GameSession.puzzle_id == puzzle_id)
        .where(GameSession.completed_at.is_not(None))
    ).first()

    return (existing is not None, existing)


async def get_or_create_session(
    player_id: UUID,
    puzzle_id: UUID,
    db: Session
) -> tuple[GameSession, bool]:
    """
    Get existing active session or create new one.

    Returns:
        (session, is_new) - is_new is False if resuming existing session
    """
    # Check for uncompleted session (resumable)
    active = db.exec(
        select(GameSession)
        .where(GameSession.player_id == player_id)
        .where(GameSession.puzzle_id == puzzle_id)
        .where(GameSession.completed_at.is_(None))
    ).first()

    if active:
        return (active, False)

    # Create new session
    session = GameSession(
        player_id=player_id,
        puzzle_id=puzzle_id,
        start_time=datetime.now(timezone.utc),
        words_found_json="[]",
        final_score=0,
        hints_used=0,
        hint_penalty_ms=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return (session, True)
```

#### API Integration

Update `POST /game/start` to enforce first-play-wins:

```python
@router.post("/start", response_model=GameStartResponse)
async def start_game(
    request: GameStartRequest,
    db: SessionDep
) -> GameStartResponse:
    """Start or resume a game session."""

    # Get or create player
    player = await get_or_create_player(
        device_fingerprint=request.device_fingerprint,
        player_id=request.player_id,
        db=db
    )

    # Get today's puzzle
    puzzle = await get_todays_puzzle(db)

    # Check first-play-wins
    already_played, previous_session = await check_already_played(
        player.id, puzzle.id, db
    )

    if already_played:
        return GameStartResponse(
            session_id=previous_session.id,
            player_id=str(player.id),
            display_name=player.display_name,
            tiles=deserialize_tiles(puzzle.tiles_json),
            already_played=True,
            previous_result=PreviousResultSchema(
                final_score=previous_session.final_score,
                solve_time_ms=previous_session.solve_time_ms,
                words_found=json.loads(previous_session.words_found_json),
            )
        )

    # Create or resume session
    session, is_new = await get_or_create_session(player.id, puzzle.id, db)

    return GameStartResponse(
        session_id=session.id,
        player_id=str(player.id),
        display_name=player.display_name,
        tiles=deserialize_tiles(puzzle.tiles_json),
        already_played=False,
        previous_result=None,
    )
```

### 8.2 Automatic Puzzle Generation

Puzzles are pre-generated to ensure availability and avoid generation latency during gameplay.

#### Puzzle Scheduler Service

**File:** `backend/app/services/puzzle_scheduler.py`

```python
from datetime import date, timedelta, datetime, timezone
from sqlmodel import Session, select
from app.models import Puzzle, QuartileCooldown
from app.game.generator import generate_puzzle
from app.game.dictionary import Dictionary

# Load dictionary once at module level
_dictionary: Dictionary | None = None

def get_dictionary() -> Dictionary:
    global _dictionary
    if _dictionary is None:
        _dictionary = Dictionary.load("backend/data/dictionary.bin")
    return _dictionary


async def ensure_puzzle_exists_for_date(
    target_date: date,
    db: Session
) -> Puzzle:
    """
    Get existing puzzle for date or generate a new one.

    This is the core function for on-demand puzzle generation.
    """
    # Check if puzzle already exists
    existing = db.exec(
        select(Puzzle).where(Puzzle.date == target_date)
    ).first()

    if existing:
        return existing

    # Get excluded quartiles (used in last 30 days)
    cooldown_cutoff = target_date - timedelta(days=30)
    cooled_down = db.exec(
        select(QuartileCooldown.word)
        .where(QuartileCooldown.last_used_date > cooldown_cutoff)
    ).all()
    excluded_quartiles = set(cooled_down)

    # Generate new puzzle
    dictionary = get_dictionary()
    puzzle_data = generate_puzzle(dictionary, excluded_quartiles)

    if puzzle_data is None:
        raise RuntimeError(f"Failed to generate puzzle for {target_date}")

    # Create database record
    puzzle = Puzzle(
        date=target_date,
        tiles_json=json.dumps([
            {"id": t.id, "letters": t.letters}
            for t in puzzle_data.tiles
        ]),
        quartile_words_json=json.dumps(list(puzzle_data.quartile_words)),
        valid_words_json=json.dumps(list(puzzle_data.valid_words)),
        total_available_points=puzzle_data.total_points,
        created_at=datetime.now(timezone.utc),
    )
    db.add(puzzle)

    # Update cooldowns for quartile words
    for word in puzzle_data.quartile_words:
        cooldown = db.exec(
            select(QuartileCooldown).where(QuartileCooldown.word == word)
        ).first()

        if cooldown:
            cooldown.last_used_date = target_date
        else:
            cooldown = QuartileCooldown(word=word, last_used_date=target_date)
            db.add(cooldown)

    db.commit()
    db.refresh(puzzle)

    return puzzle


async def generate_upcoming_puzzles(
    days_ahead: int = 7,
    db: Session = None
) -> list[date]:
    """
    Pre-generate puzzles for the next N days.

    Returns list of dates for which puzzles were generated.
    """
    generated_dates = []
    today = date.today()

    for offset in range(days_ahead):
        target_date = today + timedelta(days=offset)
        try:
            await ensure_puzzle_exists_for_date(target_date, db)
            generated_dates.append(target_date)
        except RuntimeError as e:
            # Log error but continue with other dates
            logger.error(f"Failed to generate puzzle for {target_date}: {e}")

    return generated_dates
```

#### Background Task / Cron Job

**Option A: APScheduler (in-process)**

**File:** `backend/app/core/scheduler.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.puzzle_scheduler import generate_upcoming_puzzles
from app.core.db import get_db_session

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(CronTrigger(hour=0, minute=0))
async def daily_puzzle_generation():
    """Generate puzzles at midnight server time."""
    async with get_db_session() as db:
        generated = await generate_upcoming_puzzles(days_ahead=7, db=db)
        logger.info(f"Generated puzzles for dates: {generated}")


def start_scheduler():
    """Call this from app startup."""
    scheduler.start()
```

**Option B: Celery Beat (separate worker)**

```python
# backend/app/tasks.py
from celery import Celery
from celery.schedules import crontab

app = Celery('quartiles')

@app.task
def generate_daily_puzzles():
    from app.services.puzzle_scheduler import generate_upcoming_puzzles
    # Sync wrapper for async function
    import asyncio
    asyncio.run(generate_upcoming_puzzles(days_ahead=7))

app.conf.beat_schedule = {
    'generate-puzzles-daily': {
        'task': 'app.tasks.generate_daily_puzzles',
        'schedule': crontab(hour=0, minute=0),
    },
}
```

**Recommendation:** Use APScheduler for simplicity in MVP; migrate to Celery if scaling requires it.

#### Startup Hook

**File:** `backend/app/main.py` (update)

```python
from contextlib import asynccontextmanager
from app.core.scheduler import start_scheduler
from app.services.puzzle_scheduler import ensure_puzzle_exists_for_date

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure today's puzzle exists
    async with get_db_session() as db:
        await ensure_puzzle_exists_for_date(date.today(), db)

    # Start background scheduler
    start_scheduler()

    yield

    # Shutdown: cleanup if needed


app = FastAPI(lifespan=lifespan)
```

### 8.3 Timezone Handling

The challenge: "today" means different things to players in different timezones. A player in Tokyo at 10am is 14 hours ahead of a player in San Francisco at 8pm the previous day.

#### Strategy: Client-Determined Date

The client determines which puzzle date to request based on local time. The server provides puzzles by date, not by "today."

#### Frontend Implementation

**File:** `frontend/src/utils/timezone.ts`

```typescript
/**
 * Get today's date in the user's local timezone.
 * Returns ISO format: YYYY-MM-DD
 */
export function getLocalPuzzleDate(): string {
  const now = new Date();
  // toLocaleDateString with 'en-CA' locale gives YYYY-MM-DD format
  return now.toLocaleDateString('en-CA');
}

/**
 * Check if a stored session date matches today's local date.
 */
export function isSessionForToday(sessionDate: string): boolean {
  return sessionDate === getLocalPuzzleDate();
}

/**
 * Get the next puzzle date (tomorrow in local time).
 */
export function getNextPuzzleDate(): string {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return tomorrow.toLocaleDateString('en-CA');
}

/**
 * Calculate time until next puzzle (local midnight).
 */
export function getTimeUntilNextPuzzle(): number {
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(0, 0, 0, 0);
  return tomorrow.getTime() - now.getTime();
}
```

#### API Date Parameter

**File:** `backend/app/api/routes/puzzle.py` (update)

```python
@router.get("/by-date/{puzzle_date}", response_model=PuzzleResponse)
async def get_puzzle_by_date(
    puzzle_date: date,
    db: SessionDep
) -> PuzzleResponse:
    """
    Get puzzle for a specific date.

    The client sends their local date; the server returns that puzzle.
    """
    puzzle = await ensure_puzzle_exists_for_date(puzzle_date, db)

    return PuzzleResponse(
        id=puzzle.id,
        date=puzzle.date,
        tiles=json.loads(puzzle.tiles_json),
        total_available_points=puzzle.total_available_points,
    )
```

#### Frontend API Call

**File:** `frontend/src/api/game.ts` (update)

```typescript
import { getLocalPuzzleDate } from '../utils/timezone';

export async function startGame(
  deviceFingerprint: string,
  playerId?: string
): Promise<GameStartResponse> {
  const puzzleDate = getLocalPuzzleDate();

  return apiClient.post('/game/start', {
    device_fingerprint: deviceFingerprint,
    player_id: playerId,
    puzzle_date: puzzleDate,  // Client sends local date
  });
}
```

### 8.4 Player Identity Management

Players need persistent identity across sessions for first-play-wins and leaderboard tracking.

#### Device Fingerprint

**File:** `frontend/src/utils/fingerprint.ts`

```typescript
import FingerprintJS from '@fingerprintjs/fingerprintjs';

let cachedFingerprint: string | null = null;

export async function getDeviceFingerprint(): Promise<string> {
  if (cachedFingerprint) {
    return cachedFingerprint;
  }

  // First check localStorage for existing fingerprint
  const stored = localStorage.getItem('device_fingerprint');
  if (stored) {
    cachedFingerprint = stored;
    return stored;
  }

  // Generate new fingerprint
  const fp = await FingerprintJS.load();
  const result = await fp.get();
  cachedFingerprint = result.visitorId;

  // Persist for consistency
  localStorage.setItem('device_fingerprint', cachedFingerprint);

  return cachedFingerprint;
}
```

#### Player ID Storage

**File:** `frontend/src/hooks/usePlayer.ts`

```typescript
const PLAYER_ID_KEY = 'quartiles_player_id';
const PLAYER_NAME_KEY = 'quartiles_player_name';

export function usePlayer() {
  const [playerId, setPlayerId] = useState<string | null>(() =>
    localStorage.getItem(PLAYER_ID_KEY)
  );
  const [displayName, setDisplayName] = useState<string | null>(() =>
    localStorage.getItem(PLAYER_NAME_KEY)
  );

  const savePlayer = useCallback((id: string, name: string) => {
    localStorage.setItem(PLAYER_ID_KEY, id);
    localStorage.setItem(PLAYER_NAME_KEY, name);
    setPlayerId(id);
    setDisplayName(name);
  }, []);

  const clearPlayer = useCallback(() => {
    localStorage.removeItem(PLAYER_ID_KEY);
    localStorage.removeItem(PLAYER_NAME_KEY);
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

### 8.5 Already-Played UI State

When a player has already completed today's puzzle, show their result instead of the game.

**File:** `frontend/src/components/Game/AlreadyPlayed.tsx`

```typescript
interface AlreadyPlayedProps {
  result: PreviousResult;
  displayName: string;
  onViewLeaderboard: () => void;
}

export function AlreadyPlayed({
  result,
  displayName,
  onViewLeaderboard
}: AlreadyPlayedProps) {
  return (
    <div className="card bg-base-200 shadow-xl max-w-md mx-auto">
      <div className="card-body text-center">
        <h2 className="card-title justify-center">
          Already Played Today!
        </h2>

        <p className="text-base-content/70">
          You completed today's puzzle as <strong>{displayName}</strong>
        </p>

        <div className="stats stats-vertical shadow mt-4">
          <div className="stat">
            <div className="stat-title">Final Score</div>
            <div className="stat-value">{result.final_score}</div>
          </div>

          {result.solve_time_ms && (
            <div className="stat">
              <div className="stat-title">Solve Time</div>
              <div className="stat-value">
                {formatTime(result.solve_time_ms)}
              </div>
            </div>
          )}

          <div className="stat">
            <div className="stat-title">Words Found</div>
            <div className="stat-value">{result.words_found.length}</div>
          </div>
        </div>

        <div className="card-actions justify-center mt-4">
          <button
            className="btn btn-primary"
            onClick={onViewLeaderboard}
          >
            View Leaderboard
          </button>
        </div>

        <p className="text-sm text-base-content/50 mt-4">
          Come back tomorrow for a new puzzle!
        </p>

        <CountdownTimer />
      </div>
    </div>
  );
}

function CountdownTimer() {
  const [timeLeft, setTimeLeft] = useState(getTimeUntilNextPuzzle());

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft(getTimeUntilNextPuzzle());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const hours = Math.floor(timeLeft / (1000 * 60 * 60));
  const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

  return (
    <div className="text-sm text-base-content/70">
      Next puzzle in: {hours}h {minutes}m {seconds}s
    </div>
  );
}
```

### 8.6 Game Hook Updates

Update useGame to handle the already-played state.

**File:** `frontend/src/hooks/useGame.ts` (additions)

```typescript
// Add to GameState interface
interface GameState {
  // ... existing fields
  phase: 'loading' | 'playing' | 'solved' | 'completed' | 'already_played';
  previousResult: PreviousResult | null;
}

// Update startGame action
const startGame = async () => {
  dispatch({ type: 'SET_LOADING' });

  try {
    const fingerprint = await getDeviceFingerprint();
    const response = await api.startGame(fingerprint, playerId);

    // Save player info
    savePlayer(response.player_id, response.display_name);

    if (response.already_played) {
      dispatch({
        type: 'SET_ALREADY_PLAYED',
        payload: {
          previousResult: response.previous_result,
          puzzle: response.tiles,
        }
      });
    } else {
      dispatch({
        type: 'SET_PLAYING',
        payload: {
          sessionId: response.session_id,
          puzzle: response.tiles,
        }
      });
    }
  } catch (error) {
    dispatch({ type: 'SET_ERROR', payload: error.message });
  }
};
```

## Acceptance Criteria

### First-Play-Wins
- [ ] Player can complete puzzle only once per day
- [ ] Second visit shows previous result with score and time
- [ ] Session can be resumed if browser closes before completion
- [ ] Device fingerprint + player ID combo is enforced server-side

### Automatic Generation
- [ ] Puzzle exists for today on first request (lazy generation)
- [ ] Background job pre-generates 7 days of puzzles
- [ ] Quartile word cooldown (30 days) is respected
- [ ] Generation failure is logged and handled gracefully
- [ ] Server startup ensures today's puzzle exists

### Timezone Handling
- [ ] Client sends local date to API
- [ ] Server returns puzzle for requested date
- [ ] Player in any timezone sees consistent puzzle for their local date
- [ ] Countdown timer shows time until local midnight

### Player Identity
- [ ] Device fingerprint generated on first visit
- [ ] Player ID persisted in localStorage
- [ ] Display name persisted in localStorage
- [ ] Returning player recognized across sessions
- [ ] Player can be linked to authenticated user (future)

### UI States
- [ ] Loading state while starting game
- [ ] Already-played state with previous result
- [ ] Countdown timer to next puzzle
- [ ] View leaderboard button from already-played screen

## Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/first_play.py` | First-play-wins logic |
| `backend/app/services/puzzle_scheduler.py` | Puzzle generation scheduling |
| `backend/app/core/scheduler.py` | APScheduler configuration |
| `frontend/src/utils/timezone.ts` | Timezone/date utilities |
| `frontend/src/utils/fingerprint.ts` | Device fingerprint generation |
| `frontend/src/hooks/usePlayer.ts` | Player identity management |
| `frontend/src/components/Game/AlreadyPlayed.tsx` | Already-played UI |
| `frontend/src/components/Game/CountdownTimer.tsx` | Next puzzle countdown |

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/api/routes/game.py` | Add first-play-wins check, date parameter |
| `backend/app/api/routes/puzzle.py` | Add by-date endpoint |
| `backend/app/main.py` | Add lifespan hook for scheduler |
| `frontend/src/hooks/useGame.ts` | Add already_played phase, previousResult |
| `frontend/src/components/Game/GameBoard.tsx` | Render AlreadyPlayed when applicable |
| `frontend/package.json` | Add @fingerprintjs/fingerprintjs dependency |

## Testing Notes

- Test first-play-wins with multiple browser sessions
- Test timezone handling by changing system clock
- Test puzzle generation failure recovery
- Test session resume after browser close
- Verify leaderboard only shows first attempts
