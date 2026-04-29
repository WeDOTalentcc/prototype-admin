#!/bin/bash
set -e

# =============================================================================
# DOCKER ENTRYPOINT INTELIGENTE
# =============================================================================
# Este script resolve o problema clássico de Docker + volumes de gems:
# - Detecta mudanças no Gemfile.lock via checksum MD5
# - Roda bundle install automaticamente se necessário
# - Remove server.pid órfão
# - Executa o comando passado (rails server, sidekiq, etc)
# =============================================================================

GEMFILE_LOCK="/rails/Gemfile.lock"
CHECKSUM_FILE="/tmp/gemfile_lock_checksum"
BUNDLE_PATH="${BUNDLE_PATH:-/usr/local/bundle}"

# Função para calcular MD5 do Gemfile.lock
calculate_checksum() {
    if [ -f "$GEMFILE_LOCK" ]; then
        # Tenta md5sum primeiro, depois md5 (macOS), depois fallback para stat
        if command -v md5sum >/dev/null 2>&1; then
            md5sum "$GEMFILE_LOCK" | cut -d' ' -f1
        elif command -v md5 >/dev/null 2>&1; then
            md5 -q "$GEMFILE_LOCK"
        else
            # Fallback: usa stat para detectar mudanças (menos preciso, mas funciona)
            stat -c %Y "$GEMFILE_LOCK" 2>/dev/null || stat -f %m "$GEMFILE_LOCK" 2>/dev/null || echo "unknown"
        fi
    else
        echo ""
    fi
}

# Função para obter checksum salvo
get_saved_checksum() {
    if [ -f "$CHECKSUM_FILE" ]; then
        cat "$CHECKSUM_FILE"
    else
        echo ""
    fi
}

# Função para salvar checksum
save_checksum() {
    local checksum=$1
    echo "$checksum" > "$CHECKSUM_FILE"
}

# Função para instalar gems
install_gems() {
    echo "📦 Gemfile.lock mudou! Instalando gems..."
    
    # Configura bundle para desenvolvimento se necessário
    if [ "$RAILS_ENV" = "development" ]; then
        bundle config unset without || true
    fi
    
    # Instala gems
    bundle install
    
    echo "✅ Gems instaladas com sucesso!"
}

# =============================================================================
# MAIN
# =============================================================================

if [ "$RAILS_ENV" != "production" ]; then
    CURRENT_CHECKSUM=$(calculate_checksum)
    SAVED_CHECKSUM=$(get_saved_checksum)

    if [ "$CURRENT_CHECKSUM" != "$SAVED_CHECKSUM" ] || [ -z "$CURRENT_CHECKSUM" ]; then
        install_gems
        save_checksum "$CURRENT_CHECKSUM"
    fi
fi

# Remove server.pid órfão (se existir)
if [ -f "/rails/tmp/pids/server.pid" ]; then
    rm -f /rails/tmp/pids/server.pid
fi

# Executa o comando passado
exec "$@"

