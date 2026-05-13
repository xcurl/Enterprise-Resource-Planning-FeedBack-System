#!/usr/bin/env bash
set -e

cd ug_feedback_system

echo "[startup] Ensuring test users are initialized..."

max_attempts="${SEED_MAX_RETRIES:-10}"
attempt=1
while [ "$attempt" -le "$max_attempts" ]; do
  if python create_test_users.py; then
    echo "[startup] Test users ready."
    break
  fi
  echo "[startup] Seed attempt ${attempt}/${max_attempts} failed. Retrying in 5s..."
  attempt=$((attempt + 1))
  sleep 5
done

if [ "$attempt" -gt "$max_attempts" ]; then
  echo "[startup] Failed to initialize test users after ${max_attempts} attempts."
  exit 1
fi

exec gunicorn wsgi:app --bind 0.0.0.0:${PORT:-5000}
