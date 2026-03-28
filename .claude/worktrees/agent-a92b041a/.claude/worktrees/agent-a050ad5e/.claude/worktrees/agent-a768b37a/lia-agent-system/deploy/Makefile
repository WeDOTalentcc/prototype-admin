# ==============================================================================
# deploy/Makefile — LIA Agent System deployment commands
#
# Uso: make <target>
# Variáveis: IMAGE_TAG, PROJECT_ID (GCP), AWS_REGION, ECR_REPO
# ==============================================================================

IMAGE_TAG  ?= $(shell git rev-parse --short HEAD)
REGISTRY   ?= gcr.io/$(PROJECT_ID)/lia-agent-system
APP_DIR    := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))..

.PHONY: help build push deploy-gcp deploy-aws health-check rollback

help:
	@echo "LIA Agent System — Deploy Commands"
	@echo ""
	@echo "  make build           Build production Docker image"
	@echo "  make push            Push image to registry (set REGISTRY)"
	@echo "  make deploy-gcp      Full deploy to GCP VM (set PROJECT_ID, GCP_VM_NAME, GCP_ZONE)"
	@echo "  make deploy-aws      Full deploy to AWS EC2 (set AWS_INSTANCE_ID, AWS_REGION)"
	@echo "  make health-check    Check API health endpoint"
	@echo "  make rollback        Roll back to previous image (set PREV_TAG)"

build:
	@echo "→ Building $(REGISTRY):$(IMAGE_TAG)"
	cd $(APP_DIR) && docker build \
		-f Dockerfile.prod \
		-t $(REGISTRY):$(IMAGE_TAG) \
		-t $(REGISTRY):latest \
		.

push: build
	@echo "→ Pushing $(REGISTRY):$(IMAGE_TAG)"
	docker push $(REGISTRY):$(IMAGE_TAG)
	docker push $(REGISTRY):latest

deploy-gcp: push
	@echo "→ Deploying to GCP VM $(GCP_VM_NAME) in $(GCP_ZONE)"
	gcloud compute ssh $(GCP_VM_NAME) \
		--zone=$(GCP_ZONE) \
		--project=$(PROJECT_ID) \
		--command="\
			cd /opt/lia && \
			IMAGE_TAG=$(IMAGE_TAG) \
			docker compose -f docker-compose.yml -f docker-compose.prod.yml pull api celery_worker celery_beat && \
			IMAGE_TAG=$(IMAGE_TAG) \
			docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps api celery_worker celery_beat"

deploy-aws: push
	@echo "→ Deploying to AWS EC2 $(AWS_INSTANCE_ID)"
	aws ssm send-command \
		--region $(AWS_REGION) \
		--instance-ids $(AWS_INSTANCE_ID) \
		--document-name "AWS-RunShellScript" \
		--parameters 'commands=["cd /opt/lia && IMAGE_TAG=$(IMAGE_TAG) docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps api celery_worker celery_beat"]' \
		--output text

health-check:
	@echo "→ Checking health at $(API_URL)/api/v1/health"
	curl -sf $(API_URL)/api/v1/health | python3 -m json.tool

rollback:
	@echo "→ Rolling back to $(PREV_TAG)"
	IMAGE_TAG=$(PREV_TAG) docker compose \
		-f docker-compose.yml \
		-f docker-compose.prod.yml \
		up -d --no-deps api celery_worker celery_beat
