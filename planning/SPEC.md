# Quartiles Game Specification

## Overview

A web-based word puzzle game inspired by Apple News+ Quartiles. Players combine word fragments (tiles) to form valid English words, with bonus points for combining exactly 4 tiles to form "quartile" words. The game features daily puzzles with competitive leaderboards based on solve time.

## Core Gameplay

### Puzzle Structure
- **20 tiles** arranged in a 4x5 grid
- **5 quartile words** per puzzle (words formed from exactly 4 tiles)
- Each tile contains **2-4 letters**
- Quartile words are **8-16 letters** in length
- Tiles can be reused across multiple words (not consumed)

### Word Formation
- Players select tiles to form words
- Valid words can use 1, 2, 3, or 4 tiles
- Words are validated against a curated dictionary:
  - **Quartile words (4-tile):** Accessible but challenging vocabulary
  - **Smaller words (1-3 tile):** Extensive list, no obscure Scrabble words

### Scoring
| Tiles Used | Points |
|------------|--------|
| 1 tile     | 2 pts  |
| 2 tiles    | 4 pts  |
| 3 tiles    | 7 pts  |
| 4 tiles    | 10 pts |

*Note: Point values may be adjusted during development to balance gameplay.*

### Solve Threshold
- **100 points** to "solve" a puzzle
- Puzzles must have **minimum 130-150 points** available to ensure solvability
- Puzzle generation rejects puzzles that don't meet this threshold

### Two-Phase Gameplay

**Phase 1: Timed Competition**
- Timer starts when player begins puzzle
- Timer stops when player reaches 100 points (solve threshold)
- Solve time is recorded for leaderboards
- Hints available but add time penalties

**Phase 2: Relaxed Completion**
- After solving, player can continue finding remaining words
- No time pressure
- Personal stats track total words found per puzzle

## Hints System

- Hints reveal the **definition of an unfound quartile word**
- Progressive time penalties:
  - 1st hint: +30 seconds
  - 2nd hint: +60 seconds
  - 3rd hint: +120 seconds
  - 4th hint: +240 seconds
  - 5th hint: +480 seconds

## Daily Puzzle System

### Schedule
- **Timezone-aware reset** at local midnight
- Each calendar date has one puzzle
- Same puzzle for all players on the same date (regardless of timezone)

### Leaderboards
- **Date-based grouping:** All players who complete "January 26 puzzle" compete together
- **Ranking metric:** Solve time (including hint penalties)
- Players who don't reach solve threshold are **excluded** from leaderboard (no DNF entries)

### Practice Mode
- Access to **past daily puzzles** you missed
- Practice plays do **not** count toward:
  - Leaderboards
  - Personal statistics
  - Streaks

## User System

### Authentication
- **Anonymous play** by default (data stored locally)
- **Optional account upgrade** to sync across devices
- Account creation via **email/password only** (no OAuth)

### Friends System
- Add friends via **username search**
- Add friends via **invite links**
- Friend-only leaderboard views

### Personal Statistics
Comprehensive dashboard tracking:

**Speed Metrics:**
- Average solve time
- Fastest solve
- Time trends over weeks/months

**Completion Metrics:**
- Current streak
- Longest streak
- Total puzzles completed
- Percentage of words found per puzzle

**Vocabulary Insights:**
- Total unique words found
- Longest words discovered
- Rarest words found

## Visual Design

### Aesthetic
- **Grain & Gradient / Lo-Fi Organic** style
- Muted, earthy color palette with subtle texture
- Organic shapes and soft edges
- **Dark and light modes** supported

### Color Accessibility
- Color-blind friendly palette
- Tile states and feedback use shapes/patterns, not color alone

### Motion Design
**Hover/Select States:**
- Gentle wobble on hover
- Soft snap when tiles combine
- Organic easing curves

**Success Feedback:**
- Subtle celebratory animation on valid word
- Understated particle effects (not flashy)

**Ambient Motion:**
- Tiles have constant subtle movement (floating/breathing)
- Creates a living, organic feel

### Tile States
- **Default:** Available for selection
- **Selected:** Currently part of word being built
- **Quartile found:** Subtle indicator showing tile has formed a quartile (still usable)

## Interaction Design

### Input Methods
- **Tap/click to select** tiles (primary)
- **Drag and drop** tiles to word zone (optional alternative)
- Grid layout: 4x5 arrangement

### Keyboard Support
- **Standard:** Arrow keys, Enter to submit, Escape to clear
- **Vim-style option:** hjkl navigation for power users
- Type letters to filter/highlight matching tiles

### Found Words Display
- Grouped by tile count (1-tile, 2-tile, 3-tile, 4-tile sections)
- Shows progress toward quartiles
- Real-time score display

## Technical Architecture

### Platform
- **Web-first** with responsive design
- PWA-capable for home screen install
- **Online only** (no offline play)

### Security
- **Hashed solutions** sent to client
- Instant local validation without exposing answer key
- Server validates final results
- Timer runs client-side (acceptable for target audience)

### Tech Stack (existing in repo)
- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Frontend:** React + TypeScript + TanStack Router/Query + Tailwind CSS + shadcn/ui
- Game logic in **pure Python** (no FastAPI/Pydantic dependencies)

### Puzzle Generation
- **Algorithmic generation** with quality filters
- Validation ensures:
  - Exactly 5 valid quartile words
  - Minimum 130-150 total points available
  - Quartile words are accessible vocabulary
  - No obscure/offensive words
- **Quartile cooldown:** Once a word is used as a quartile, it cannot appear as a quartile in another puzzle for **30 days**
  - Requires tracking quartile usage dates in database
  - Affects puzzle generation candidate pool

### Dictionary Requirements
- **Quartile words:** Curated list of 8-16 letter words, accessible but challenging
- **Sub-words:** Extensive list excluding BS Scrabble words (no "aa", "qat", etc.)
- Tiles: 2-4 letters each

---

## Architecture Diagrams

Detailed architecture documentation with Mermaid diagrams. Each diagram is in a separate file for easier maintenance.

| # | Diagram | Description |
|---|---------|-------------|
| 1 | [System Overview](diagrams/01-system-overview.md) | High-level view of all system components |
| 2 | [Backend Architecture](diagrams/02-backend-architecture.md) | FastAPI structure, routes, and dependencies |
| 3 | [Authentication Flow](diagrams/03-authentication-flow.md) | JWT login and token validation sequence |
| 4 | [Game Domain Architecture](diagrams/04-game-domain-architecture.md) | Pure Python game logic separation |
| 5 | [Gameplay Data Flow](diagrams/05-gameplay-data-flow.md) | End-to-end puzzle play sequence |
| 6 | [Database ERD](diagrams/06-database-erd.md) | Entity relationships (current + planned) |
| 7 | [Frontend Components](diagrams/07-frontend-components.md) | React/TanStack Router hierarchy |
| 8 | [Deployment](diagrams/08-deployment.md) | Docker Compose orchestration |
| 9 | [API Routes](diagrams/09-api-routes.md) | Endpoint hierarchy with auth levels |
| 10 | [Model Schema Pattern](diagrams/10-model-schema-pattern.md) | SQLModel naming conventions |

---

## Audio
- **No audio** (silent experience)

## Monetization
- **Free, no monetization**
- No ads, no premium features

## Target Audience
- Friends and family
- Word game enthusiasts (Wordle, NYT games players)

## Onboarding
- **Help page** accessible from menu
- No forced tutorial
- Assume some familiarity with word puzzle games

## Future Accessibility (Post-MVP)
- Screen reader support (ARIA labels, announcements)
- Reduced motion option
- Full WCAG compliance

---

## Resolved Decisions

### Streak Definition
- **Consecutive days solved:** Player must reach 100-point threshold each day to maintain streak
- Missing a day or failing to solve breaks the streak

### Word List Source
- **SCOWL/SOWPODS corpus** filtered by:
  - Length (8-16 letters for quartiles, standard dictionary for sub-words)
  - Frequency (filter out overly obscure words)
  - Profanity/offensive word exclusion
- Sub-words exclude BS Scrabble words (no "aa", "qat", etc.)

### Hint Definitions
- **WordNet** as the source for all word definitions
- Definitions stored in database alongside words (not fetched on-demand)
- Single-sentence gloss format (WordNet's native format)
- Bulk-exported during word list generation

---

## Open Questions / Decisions Deferred

1. **Exact point values** (2/4/7/10) may need tuning after playtesting
2. **Minimum puzzle score threshold** (130-150) needs validation

---

## MVP Scope

For initial release, focus on:
1. Core puzzle gameplay (tile selection, word validation, scoring)
2. Single daily puzzle
3. Anonymous play with local storage
4. Basic leaderboard (global)
5. Dark/light mode
6. Responsive design
7. Keyboard support

Defer to post-MVP:
1. Account system and sync
2. Friends system
3. Practice mode (past puzzles)
4. Full statistics dashboard
5. Comprehensive accessibility features
