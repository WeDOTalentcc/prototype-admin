#!/usr/bin/env bash
#
# safe_commit.sh — race-condition guard para Replit multi-agent
#
# Usage:
#   ./scripts/safe_commit.sh \
#     --message "feat(xxx): subject" \
#     --files "path/file1 path/file2 ..."
#
# Optional flags:
#   --allow-empty   permite commit vazio (default: rejeita)
#   --dry-run       só valida staging + exit sem commit
#
# Capabilities:
# - Captura HEAD antes/depois (detecta absorption)
# - Stages SO files declarados (no `git add .`)
# - Verifica staged == declared (detecta rogue files)
# - Verifica commit message bate com --message (detecta capture)
# - Verifica commit contem files declarados (detecta drop)
# - Exit non-zero em qualquer guard fail
#
# Refs:
# - CLAUDE.md "Race-condition harness — commits multi-agent" (registrado 2026-05-23)
# - Historico: Sprint 3.3 (WSI absorbed), T4 (TemplateClonePanel absorbed),
#   Workstream A T5 (commit absorption).

set -euo pipefail

MESSAGE=""
FILES_RAW=""
ALLOW_EMPTY="false"
DRY_RUN="false"

while [ $# -gt 0 ]; do
    case "$1" in
        --message|-m) MESSAGE="$2"; shift 2 ;;
        --files|-f) FILES_RAW="$2"; shift 2 ;;
        --allow-empty) ALLOW_EMPTY="true"; shift ;;
        --dry-run) DRY_RUN="true"; shift ;;
        -h|--help)
            sed -n '1,30p' "$0"
            exit 0
            ;;
        *)
            echo "❌ Unknown arg: $1"
            echo "   Use --help para sintaxe."
            exit 2
            ;;
    esac
done

if [ -z "$MESSAGE" ]; then
    echo "❌ --message required"
    exit 2
fi

if [ -z "$FILES_RAW" ]; then
    echo "❌ --files required (espaco-separados)"
    exit 2
fi

# Parse FILES_RAW into array (POSIX-friendly word splitting)
# shellcheck disable=SC2206
FILES=( $FILES_RAW )

if [ "${#FILES[@]}" -eq 0 ]; then
    echo "❌ --files vazio apos parsing"
    exit 2
fi

echo "🔍 safe_commit guard ativo (race-condition harness)"

# 0. Normalize paths to repo-root-relative (script funciona em qualquer subdir do monorepo)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
    echo "❌ Nao esta dentro de um repo git"
    exit 2
fi
CWD=$(pwd)
NORMALIZED_FILES=()
for f in "${FILES[@]}"; do
    # Strip leading ./
    f_clean="${f#./}"
    # If file path is absolute, make it relative to repo root
    if [[ "$f_clean" = /* ]]; then
        rel="${f_clean#$REPO_ROOT/}"
    else
        # Resolve absolute path of "$CWD/$f_clean", then make relative to REPO_ROOT
        abs="$CWD/$f_clean"
        # Best-effort normalize without realpath (POSIX): collapse to abs form
        rel="${abs#$REPO_ROOT/}"
    fi
    NORMALIZED_FILES+=("$rel")
done
FILES=("${NORMALIZED_FILES[@]}")

# Operate from REPO_ROOT for consistent path semantics
cd "$REPO_ROOT" || exit 2

# 1. Capture HEAD before
HEAD_BEFORE=$(git rev-parse HEAD 2>/dev/null || echo "NONE")
echo "  HEAD before: $HEAD_BEFORE"

# 2. Aviso para files inexistentes (podem ser deletes intencionais)
for f in "${FILES[@]}"; do
    if [ ! -e "$f" ]; then
        echo "  ⚠ File nao existe (sera tratado como delete se tracked): $f"
    fi
done

# 3. Detecta files ja stageados ANTES (rogue staging por outro agent)
DECLARED_PRECHECK=$(printf '%s\n' "${FILES[@]}" | sed 's|^\./||' | sort -u)
PRE_STAGED=$(git diff --cached --name-only --no-renames | sed 's|^\./||' | sort -u)
if [ -n "$PRE_STAGED" ]; then
    PRE_ROGUE=$(comm -23 <(printf '%s\n' "$PRE_STAGED") <(printf '%s\n' "$DECLARED_PRECHECK"))
    if [ -n "$PRE_ROGUE" ]; then
        echo "  🚨 PRE-EXISTING ROGUE STAGING detected — files staged antes do script:"
        printf '%s\n' "$PRE_ROGUE" | sed 's/^/    /'
        echo ""
        echo "  Declared files:"
        printf '%s\n' "$DECLARED_PRECHECK" | sed 's/^/    /'
        echo ""
        echo "  Likely cause: outro agent ou comando staged files antes desta invocacao."
        echo "  Action: rodar 'git reset HEAD' manualmente, revisar, e rerun."
        exit 3
    fi
fi

# 4. Reset staging area para staging limpo (so files declarados)
git reset --quiet HEAD -- . 2>/dev/null || true

# 5. Stage SO files declarados
STAGE_FAILED=0
for f in "${FILES[@]}"; do
    if ! git add -- "$f" 2>/dev/null; then
        # Try delete (file gone but tracked)
        if ! git add -u -- "$f" 2>/dev/null; then
            echo "  ⚠ git add falhou em: $f"
            STAGE_FAILED=1
        fi
    fi
done

if [ "$STAGE_FAILED" -eq 1 ]; then
    echo "  ❌ Falha ao stage algum file declarado. Abortando."
    git reset --quiet HEAD -- . 2>/dev/null || true
    exit 2
fi

# 5. Verify staged matches declared
# Use --no-renames para evitar staged showing as "from/to" pairs
STAGED=$(git diff --cached --name-only --no-renames | sort -u)
DECLARED=$(printf '%s\n' "${FILES[@]}" | sed 's|^\./||' | sort -u)
STAGED_NORM=$(printf '%s\n' "$STAGED" | sed 's|^\./||' | sort -u)

# Compute set difference: lines in STAGED but not in DECLARED
ROGUE=$(comm -23 <(printf '%s\n' "$STAGED_NORM") <(printf '%s\n' "$DECLARED"))

if [ -n "$ROGUE" ]; then
    echo "  🚨 STAGE MISMATCH detected — files staged mas nao declarados:"
    printf '%s\n' "$ROGUE" | sed 's/^/    /'
    echo ""
    echo "  Declared files:"
    printf '%s\n' "$DECLARED" | sed 's/^/    /'
    echo "  Actual staged:"
    printf '%s\n' "$STAGED_NORM" | sed 's/^/    /'
    echo ""
    echo "  Likely cause: another agent staged files simultaneously,"
    echo "  OR files were staged outside this script before invocation."
    echo "  Action: revisar staged + rerun com --files corrigido."
    git reset --quiet HEAD -- . 2>/dev/null || true
    exit 3
fi

# 6. Check empty commit
if [ -z "$STAGED" ] && [ "$ALLOW_EMPTY" != "true" ]; then
    echo "  ⚠ Nothing staged (use --allow-empty se intencional)"
    exit 2
fi

# 7. Dry-run exit point
if [ "$DRY_RUN" = "true" ]; then
    echo "  🏃 DRY RUN — nao commiting. Staged files validados:"
    printf '%s\n' "$STAGED_NORM" | sed 's/^/    /'
    echo "  Message preview:"
    printf '%s\n' "$MESSAGE" | head -3 | sed 's/^/    /'
    git reset --quiet HEAD -- . 2>/dev/null || true
    exit 0
fi

# 8. Commit
EXTRA_FLAGS=""
if [ "$ALLOW_EMPTY" = "true" ]; then
    EXTRA_FLAGS="--allow-empty"
fi

COMMIT_OUTPUT=$(git commit $EXTRA_FLAGS -m "$MESSAGE" 2>&1) || {
    echo "  ❌ git commit falhou:"
    printf '%s\n' "$COMMIT_OUTPUT" | head -10 | sed 's/^/    /'
    exit 4
}

# 9. Verify HEAD advanced
HEAD_AFTER=$(git rev-parse HEAD)
if [ "$HEAD_BEFORE" = "$HEAD_AFTER" ]; then
    echo "  ⚠ HEAD nao avancou — commit pode ter sido absorvido OU foi no-op"
    exit 5
fi
echo "  HEAD after:  $HEAD_AFTER"

# 10. Verify commit subject matches input
ACTUAL_SUBJECT=$(git log -1 --pretty=%s "$HEAD_AFTER")
DECLARED_SUBJECT=$(printf '%s\n' "$MESSAGE" | head -1)
if [ "$ACTUAL_SUBJECT" != "$DECLARED_SUBJECT" ]; then
    echo "  🚨 COMMIT MESSAGE MISMATCH (likely absorbed by parallel agent):"
    echo "    Declared: $DECLARED_SUBJECT"
    echo "    Actual:   $ACTUAL_SUBJECT"
    echo "  Action: investigar git log -3, decidir manual rollback OR registrar ticket harness."
    exit 6
fi

# 11. Verify commit contains all declared files
COMMIT_FILES=$(git show --pretty="" --name-only "$HEAD_AFTER" | sort -u | grep -v '^$' || true)
MISSING=""
for f in $DECLARED; do
    if ! printf '%s\n' "$COMMIT_FILES" | grep -qxF "$f"; then
        MISSING="$MISSING $f"
    fi
done
if [ -n "$MISSING" ]; then
    echo "  🚨 Files DECLARADOS nao aparecem no commit final:"
    echo "    Missing:$MISSING"
    echo "  Action: rerun safe_commit explicito ou investigar pre-commit hook que ignorou."
    exit 7
fi

echo "✅ safe_commit OK: $HEAD_AFTER ($DECLARED_SUBJECT)"
exit 0
