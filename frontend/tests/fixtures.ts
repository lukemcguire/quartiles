import { test as base } from "@playwright/test"

// Extend the base test to add API mocking for game start
// This ensures all tests get a fresh game session
export const test = base.extend({
  page: async ({ page }, use) => {
    // Mock the game start API before any page loads
    await page.route("**/api/v1/game/start", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          session_id: `test-session-${Date.now()}-${Math.random()}`,
          player_id: `test-player-${Date.now()}-${Math.random()}`,
          display_name: "Test Player",
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
          already_played: false,
        }),
      })
    })

    await use(page)
  },
})

export { expect } from "@playwright/test"
