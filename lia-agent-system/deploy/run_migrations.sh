#!/bin/sh
# LIA-D02: Separate migration runner for deploy safety
# Runs BEFORE containers start serving traffic.
# Use as: Cloud Run Job, init container, or GitHub Actions pre-deploy step.
# DO NOT run migrations inside the serving container CMD — race condition on scale-up.
set -e
echo "[LIA-D02] Running alembic migrations..."
alembic upgrade head
echo "[LIA-D02] Migrations complete."
