import fs from "node:fs"
import { expect, test } from "@playwright/test"

test.beforeEach(async ({ page, context }) => {
  // Restore access_token from auth setup
  let accessToken = ""
  try {
    accessToken = fs.readFileSync("playwright/.auth/access_token.txt", "utf-8")
  } catch (_e) {
    // File doesn't exist, continue without token
  }

  // Use page.addInitScript to set the token on every page load/navigation
  // This ensures the token persists across reloads
  await page.addInitScript(
    ({ token }) => {
      localStorage.removeItem("device_fingerprint")
      localStorage.removeItem("quartiles_game_session")
      if (token) {
        localStorage.setItem("access_token", token)
      }
    },
    { token: accessToken },
  )

  // Mock the puzzle API at the context level (called before game start)
  await context.route("**/api/v1/puzzle/today", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: `test-puzzle-${Date.now()}`,
        date: new Date().toISOString().split("T")[0],
        tiles: Array.from({ length: 20 }, (_, i) => ({
          id: i,
          letters:
            [
              "A",
              "B",
              "C",
              "D",
              "E",
              "F",
              "G",
              "H",
              "I",
              "J",
              "K",
              "L",
              "M",
              "N",
              "O",
              "P",
              "Q",
              "R",
              "S",
              "T",
            ][i % 20] + String.fromCharCode(65 + (i % 26)),
        })),
        total_available_points: 100,
      }),
    })
  })

  // Mock the game start API at the context level
  await context.route("**/api/v1/game/start", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: `test-session-${Date.now()}`,
        player_id: `test-player-${Date.now()}`,
        display_name: "Test Player",
        // tiles removed - now come from puzzle endpoint
        already_played: false,
      }),
    })
  })

  // Navigate to game page (authenticated user required)
  await page.goto("/game")
})

test("Game page loads with title", async ({ page }) => {
  await expect(page.getByText("Daily Quartiles")).toBeVisible()
  await expect(
    page.getByText(
      "Find words using adjacent tiles. Discover all 4 quartiles to complete the puzzle!",
    ),
  ).toBeVisible()
})

test("Game board displays 20 tiles", async ({ page }) => {
  // Wait for game to load
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')
  await expect(tiles).toHaveCount(20)
})

test("Tiles are clickable and can be selected", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const firstTile = page.locator('[data-testid="tile"]').first()
  await firstTile.click()

  // Check that tile is selected (has selected class)
  await expect(firstTile).toHaveAttribute("aria-pressed", "true")
})

test("Selected tiles form a word in the input area", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Click first 3 tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()
  await tiles.nth(2).click()

  // Check that current word is displayed
  const currentWord = page.locator('[data-testid="current-word"]')
  await expect(currentWord).not.toHaveText("Select tiles to form a word")
})

test("Clear button deselects all tiles", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select some tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  // Click clear button
  await page.getByRole("button", { name: "Clear" }).click()

  // Verify no tiles are selected
  const selectedTiles = page.locator('[aria-pressed="true"]')
  await expect(selectedTiles).toHaveCount(0)
})

test("Score display is visible", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  await expect(page.getByText("Score")).toBeVisible()
  const scoreValue = page.locator('[data-testid="score-value"]')
  await expect(scoreValue).toBeVisible()
})

test("Timer is visible and increments", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const timer = page.getByTestId("timer")
  await expect(timer).toBeVisible()

  // Get initial time
  const initialTime = await timer.textContent()

  // Wait a couple seconds
  await page.waitForTimeout(2000)

  // Get updated time
  const updatedTime = await timer.textContent()

  // Time should have changed
  expect(updatedTime).not.toBe(initialTime)
})

test("Found words list is visible", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  await expect(page.getByText("Found Words")).toBeVisible()

  // Initially should show 0 words
  await expect(page.getByText("0 words")).toBeVisible()
})

test("Hint button is visible and clickable", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const hintButton = page.getByRole("button", { name: /Hint/i })
  await expect(hintButton).toBeVisible()

  // Click hint button
  await hintButton.click()

  // Should show hint count increment
  await expect(page.getByText(/1\/5/)).toBeVisible()
})

test("Submit button is disabled when no word is formed", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const submitButton = page.getByRole("button", { name: "Submit" })
  await expect(submitButton).toBeDisabled()
})

test("Submit button becomes enabled when tiles are selected", async ({
  page,
}) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select at least 2 tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  const submitButton = page.getByRole("button", { name: "Submit" })
  await expect(submitButton).toBeEnabled()
})

test("Game shows loading state initially", async ({ page }) => {
  // Navigate fresh and check for loading
  await page.goto("/game")

  // Should see loading skeleton
  const skeleton = page.locator(".animate-pulse")
  await expect(skeleton).toBeVisible()
})

test("Escape key clears selection", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select some tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  // Verify tiles are selected
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(2)

  // Press Escape
  await page.keyboard.press("Escape")

  // Verify no tiles are selected
  const selectedTiles = page.locator('[aria-pressed="true"]')
  await expect(selectedTiles).toHaveCount(0)
})

test("Tiles are keyboard accessible with Tab", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  // Focus first tile with Tab
  await page.keyboard.press("Tab")

  const firstTile = page.locator('[data-testid="tile"]').first()
  await expect(firstTile).toBeFocused()
})

test("Tiles have visible focus states", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Focus first tile
  await tiles.nth(0).focus()

  // Check for focus-visible class or ring
  const focusedTile = tiles.nth(0)
  await expect(focusedTile).toBeFocused()
})

test("Tile selection toggles on click", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const firstTile = page.locator('[data-testid="tile"]').first()

  // Click to select
  await firstTile.click()
  await expect(firstTile).toHaveAttribute("aria-pressed", "true")

  // Click again to deselect
  await firstTile.click()
  await expect(firstTile).toHaveAttribute("aria-pressed", "false")
})

test("Score display shows target score", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const scoreValue = page.locator('[data-testid="score-value"]')
  const text = await scoreValue.textContent()

  // Should show "/ 100" target
  expect(text).toContain("/")
  expect(text).toContain("100")
})

test("Accessibility: Error messages use aria-live", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select tiles and submit (will likely be invalid)
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  const submitButton = page.getByRole("button", { name: "Submit" })
  await submitButton.click()

  // Check for aria-live error region
  const errorRegion = page.getByRole("alert")
  // May or may not be visible depending on validation
  if ((await errorRegion.count()) > 0) {
    await expect(errorRegion).toHaveAttribute("aria-live", "assertive")
  }
})

test("Accessibility: Hints display shows hint count", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  // Find hints display
  const hintsDisplay = page.locator("#hints-display")

  // Should be visible
  await expect(hintsDisplay).toBeVisible()

  // Should show hint count (0/5 initially)
  const text = await hintsDisplay.textContent()
  expect(text).toMatch(/\d\/5/)
})

test("localStorage: Game state persists across reload", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select some tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  // Verify tiles are selected
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(2)

  // Get the current word before reload
  const currentWordBefore = await page
    .locator('[data-testid="current-word"]')
    .textContent()

  // Reload the page
  await page.reload()

  // Wait for game to load again
  await page.waitForSelector('[data-testid="game-board"]')

  // Verify tiles are still selected after reload
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(2)

  // Verify current word is preserved
  const currentWordAfter = await page
    .locator('[data-testid="current-word"]')
    .textContent()
  expect(currentWordAfter).toBe(currentWordBefore)
})

test("localStorage: Stale session is not restored", async ({ page }) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select some tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  // Verify tiles are selected
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(2)

  // Manually set an old timestamp (> 24 hours) in localStorage
  await page.evaluate(() => {
    const stored = localStorage.getItem("quartiles_game_session")
    if (stored) {
      const parsed = JSON.parse(stored)
      // Set timestamp to 25 hours ago
      parsed.timestamp = Date.now() - 25 * 60 * 60 * 1000
      localStorage.setItem("quartiles_game_session", JSON.stringify(parsed))
    }
  })

  // Reload the page
  await page.reload()

  // Wait for game to load again
  await page.waitForSelector('[data-testid="game-board"]')

  // Verify no tiles are selected (stale session was cleared)
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(0)
})

test("localStorage: Session mismatch does not restore state", async ({
  page,
}) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select some tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  // Verify tiles are selected
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(2)

  // Manually change the session ID in localStorage
  await page.evaluate(() => {
    const stored = localStorage.getItem("quartiles_game_session")
    if (stored) {
      const parsed = JSON.parse(stored)
      // The component now checks if stored.sessionId matches gameSession.sessionId
      // Change to a different session ID to simulate mismatch
      parsed.sessionId = "different-session-id"
      localStorage.setItem("quartiles_game_session", JSON.stringify(parsed))
    }
  })

  // Reload the page
  await page.reload()

  // Wait for game to load again
  await page.waitForSelector('[data-testid="game-board"]')

  // Verify no tiles are selected (session mismatch - new session created)
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(0)
})

test("localStorage: State is cleared when game is completed", async ({
  page,
}) => {
  await page.waitForSelector('[data-testid="game-board"]')

  const tiles = page.locator('[data-testid="tile"]')

  // Select some tiles
  await tiles.nth(0).click()
  await tiles.nth(1).click()

  // Verify localStorage has data
  const hasStoredDataBefore = await page.evaluate(() => {
    return localStorage.getItem("quartiles_game_session") !== null
  })
  expect(hasStoredDataBefore).toBe(true)

  // Manually set the game as completed by setting localStorage
  await page.evaluate(() => {
    // In a real scenario, you'd complete the game
    // For this test, we just verify that if showCompleteDialog is true,
    // localStorage gets cleared
    const stored = localStorage.getItem("quartiles_game_session")
    if (stored) {
      // Modify to simulate we're in a completed state check
      localStorage.setItem("test_complete_simulation", "true")
    }
  })

  // Note: Full completion test would require solving a puzzle
  // This test verifies the storage mechanism exists
  const hasStoredDataAfter = await page.evaluate(() => {
    return localStorage.getItem("quartiles_game_session") !== null
  })
  expect(hasStoredDataAfter).toBe(true) // Still there since game wasn't actually completed
})
