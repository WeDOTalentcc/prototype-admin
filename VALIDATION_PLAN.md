# Plano de Validação e Smoke Tests — Pré Go-Live

> **Plataforma LIA** — Checklist de validação funcional para staging e produção.
> Última atualização: Abril 2026
>
> **Staging:** `staging.wedotalent.cc`
> **Produção:** `wedotalent.cc`
> **API Staging:** `api-staging.wedotalent.cc`
> **API Produção:** `api.wedotalent.cc`

---

## 1. Smoke Tests — Checklist por Funcionalidade

### 1.1 Autenticação e Autorização

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| A1 | Login SSO Google | Clicar "Entrar com Google" → selecionar conta → redirect | Dashboard carrega com nome do usuário | Sim |
| A2 | Login SSO Microsoft | Clicar "Entrar com Microsoft" → autenticar → redirect | Dashboard carrega com nome do usuário | Sim |
| A3 | Sessão persiste após refresh | Fazer login → F5 na página | Permanece logado, sem redirect para /login | Sim |
| A4 | Logout | Clicar menu usuário → Sair | Redirect para /login, cookies limpos | Sim |
| A5 | Acesso não-autenticado bloqueado | Acessar /dashboard sem login | Redirect automático para /login | Sim |
| A6 | Permissões por role | Logar como viewer → tentar criar vaga | Botão "Criar Vaga" não aparece ou retorna 403 | Sim |

### 1.2 Vagas (Jobs)

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| V1 | Criar vaga via wizard (7 steps) | Preencher steps 1-7 → publicar | Vaga aparece na listagem com status "Aberta" | Sim |
| V2 | Criar vaga via chat LIA | No chat, dizer "Criar vaga de Dev Pleno React" | LIA faz perguntas e cria vaga pelo wizard | Sim |
| V3 | Editar vaga existente | Abrir vaga → editar título → salvar | Título atualizado na listagem | Sim |
| V4 | Fechar vaga | Abrir vaga → mudar status para "Fechada" | Vaga não aparece mais para candidatos | Não |
| V5 | Filtrar vagas por status | Usar filtro "Abertas" / "Fechadas" | Lista filtra corretamente | Não |
| V6 | WSI (Work Style Indicator) | No step 5, configurar WSI → avançar | Competências salvas sem erro | Sim |

### 1.3 Candidatos

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| C1 | Upload de CV (PDF) | Upload de arquivo PDF na vaga | CV processado, dados extraídos e exibidos | Sim |
| C2 | Triagem automática Claude | Após upload, aguardar triagem | Score e recomendação aparecem no perfil | Sim |
| C3 | Busca de candidatos | Buscar por nome/skill na listagem | Resultados relevantes retornados | Sim |
| C4 | Perfil do candidato | Clicar em candidato → ver perfil completo | Dados pessoais, CV, histórico, scores visíveis | Sim |
| C5 | Adicionar candidato a vaga | No perfil, clicar "Adicionar a Vaga" → selecionar vaga | Candidato aparece no kanban da vaga | Sim |
| C6 | Detecção de duplicatas | Adicionar mesmo candidato novamente | Aviso de duplicata exibido | Não |

### 1.4 Kanban (Pipeline)

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| K1 | Visualizar kanban da vaga | Abrir vaga → aba Pipeline | Colunas do kanban visíveis com candidatos | Sim |
| K2 | Mover candidato entre etapas | Drag-and-drop candidato para próxima coluna | Candidato move, status atualiza no backend | Sim |
| K3 | Ações rápidas no card | Clicar menu do card → "Agendar entrevista" | Modal de agendamento abre | Não |
| K4 | Filtros no kanban | Filtrar por score/etapa | Cards filtram corretamente | Não |

### 1.5 Chat LIA (Assistente IA)

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| L1 | Chat principal responde | Abrir chat → enviar "Olá" | LIA responde em < 10s com saudação contextual | Sim |
| L2 | Chat no wizard | No wizard de vaga, interagir com LIA | LIA ajuda a preencher campos do wizard | Sim |
| L3 | Chat flutuante | Clicar ícone de chat flutuante em qualquer página | Chat abre e responde | Sim |
| L4 | Tool calling | No chat, pedir "Listar vagas abertas" | LIA chama ferramenta e retorna dados reais | Sim |
| L5 | Memória conversacional | Perguntar algo → perguntar "o que eu disse?" | LIA lembra do contexto anterior | Não |
| L6 | Formatação de resposta | Pedir lista ou tabela | LIA retorna markdown formatado corretamente | Não |

### 1.6 Comunicação (Twilio / Email / Teams)

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| T1 | Triagem por voz | Iniciar triagem por voz para candidato | Ligação realizada via Twilio, áudio transcrito | Não* |
| T2 | VoIP no browser | Ligar para candidato pelo browser | Conexão WebRTC estabelecida, áudio funciona | Não* |
| T3 | Envio de email | Disparar email de convite | Email recebido pelo destinatário | Sim |
| T4 | Template de email | Visualizar preview do email | Template renderiza corretamente | Não |
| T5 | Bot Teams | Enviar comando ao bot no Teams | Bot responde com informação da plataforma | Não* |
| T6 | WhatsApp | Enviar mensagem WhatsApp via plataforma | Mensagem entregue (depende aprovação Meta) | Não** |

\* Funcionalidade pode ser adiada se infraestrutura não estiver pronta.
\** WhatsApp depende de aprovação Meta Business — não bloqueia go-live.

### 1.7 LGPD e Compliance

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| G1 | Portal LGPD acessível | Acessar /lgpd ou link no footer | Página LGPD carrega com opções | Sim |
| G2 | Consentimento obrigatório | Candidato sem consentimento → tentar processar | Sistema bloqueia processamento | Sim |
| G3 | Exportar dados pessoais (DSR) | Solicitar exportação → gerar relatório | JSON/PDF com todos os dados do candidato | Não |
| G4 | Excluir dados pessoais | Solicitar exclusão → confirmar | Dados anonimizados/removidos | Não |
| G5 | FairnessGuard ativo | Processar candidato → verificar logs | Sem viés detectado (3 camadas ativas) | Sim |

### 1.8 Multi-Tenant

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| M1 | Isolamento de dados | Criar vaga na Empresa A → logar na Empresa B | Vaga da Empresa A não aparece na B | Sim |
| M2 | Isolamento de candidatos | Upload CV na Empresa A → buscar na Empresa B | Candidato não encontrado na Empresa B | Sim |
| M3 | Admin multi-empresa | Admin vê painel de gestão de empresas | Lista de empresas carrega com dados corretos | Não |

### 1.9 Infraestrutura e Performance

| # | Teste | Passos | Resultado Esperado | Bloqueante? |
|---|---|---|---|---|
| I1 | Health endpoint API | `curl api.wedotalent.cc/api/v1/health` | JSON com status: ok | Sim |
| I2 | Readiness check | `curl api.wedotalent.cc/api/v1/health/ready` | database: ok, redis: ok | Sim |
| I3 | Frontend carrega | Acessar `wedotalent.cc` | Página carrega em < 5s | Sim |
| I4 | SSL válido | Verificar cadeado no browser | Certificado válido para wedotalent.cc | Sim |
| I5 | Sentry recebe erros | Forçar erro → verificar Sentry | Evento registrado com stack trace | Não |
| I6 | CSP headers presentes | Inspecionar response headers | Content-Security-Policy presente | Não |

---

## 2. Critérios Go / No-Go

### GO — Todos devem passar

| Categoria | Critérios obrigatórios |
|---|---|
| **Auth** | Login SSO (Google ou Microsoft) funciona, sessão persiste, logout funciona |
| **Core CRUD** | Criar vaga (wizard), upload CV, triagem automática funciona |
| **Kanban** | Pipeline carrega, mover candidato funciona |
| **Chat** | LIA responde no chat principal e no wizard |
| **Multi-Tenant** | Dados isolados entre empresas (testes M1 e M2 passam) |
| **LGPD** | Portal acessível, consentimento obrigatório funciona |
| **Infra** | Health checks retornam 200, SSL válido, frontend carrega |

### NO-GO — Qualquer um destes bloqueia

| Condição | Ação |
|---|---|
| Login SSO falha em ambos os providers | Investigar WorkOS config, não lançar |
| API health retorna erro | Verificar Cloud SQL/Redis connectivity |
| Dados vazam entre empresas | Bug crítico de isolamento, não lançar |
| Triagem automática não processa | Verificar ANTHROPIC_API_KEY no Secret Manager |
| Frontend não carrega (500/502/503) | Verificar Cloud Run logs e deployment |

### Aceitável com workaround (não bloqueia go-live)

| Funcionalidade | Workaround | Prazo para corrigir |
|---|---|---|
| WhatsApp não funciona | Usar email/telefone | Quando Meta aprovar |
| Teams bot offline | Notificar via email | Sprint seguinte |
| Triagem por voz indisponível | Triagem por texto/CV | Sprint seguinte |
| VoIP no browser não conecta | Usar telefone convencional | Sprint seguinte |
| Exportação LGPD manual | Time suporte exporta manualmente | 2 semanas |
| Busca semântica lenta (>5s) | Busca keyword funciona como fallback | Sprint seguinte |

---

## 3. Testes E2E Automatizados (Playwright)

### 3.1 Configuração para staging

Os testes E2E existentes usam URLs relativas (`/dashboard`, `/vagas/nova`, etc.).
Para rodar contra staging, basta configurar a variável `PLAYWRIGHT_BASE_URL`:

```bash
# Rodar contra staging
PLAYWRIGHT_BASE_URL=https://staging.wedotalent.cc npx playwright test

# Rodar contra produção (smoke tests apenas)
PLAYWRIGHT_BASE_URL=https://wedotalent.cc npx playwright test --grep @smoke

# Rodar localmente (padrão)
npx playwright test
```

### 3.2 Playwright config

O arquivo `plataforma-lia/playwright.config.ts` já existe e usa `PLAYWRIGHT_BASE_URL`
para parametrizar a URL base. Inclui projetos desktop-chrome e mobile-chrome.

### 3.3 Auth fixture para staging

O auth fixture (`e2e/fixtures/auth.fixture.ts`) foi atualizado para extrair o domínio
automaticamente da variável `PLAYWRIGHT_BASE_URL`:

```typescript
const AUTH_DOMAIN = process.env.PLAYWRIGHT_BASE_URL
  ? new URL(process.env.PLAYWRIGHT_BASE_URL).hostname
  : 'localhost';
```

Isso permite que os cookies de autenticação funcionem tanto localmente (`localhost`)
quanto em staging (`staging.wedotalent.cc`) sem alteração manual.

### 3.4 Suítes de teste existentes

| Suíte | Arquivos | Cobre |
|---|---|---|
| Auth | `auth/login.spec.ts` | Login, validação, sessão |
| Wizard | `wizard/step1-7.spec.ts`, `complete-flow.spec.ts` | Criação de vaga 7 steps |
| Chat | `chat/*.spec.ts` (7 arquivos) | Chat principal, flutuante, wizard, tool calling, memória |
| Kanban | `kanban/move-candidate.spec.ts` | Mover candidato no pipeline |
| Quality | `quality-suite/*.spec.ts` | Qualidade de respostas e roteamento |
| Search | `search-*.spec.ts` | Busca e prompt UX |

### 3.5 Testes de smoke tag @smoke

Para go-live, rodar apenas os testes marcados `@smoke` — os mais críticos:

```bash
PLAYWRIGHT_BASE_URL=https://staging.wedotalent.cc npx playwright test --grep @smoke
```

Testes que devem ter tag `@smoke`: login, criar vaga (complete flow), mover candidato,
chat principal responde.

---

## 4. Validação Multi-Tenant (Detalhado)

### 4.1 Setup do teste

```
1. Criar Empresa A ("TechCorp") com admin userA@techcorp.com
2. Criar Empresa B ("FinBank") com admin userB@finbank.com
3. Ambas no mesmo staging environment
```

### 4.2 Testes de isolamento

| Step | Ação (como userA) | Verificação (como userB) | Resultado |
|---|---|---|---|
| 1 | Criar vaga "Dev Pleno" | GET /api/v1/vacancies → listar vagas | Vaga "Dev Pleno" NÃO aparece |
| 2 | Upload CV "João Silva" | GET /api/v1/candidates → buscar "João" | Candidato NÃO encontrado |
| 3 | Criar template email "Convite" | GET /api/v1/email-templates → listar | Template NÃO aparece |
| 4 | Chat LIA "Listar vagas" | Chat LIA "Listar vagas" | Cada um vê só suas vagas |
| 5 | Acessar /api/v1/vacancies/{id_da_empresa_A} direto | — | Retorna 403 ou 404 |

### 4.3 Teste de API direta (curl)

```bash
# Como userA — criar vaga
TOKEN_A=$(curl -s -X POST https://staging.wedotalent.cc/api/backend-proxy/auth/login \
  -d '{"email":"userA@techcorp.com","password":"..."}' | jq -r '.token')

VAGA_ID=$(curl -s -X POST https://staging.wedotalent.cc/api/backend-proxy/vacancies \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{"title":"Dev Pleno","department":"Tech"}' | jq -r '.id')

# Como userB — tentar acessar vaga de A
TOKEN_B=$(curl -s -X POST https://staging.wedotalent.cc/api/backend-proxy/auth/login \
  -d '{"email":"userB@finbank.com","password":"..."}' | jq -r '.token')

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  https://staging.wedotalent.cc/api/backend-proxy/vacancies/$VAGA_ID \
  -H "Authorization: Bearer $TOKEN_B")

if [ "$HTTP_STATUS" = "403" ] || [ "$HTTP_STATUS" = "404" ]; then
  echo "✅ Isolamento OK — Empresa B não acessa vaga da Empresa A"
else
  echo "❌ FALHA DE ISOLAMENTO — HTTP $HTTP_STATUS (esperado 403 ou 404)"
fi
```

---

## 5. Runbook de Rollback

### 5.1 Rollback rápido — Cloud Run Revision

O Cloud Run mantém revisões anteriores. Reverter é instantâneo:

```bash
# Listar revisões disponíveis
gcloud run revisions list --service=lia-api --region=$REGION \
  --format="table(REVISION,ACTIVE,CREATED)"

gcloud run revisions list --service=lia-frontend --region=$REGION \
  --format="table(REVISION,ACTIVE,CREATED)"

# Reverter API para revisão anterior
gcloud run services update-traffic lia-api \
  --region=$REGION \
  --to-revisions=lia-api-REVISION_NAME=100

# Reverter Frontend para revisão anterior
gcloud run services update-traffic lia-frontend \
  --region=$REGION \
  --to-revisions=lia-frontend-REVISION_NAME=100

# Reverter Worker para revisão anterior
gcloud run services update-traffic lia-worker \
  --region=$REGION \
  --to-revisions=lia-worker-REVISION_NAME=100
```

**Tempo estimado:** ~15-30 segundos por serviço.

### 5.2 Rollback via Feature Flags

Para reverter funcionalidades sem redeploy:

```bash
# Desabilitar feature específica via env var
gcloud run services update lia-api \
  --region=$REGION \
  --update-env-vars "ENABLE_TWILIO=false"

# Reverter backend de domínio para FastAPI (se Rails estiver ativo)
gcloud run services update lia-frontend \
  --region=$REGION \
  --update-env-vars "CANDIDATES_BACKEND=fastapi"
```

**Tempo estimado:** ~15-30 segundos (nova revisão sem rebuild).

### 5.3 Rollback de banco (Alembic)

```bash
# Ver migration atual
alembic current

# Voltar 1 migration
alembic downgrade -1

# Voltar para migration específica
alembic downgrade <revision_id>
```

**CUIDADO:** Rollback de banco pode causar perda de dados. Sempre fazer backup antes:

```bash
gcloud sql export sql lia-postgres gs://lia-backup/pre-rollback-$(date +%Y%m%d).sql \
  --database=lia_db
```

### 5.4 Rollback completo — DNS Switch

Se tudo falhar e precisar voltar ao ambiente anterior:

```bash
# Mudar DNS para apontar para o IP do ambiente anterior
# No painel DNS do registrador:
# wedotalent.cc → A → <IP_AMBIENTE_ANTERIOR>
# api.wedotalent.cc → A → <IP_AMBIENTE_ANTERIOR>
```

**Tempo estimado:** Propagação DNS de 5-30 minutos (depende do TTL).

### 5.5 Árvore de decisão de rollback

```
Problema detectado em produção
│
├── É apenas UI/visual?
│   └── Fix forward (hotfix no frontend) — ~5 min deploy
│
├── É uma feature nova quebrando?
│   └── Feature flag OFF → rollback instantâneo (~30s)
│
├── API retornando 500?
│   ├── Só endpoints novos afetados?
│   │   └── Rollback API para revisão anterior (~30s)
│   └── Tudo quebrado?
│       └── Rollback API + verificar Cloud SQL/Redis
│
├── Dados corrompidos?
│   └── Restaurar backup SQL + rollback Alembic
│
└── Tudo falhou?
    └── DNS switch para ambiente anterior (~5-30 min)
```

---

## 6. Ordem de Execução da Validação

### Dia D-2 (2 dias antes do go-live)

1. [ ] Rodar testes E2E completos contra staging
2. [ ] Validar auth SSO (Google + Microsoft)
3. [ ] Testar isolamento multi-tenant (seção 4)
4. [ ] Verificar health endpoints e SSL
5. [ ] Confirmar Sentry recebendo eventos
6. [ ] Testar envio de email (pelo menos 1 email real)

### Dia D-1 (1 dia antes)

7. [ ] Smoke tests manuais completos (seção 1)
8. [ ] Teste de triagem: upload CV → score → mover no kanban
9. [ ] Chat LIA funcional em todos os contextos
10. [ ] Revisar critérios go/no-go (seção 2)
11. [ ] Preparar runbook de rollback (confirmar que revisões existem)
12. [ ] Comunicar time: go ou no-go

### Dia D (go-live)

13. [ ] Deploy para produção (merge develop → main)
14. [ ] Smoke test imediato: health + login + criar vaga
15. [ ] Monitorar Sentry por 1h (zero erros críticos)
16. [ ] Confirmar DNS e SSL em produção
17. [ ] Notificar stakeholders: plataforma no ar

### Dia D+1 (pós go-live)

18. [ ] Verificar logs do dia anterior (Cloud Run + Sentry)
19. [ ] Confirmar que worker processou tasks overnight
20. [ ] Coletar feedback inicial de usuários
21. [ ] Documentar issues encontrados para sprint seguinte

---

## 7. Contatos e Escalação

| Papel | Responsabilidade | Escalação |
|---|---|---|
| Dev Lead | Decisão go/no-go, fix técnico | — |
| DevOps/Infra | Cloud Run, DNS, SSL, rollback | Dev Lead |
| QA | Execução dos smoke tests | Dev Lead |
| PM | Comunicação com stakeholders | Dev Lead |

---

## Arquivos relacionados

| Arquivo | Conteúdo |
|---|---|
| `plataforma-lia/e2e/` | Testes E2E Playwright |
| `plataforma-lia/e2e/fixtures/auth.fixture.ts` | Auth fixture (cookies) |
| `GCP_INFRASTRUCTURE_CHECKLIST.md` | Provisionamento GCP |
| `GITHUB_SECRETS_SETUP.md` | Secrets CI/CD |
| `DEPLOY_GUIDE.md` | Guia geral de deploy |
