# LIA Agent System - API Examples

## 🚀 Quick Start

### Base URL
```
http://localhost:8000
```

---

## 📍 Endpoints

### 1. Health Check
Verifica se o serviço está operacional.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "app": "lia-agent-system",
  "environment": "development",
  "version": "0.1.0"
}
```

---

### 2. Root Endpoint
Informações gerais da API.

**Request:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "LIA Agent System API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### 3. Send Message (Chat)
Enviar mensagem para LIA e receber resposta inteligente.

**Endpoint:** `POST /api/v1/chat`

#### Exemplo 1: Criar Vaga

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Olá LIA! Preciso criar uma vaga de Desenvolvedor Python Sênior."
  }'
```

**Response:**
```json
{
  "message": {
    "id": "a3ea6489-85ef-49a7-9982-f5160e9b7b5d",
    "conversation_id": "2a81e738-dee8-47a1-9760-3a42b034a69c",
    "role": "ai",
    "content": "Olá! 👋 Perfeito, vou te ajudar a criar essa vaga de Desenvolvedor Python Sênior.\n\nVou precisar de algumas informações...",
    "message_metadata": {
      "intent": "create_job",
      "confidence": 0.98,
      "entities": {
        "job_title": "Desenvolvedor Python",
        "department": null,
        "location": null,
        "seniority": "senior",
        "job_type": null,
        "salary_range": null,
        "required_skills": ["Python"],
        "years_experience": null
      }
    },
    "created_at": "2025-11-23T22:31:43.823423"
  },
  "conversation": {
    "id": "2a81e738-dee8-47a1-9760-3a42b034a69c",
    "user_id": "demo-user",
    "user_role": "recruiter",
    "title": "Olá LIA! Preciso criar uma vaga de Desenvolvedor Python Sênior.",
    "intent": "create_job",
    "workflow_type": null,
    "workflow_step": 0,
    "status": "active",
    "created_at": "2025-11-23T22:31:29.865453",
    "updated_at": "2025-11-23T22:31:43.751593"
  }
}
```

#### Exemplo 2: Continuar Conversa

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "É uma vaga remota, para o time de Produto, faixa de R$ 12-15k.",
    "conversation_id": "2a81e738-dee8-47a1-9760-3a42b034a69c"
  }'
```

**Response:**
```json
{
  "message": {
    "id": "b4fb7599-96fg-50b8-a093-g6271f0c8c6e",
    "conversation_id": "2a81e738-dee8-47a1-9760-3a42b034a69c",
    "role": "ai",
    "content": "Ótimo! Anotei:\n✅ Remoto\n✅ Departamento: Produto\n✅ Salário: R$ 12-15k\n\nAgora me conta sobre as tecnologias...",
    "message_metadata": {
      "intent": "create_job",
      "confidence": 0.99,
      "entities": {
        "location": "remote",
        "department": "Produto",
        "salary_range": "R$ 12-15k",
        "job_type": "CLT"
      }
    },
    "created_at": "2025-11-23T22:35:12.456789"
  },
  "conversation": {
    "id": "2a81e738-dee8-47a1-9760-3a42b034a69c",
    "workflow_step": 1,
    "status": "active"
  }
}
```

#### Exemplo 3: Buscar Candidatos

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Preciso buscar candidatos para desenvolvedor backend Node.js com experiência em AWS."
  }'
```

**Response (expected):**
```json
{
  "message": {
    "content": "Vou buscar candidatos para você! Encontrei alguns perfis relevantes...",
    "message_metadata": {
      "intent": "search_candidates",
      "confidence": 0.96,
      "entities": {
        "job_title": "desenvolvedor backend",
        "required_skills": ["Node.js", "AWS"],
        "seniority": null
      }
    }
  }
}
```

---

### 4. List Conversations
Listar conversas do usuário.

**Endpoint:** `GET /api/v1/chat/conversations`

**Request:**
```bash
curl "http://localhost:8000/api/v1/chat/conversations?user_id=demo-user&page=1&page_size=20"
```

**Response:**
```json
{
  "conversations": [
    {
      "id": "2a81e738-dee8-47a1-9760-3a42b034a69c",
      "user_id": "demo-user",
      "user_role": "recruiter",
      "title": "Olá LIA! Preciso criar uma vaga de...",
      "intent": "create_job",
      "workflow_type": null,
      "workflow_step": 1,
      "status": "active",
      "created_at": "2025-11-23T22:31:29.865453",
      "updated_at": "2025-11-23T22:35:12.456789"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## 🧪 Testing with Python

### Install requests
```bash
pip install requests
```

### Example Script
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def chat_with_lia(message, conversation_id=None):
    """Send message to LIA and get response."""
    payload = {"content": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json=payload
    )
    return response.json()

# Example usage
response = chat_with_lia("Olá LIA! Preciso criar uma vaga de Data Engineer.")
print(json.dumps(response, indent=2, ensure_ascii=False))

# Get conversation ID
conv_id = response["conversation"]["id"]

# Continue conversation
response2 = chat_with_lia(
    "É uma vaga presencial em São Paulo, faixa de R$ 10-13k.",
    conversation_id=conv_id
)
print(json.dumps(response2, indent=2, ensure_ascii=False))
```

---

## 🔍 Intent Types (Implemented)

LIA atualmente classifica os seguintes intents:

1. **create_job** - Criar nova vaga
2. **search_candidates** - Buscar candidatos
3. **schedule_interview** - Agendar entrevista
4. **general_inquiry** - Pergunta geral
5. **status_check** - Verificar status de processo

**Confiança mínima**: 0.7 (70%)

---

## 📊 Entity Extraction Fields

Campos extraídos automaticamente:

- `job_title`: Título da vaga
- `department`: Departamento
- `location`: Localização (remote, hybrid, city name)
- `seniority`: Senioridade (junior, pleno, senior, staff, etc.)
- `job_type`: Tipo (CLT, PJ, Freelancer, Estágio)
- `salary_range`: Faixa salarial
- `required_skills`: Lista de tecnologias/skills
- `years_experience`: Anos de experiência

---

## 🐛 Error Responses

### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "content"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to generate response"
}
```

---

## 📚 API Documentation

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

---

**Última atualização**: 23/11/2025
