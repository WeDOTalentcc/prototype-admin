#!/usr/bin/env bash
# ==============================================================================
# deploy/gcp_setup.sh — GCP VM first-time setup for LIA Agent System
#
# Uso: ./deploy/gcp_setup.sh
# Pré-requisitos:
#   - gcloud CLI autenticado (gcloud auth login)
#   - Variáveis de ambiente definidas (ver seção CONFIG abaixo)
#
# O que faz:
#   1. Cria VM na GCP (e2-standard-4) com Docker instalado
#   2. Configura firewall (porta 8000 + 443)
#   3. Instala docker-compose no host
#   4. Copia arquivos de configuração
#   5. Faz primeiro deploy
# ==============================================================================
set -euo pipefail

# ── CONFIG — ajuste antes de executar ─────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
ZONE="${GCP_ZONE:-us-central1-a}"
VM_NAME="${GCP_VM_NAME:-lia-agent-vm}"
MACHINE_TYPE="${GCP_MACHINE_TYPE:-e2-standard-4}"  # 4 vCPU, 16 GB RAM
DISK_SIZE="${GCP_DISK_SIZE:-50GB}"
IMAGE_FAMILY="debian-12"
IMAGE_PROJECT="debian-cloud"
REGISTRY="gcr.io/${PROJECT_ID}/lia-agent-system"
# ──────────────────────────────────────────────────────────────────────────────

echo "→ [1/6] Criando VM ${VM_NAME} no projeto ${PROJECT_ID}..."
gcloud compute instances create "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --machine-type="${MACHINE_TYPE}" \
  --image-family="${IMAGE_FAMILY}" \
  --image-project="${IMAGE_PROJECT}" \
  --boot-disk-size="${DISK_SIZE}" \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server,lia-api \
  --scopes=cloud-platform \
  --metadata=startup-script='#!/bin/bash
    apt-get update -y
    apt-get install -y docker.io docker-compose-v2 curl
    systemctl enable docker
    systemctl start docker
    usermod -aG docker $(whoami)
    mkdir -p /opt/lia
  '

echo "→ [2/6] Aguardando VM iniciar (60s)..."
sleep 60

echo "→ [3/6] Configurando firewall..."
gcloud compute firewall-rules create allow-lia-api \
  --project="${PROJECT_ID}" \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:8000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=lia-api \
  2>/dev/null || echo "  (firewall rule already exists)"

echo "→ [4/6] Copiando arquivos de configuração..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/.."

gcloud compute scp \
  "${APP_DIR}/docker-compose.yml" \
  "${APP_DIR}/docker-compose.prod.yml" \
  "${VM_NAME}:/opt/lia/" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}"

# Copia .env.prod se existir localmente
if [ -f "${APP_DIR}/.env.prod" ]; then
  gcloud compute scp \
    "${APP_DIR}/.env.prod" \
    "${VM_NAME}:/opt/lia/.env.prod" \
    --project="${PROJECT_ID}" \
    --zone="${ZONE}"
  echo "  .env.prod copiado"
else
  echo "  AVISO: .env.prod não encontrado — configure manualmente em /opt/lia/.env.prod"
fi

echo "→ [5/6] Configurando GCR auth no host..."
gcloud compute ssh "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --command="gcloud auth configure-docker gcr.io --quiet"

echo "→ [6/6] Primeiro deploy..."
IMAGE_TAG=$(git -C "${APP_DIR}" rev-parse --short HEAD 2>/dev/null || echo "latest")
GCP_VM_NAME="${VM_NAME}" GCP_ZONE="${ZONE}" PROJECT_ID="${PROJECT_ID}" \
  make -C "${APP_DIR}/deploy" deploy-gcp IMAGE_TAG="${IMAGE_TAG}"

VM_IP=$(gcloud compute instances describe "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✓ Setup concluído!"
echo "  VM:    ${VM_NAME} (${VM_IP})"
echo "  API:   http://${VM_IP}:8000/api/v1/health"
echo "  Docs:  http://${VM_IP}:8000/docs"
