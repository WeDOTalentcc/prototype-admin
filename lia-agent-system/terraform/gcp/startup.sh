#!/bin/bash
# startup.sh — Script de inicialização da VM GCP para LIA Agent System
# Executado uma vez na primeira inicialização da instância Compute Engine.
# Equivalente ao bloco --metadata=startup-script em gcp_setup.sh
set -euo pipefail

echo "[startup] Atualizando pacotes..."
apt-get update -y

echo "[startup] Instalando docker.io e docker-compose-v2..."
apt-get install -y docker.io docker-compose-v2 curl

echo "[startup] Habilitando e iniciando o serviço Docker..."
systemctl enable docker
systemctl start docker

echo "[startup] Adicionando usuário padrão ao grupo docker..."
usermod -aG docker "$(whoami)" || true

echo "[startup] Criando diretório da aplicação /opt/lia..."
mkdir -p /opt/lia

echo "[startup] Concluído."
