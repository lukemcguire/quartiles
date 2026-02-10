import type { FullConfig } from "@playwright/test"

async function globalSetup(_config: FullConfig) {
  // This is a global setup that runs before all tests
  // We'll use per-test setup instead (see test fixtures or beforeEach hooks)
  console.log("Playwright global setup: Tests starting...")
}

export default globalSetup
