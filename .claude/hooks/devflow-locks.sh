#!/usr/bin/env bash
# DevFlow v3.6 — Global Lock Utilities
# Source this file in SKILL.md bash snippets:
#   source .claude/hooks/devflow-locks.sh

# Git Lock — prevents concurrent git operations across sessions
acquire_git_lock() {
  local feature="${1:-unknown}"
  local lock_file=".git/devflow-lock"
  local max_wait=300  # 5 minutes max
  local waited=0

  while [ -f "$lock_file" ]; do
    local holder=$(cat "$lock_file" 2>/dev/null || echo "unknown")
    local now=$(date +%s)
    local lock_time=$(stat -c%Y "$lock_file" 2>/dev/null || echo "$now")
    local lock_age=$(( now - lock_time ))

    if [ "$lock_age" -gt "$max_wait" ]; then
      echo "⚠️ Git lock held by '$holder' for ${lock_age}s (timeout). Force-releasing."
      rm -f "$lock_file"
      break
    fi

    if [ "$waited" -eq 0 ]; then
      echo "⏳ Waiting for git lock (held by '$holder')..."
    fi
    sleep 2
    waited=$(( waited + 2 ))
  done

  echo "$feature" > "$lock_file"
}

release_git_lock() {
  rm -f .git/devflow-lock
}

# Verify Lock — ensures only one session runs Playwright at a time
acquire_verify_lock() {
  local feature="${1:-unknown}"
  local lock_file=".devflow-verify-lock"
  local max_wait=900  # 15 minutes
  local waited=0

  while [ -f "$lock_file" ]; do
    local holder=$(cat "$lock_file" 2>/dev/null || echo "unknown")
    local now=$(date +%s)
    local lock_time=$(stat -c%Y "$lock_file" 2>/dev/null || echo "$now")
    local lock_age=$(( now - lock_time ))

    if [ "$lock_age" -gt "$max_wait" ]; then
      echo "⚠️ Verify lock held by '$holder' for ${lock_age}s (timeout). Force-releasing."
      rm -f "$lock_file"
      break
    fi

    if [ "$waited" -eq 0 ]; then
      echo "⏳ Waiting for verify lock (held by '$holder', ${lock_age}s)..."
    fi
    sleep 5
    waited=$(( waited + 5 ))
  done

  echo "$feature" > "$lock_file"
}

release_verify_lock() {
  rm -f .devflow-verify-lock
}

# Port Allocation — find first available port starting from 3001
allocate_port() {
  local registry=".global-registry.json"
  local base_port=3001

  if [ ! -f "$registry" ]; then
    echo "$base_port"
    return
  fi

  local used_ports=$(jq -r '[.sessions[].port // empty] | .[]' "$registry" 2>/dev/null)
  local port=$base_port
  while echo "$used_ports" | grep -q "^$port$"; do
    port=$(( port + 1 ))
  done
  echo "$port"
}
