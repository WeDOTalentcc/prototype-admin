#!/bin/bash
# userdata.sh — Script de inicialização EC2 para LIA Agent System
# Executado uma vez na primeira inicialização da instância.
# Equivalente ao bloco --user-data em aws_setup.sh (dnf + docker-compose v2)
set -euo pipefail

echo "[userdata] Instalando Docker via dnf (Amazon Linux 2023)..."
dnf install -y docker

echo "[userdata] Habilitando e iniciando o serviço Docker..."
systemctl enable docker
systemctl start docker

echo "[userdata] Adicionando ec2-user ao grupo docker..."
usermod -aG docker ec2-user

echo "[userdata] Instalando docker-compose v2 como plugin CLI..."
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL \
  "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

echo "[userdata] Criando diretório da aplicação /opt/lia..."
mkdir -p /opt/lia

echo "[userdata] Concluído."
