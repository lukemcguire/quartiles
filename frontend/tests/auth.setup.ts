import fs from "node:fs"
import { test as setup } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

const authFile = "playwright/.auth/user.json"

setup("authenticate", async ({ page, context }) => {
  // Clear localStorage before login to ensure fresh state
  await page.addInitScript(() => {
    localStorage.clear()
    localStorage.removeItem("device_fingerprint")
    localStorage.removeItem("quartiles_game_session")
  })

  // Mock the login API to return a fake token
  await context.route("**/api/v1/login/access-token", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "test-fake-access-token-12345",
        token_type: "bearer",
      }),
    })
  })

  // Mock the user/me API
  await context.route("**/api/v1/users/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "test-user-id",
        email: firstSuperuser,
        full_name: "Test User",
        is_active: true,
        is_superuser: true,
      }),
    })
  })

  // Mock the puzzle API at the context level (persists across pages)
  // This ensures all tests using this auth state get a fresh puzzle
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

  // Mock the game start API at the context level (persists across pages)
  // This ensures all tests using this auth state get a fresh game
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

  await page.goto("/login")
  await page.getByTestId("email-input").fill(firstSuperuser)
  await page.getByTestId("password-input").fill(firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  // Wait for navigation to complete
  await page.waitForLoadState("networkidle", { timeout: 10000 })

  // Wait a bit more for the token to be saved
  await page.waitForTimeout(1000)

  // Save the access_token for later restoration in tests
  const localStorageContents = await page.evaluate(() => {
    const contents: Record<string, string> = {}
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key) {
        contents[key] = localStorage.getItem(key) || ""
      }
    }
    return contents
  })

  console.log(
    "LocalStorage contents after login:",
    Object.keys(localStorageContents),
  )

  const accessToken = localStorageContents.access_token || ""

  if (!accessToken) {
    console.log("WARNING: access_token not found in localStorage after login!")
    console.log("Available keys:", Object.keys(localStorageContents))
  }

  // Clear device_fingerprint and game session before saving
  await page.evaluate(() => {
    localStorage.removeItem("device_fingerprint")
    localStorage.removeItem("quartiles_game_session")
  })

  await context.storageState({ path: authFile })

  // Save access_token to a file for restoration (storageState doesn't save localStorage)
  if (accessToken) {
    fs.mkdirSync("playwright/.auth", { recursive: true })
    fs.writeFileSync("playwright/.auth/access_token.txt", accessToken)
    console.log("Saved access_token to file")
  }
})
