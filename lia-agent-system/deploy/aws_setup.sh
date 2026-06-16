#!/usr/bin/env bash
# ==============================================================================
# deploy/aws_setup.sh — AWS EC2 first-time setup for LIA Agent System
#
# Uso: ./deploy/aws_setup.sh
# Pré-requisitos:
#   - AWS CLI configurado (aws configure)
#   - Variáveis de ambiente definidas (ver seção CONFIG)
#   - IAM role com permissões: EC2, ECR, SSM, SecretsManager
#
# O que faz:
#   1. Cria security group (portas 22, 8000, 443)
#   2. Cria instância EC2 (t3.xlarge) com user-data Docker
#   3. Registra repositório no ECR
#   4. Copia configs via SSM + S3
#   5. Faz primeiro deploy via SSM Run Command
# ==============================================================================
set -euo pipefail

# ── CONFIG — ajuste antes de executar ─────────────────────────────────────────
AWS_REGION="${AWS_REGION:-us-east-1}"
INSTANCE_TYPE="${AWS_INSTANCE_TYPE:-t3.xlarge}"  # 4 vCPU, 16 GB RAM
AMI_ID="${AWS_AMI_ID:-}"  # se vazio, resolve automaticamente
KEY_NAME="${AWS_KEY_NAME:?Set AWS_KEY_NAME (EC2 key pair)}"
VPC_ID="${AWS_VPC_ID:-}"  # se vazio, usa default VPC
INSTANCE_NAME="lia-agent-system"
ECR_REPO_NAME="lia-agent-system"
S3_CONFIG_BUCKET="${AWS_S3_CONFIG_BUCKET:-}"  # bucket para .env.prod
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/.."

# Resolve AMI mais recente do Amazon Linux 2023 se não fornecida
if [ -z "${AMI_ID}" ]; then
  echo "→ Resolvendo AMI mais recente do Amazon Linux 2023..."
  AMI_ID=$(aws ec2 describe-images \
    --region "${AWS_REGION}" \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023*-x86_64" \
    --query "sort_by(Images, &CreationDate)[-1].ImageId" \
    --output text)
  echo "  AMI: ${AMI_ID}"
fi

# Resolve VPC default se não fornecida
if [ -z "${VPC_ID}" ]; then
  VPC_ID=$(aws ec2 describe-vpcs \
    --region "${AWS_REGION}" \
    --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" \
    --output text)
  echo "→ Usando VPC default: ${VPC_ID}"
fi

echo "→ [1/5] Criando Security Group..."
SG_ID=$(aws ec2 create-security-group \
  --region "${AWS_REGION}" \
  --group-name "lia-agent-sg" \
  --description "LIA Agent System security group" \
  --vpc-id "${VPC_ID}" \
  --query "GroupId" \
  --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
    --region "${AWS_REGION}" \
    --filters "Name=group-name,Values=lia-agent-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text)
echo "  SG: ${SG_ID}"

# Regras de ingresso (idempotente)
for port in 22 8000 443; do
  aws ec2 authorize-security-group-ingress \
    --region "${AWS_REGION}" \
    --group-id "${SG_ID}" \
    --protocol tcp --port "${port}" \
    --cidr "0.0.0.0/0" 2>/dev/null || true
done

echo "→ [2/5] Criando repositório ECR..."
ECR_URI=$(aws ecr describe-repositories \
  --region "${AWS_REGION}" \
  --repository-names "${ECR_REPO_NAME}" \
  --query "repositories[0].repositoryUri" \
  --output text 2>/dev/null || \
  aws ecr create-repository \
    --region "${AWS_REGION}" \
    --repository-name "${ECR_REPO_NAME}" \
    --image-scanning-configuration scanOnPush=true \
    --query "repository.repositoryUri" \
    --output text)
echo "  ECR: ${ECR_URI}"

echo "→ [3/5] Criando instância EC2..."
INSTANCE_ID=$(aws ec2 run-instances \
  --region "${AWS_REGION}" \
  --image-id "${AMI_ID}" \
  --instance-type "${INSTANCE_TYPE}" \
  --key-name "${KEY_NAME}" \
  --security-group-ids "${SG_ID}" \
  --iam-instance-profile Name=lia-ec2-ssm-profile \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${INSTANCE_NAME}}]" \
  --user-data '#!/bin/bash
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user
    # docker-compose v2
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    mkdir -p /opt/lia
  ' \
  --query "Instances[0].InstanceId" \
  --output text)

echo "  Instance: ${INSTANCE_ID}"
echo "→ Aguardando instância iniciar (status check)..."
aws ec2 wait instance-status-ok \
  --region "${AWS_REGION}" \
  --instance-ids "${INSTANCE_ID}"

echo "→ [4/5] Copiando configurações via SSM..."
if [ -n "${S3_CONFIG_BUCKET}" ] && [ -f "${APP_DIR}/.env.prod" ]; then
  aws s3 cp "${APP_DIR}/.env.prod" "s3://${S3_CONFIG_BUCKET}/lia/.env.prod"
  aws ssm send-command \
    --region "${AWS_REGION}" \
    --instance-ids "${INSTANCE_ID}" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"aws s3 cp s3://${S3_CONFIG_BUCKET}/lia/.env.prod /opt/lia/.env.prod\"]" \
    --output text >/dev/null
else
  echo "  AVISO: configure /opt/lia/.env.prod manualmente na instância"
fi

# Copia docker-compose via SSM (inline)
DC_CONTENT=$(cat "${APP_DIR}/docker-compose.yml" | base64 -w0)
DC_PROD_CONTENT=$(cat "${APP_DIR}/docker-compose.prod.yml" | base64 -w0)
aws ssm send-command \
  --region "${AWS_REGION}" \
  --instance-ids "${INSTANCE_ID}" \
  --document-name "AWS-RunShellScript" \
  --parameters "commands=[
    \"echo '${DC_CONTENT}' | base64 -d > /opt/lia/docker-compose.yml\",
    \"echo '${DC_PROD_CONTENT}' | base64 -d > /opt/lia/docker-compose.prod.yml\"
  ]" \
  --output text >/dev/null

echo "→ [5/5] Primeiro deploy..."
IMAGE_TAG=$(git -C "${APP_DIR}" rev-parse --short HEAD 2>/dev/null || echo "latest")
REGISTRY="${ECR_URI}" IMAGE_TAG="${IMAGE_TAG}" \
  make -C "${APP_DIR}/deploy" build push

aws ssm send-command \
  --region "${AWS_REGION}" \
  --instance-ids "${INSTANCE_ID}" \
  --document-name "AWS-RunShellScript" \
  --parameters "commands=[
    \"aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}\",
    \"cd /opt/lia && IMAGE_TAG=${IMAGE_TAG} docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d\"
  ]" \
  --output text

INSTANCE_IP=$(aws ec2 describe-instances \
  --region "${AWS_REGION}" \
  --instance-ids "${INSTANCE_ID}" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

echo ""
echo "✓ Setup concluído!"
echo "  Instance: ${INSTANCE_ID} (${INSTANCE_IP})"
echo "  ECR:      ${ECR_URI}"
echo "  API:      http://${INSTANCE_IP}:8000/api/v1/health"
echo "  Docs:     http://${INSTANCE_IP}:8000/docs"
echo ""
echo "  Próximos passos:"
echo "  1. Configure um Load Balancer (ALB) na frente"
echo "  2. Habilite HTTPS via ACM + ALB"
echo "  3. Configure o .env.prod na instância"
