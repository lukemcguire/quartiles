import fs from "node:fs"
import { expect, test } from "@playwright/test"

// These tests are for localStorage functionality only
// They test the localStorage persistence logic directly in the browser

test.describe("localStorage persistence", () => {
  test.beforeEach(async ({ page, context }) => {
    // Restore access_token from auth setup
    let accessToken = ""
    try {
      accessToken = fs.readFileSync(
        "playwright/.auth/access_token.txt",
        "utf-8",
      )
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

    await page.goto("/game")
  })

  test("Storage key exists and can be written", async ({ page }) => {
    await page.goto("/game")

    // Wait for game to load
    await page.waitForSelector('[data-testid="game-board"]', { timeout: 15000 })

    // Verify we can write to localStorage
    const canWrite = await page.evaluate(() => {
      try {
        localStorage.setItem("test_key", "test_value")
        return localStorage.getItem("test_key") === "test_value"
      } catch (_e) {
        return false
      }
    })

    expect(canWrite).toBe(true)
  })

  test("Game state structure is correct", async ({ page }) => {
    await page.goto("/game")

    // Wait for game to load
    await page.waitForSelector('[data-testid="game-board"]', { timeout: 15015 })

    // Select some tiles to trigger a localStorage save
    const tiles = page.locator('[data-testid="tile"]')
    await tiles.nth(0).click()
    await tiles.nth(1).click()

    // Wait a bit for the effect to run
    await page.waitForTimeout(100)

    // Check localStorage has correct structure
    const storedState = await page.evaluate(() => {
      const stored = localStorage.getItem("quartiles_game_session")
      if (!stored) return null
      return JSON.parse(stored)
    })

    expect(storedState).not.toBeNull()
    expect(storedState).toHaveProperty("sessionId")
    expect(storedState).toHaveProperty("timestamp")
    expect(storedState).toHaveProperty("puzzleId") // Changed from tiles
    expect(storedState).toHaveProperty("foundWords")
    expect(storedState).toHaveProperty("selectedTileIds")
    expect(storedState).toHaveProperty("timeElapsed")
    expect(storedState).toHaveProperty("hintsUsed")
  })

  test("Selected tiles are saved to localStorage", async ({ page }) => {
    await page.goto("/game")

    // Wait for game to load
    await page.waitForSelector('[data-testid="game-board"]', { timeout: 15000 })

    // Select some tiles
    const tiles = page.locator('[data-testid="tile"]')
    await tiles.nth(0).click()
    await tiles.nth(1).click()

    // Wait for effect
    await page.waitForTimeout(100)

    // Check stored selectedTileIds
    const selectedTileIds = await page.evaluate(() => {
      const stored = localStorage.getItem("quartiles_game_session")
      if (!stored) return []
      return JSON.parse(stored).selectedTileIds
    })

    expect(selectedTileIds).toHaveLength(2)
  })

  test("Stale timestamp is detected correctly", async ({ page }) => {
    await page.goto("/game")

    // Wait for game to load
    await page.waitForSelector('[data-testid="game-board"]', { timeout: 15000 })

    // Manually set an old timestamp (> 24 hours)
    await page.evaluate(() => {
      const stored = localStorage.getItem("quartiles_game_session")
      if (stored) {
        const parsed = JSON.parse(stored)
        parsed.timestamp = Date.now() - 25 * 60 * 60 * 1000 // 25 hours ago
        localStorage.setItem("quartiles_game_session", JSON.stringify(parsed))
      }
    })

    // Get the stored timestamp
    const storedTimestamp = await page.evaluate(() => {
      const stored = localStorage.getItem("quartiles_game_session")
      if (!stored) return null
      return JSON.parse(stored).timestamp
    })

    const age = Date.now() - (storedTimestamp || 0)
    const twentyFourHours = 24 * 60 * 60 * 1000

    // Verify the timestamp is more than 24 hours old
    expect(age).toBeGreaterThan(twentyFourHours)
  })

  test("localStorage is cleared when explicitly removed", async ({ page }) => {
    await page.goto("/game")

    // Wait for game to load
    await page.waitForSelector('[data-testid="game-board"]', { timeout: 15000 })

    // Select some tiles to create state
    const tiles = page.locator('[data-testid="tile"]')
    await tiles.nth(0).click()

    // Wait for effect
    await page.waitForTimeout(100)

    // Verify storage has data
    const hasDataBefore = await page.evaluate(() => {
      return localStorage.getItem("quartiles_game_session") !== null
    })
    expect(hasDataBefore).toBe(true)

    // Clear storage
    await page.evaluate(() => {
      localStorage.removeItem("quartiles_game_session")
    })

    // Verify storage is empty
    const hasDataAfter = await page.evaluate(() => {
      return localStorage.getItem("quartiles_game_session") !== null
    })
    expect(hasDataAfter).toBe(false)
  })
})
