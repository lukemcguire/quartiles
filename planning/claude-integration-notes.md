# Integration Notes: External Review Feedback

## Source: Gemini Review

---

## Suggestions ACCEPTED and Integrated

### 1. Remove `valid_words` from `GameStartResponse` - CRITICAL

**Gemini's Concern:** Sending the complete word list to the client exposes all answers, enabling trivial cheating.

**Decision:** ACCEPT - This is a valid security concern.

**Integration:**
- Remove `valid_words` from `GameStartResponse`
- Add per-word validation endpoint: `POST /api/v1/game/sessions/{session_id}/word`
- Server validates and returns immediate feedback without exposing word list

### 2. Make Server Authoritative for Time/Score

**Gemini's Concern:** Client submits `solve_time_ms` and `final_score` which can be manipulated.

**Decision:** ACCEPT - Server should calculate these values.

**Integration:**
- Server tracks `start_time` in `GameSession` record
- On submission, server calculates `solve_time_ms = now() - start_time + hint_penalties`
- Server recalculates score from validated words
- Client only submits `words_found` list

### 3. Separate `player_id` from `display_name`

**Gemini's Concern:** Using AdjectiveNoun as the identifier could cause duplicates.

**Decision:** ACCEPT - Better data modeling.

**Integration:**
- `player_id`: UUID stored in localStorage (stable identifier)
- `display_name`: AdjectiveNoun generated once and stored with player record
- Database ensures uniqueness on `player_id`, not `display_name`

### 4. Mid-Game State Persistence

**Gemini's Concern:** Page refresh loses all game state.

**Decision:** ACCEPT - Important for UX.

**Integration:**
- `useGame` hook saves state to localStorage on every change
- On mount, rehydrate from localStorage if session exists
- Include `found_words`, `current_score`, `timer_position`, `hints_used`

### 5. Error Handling Strategy

**Gemini's Concern:** No detail on error communication to users.

**Decision:** ACCEPT - Should document this.

**Integration:**
- Add error states to `GameState` interface
- Use daisyUI toast/alert components for user feedback
- Handle network errors, validation failures, API errors
- Document error handling patterns in frontend section

---

## Suggestions PARTIALLY Accepted

### 6. Admin/Curation Interface

**Gemini's Suggestion:** Admin dashboard for puzzle management.

**Decision:** PARTIALLY ACCEPT - Note as future enhancement, not MVP.

**Rationale:** Good suggestion but adds scope. The spec already marks this as post-MVP. Will add a note about admin endpoints but not full implementation.

**Integration:**
- Add admin API endpoints section (noted as post-MVP)
- Include in risk mitigation: fallback pool of curated puzzles

### 7. Practice Mode / Archive

**Gemini's Note:** API supports date-based puzzles but frontend doesn't implement it.

**Decision:** PARTIALLY ACCEPT - Already in spec as post-MVP.

**Rationale:** The spec explicitly lists "Practice mode (past puzzles)" as post-MVP scope. No change needed.

---

## Suggestions NOT Integrated

### None

All of Gemini's suggestions were valid and have been accepted in full or partial form.

---

## Summary of Plan Changes

1. **API Design (Phase 2.3):**
   - Add `POST /game/sessions/{session_id}/word` endpoint for per-word validation
   - Remove `valid_words` from `GameStartResponse`
   - Make `GameSubmitRequest` simpler (only `words_found`)
   - Server calculates score and time

2. **Database Schema (Phase 2.1):**
   - Clarify `player_id` is UUID, `display_name` is AdjectiveNoun
   - Track `start_time` in GameSession for server-side timing

3. **Frontend State (Phase 3.3):**
   - Add localStorage persistence to `useGame` hook
   - Add error state handling
   - Document rehydration on page load

4. **Error Handling (Phase 3):**
   - Add new section on error handling patterns
   - Use daisyUI toast components

5. **Risk Mitigation:**
   - Emphasize fallback puzzle pool for generation failures
