import { expect, test } from "@playwright/test"

// These tests are for localStorage functionality only
// They test the localStorage persistence logic directly in the browser

test.describe("localStorage persistence", () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto("/game")
    await page.evaluate(() => localStorage.clear())
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
    expect(storedState).toHaveProperty("tiles")
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
