# Quartiles Research Findings

## 1. Codebase Analysis

### Project Structure

**Quartiles** is a full-stack web application with the following architecture:

```
quartiles/
├── backend/app/
│   ├── main.py                 # FastAPI entry point
│   ├── api/routes/             # API endpoints (login, users, items)
│   ├── game/                   # PURE PYTHON game logic (placeholders)
│   │   ├── types.py            # Domain dataclasses (placeholder)
│   │   ├── dictionary.py       # Word lookups (placeholder)
│   │   ├── generator.py        # Puzzle generation (placeholder)
│   │   └── solver.py           # Validation/scoring (placeholder)
│   ├── core/                   # Config, security, database
│   ├── models.py               # SQLModel tables + Pydantic schemas
│   └── crud.py                 # Database operations
├── frontend/src/
│   ├── routes/                 # TanStack Router (file-based)
│   ├── components/             # React components (shadcn/ui)
│   ├── hooks/                  # useAuth, useCustomToast, etc.
│   └── client/                 # Auto-generated API client
└── planning/                   # Spec and diagrams
```

### Established Patterns

**Critical: Game Logic Boundary**
- `backend/app/game/` uses **pure Python dataclasses only**
- NO imports from FastAPI, SQLModel, or Pydantic
- API routes act as adapters between Pydantic and game domain types

**Authentication**
- JWT-based with Argon2/Bcrypt password hashing
- Token stored in localStorage
- Dependencies: `CurrentUser`, `SessionDep`

**Database**
- SQLModel (SQLAlchemy ORM + Pydantic)
- UUID primary keys
- Timezone-aware datetimes
- Alembic migrations

**Frontend Patterns**
- File-based routing (TanStack Router)
- Protected routes with `beforeLoad` auth checks
- React Query for server state
- Form validation with Zod + react-hook-form

### Current State

**Implemented:**
- User authentication (login, signup, password recovery)
- User CRUD operations
- Item CRUD (template resource)
- Database schema and migrations
- Frontend routing and layout
- Dark/light mode
- Form validation and data tables

**Placeholder/Empty:**
- `game/types.py` - Game domain dataclasses
- `game/dictionary.py` - Word validation
- `game/generator.py` - Puzzle generation
- `game/solver.py` - Scoring/validation
- Game API routes (need creation)
- Game-specific database models
- Game UI components

---

## 2. Word Puzzle Generation Algorithms

### Constraint Satisfaction Problem (CSP) Formulation

The Quartiles puzzle generation is fundamentally a CSP:

**Variables:** {Word1, Word2, Word3, Word4, Word5}
**Domains:** Dictionary of 8-16 letter words
**Constraints:**
- All-different tiles: No tile shared between words
- Sum tiles: Total tiles = 20
- Tile count: Each word uses exactly 4 tiles

### Recommended Algorithm: Forward Checking + MRV

```python
def generate_puzzle(dictionary, max_attempts=1000):
    for attempt in range(max_attempts):
        # Select first word using Minimum Remaining Values heuristic
        word1 = select_word_mrv(remaining_tiles=None)
        tiles1 = extract_tiles(word1)

        # Forward-check remaining possibilities
        remaining = all_tiles - tiles1

        # Recursively find 4 more words with pruning
        solution = backtrack_with_fc(
            remaining_tiles=remaining,
            words_found=[word1],
            domains=compute_domains(remaining)
        )

        if solution:
            # Verify uniqueness
            all_solutions = find_all_solutions(solution)
            if len(all_solutions) == 1:
                return solution

    return None
```

### Key Optimizations

1. **Early Constraint Propagation** - Pre-filter dictionary by letter count compatibility
2. **MRV Heuristic** - Select words with fewest valid tile combinations first
3. **Arc Consistency (AC-3)** - Maintain consistency through domain reduction
4. **Dictionary Organization** - Pre-compute word-to-tiles mappings

### Avoiding Degenerate Puzzles

**Acceptance Criteria:**
- Exactly 1 solution = UNIQUE (preferred)
- 2-3 solutions = ACCEPTABLE
- 4+ solutions = DEGENERATE (reject)

**Quality Filters:**
- Curate dictionary to remove obscure words
- Use entropy-based scoring (high entropy = too many solutions)
- Forward-validate during generation

---

## 3. Word Lists and Definitions

### SCOWL (Spell Checker Oriented Word Lists)

**Recommended for Quartiles:** Size 60-70

| Size | Words | Purpose |
|------|-------|---------|
| 35 | ~15,000 | Compact, basic |
| 50 | ~25,000 | Balanced |
| **60** | ~35,000 | **Default** - recommended |
| 70 | ~80,000 | Comprehensive |
| 80 | ~280,000 | Includes obscure game words |

**Sources:**
- [GitHub: en-wl/wordlist](https://github.com/en-wl/wordlist)
- [SCOWL Website](http://wordlist.aspell.net/)

### SOWPODS vs SCOWL

| Aspect | SOWPODS | SCOWL |
|--------|---------|-------|
| Purpose | Scrabble tournaments | Spell checking |
| Two-letter words | Extensive (aa, qi, xu) | Conservative |
| Obscure words | Intentionally included | Frequency-filtered |

**Recommendation:** Use SCOWL size 60 for Quartiles - removes "BS Scrabble words" while keeping legitimate vocabulary.

### Filtering Strategies

```python
# Remove problematic words
bs_scrabble_words = {'aa', 'qi', 'xu', 'qat', 'ja', 'za', 'xi'}

# Frequency-based filtering (COCA)
quality_words = [w for w in word_list
                 if coca_freq.get(w, 999999) < 30000]

# Length-based filtering
words = [w for w in word_list if len(w) >= 3]
```

### WordNet for Definitions

```python
from nltk.corpus import wordnet as wn

def export_word_definitions(word_list, output_file):
    definitions = {}
    for word in word_list:
        synsets = wn.synsets(word)
        if synsets:
            definitions[word] = {
                'definition': synsets[0].definition(),
                'examples': synsets[0].examples(),
                'pos': synsets[0].pos()
            }
    return definitions
```

**Bulk Export Strategy:**
- Process all words at build time
- Store definitions in database
- Use `wn` package (SQLite-backed) for performance

### Word Frequency Sources

- **COCA** (Corpus of Contemporary American English) - 1+ billion words, balanced genres
- **Google Books N-grams** - Historical coverage 1500-2022
- **iWeb Corpus** - Modern web text

---

## 4. Client-Side Validation Patterns

### Two-Dictionary Approach

**Solution Dictionary:** Hashed answers kept server-side only
**Validation Dictionary:** Unhashed list of valid guessable words sent to client

```typescript
interface GameState {
  validWords: Set<string>;    // ~10K words, sent to client
  solutionHash: string;       // Hash of today's solution, client never decodes
}
```

### Bloom Filters vs Hash Sets

| Scenario | Best Choice | Reason |
|----------|------------|--------|
| <1000 words | Hash Set | Payload size negligible |
| 5-50K words | **Bloom Filter** | 90% size reduction |
| Zero false positives required | Hash Set | Exact matching |

**Bloom Filter Benefits:**
- 10K words in ~5KB (vs 100KB+ for full list)
- 3% false positive rate acceptable for "reject invalid"
- Fast O(k) lookup where k = hash functions

### Anti-Cheat Strategy for Casual Games

**Layer 1: Client-Side Validation**
- Instant feedback using validWords set
- Generate letter feedback locally

**Layer 2: Server Submission Validation**
```python
def verify_submission(submission):
    # Verify words are valid
    if not all(word in VALID_WORDS for word in submission.guesses):
        return invalid("Invalid word")

    # Behavioral checks
    if submission.timeElapsed < 5000:  # <5 seconds
        log_suspicious_activity("timing_anomaly")

    # Pattern analysis
    cheat_score = analyze_behavior(submission)
    if cheat_score > THRESHOLD:
        flag_for_review(submission.user_id)

    return valid(cheat_score)
```

**Key Principle:** For friends/family audience, don't over-engineer security. Simple server validation is sufficient.

### Wordle-Style Pattern

```javascript
// Deterministic daily word selection
const DAY_OFFSET = Math.floor(
  (new Date() - new Date(2021, 5, 19)) / 86400000
);
const ANSWER = SOLUTIONS[DAY_OFFSET % SOLUTIONS.length];

// Feedback generation (client-side)
const getColoring = (guess, answer) => {
  const result = Array(5).fill('gray');
  // First pass: exact matches (green)
  // Second pass: wrong position (yellow)
  return result;
};
```

---

## 5. Quartiles-Solver Repository Analysis

### Solver Implementations Reviewed

1. **nilsstreedain/quartiles-solver** (JavaScript) - Web-based solver
2. **xebia-functional/quartiles-solver** (Rust) - High-performance CLI, 16ms execution
3. Various Python implementations

### Core Algorithm: State Space Exploration

```
State: Tuple of selected tile indices [i0, i1, i2, i3]
Permutations:
- P(20,1) = 20
- P(20,2) = 380
- P(20,3) = 6,840
- P(20,4) = 116,280
Total: 123,520 permutations
```

**Optimization: Prefix Tree (Trie)**
- Store dictionary as trie
- Early pruning: if prefix invalid, skip all extensions
- Example: "rmut" isn't valid prefix → skip 6,840+ permutations

### Cursor-Based State Explorer

```
Motion operators:
- APPEND: Add next tile (0,1) → (0,1,2)
- INCREMENT: Move rightmost forward (0,1,2) → (0,1,3)
- POPCREMENT: Pop + increment previous (0,1,5) → (0,2)
- End: Empty tuple = sentinel

Properties:
- Exhaustive: visits every combination exactly once
- Resumable: state captured by cursor position
- Deterministic: same order every execution
```

### Applicability to Puzzle Generation

| Use Case | Difficulty | Reusability |
|----------|-----------|-------------|
| Word validation | Easy | 100% |
| Solvability testing | Easy | 90% |
| Puzzle generation (reverse) | Medium | 70% |
| Fragment optimization | Medium | 60% |

### Recommended Pipeline

```
1. WORD SELECTION - Pick 5 target quartile words
2. DECOMPOSITION - Fragment each into 2-4 letter pieces
3. PADDING - Add neutral fragments to reach 20 tiles
4. BOARD GENERATION - Randomize tile positions
5. VALIDATION - Run solver, verify 5 quartiles found
6. ITERATION - Adjust if solvability/difficulty wrong
```

### Key Patterns to Adopt

1. **Trie-based dictionary** for efficient prefix matching
2. **Binary serialization** for fast dictionary loading (~24ms)
3. **Cursor-based iteration** for exploring fragment combinations
4. **Benchmark aggressively** - target sub-50ms puzzle generation

---

## Summary of Key Decisions

### Algorithm
- Use **Forward Checking + MRV heuristic** for puzzle generation
- Implement **prefix tree (trie)** for word validation
- Generate-and-validate approach with uniqueness verification

### Word Lists
- **SCOWL size 60** as base dictionary
- **COCA frequency filtering** (top 30K words)
- **WordNet bulk export** for definitions at build time
- Explicit blocklist for offensive words

### Client/Server Architecture
- Client: Instant validation against valid word set
- Server: Verify submissions, behavioral analysis
- Hash-based commitment for solutions (server-side only)
- Timer runs client-side (acceptable for casual audience)

### Performance Targets
- Puzzle generation: <50ms
- Word validation: <10ms
- Server submission: <100ms
