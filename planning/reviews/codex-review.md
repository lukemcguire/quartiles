# Codex Review

**Status:** Review not completed - API quota exceeded.

The Codex CLI was available but the review could not be completed due to quota limitations on the OpenAI account.

A single external review (Gemini) was obtained successfully and provides comprehensive feedback on the implementation plan.

---

# This review was done after the fact but I wanted to save it here for completeness/future reference.

**Game Rules / Requirements Ambiguity**

- **“Solve” definition conflicts with “quartile words.”** In _Overview_ you say “Race to reach 100 points” and also “Exactly 5 quartile words per puzzle” + hints reveal quartile definitions. If “solve” is just `score >= 100`, players can ignore quartiles/hints; if quartiles are required, “solve threshold 100” is misleading. Decide and state one: (A) solved when `score>=100` only, (B) solved when all 5 quartiles found, or (C) both.
- **Word construction rules are underspecified.** In _Overview_ and _Phase 1.4 Solver_ it implies “combine tiles” by concatenation, but not whether order matters, whether you can reorder tiles arbitrarily, whether tiles can be reused within a word, and whether you can submit the same word multiple times. Write explicit rules; generator/solver/API must match.
- **2-letter tiles vs “remove words < 3 letters” mismatch.** In _1.2 Dictionary Filter_ you remove words `< 3 letters` but tiles can be `2` letters, and scoring includes `1-tile` words. If 2-letter words are excluded, many 1-tile plays become impossible and “1-tile=2pts” becomes confusing. Either allow 2-letter words (with a curated list) or restrict tiles to 3–4 letters (and update docs).

**Core Data Model Footguns (Phase 1 & 2)**

- **You can’t derive tile count from `word: str` reliably.** You frequently store/return words as strings (`valid_words: frozenset[str]`, `words_found_json: str`) but later need `tile_count`, `tile_ids`, and “quartileFoundIds” on the frontend (_3.8 FoundWordsList_, _3.10 getQuartileFoundTileIds_). A word text can have multiple valid tile segmentations. Fix: make the canonical server primitive “a found word instance” = `{text, tile_ids, tile_count, points}` and persist that (normalized table or JSONB).
- **`validate_word` request is underpowered and enables easy abuse.** In _2.3 Game API Endpoints_, `WordValidationRequest` only contains `word: str`. Server can confirm “word is in puzzle’s valid set,” but cannot verify the player actually formed it from selected tiles (and cannot determine tile count deterministically). Fix: require `tile_ids: [int]` (or positions) and have server verify `concat(tiles[tile_ids]) == word` with uniqueness + length 1–4.
- **JSON-in-text columns are a long-term trap.** In _2.1 Database Models_, `tiles_json`, `valid_words_json`, `words_found_json` as `str` invites corruption, hard migrations, and racey updates. If you keep JSON, use Postgres `JSONB` (or SQLModel support) and/or normalize:
  - `puzzle_tiles` table (20 rows per puzzle)
  - `session_found_words` table with `UNIQUE(session_id, word_text)` and stored `tile_ids`, `points`
- **LeaderboardEntry `rank` column will rot.** In _2.1_, storing `rank` is hard to keep correct under concurrent inserts/deletes. Compute rank at query time (`ROW_NUMBER() OVER (...)`) or maintain a materialized view/job if needed.

**Concurrency / Integrity Problems**

- **Double-scoring and lost updates are likely.** `POST /sessions/{id}/word` updates a JSON array field; two rapid requests can both see “word not present” and both add points. Fix: transaction + row lock, or (better) a normalized `found_word` table with a uniqueness constraint.
- **“First-play-wins” is not actually enforceable with the current identity plan.** In _4.1_ and _2.3 start_game_, you rely on `player_id` stored in localStorage and/or `device_fingerprint`. Users ca:n clear storage or spoof fingerprints to replay. If that’s acceptable, state it explicitly (“best-effort casual enforcement”). If not acceptable, you need stronger identity (login, passkey, or server-issued device credential stored in httpOnly cookie).
- **Session authorization is missing.** Any client who learns a `session_id` can call `word/hint/submit` unless you tie sessions to an auth context. Add an unguessable session secret/token (separate from UUID) or authenticate requests (even for anonymous) via signed httpOnly cookie bound to the session/player.

**Security Vulnerabilities / Abuse Vectors**

- **Wordlist enumeration via `validate_word` API.** Even if you don’t send `valid_words`, an attacker can brute-force common words against `/word` and scrape what’s accepted, or DoS by high-rate submissions. Add:
  - per-IP + per-session rate limits
  - request validation (max length, A–Z only)
  - require `tile_ids` (reduces pure dictionary attacks)
  - suspicious-activity logging (but also action: temporary blocks)
- **Unsafe dictionary serialization risk.** In _1.2 Serialize: Save as binary format_, do not use `pickle` or any code-executing deserializer. Use a safe format (custom bytes, msgpack, protobuf) with explicit bounds checks.
- **Device fingerprinting privacy/regulatory risk.** In _2.1 Player.device_fingerprint_ and _2.3 GameStartRequest_, this is likely personal data. You need an explicit privacy stance (what’s stored, retention, purpose) and ideally avoid “fingerprinting” language by using a random “device_id” generated client-side.
- **Hint definitions may leak answers.** WordNet definitions sometimes include the word itself or obvious morphological variants. If hints must not “give away,” add sanitization/redaction and/or define hint type (“definition may contain the answer”).

**Performance / Scalability Issues**

- **Puzzle generation <50ms is unrealistic.** In _5.3 Targets_ and _1.3 Generate-First with CSP_, selecting 5 words + backtracking decomposition + full solver validation can take far longer, especially with cooldown constraints. Treat generation as an offline job with time budget (seconds) and strong observability; don’t set an optimistic SLO that will constantly fail.
- **Storing `valid_words_json` may be huge.** Depending on dictionary size and tile permutations, a puzzle could have hundreds/thousands of valid words. Persisting them for every puzzle bloats DB and increases IO. Alternative: store a compact representation (e.g., hash set via minimal perfect hash, bloom+server recompute, or store only quartiles + a deterministic seed + regenerate on demand with caching).
- **Frontend “animate-float” on 20 buttons is battery/CPU heavy.** In _3.5_, infinite animations on many elements can degrade mobile performance. Gate by `prefers-reduced-motion` and consider subtle non-continuous effects.

**Timezone / “Daily” Semantics (Phase 4.3)**

- **Client-decided “today” will cause inconsistency.** In _4.3_, client computes date via `toLocaleDateString('en-CA')` and requests puzzle by that date. Users near midnight, travelers, or incorrect device clocks will see different puzzles and leaderboards. Decide a canonical “puzzle day” policy:
  - Global UTC day (simple), or
  - A fixed timezone (e.g., America/New_York), or
  - Per-user local day (then leaderboards must be per-timezone/day and “today” is user-relative)
    Then have the server return the authoritative puzzle date/key in `/game/start` and use that everywhere.

**API Design Gaps**

- **Idempotency is unspecified.** What happens if `/submit` is called twice, or `/word` is retried? Define and implement idempotent behavior (same response, no double inserts).
- **Schema typing issues.** In _2.3 GameStartRequest_, `player_id: Optional[str]` should be `Optional[uuid.UUID]` (or validated string) to avoid mixed identifiers.
- **Two-phase gameplay not defined in backend.** You mention “timed competition then relaxed completion,” but the API/state machine doesn’t define when timer stops, whether hints after solve affect leaderboard time, and whether post-solve words are persisted. Add explicit server-side state transitions.

**Frontend Implementation Footguns**

- **LocalStorage state needs versioning.** In _3.3 useGame_, you rehydrate blindly; schema changes will break users. Add `state_version` and reset on mismatch.
- **Keyboard handler is global and can break accessibility.** In _3.9_, binding `window` keydown without `preventDefault()` and without checking focused element will interfere with forms, screen readers, and page scrolling (Space). Scope it to the game area and ignore events when focus is inside inputs/buttons not owned by the grid.
- **FoundWordsList grouping can’t work without server-provided tile metadata.** As written, `getTileCount(word, tiles)` is underspecified and likely incorrect; fix by storing `tile_ids/tile_count` per found word from the API.

**Operational / Build Considerations Missing**

- **Dictionary build reproducibility and licensing.** In _1.2_, SCOWL + COCA + WordNet have licensing/redistribution constraints; you should decide whether `dictionary.bin` is committed, built in CI, or built offline and uploaded. Also specify pinned versions and checksums so daily puzzles are stable.
- **Observability for generator/scheduler.** In _2.6/4.2_, add structured logs + metrics (generation duration, failure reasons, attempts) and alerting if the next-day puzzle is missing.

If you want, I can rewrite the plan’s “unclear rules” into a crisp spec section (word formation, solve condition, hint semantics, identity/first-play-wins policy) so the implementation doesn’t drift.
