# Quartiles Game - Synthesized Specification

## Executive Summary

Quartiles is a web-based word puzzle game inspired by Apple News+ Quartiles. Players combine word fragments (tiles) to form valid English words, earning bonus points for 4-tile "quartile" words. The game features daily puzzles with competitive leaderboards based on solve time.

**Target Audience:** Friends and family, word game enthusiasts (Wordle, NYT games players)

**Key Differentiators:**
- Two-phase gameplay: timed competition + relaxed completion
- "Grain & Gradient / Lo-Fi Organic" visual aesthetic
- Accessible vocabulary (no obscure Scrabble words)

---

## Core Gameplay

### Puzzle Structure
- **20 tiles** arranged in a 4x5 grid
- **5 quartile words** per puzzle (words formed from exactly 4 tiles)
- Each tile contains **2-4 letters**
- Quartile words are **8-16 letters** in length
- Tiles can be reused across multiple words (not consumed)

### Word Formation
- Players select tiles by clicking to toggle selection
- Valid words can use 1, 2, 3, or 4 tiles
- Words validated against SCOWL size 60 dictionary (~35K words)
- Submit via Enter key or Submit button

### Scoring
| Tiles Used | Points |
|------------|--------|
| 1 tile     | 2 pts  |
| 2 tiles    | 4 pts  |
| 3 tiles    | 7 pts  |
| 4 tiles    | 10 pts |

### Solve Threshold
- **100 points** to "solve" a puzzle
- Puzzles must have **minimum 130-150 points** available
- Puzzle generation rejects puzzles below threshold

### Two-Phase Gameplay

**Phase 1: Timed Competition**
- Timer starts when player begins puzzle
- Timer stops at 100 points (solve threshold)
- Solve time recorded for leaderboards (format: M:SS)
- Hints available with time penalties

**Phase 2: Relaxed Completion**
- After solving, continue finding remaining words
- No time pressure
- Personal stats track total words found

---

## Hints System

- Hints reveal **definition of an unfound quartile word only**
- Progressive time penalties:
  - 1st hint: +30 seconds
  - 2nd hint: +60 seconds
  - 3rd hint: +120 seconds
  - 4th hint: +240 seconds
  - 5th hint: +480 seconds

---

## Daily Puzzle System

### Schedule
- **Timezone-aware reset** at local midnight
- One puzzle per calendar date
- **Automatic daily generation** by the system
- Same puzzle for all players on the same date

### Leaderboards
- **Date-based grouping:** All players who complete same date's puzzle compete together
- **Ranking metric:** Solve time (including hint penalties)
- **Time format:** Minutes:seconds (e.g., "2:34")
- Players who don't reach solve threshold excluded from leaderboard

---

## User System

### Anonymous Play (MVP)
- Anonymous play by default (data stored locally + server)
- Players identified by **generated silly names** using "AdjectiveNoun" format
  - Examples: ChubbyPenguin, RotundUnicorn, SleepyMango
- **First play wins:** If same player attempts from multiple devices, only first submission counts for leaderboard

### Future: Account System (Post-MVP)
- Optional account upgrade to sync across devices
- Account creation via email/password only (no OAuth)

---

## Visual Design

### Aesthetic: Grain & Gradient / Lo-Fi Organic
- Muted, earthy color palette with subtle texture
- Organic shapes and soft edges
- **Dark and light modes** supported
- Design mockup in **Figma** before implementation
- Research needed for style references

### Component Library
- **daisyUI** (replacing shadcn/ui from template)
- Built-in theming for organic aesthetic
- Tailwind CSS foundation

### Color Accessibility
- Color-blind friendly palette
- Tile states use shapes/patterns, not color alone

### Motion Design

**Tile Animations:**
- **Ambient:** Subtle floating/breathing (barely perceptible)
- **Hover:** Gentle wobble
- **Select:** Soft snap when tiles combine
- **Invalid:** Shake animation for rejected words

**Success Feedback:**
- Subtle celebratory animation on valid word
- Understated particle effects (not flashy)

### Tile States
- **Default:** Available for selection
- **Selected:** Currently part of word being built
- **Quartile found:** Subtle indicator showing tile has formed a quartile (still usable)

---

## Interaction Design

### Input Methods
- **Click to toggle** tile selection (primary)
- **Drag and drop** to word zone (post-MVP)
- Grid layout: 4x5 arrangement

### Keyboard Support (MVP)
- **Arrow keys:** Navigate grid
- **Enter:** Submit word
- **Escape:** Clear selection
- **Vim-style:** hjkl navigation for power users

### Found Words Display
- **Grouped by tile count** (1-tile, 2-tile, 3-tile, 4-tile sections)
- **Score only** displayed prominently (no word count remaining)
- Real-time score updates

### Invalid Word Handling
- **Shake animation** on tiles
- Selection clears after shake

---

## Technical Architecture

### Platform
- **Web-first** with responsive design
- PWA-capable for home screen install
- **Online only** (no offline play)

### Tech Stack
- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Frontend:** React + TypeScript + TanStack Router/Query + Tailwind CSS + **daisyUI**
- **Game logic:** Pure Python module (no FastAPI/Pydantic imports)

### Security: Client-Side Validation
- **Two-dictionary approach:**
  - Valid words list (~10K) sent to client for instant feedback
  - Solutions kept server-side only
- Instant local validation without exposing answer key
- Server validates final results
- Client-side timer (acceptable for target audience)

### Puzzle Generation Algorithm
- **Generate-first approach:**
  1. Select 5 target quartile words from curated dictionary
  2. Decompose each word into 2-4 letter tiles
  3. Ensure no tile overlap between words
  4. Add padding tiles if needed (total = 20)
  5. Validate via solver: confirm 5 quartiles found
  6. Check total score meets 130-150 point threshold

- **Algorithm:** Forward Checking + MRV heuristic (CSP approach)
- **Data structure:** Prefix tree (trie) for word validation

### Dictionary Requirements
- **Source:** SCOWL size 60 (~35K words)
- **Quartile words:** 8-16 letter words, accessible vocabulary
- **Sub-words:** Extensive list excluding "BS Scrabble words"
- **Filtering:** COCA frequency data (top 30K words)
- **Definitions:** WordNet bulk export at build time

### Quartile Cooldown
- Once a word is used as a quartile, cannot appear as quartile again for **30 days**
- Tracked in database
- Affects puzzle generation candidate pool

---

## Database Schema (New Tables)

### Puzzle
- id (UUID)
- date (date, unique)
- tiles (JSON array of 20 tiles)
- quartile_words (JSON array of 5 words)
- all_valid_words (JSON array)
- total_available_points (int)
- created_at (datetime)

### GameSession
- id (UUID)
- player_id (string - generated name or user ID)
- puzzle_id (FK)
- device_fingerprint (string)
- start_time (datetime)
- solve_time_ms (int, nullable - null if not solved)
- final_score (int)
- hints_used (int)
- hint_penalty_ms (int)
- words_found (JSON array)
- completed_at (datetime)

### LeaderboardEntry
- id (UUID)
- puzzle_id (FK)
- player_id (string)
- display_name (string - AdjectiveNoun)
- solve_time_ms (int, includes penalties)
- rank (int, computed)
- created_at (datetime)

### QuartileCooldown
- word (string, PK)
- last_used_date (date)

### Word (for dictionary caching)
- word (string, PK)
- definition (text)
- length (int)
- frequency_rank (int)

---

## API Endpoints (Game-Specific)

### Puzzle
- `GET /api/v1/puzzle/today` - Get today's puzzle (tiles, valid words hash)
- `GET /api/v1/puzzle/{date}` - Get puzzle by date (for practice mode, post-MVP)

### Game
- `POST /api/v1/game/start` - Start game session, returns puzzle + valid words
- `POST /api/v1/game/submit` - Submit game result (words found, time, hints)
- `POST /api/v1/game/validate` - Validate a word (optional, for server-side check)

### Leaderboard
- `GET /api/v1/leaderboard/today` - Today's leaderboard
- `GET /api/v1/leaderboard/{date}` - Leaderboard by date

### Admin (Future)
- `POST /api/v1/admin/puzzle/generate` - Force generate puzzle
- `GET /api/v1/admin/puzzle/preview` - Preview tomorrow's puzzle

---

## Testing Strategy

### Unit Tests (Game Logic)
- Puzzle generation algorithm
- Word validation
- Scoring calculation
- Tile decomposition
- Solvability verification

### E2E Tests (Playwright)
- Complete game flow
- Timer accuracy
- Leaderboard submission
- Anonymous player identification
- Multi-device first-play-wins

---

## MVP Scope

### Must Have
1. Core puzzle gameplay (tile selection, word validation, scoring)
2. Single daily puzzle with automatic generation
3. Anonymous play with generated silly names
4. Basic global leaderboard
5. Dark/light mode
6. Responsive design
7. Keyboard support (arrows + vim-style)
8. daisyUI component library
9. Figma design mockup
10. Puzzle generator algorithm
11. Unit tests for game logic + E2E tests

### Post-MVP
1. Account system and sync
2. Friends system
3. Practice mode (past puzzles)
4. Full statistics dashboard
5. Comprehensive accessibility features
6. Drag-and-drop tile selection
7. Letter filtering (type to highlight tiles)

---

## Implementation Phases

### Phase 0: Design
- Research "Grain & Gradient / Lo-Fi Organic" aesthetic references
- Create Figma mockups for game UI
- Define daisyUI theme configuration

### Phase 1: Game Core
- Implement pure Python game logic module
- Build puzzle generation algorithm
- Create dictionary processing pipeline
- Unit tests for game logic

### Phase 2: Backend API
- Puzzle and game session database models
- Game API endpoints
- Leaderboard logic
- Anonymous player name generation

### Phase 3: Frontend Game UI
- Replace shadcn/ui with daisyUI
- Tile grid component
- Word formation interface
- Timer and score display
- Found words list
- Animations (ambient, hover, select, invalid)

### Phase 4: Daily System
- Automatic puzzle generation scheduler
- Leaderboard display
- First-play-wins enforcement

### Phase 5: Polish & Testing
- E2E test suite
- Performance optimization
- Accessibility audit
- Bug fixes
