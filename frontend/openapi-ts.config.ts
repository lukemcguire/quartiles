import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  client: "@hey-api/client-fetch",
  input: "http://localhost:8000/api/v1/openapi.json",
  output: "src/client",
})
