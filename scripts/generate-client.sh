#!/usr/bin/env bash

# Generate the TypeScript client from the OpenAPI schema

set -e

echo "Generating TypeScript API client..."

cd "$(dirname "$0")/../frontend"

# Ensure the backend is running and accessible
if ! curl -s http://localhost:8000/api/v1/openapi.json > /dev/null 2>&1; then
    echo "Warning: Backend API is not accessible at http://localhost:8000"
    echo "Make sure the backend is running before generating the client."
    exit 1
fi

npm run generate-client

echo "Client generated successfully in frontend/src/client/"
