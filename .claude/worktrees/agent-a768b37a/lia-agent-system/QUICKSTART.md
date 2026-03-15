# 🚀 Quick Start Guide - LIA Agent System

## 📋 Pré-requisitos

Antes de começar, você precisa ter:

### 1. **Claude API Key** (Anthropic)
- Acesse: https://console.anthropic.com/
- Crie uma API key
- Copie e guarde (vamos usar no passo 3)

### 2. **Docker Desktop** (Opcional mas recomendado)
- Download: https://www.docker.com/products/docker-desktop
- Instale e inicie o Docker

### 3. **Python 3.11+**
```bash
python --version  # Deve ser 3.11 ou superior
```

---

## ⚡ Instalação Rápida (5 minutos)

### Passo 1: Configurar Variáveis de Ambiente

```bash
# 1. Copie o arquivo de exemplo
cp .env.example .env

# 2. Edite .env e adicione sua Claude API key
nano .env  # ou use seu editor preferido

# Mínimo necessário para começar:
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db
```

### Passo 2: Instalar Dependências

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Passo 3: Iniciar Banco de Dados

**Opção A: Com Docker (RECOMENDADO)**
```bash
# Iniciar PostgreSQL, Redis, RabbitMQ
docker-compose up -d postgres redis rabbitmq

# Verificar se está rodando
docker-compose ps
```

**Opção B: PostgreSQL Local**
```bash
# Se você já tem PostgreSQL instalado localmente:
createdb lia_db
createuser lia_user
psql -c "ALTER USER lia_user WITH PASSWORD 'lia_password';"
```

### Passo 4: Criar Tabelas do Banco

```bash
# Instalar Alembic (se não instalou via requirements.txt)
pip install alembic

# Criar migração inicial
alembic revision --autogenerate -m "Initial migration"

# Aplicar migração
alembic upgrade head
```

### Passo 5: Iniciar API

```bash
# Desenvolvimento (com reload automático)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# OU usando Python diretamente
python -m app.main
```

### Passo 6: Testar!

```bash
# Health check
curl http://localhost:8000/health

# Abrir documentação interativa
open http://localhost:8000/docs  # Mac
# OU
start http://localhost:8000/docs  # Windows
# OU simplesmente acesse no navegador: http://localhost:8000/docs
```

---

## 💬 Testar o Chat

### Método 1: Via Swagger UI (Mais Fácil)

1. Acesse: http://localhost:8000/docs
2. Clique em `POST /api/v1/chat`
3. Clique em "Try it out"
4. Cole este JSON:
```json
{
  "content": "Oi LIA, preciso criar uma vaga de desenvolvedor Python"
}
```
5. Clique em "Execute"
6. Veja a resposta da LIA! 🎉

### Método 2: Via curl

```bash
# Primeira mensagem (cria nova conversa)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Preciso contratar um desenvolvedor Python sênior"
  }'

# Copie o conversation_id da resposta e continue:
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Remoto, em São Paulo",
    "conversation_id": "COLE_O_UUID_AQUI"
  }'
```

### Método 3: Via WebSocket (JavaScript)

```javascript
// Conectar
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/demo-user');

// Enviar mensagem
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'message',
    content: 'Oi LIA, tudo bem?'
  }));
};

// Receber resposta
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('LIA disse:', data.content);
};
```

---

## 🔧 Troubleshooting

### Erro: "ANTHROPIC_API_KEY not configured"
- ✅ Verifique se você editou o arquivo `.env`
- ✅ Certifique-se de que a chave começa com `sk-ant-`
- ✅ Reinicie a API após editar `.env`

### Erro: "Database connection failed"
- ✅ Verifique se o Docker está rodando: `docker ps`
- ✅ Verifique se o PostgreSQL está rodando: `docker-compose ps`
- ✅ Teste a conexão: `psql postgresql://lia_user:lia_password@localhost:5432/lia_db`

### Erro: "Port 8000 already in use"
- ✅ Mude a porta no comando: `uvicorn app.main:app --port 8001`
- ✅ Ou mate o processo: `lsof -ti:8000 | xargs kill -9` (Mac/Linux)

### API muito lenta
- ✅ Claude pode demorar 2-5 segundos para responder (é normal)
- ✅ Verifique sua internet
- ✅ Verifique os logs: `docker-compose logs -f api`

---

## 📊 Próximos Passos

### 1. Explorar a Documentação
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. Ver os Logs
```bash
# Logs da API
docker-compose logs -f api

# Logs do PostgreSQL
docker-compose logs -f postgres
```

### 3. Conectar Frontend Next.js
Veja: `FRONTEND_INTEGRATION.md`

### 4. Configurar LangSmith (Observability)
```bash
# No .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=sua_chave_aqui
LANGCHAIN_PROJECT=lia-agent-system
```

Acesse: https://smith.langchain.com/

---

## 🎯 Exemplos de Conversação

Experimente perguntar para a LIA:

- ✅ "Preciso contratar um desenvolvedor Python sênior"
- ✅ "Crie uma vaga de Product Manager remoto"
- ✅ "Me ajude a encontrar candidatos para uma vaga de designer"
- ✅ "Como está o processo de recrutamento da vaga X?"
- ✅ "Oi, tudo bem?" (chitchat)

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Leia o README.md completo
2. Verifique os logs: `docker-compose logs -f`
3. Contate o time de desenvolvimento

---

**Pronto! Você tem a LIA rodando localmente! 🚀**
