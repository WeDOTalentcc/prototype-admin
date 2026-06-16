#!/usr/bin/env bash
# install_hooks.sh — bootstrap de git hooks WeDOTalent (GAP-00-008)
#
# Replit pode resetar .git/hooks/ ao reiniciar o workspace.
# Rodar este script recria os hooks em <1s.
#
# Uso:
#   bash scripts/install_hooks.sh          # instala
#   bash scripts/install_hooks.sh --check  # verifica sem instalar
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
LIA_DIR="$REPO_ROOT/lia-agent-system"
HOOK_SRC="$LIA_DIR/scripts/pre-commit-hook.sh"
HOOK_DEST="$HOOKS_DIR/pre-commit"

CHECK_ONLY=0
if [[ "${1:-}" == "--check" ]]; then
    CHECK_ONLY=1
fi

if [[ ! -f "$HOOK_SRC" ]]; then
    echo "❌ Hook source não encontrado: $HOOK_SRC" >&2
    exit 1
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
    if [[ -x "$HOOK_DEST" ]]; then
        echo "✅ pre-commit hook instalado e executável: $HOOK_DEST"
        exit 0
    else
        echo "❌ pre-commit hook ausente ou não executável: $HOOK_DEST" >&2
        exit 1
    fi
fi

mkdir -p "$HOOKS_DIR"

cat > "$HOOK_DEST" << HOOK
#!/usr/bin/env bash
# Auto-gerado por scripts/install_hooks.sh — NÃO editar diretamente.
# Para alterar o comportamento: editar scripts/pre-commit-hook.sh e reinstalar.
exec "\$(git rev-parse --show-toplevel)/lia-agent-system/scripts/pre-commit-hook.sh" "\$@"
HOOK

chmod +x "$HOOK_DEST"
echo "✅ pre-commit hook instalado: $HOOK_DEST"
echo "   → Roda: lia-agent-system/scripts/pre-commit-hook.sh"
echo "   → Pular lentos: SKIP_SLOW_SENSORS=1 git commit ..."
echo "   → Emergência: SKIP_ALL_SENSORS=1 git commit ..."
