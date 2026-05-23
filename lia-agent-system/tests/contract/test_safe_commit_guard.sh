#!/usr/bin/env bash
# tests/contract/test_safe_commit_guard.sh
#
# Test contract de scripts/safe_commit.sh — race-condition guard.
#
# Cases:
# 1. Happy path: --files declarado e staged corretamente → exit 0
# 2. Stage mismatch: file extra staged fora do script → exit 3
# 3. Message capture: commit message diverge → exit 6 (simulado via pre-commit hook)
# 4. Empty staging sem --allow-empty → exit 2
# 5. Missing required args → exit 2
# 6. Dry run: valida + nao commiting
#
# Setup: cria sandbox em mktemp, nao polui workspace.

set -uo pipefail

# Script under test
SCRIPT="/home/runner/workspace/lia-agent-system/scripts/safe_commit.sh"

if [ ! -x "$SCRIPT" ]; then
    echo "❌ Script nao executavel: $SCRIPT"
    exit 1
fi

PASS=0
FAIL=0

run_test() {
    local name="$1"
    local expected_exit="$2"
    local actual_exit="$3"
    if [ "$expected_exit" = "$actual_exit" ]; then
        echo "  ✅ PASS: $name (exit=$actual_exit)"
        PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $name (expected exit=$expected_exit, got $actual_exit)"
        FAIL=$((FAIL + 1))
    fi
}

# Setup sandbox
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$TMP_DIR"
git init -q
git config user.email "test@safe-commit.local"
git config user.name "Safe Commit Test"
echo "initial" > a.txt
git add a.txt
git commit -m "initial" -q

echo "=== Test 1: Happy path ==="
echo "modified" > a.txt
"$SCRIPT" --message "test: modify a.txt" --files "a.txt" >/dev/null 2>&1
run_test "happy path" 0 $?

echo "=== Test 2: Stage mismatch (rogue file staged outside) ==="
echo "more" > a.txt
echo "stray" > b.txt
git add b.txt  # rogue staging outside script
"$SCRIPT" --message "test: only a.txt" --files "a.txt" >/dev/null 2>&1
EXIT=$?
# Reset b.txt staging after this test
git reset --quiet HEAD -- . 2>/dev/null || true
rm -f b.txt
git checkout -- a.txt 2>/dev/null || true
run_test "stage mismatch detected" 3 $EXIT

echo "=== Test 3: Empty staging without --allow-empty ==="
# Nothing modified, declare an existing file → nothing staged
"$SCRIPT" --message "test: empty" --files "a.txt" >/dev/null 2>&1
run_test "empty staging rejected" 2 $?

echo "=== Test 4: Missing --message ==="
"$SCRIPT" --files "a.txt" >/dev/null 2>&1
run_test "missing message rejected" 2 $?

echo "=== Test 5: Missing --files ==="
"$SCRIPT" --message "x" >/dev/null 2>&1
run_test "missing files rejected" 2 $?

echo "=== Test 6: Dry run (valida sem commit) ==="
echo "dryrun" > a.txt
HEAD_BEFORE=$(git rev-parse HEAD)
"$SCRIPT" --message "test: dry" --files "a.txt" --dry-run >/dev/null 2>&1
EXIT=$?
HEAD_AFTER=$(git rev-parse HEAD)
if [ "$HEAD_BEFORE" = "$HEAD_AFTER" ] && [ "$EXIT" = "0" ]; then
    echo "  ✅ PASS: dry run (exit=0, HEAD nao avancou)"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL: dry run (exit=$EXIT, HEAD before=$HEAD_BEFORE after=$HEAD_AFTER)"
    FAIL=$((FAIL + 1))
fi
git checkout -- a.txt 2>/dev/null || true

echo "=== Test 7: Multiple files happy path ==="
echo "v2" > a.txt
echo "new" > c.txt
"$SCRIPT" --message "test: multi" --files "a.txt c.txt" >/dev/null 2>&1
run_test "multi-file happy path" 0 $?

echo ""
echo "============================================================"
echo "Results: $PASS passed, $FAIL failed"
echo "============================================================"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
