# Quartiles Implementation Interview Transcript

## Puzzle Generation

**Q: For puzzle generation, which approach do you prefer for the initial implementation?**
- Generate-first (Recommended)
- Tiles-first
- Hybrid

**A:** Generate-first (Recommended) - Start with 5 random quartile words, decompose into tiles, validate solvability

---

## Dictionary

**Q: For word validation during gameplay, which dictionary approach?**
- SCOWL size 60 (Recommended)
- SCOWL size 70
- Custom curated

**A:** SCOWL size 60 (Recommended) - ~35K words, filters obscure terms, good balance

---

## Anonymous Player Identity

**Q: How should anonymous (non-authenticated) players be identified for leaderboards?**
- Device fingerprint
- localStorage UUID
- Optional nickname

**A:** Generated silly names using "AdjectiveNoun" format (e.g., ChubbyPenguin, RotundUnicorn)

---

## Multi-Device Handling

**Q: For the MVP daily puzzle, what happens if a user plays from multiple devices?**
- Independent sessions
- First play wins
- Best score wins

**A:** First play wins - Only first submission counts for leaderboard (requires server tracking)

---

## Tile Selection Model

**Q: For the tile UI interaction, which selection model do you prefer?**
- Toggle selection
- Ordered selection
- Free reorder

**A:** Toggle selection - Click to add/remove from current word. Click again to deselect.

---

## Hints System

**Q: Should hints reveal definitions for ANY unfound word, or only quartiles (4-tile words)?**
- Quartiles only (Recommended)
- Any word
- Adaptive

**A:** Quartiles only (Recommended) - Hints only reveal 4-tile word definitions (per spec)

---

## Word Submission

**Q: For word submission, how should the player confirm their selection?**
- Enter key / Submit button
- Auto-submit on valid
- Both options

**A:** Enter key / Submit button - Explicit confirmation required to submit word

---

## Invalid Word Feedback

**Q: How should invalid word attempts be handled?**
- Silent rejection
- Shake animation
- Toast message
- Shake + toast

**A:** Shake animation - Tiles shake to indicate invalid, then clear

---

## Component Library

**Q: For component library approach, which do you prefer?**
- Keep shadcn/ui
- Switch to daisyUI
- Hybrid approach

**A:** Switch to daisyUI - While noted that the project currently uses shadcn/ui extensively, most of those files are just placeholders so this shouldn't be too much of an issue.

---

## Visual Design Approach

**Q: For visual design approach, what's your preference?**
- Reference images + iterate
- Design mockup first
- Minimal viable first

**A:** Design mockup first - Create mockup (Figma/similar) before implementation

---

## Ambient Animation

**Q: For ambient tile animation (floating/breathing), what intensity level?**
- Subtle (Recommended)
- Noticeable
- Configurable

**A:** Subtle (Recommended) - Barely perceptible movement, professional feel

---

## Leaderboard Time Format

**Q: For the leaderboard, what time granularity should be shown?**
- Seconds only
- With milliseconds
- Relative buckets

**A:** Seconds only - Show as '2:34' (minutes:seconds)

---

## MVP Keyboard Features

**Q: For the MVP scope, which features are must-haves vs nice-to-haves?**
(Multi-select)
- Keyboard support
- Vim-style keys (hjkl)
- Letter filtering
- Drag-and-drop

**A:** Selected: Keyboard support + Vim-style keys (hjkl)

---

## Puzzle Generator Approach

**Q: For puzzle generation, should we build the generator as part of MVP or use pre-generated puzzles?**
- Build generator (Recommended)
- Pre-generated set
- Hybrid

**A:** Build generator (Recommended) - Implement full puzzle generation algorithm

---

## Daily Puzzle Schedule

**Q: How should the daily puzzle schedule work for initial launch?**
- Automatic daily generation
- Pre-scheduled queue
- Manual publish

**A:** Automatic daily generation - System generates a new puzzle each day automatically

---

## Testing Strategy

**Q: For testing during development, what's your preferred approach?**
- E2E with Playwright
- Unit tests + E2E
- Game logic unit tests only

**A:** Unit tests + E2E - Comprehensive unit tests for game logic + E2E for flows

---

## Design Tool

**Q: For the design mockup phase, what tool should be used?**
- Figma
- Excalidraw
- AI generation + iteration

**A:** Figma

---

## Design References

**Q: Any specific games or websites that capture the aesthetic you're going for?**
- I'll provide references
- Research needed
- Apple News+ Quartiles

**A:** Research needed - Find examples of 'Grain & Gradient / Lo-Fi Organic' style

---

## Found Words Display

**Q: For the found words display, how should words be organized?**
- Grouped by tile count
- Alphabetical
- Chronological

**A:** Grouped by tile count - Sections: 1-tile, 2-tile, 3-tile, 4-tile (per spec)

---

## Progress Display

**Q: Should the game show how many words remain to be found?**
- Show count per category
- Score only
- Both

**A:** Score only - Just show current score and threshold (100 pts)

---

## Summary of Key Decisions

| Area | Decision |
|------|----------|
| Puzzle Generation | Generate-first approach (5 words → tiles) |
| Dictionary | SCOWL size 60 (~35K words) |
| Anonymous Players | Generated AdjectiveNoun names |
| Multi-device | First play wins |
| Tile Selection | Toggle (click to add/remove) |
| Hints | Quartiles only (4-tile words) |
| Submit | Enter key / Submit button |
| Invalid Feedback | Shake animation |
| Component Library | daisyUI (replacing shadcn/ui) |
| Design Process | Figma mockup first |
| Animation | Subtle ambient motion |
| Time Format | Minutes:seconds (no ms) |
| Keyboard | Arrow keys + vim-style (hjkl) |
| Generator | Build full algorithm for MVP |
| Scheduling | Automatic daily generation |
| Testing | Unit tests + E2E |
| Found Words | Grouped by tile count |
| Progress | Score only (no word counts) |
