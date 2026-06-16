#!/bin/bash
set -e

# Install any missing packages that aren't in the base image
echo "[entrypoint] Checking missing dependencies..."
pip install --no-cache-dir --quiet \
    reportlab \
    workos \
    deepgram-sdk \
    google-genai \
    pypdf \
    hubspot-api-client \
    2>&1 | grep -E "Successfully installed|already satisfied|ERROR" || true

echo "[entrypoint] Starting application: $@"
exec "$@"
