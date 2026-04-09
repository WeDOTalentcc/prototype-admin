# Terraform — LIA Agent System

Configuração IaC que substitui os scripts imperativos `deploy/gcp_setup.sh` por infraestrutura declarativa e idempotente.

> **Nota:** O projeto usa exclusivamente **GCP (Google Cloud Platform)** como plataforma de deploy. O diretório `terraform/aws/` foi removido.

---

## Estrutura

```
terraform/
└── gcp/
    ├── main.tf        # VM e2-standard-4, firewall lia-api, GCR
    ├── variables.tf   # project_id (obrigatório), region, zone, vm_name, image_tag
    ├── outputs.tf     # vm_ip, vm_name, registry_url
    └── startup.sh     # Script de inicialização da VM (Docker + /opt/lia)
```

---

## Pre-requisitos

| Ferramenta | Versão mínima |
|------------|--------------|
| Terraform  | >= 1.6       |
| gcloud CLI | qualquer     |

**GCP:** autentique com `gcloud auth application-default login` antes de rodar.

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

## Destruir recursos

```bash
cd terraform/gcp && terraform destroy -var="project_id=meu-projeto-gcp"
```

---

## Notas

- O script `deploy/gcp_setup.sh` permanece disponível para uso imperativo pontual.
- O `.env.prod` deve ser configurado manualmente em `/opt/lia/.env.prod` na instância após o primeiro `apply`.
- Para produção, recomenda-se armazenar o state em backend remoto (GCS bucket) em vez do state local padrão.
