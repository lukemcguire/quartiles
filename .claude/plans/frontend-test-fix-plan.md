# Plan: Fix Frontend Tests After Daily Puzzle Integration

## Overview

The daily puzzle system integration (Section 08) was successfully implemented, but introduced test failures. The "already played" logic causes frontend tests to timeout because they see the `AlreadyPlayed` component instead of the `GameBoard`.

## Current State

### Implementation Status (Daily Puzzle Integration)

| Task | Status | File |
|------|--------|------|
| Timezone utilities | ✅ Complete | `frontend/src/utils/timezone.ts` |
| usePlayer hook | ✅ Complete | `frontend/src/hooks/usePlayer.ts` |
| AlreadyPlayed component | ✅ Complete | `frontend/src/components/Game/AlreadyPlayed.tsx` |
| Backend game route | ✅ Complete | `backend/app/api/routes/game.py` |
| useGame hook update | ✅ Complete | `frontend/src/hooks/useGame.ts` |
| Game component integration | ✅ Complete | `frontend/src/components/Game/Game.tsx` |
| Component exports | ✅ Complete | `frontend/src/components/Game/index.ts` |
| API client regenerated | ✅ Complete | Auto-generated |

### Test Status

| Suite | Status | Details |
|-------|--------|---------|
| `make check` | ✅ Pass | Linting, formatting, type checks all pass |
| Backend tests | ✅ Pass | 238 tests passed |
| Frontend tests (chromium-no-auth) | ✅ Pass | 10 localStorage tests pass |
| Frontend tests (chromium) | ❌ Fail | 54 tests timeout |

### Test Failure Details

**Error pattern:** All failing tests timeout waiting for `[data-testid="game-board"]` because the `AlreadyPlayed` component renders instead.

**Failing test files:**
- `tests/game.spec.ts` (23 tests)
- `tests/login.spec.ts` (5 tests)
- `tests/signup.spec.ts` (2 tests)
- `tests/user-settings.spec.ts` (15 tests)
- `tests/reset-password.spec.ts` (3 tests)
- `tests/localstorage.spec.ts` (chromium project only)

## Root Cause Analysis

### The Issue

1. **Daily Puzzle Logic:** The new `already_played` check returns `true` when a player has completed today's puzzle
2. **Test Behavior:** Tests use a `device_fingerprint` stored in localStorage to identify players
3. **Test Database:** The test database has records showing the test player completed today's puzzle
4. **Result:** Tests see `AlreadyPlayed` component instead of `GameBoard`

### Why API Mocking Didn't Work

Attempted fixes:
- ✅ Added `page.route("**/api/v1/game/start")` in `beforeEach` hooks
- ✅ Added `context.route("**/api/v1/game/start")` at context level
- ✅ Added API mocking to `tests/auth.setup.ts`

**Why it failed:** Playwright's `storageState` feature saves cookies and localStorage, but NOT route handlers. When the `chromium` project loads the stored auth state, the mocked routes from `auth.setup.ts` are not preserved.

### Test Architecture

```
chromium project flow:
1. auth.setup.ts runs → logs in user → saves storageState
2. game.spec.ts runs → loads storageState → page loads with OLD device_fingerprint
3. Backend sees old device_fingerprint → returns already_played: true
4. Test waits for game-board → times out (sees AlreadyPlayed instead)
```

## Solution Plan

### Option 1: MSW (Mock Service Worker) - Recommended

**Approach:** Use MSW to intercept API calls at the network level, which persists across page loads and storage states.

**Steps:**
1. Install MSW: `bun add -D msw`
2. Create `frontend/tests/mocks/handlers.ts` with API route mocks
3. Create `frontend/tests/mocks/server.ts` to set up MSW
4. Update `playwright.config.ts` to initialize MSW before tests
5. Remove all `page.route()` and `context.route()` calls

**Pros:**
- Mocks persist across page loads and storage states
- Industry-standard approach
- Works with all test configurations
- Can mock any API endpoint consistently

**Cons:**
- Requires additional dependency
- Slightly more complex setup

**Estimated effort:** 1-2 hours

### Option 2: Fix at the Source - Use Future Puzzle Date

**Approach:** Modify the tests to use a future `puzzle_date` so `already_played` is always false.

**Steps:**
1. Update `frontend/tests/fixtures.ts` to generate a future date
2. Mock `getLocalPuzzleDate()` to return the future date
3. Use MSW or Vitest mock to override the function

**Pros:**
- Tests use the actual backend
- No test-specific API mocking layer

**Cons:**
- Still requires some form of mocking (function override)
- Tests run against tomorrow's puzzle (could cause confusion)

**Estimated effort:** 1-2 hours

### Option 3: Clear Test Database Daily

**Approach:** Set up a CI job that clears the `game_result` table for test users before running tests.

**Steps:**
1. Create a cleanup script: `backend/scripts/clear_test_data.py`
2. Run before tests: `make backend-test-clean`
3. Update CI pipeline to run cleanup

**Pros:**
- Tests run against real backend
- No API mocking required

**Cons:**
- Requires managing test database state
- Slower (real DB queries)
- Tests could still fail if run multiple times per day

**Estimated effort:** 1 hour

### Option 4: Add Test-Specific Backend Endpoint

**Approach:** Create a test-only API endpoint that always returns a fresh game session.

**Steps:**
1. Add `backend/app/api/routes/game_test.py` with `/api/v1/test/game/start`
2. Endpoint ignores `already_played` check and always returns fresh game
3. Update frontend tests to use test endpoint when `process.env.NODE_ENV === 'test'`

**Pros:**
- Tests use real backend
- No external dependencies
- Clean separation of test/production code

**Cons:**
- Requires backend changes
- Test-only code in production codebase
- Need to ensure test endpoint is not exposed in production

**Estimated effort:** 2-3 hours

## Recommended Approach: Option 1 (MSW)

MSW is the industry standard for API mocking in frontend tests and handles the storageState issue properly.

### Implementation Steps

1. **Install MSW**
   ```bash
   cd frontend
   bun add -D msw
   ```

2. **Create mock handlers** (`frontend/tests/mocks/handlers.ts`)
   ```typescript
   import { http, HttpResponse } from 'msw'

   export const handlers = [
     http.post('/api/v1/game/start', async () => {
       return HttpResponse.json({
         session_id: `test-session-${Date.now()}`,
         player_id: `test-player-${Date.now()}`,
         display_name: "Test Player",
         tiles: Array.from({ length: 20 }, (_, i) => ({
           id: i,
           letters: "TEST" // or generate realistic tiles
         })),
         already_played: false,
       })
     })
   ]
   ```

3. **Create MSW server** (`frontend/tests/mocks/server.ts`)
   ```typescript
   import { setupServer } from 'msw/node'
   import { handlers } from './handlers'

   export const server = setupServer(...handlers)
   ```

4. **Update Playwright config** (`frontend/playwright.config.ts`)
   ```typescript
   import { server } from './tests/mocks/server'

   export default defineConfig({
     // ... existing config
     globalSetup: ['./tests/global-setup.ts'],
     globalTeardown: ['./tests/global-teardown.ts'],
   })
   ```

5. **Create setup/teardown files**
   - `frontend/tests/global-setup.ts`: Start MSW server
   - `frontend/tests/global-teardown.ts`: Stop MSW server

6. **Remove all page.route() calls** from:
   - `tests/auth.setup.ts`
   - `tests/game.spec.ts`
   - `tests/localstorage.spec.ts`

7. **Run tests**
   ```bash
   make frontend-test
   ```

### Verification

After implementation:
- [ ] All 74 frontend tests pass
- [ ] No test-specific code in production
- [ ] MSW server starts/stops cleanly
- [ ] Tests run in isolation without interference

## Alternative Quick Fix: Skip Failing Tests

If you need to unblock CI immediately while implementing MSW:

**Update `playwright.config.ts`:**
```typescript
{
  name: 'chromium',
  testMatch: /^(?!.*(game|localstorage|login)).*\.spec\.ts$/,
  use: {
    ...devices['Desktop Chrome'],
    storageState: 'playwright/.auth/user.json',
  },
  dependencies: ['setup'],
}
```

This excludes game/login tests from the chromium project, leaving only the working tests (signup, reset-password, user-settings).

## References

- MSW documentation: https://mswjs.io/
- Playwright storage state: https://playwright.dev/docs/auth
- Playwright API mocking: https://playwright.dev/docs/mock
- Original implementation plan: `.claude/plans/daily-puzzle-integration-plan.md`
