# Guia de Deployment - Plataforma LIA

## 📋 Visão Geral

Este guia explica como fazer deploy (publicar) da Plataforma LIA no Replit, incluindo o frontend Next.js e o backend FastAPI.

---

## 🏗️ Arquitetura do Projeto

O projeto é composto por dois sistemas separados:

```
workspace/
├── plataforma-lia/          # Frontend Next.js (porta 5000)
│   ├── package.json
│   ├── next.config.ts
│   └── app/
└── lia-agent-system/        # Backend FastAPI (porta 8000)
    ├── app/
    ├── main.py
    └── requirements.txt
```

---

## ✅ Configuração de Deployment Atual

O deployment está configurado para:

**Deployment Target**: `vm` (Virtual Machine - sempre rodando)
- Necessário para o backend FastAPI permanecer ativo 24/7
- Permite receber webhooks do Microsoft Teams e Graph API

**Build Command**:
```bash
cd plataforma-lia && npm install && npm run build
```

**Run Command**:
```bash
cd lia-agent-system && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 & 
cd plataforma-lia && npm run start -- -H 0.0.0.0 -p 5000
```

Isso roda:
1. **Backend FastAPI** na porta 8000 (em background com `&`)
2. **Frontend Next.js** na porta 5000 (porta principal para usuários)

---

## 🚀 Como Fazer Deploy

### 1. Verificar Secrets Configuradas

Antes de fazer deploy, certifique-se que todas as secrets estão configuradas:

✅ **Azure Credentials** (Microsoft Graph API):
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`

✅ **Teams Bot Credentials** (quando configurar):
- `MICROSOFT_APP_ID`
- `MICROSOFT_APP_PASSWORD`

✅ **AI/LLM Keys**:
- `ANTHROPIC_API_KEY` (Claude Sonnet)

✅ **Database** (automático):
- `DATABASE_URL` (PostgreSQL - configurado automaticamente pelo Replit)

### 2. Fazer Deploy

1. Clique no botão **"Deploy"** (ou "Publicar") no Replit
2. O sistema vai:
   - Executar `npm install` em `plataforma-lia/`
   - Executar `npm run build` para criar build de produção do Next.js
   - Iniciar o backend FastAPI na porta 8000
   - Iniciar o frontend Next.js na porta 5000
3. Aguarde o deployment completar (~2-5 minutos)
4. Copie a **URL pública** do deployment

### 3. Configurar Messaging Endpoint no Azure

Após o deploy, você terá uma URL pública tipo:
```
https://seu-projeto.repl.co
```

Use essa URL para configurar o **Messaging Endpoint** no Azure Bot:
```
https://seu-projeto.repl.co/api/v1/teams/messages
```

Veja o guia completo em: `lia-agent-system/AZURE_BOT_SETUP_GUIDE.md`

---

## 🧪 Testar Deployment

### 1. Verificar Backend (API)

```bash
curl https://seu-projeto.repl.co/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "..."
}
```

### 2. Verificar Calendar API

```bash
curl https://seu-projeto.repl.co/api/v1/calendar/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "service": "calendar-api",
  "graph_configured": true
}
```

### 3. Verificar Frontend

Acesse no navegador:
```
https://seu-projeto.repl.co
```

Você deve ver a Plataforma LIA carregando.

---

## 📊 Portas e URLs

| Serviço | Porta Local | Porta Pública | URL |
|---------|-------------|---------------|-----|
| **Frontend Next.js** | 5000 | 5000 | `https://seu-projeto.repl.co` |
| **Backend FastAPI** | 8000 | 8000 | `https://seu-projeto.repl.co:8000` (ou proxy reverso) |
| **Teams Webhook** | 8000 | 8000 | `https://seu-projeto.repl.co/api/v1/teams/messages` |

**IMPORTANTE**: Apenas a porta **5000** é exposta publicamente por padrão no Replit. O backend roda internamente na 8000.

---

## 🔧 Scripts NPM Disponíveis

No diretório raiz (`workspace/`):

```bash
# Build de produção do frontend
npm run build

# Start do frontend (produção)
npm run start

# Desenvolvimento - Frontend
npm run dev:frontend

# Desenvolvimento - Backend
npm run dev:backend
```

---

## 🐛 Troubleshooting

### Erro: "Build command failed"
- **Causa**: npm install ou build falhou
- **Solução**: Verifique se `plataforma-lia/package.json` está correto

### Erro: "Port 5000 already in use"
- **Causa**: Workflow `dev-server` ainda rodando
- **Solução**: Pare o workflow antes de fazer deploy

### Backend não responde
- **Causa**: Secrets não configuradas ou erro no startup
- **Solução**: Verifique logs do deployment e confirme secrets

### Frontend mostra página em branco
- **Causa**: Build de produção pode ter falhado ou Next.js export incorreto
- **Solução**: Verifique `next.config.ts` e remova `output: 'export'` se presente

---

## 🔄 Atualizar Deployment

Para atualizar o deployment após mudanças no código:

1. Faça commit das mudanças no Git (automático no Replit)
2. Clique em **"Re-deploy"** ou **"Update deployment"**
3. O sistema vai fazer novo build e restart automático

---

## 💡 Dicas de Produção

### Performance
- ✅ Next.js build otimizado automaticamente
- ✅ API FastAPI async/await para alta concorrência
- ✅ Database connection pooling configurado

### Monitoramento
- Verifique logs do deployment regularmente
- Configure alertas para erros 500
- Monitore uso de memória e CPU no Replit

### Segurança
- ✅ Secrets gerenciadas via Replit Secrets
- ✅ JWT validation no Teams webhook
- ✅ HTTPS automático
- ⚠️ Não exponha endpoints sensíveis sem autenticação

---

## 📚 Próximos Passos Após Deploy

1. **Configurar Azure Bot** - Siga `lia-agent-system/AZURE_BOT_SETUP_GUIDE.md`
2. **Testar integração Teams** - Envie mensagens de teste para LIA
3. **Configurar domínio custom** (opcional) - Via settings do Replit
4. **Adicionar monitoramento** - Configure logs e alertas

---

## 🆘 Suporte

Para problemas com deployment:
- Verifique logs do deployment no Replit
- Consulte documentação técnica em `plataforma-lia/docs/`
- Teste endpoints individualmente (health checks)

Para problemas com Azure:
- Consulte `lia-agent-system/AZURE_BOT_SETUP_GUIDE.md`
- Verifique Azure Portal > Bot Services > Configuration
