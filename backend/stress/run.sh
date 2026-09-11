#!/usr/bin/env bash
# 用法: ./run.sh <tag> <users> <spawn-rate> <run-time>
# 例:   ./run.sh s2 100 5 10m
set -euo pipefail

TAG="${1:-s0}"
USERS="${2:-1}"
RATE="${3:-1}"
RUNTIME="${4:-30s}"

case "$TAG" in
  s1) CLASS=AuthUser ;;
  s2) CLASS=ChatUser ;;
  s3) CLASS=CacheUser ;;
  s4) CLASS=WriteUser ;;
  *)  CLASS=SmokeUser ;;
esac

cd "$(dirname "$0")"
mkdir -p results

../venv/Scripts/python -m locust -f locustfile.py \
  --host http://localhost:8001 \
  --users "$USERS" \
  --spawn-rate "$RATE" \
  --run-time "$RUNTIME" \
  --headless \
  --csv "results/${TAG}_u${USERS}" \
  "$CLASS"
