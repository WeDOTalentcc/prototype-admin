# Terraform — LIA Agent System

Configuração IaC que substitui os scripts imperativos `deploy/gcp_setup.sh` e `deploy/aws_setup.sh` por infraestrutura declarativa e idempotente.

---

## Estrutura

```
terraform/
├── gcp/
│   ├── main.tf        # VM e2-standard-4, firewall lia-api, GCR
│   ├── variables.tf   # project_id (obrigatório), region, zone, vm_name, image_tag
│   ├── outputs.tf     # vm_ip, vm_name, registry_url
│   └── startup.sh     # Script de inicialização da VM (Docker + /opt/lia)
└── aws/
    ├── main.tf        # Security Group, ECR, EC2 t3.xlarge (AL2023)
    ├── variables.tf   # region, instance_type, image_tag
    ├── outputs.tf     # instance_ip, instance_id, ecr_url, security_group_id
    └── userdata.sh    # Script user-data EC2 (Docker + docker-compose v2 + /opt/lia)
```

---

## Pre-requisitos

| Ferramenta | Versão mínima |
|------------|--------------|
| Terraform  | >= 1.6       |
| gcloud CLI | qualquer (GCP) |
| AWS CLI    | >= 2.x (AWS)  |

**GCP:** autentique com `gcloud auth application-default login` antes de rodar.

**AWS:** configure credenciais com `aws configure` ou via variáveis de ambiente (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

---

## GCP

### Variáveis

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `project_id` | Sim | — | ID do projeto GCP |
| `region` | Não | `us-central1` | Região dos recursos |
| `zone` | Não | `us-central1-a` | Zona da VM |
| `vm_name` | Não | `lia-agent-vm` | Nome da instância |
| `image_tag` | Não | `latest` | Tag da imagem Docker |

### Comandos

```bash
cd terraform/gcp

terraform init

terraform plan \
  -var="project_id=meu-projeto-gcp"

terraform apply \
  -var="project_id=meu-projeto-gcp"
```

### Exemplo com arquivo de variáveis

```hcl
# terraform/gcp/terraform.tfvars
project_id = "wedotalent-prod"
region     = "southamerica-east1"
zone       = "southamerica-east1-a"
vm_name    = "lia-agent-vm-prod"
image_tag  = "v1.2.3"
```

```bash
terraform apply -var-file="terraform.tfvars"
```

### Outputs após apply

```
vm_ip        = "34.x.x.x"
vm_name      = "lia-agent-vm"
registry_url = "gcr.io/meu-projeto-gcp/lia-agent-system"
```

---

## AWS

### Variáveis

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `region` | Não | `us-east-1` | Região AWS |
| `instance_type` | Não | `t3.xlarge` | Tipo de instância EC2 |
| `image_tag` | Não | `latest` | Tag da imagem Docker |

### Comandos

```bash
cd terraform/aws

terraform init

terraform plan

terraform apply
```

### Exemplo com região diferente

```bash
terraform apply -var="region=sa-east-1"
```

### Outputs após apply

```
instance_ip       = "54.x.x.x"
instance_id       = "i-0abc123def456"
ecr_url           = "123456789.dkr.ecr.us-east-1.amazonaws.com/lia-agent-system"
security_group_id = "sg-0abc123def456"
```

---

## Destruir recursos

```bash
# GCP
cd terraform/gcp && terraform destroy -var="project_id=meu-projeto-gcp"

# AWS
cd terraform/aws && terraform destroy
```

---

## Notas

- Os scripts `deploy/gcp_setup.sh` e `deploy/aws_setup.sh` permanecem disponíveis para uso imperativo pontual.
- O `.env.prod` deve ser configurado manualmente em `/opt/lia/.env.prod` na instância após o primeiro `apply`.
- Para produção, recomenda-se armazenar o state em backend remoto (GCS bucket ou S3) em vez do state local padrão.
