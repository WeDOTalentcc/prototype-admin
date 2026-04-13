# Relatório Completo — Agent Studio E2E Audit

**Arquivo de testes:** `e2e/tests/agent-studio-audit.spec.ts`
**Total de testes:** 137
**Total de áreas:** 31 describe blocks
**Data de geração:** 2026-04-13

---

## Sumário Executivo

| Métrica | Valor |
|---------|-------|
| Total de testes | 137 |
| Áreas cobertas | 31 |
| Bugs documentados | 9 (BUG-001 a BUG-006 + BUG-SRC, BUG-CA, BUG-MKT) |
| Testes que podem falhar por bug conhecido | ~18 |
| Testes condicionais (SKIP se sem dados) | ~22 |

---

## 1. Lista Completa de Testes por Área

### 1.1 Navigation & Access (6 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-NAV-01 | Agent Studio appears in sidebar under CONFIGURAÇÃO | critical |
| AS-NAV-02 | Page loads on sidebar click with correct content | critical |
| AS-NAV-03 | Header shows "Criar Agente" button and refresh icon | high |
| AS-NAV-04 | Page content persists after reload | medium |
| AS-NAV-05 | Agent sub-items in sidebar when agents exist | medium |
| AS-NAV-06 | No unhandled JS errors on page load | critical |

### 1.2 Empty State (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-EMPTY-01 | Agent explanation section present | medium |
| AS-EMPTY-02 | Empty state CTA when no agents | low |
| AS-EMPTY-03 | Template cards shown in empty state | low |

### 1.3 Sector Templates (5 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-TPL-01 | Sector templates API returns data | critical |
| AS-TPL-02 | Expected sector template cards rendered | high |
| AS-TPL-03 | "Personalizado" template always visible | medium |
| AS-TPL-04 | Personalizado click opens creation modal | high |
| AS-TPL-05 | Sector template pre-selects skills in modal | medium |

### 1.4 Creation Modal (10 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-CREATE-01 | "+ Criar Agente" opens dialog with role="dialog" | critical |
| AS-CREATE-02 | Modal contains Nome, Vincular, and Skills fields | high |
| AS-CREATE-03 | Submit button disabled when name is empty | high |
| AS-CREATE-04 | Submit button enables after entering name | high |
| AS-CREATE-05 | Cancel button closes modal completely | medium |
| AS-CREATE-06 | ESC key closes modal | medium |
| AS-CREATE-07 | "Vincular a" has Vaga and Pool options | high |
| AS-CREATE-08 | Skills toggle switches are interactive | medium |
| AS-CREATE-09 | Submit shows loading state then completes | high |
| AS-CREATE-10 | Created agent appears in card grid | high |

### 1.5 Agent Cards (5 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-CARD-01 | Card grid renders with card elements | high |
| AS-CARD-02 | Each card shows name and version info | medium |
| AS-CARD-03 | Active badge has green styling | low |
| AS-CARD-04 | Skills pills displayed on card | medium |
| AS-CARD-05 | Card shows stats (Analisados, Aprovados, Taxa) | high |

### 1.6 Card Actions (4 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-ACT-01 | Pause button sends PATCH to /sourcing-agents/:id/pause | critical |
| AS-ACT-02 | Resume button sends PATCH to /sourcing-agents/:id/resume | critical |
| AS-ACT-03 | Recalibrar opens calibration modal | high |
| AS-ACT-04 | "Ver" navigates to linked job or pool | high |

### 1.7 Stats Bar (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-STATS-01 | Stats bar shows agent count labels | medium |
| AS-STATS-02 | Pulsing dot element exists for active agents | low |
| AS-STATS-03 | Agent count is a valid number | medium |

### 1.8 Tab Navigation (4 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-TAB-01 | Three tabs present | high |
| AS-TAB-02 | Clicking Digital Twins tab changes content | high |
| AS-TAB-03 | Tab badge shows count number | medium |
| AS-TAB-04 | Switching back to Agents tab restores content | medium |

### 1.9 Digital Twins (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-TWIN-01 | Digital Twins tab loads content | high |
| AS-TWIN-02 | Twins header description text present | medium |
| AS-TWIN-03 | Twin action buttons or empty state CTA | medium |

### 1.10 Multi-Strategy Search (4 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-SEARCH-01 | Search tab loads with input field | high |
| AS-SEARCH-02 | Search has strategy selection | medium |
| AS-SEARCH-03 | Search with query hits API | high |
| AS-SEARCH-04 | Search execution crashes app (BUG-003) | critical |

### 1.11 Calibration Deep Flow (5 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-CAL-01 | Calibration entry point blocked by BUG-004 | critical |
| AS-CAL-02 | Candidate approval flow (BLOCKED by BUG-002 + BUG-004) | high |
| AS-CAL-03 | Reject candidate flow (BLOCKED) | high |
| AS-CAL-04 | Calibration progress indicator (BLOCKED) | high |
| AS-CAL-05 | Complete calibration flow (BLOCKED) | high |

### 1.12 Wizard Job Creation Flow (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-WIZ-01 | Wizard accessible from agent studio | high |
| AS-WIZ-02 | Multi-step wizard flow | high |
| AS-WIZ-03 | Wizard completion creates job and agent | high |

### 1.13 Visual Quality (7 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-VIS-01 | Theme colors consistent (primary/background) | low |
| AS-VIS-02 | Font families loaded properly | low |
| AS-VIS-03 | Icon rendering (no broken icon boxes) | low |
| AS-VIS-04 | Card shadow and border radius | low |
| AS-VIS-05 | Button sizes within expected range | low |
| AS-VIS-06 | No visual text truncation issues | low |
| AS-VIS-07 | No horizontal overflow causing scrollbar | low |

### 1.14 Accessibility (5 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-A11Y-01 | Page has main landmark role | medium |
| AS-A11Y-02 | Buttons have accessible names | high |
| AS-A11Y-03 | Images/icons have alt or aria-label | medium |
| AS-A11Y-04 | Color contrast meets WCAG (spot check) | medium |
| AS-A11Y-05 | Keyboard navigation works (Tab moves focus) | medium |

### 1.15 Responsiveness (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-RESP-01 | Mobile viewport (375px) loads | medium |
| AS-RESP-02 | Tablet viewport (768px) loads | medium |
| AS-RESP-03 | Desktop (1440px) loads with full layout | low |

### 1.16 Edge Cases (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-EDGE-01 | Long agent name (200 chars) accepted | low |
| AS-EDGE-02 | XSS-like characters safely rendered | medium |
| AS-EDGE-03 | Refresh reloads agent data from API | medium |

### 1.17 Sourcing Agent Creation — Full Flow (10 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-SRC-01 | Sector templates API returns 5 sectors | critical |
| AS-SRC-02 | Tecnologia template opens modal with correct skills | high |
| AS-SRC-03 | Saúde template opens modal | medium |
| AS-SRC-04 | Varejo template opens modal | medium |
| AS-SRC-05 | Manufatura template opens modal | medium |
| AS-SRC-06 | Transporte template opens modal | medium |
| AS-SRC-07 | Form validation: empty name blocks submit | high |
| AS-SRC-08 | Form POST /sourcing-agents with correct payload | critical |
| AS-SRC-09 | Agent appears in grid after creation | high |
| AS-SRC-10 | Agent data structure contains required fields | high |

### 1.18 Custom Agents — Creation & Lifecycle (12 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-CA-01 | Custom Agents tab loads with content | critical |
| AS-CA-02 | TemplateGallery visible or empty state CTA | high |
| AS-CA-03 | ConversationalCreator generates custom agent | high |
| AS-CA-04 | Manual form creates custom agent via POST | critical |
| AS-CA-05 | Edit custom agent opens edit modal | high |
| AS-CA-06 | Edit PATCH updates agent data | high |
| AS-CA-07 | Pause/Activate toggles agent status via PATCH | high |
| AS-CA-08 | Delete sends DELETE with confirm dialog | high |
| AS-CA-09 | Pause → Activate → Pause cycle works | high |
| AS-CA-10 | "Testar" button opens TestDebugPanel | high |
| AS-CA-11 | GET /custom-agents API returns list | high |
| AS-CA-12 | GET /custom-agents/available-tools accessible | medium |

### 1.19 TestDebugPanel — Message & Metrics Flow (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-TDP-01 | POST /custom-agents/:id/test intercepted | high |
| AS-TDP-02 | Panel shows tools, metrics, cost, compliance | high |
| AS-TDP-03 | Multi-turn conversation session | medium |

### 1.20 Agent ↔ Job Integration (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-JOB-01 | Sourcing agents API returns job_id field | high |
| AS-JOB-02 | "Ver" on agent with job_id navigates to job page | high |
| AS-JOB-03 | Agent with no job_id shows warning toast on Ver click | medium |

### 1.21 Agent ↔ Talent Pool Integration (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-POOL-01 | Sourcing agents have talent_pool_id field | high |
| AS-POOL-02 | Agent with talent_pool_id navigates to pool via Ver | high |
| AS-POOL-03 | Talent pools API accessible and linked pool exists | medium |

### 1.22 Calibration — Extended Tests (4 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-CAL-EXT-01 | Calibration candidates API exists | critical |
| AS-CAL-EXT-02 | Calibration thumbs-up API endpoint exists | high |
| AS-CAL-EXT-03 | Recalibrar button fires API (not hardcoded) | critical |
| AS-CAL-EXT-04 | calibration_v increments after calibrate API call | high |

### 1.23 Marketplace — Full Flow (8 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-MKT-01 | Marketplace tab loads with 3 sub-views | high |
| AS-MKT-02 | Browse marketplace calls GET /agent-marketplace/listings | high |
| AS-MKT-03 | Search filter in marketplace is interactive | medium |
| AS-MKT-04 | Category filter buttons change displayed listings | medium |
| AS-MKT-05 | Install button sends POST /agent-marketplace/install | high |
| AS-MKT-06 | Installed agents view loads from GET /my-installations | high |
| AS-MKT-07 | Publish agent button calls POST /agent-marketplace/publish | high |
| AS-MKT-08 | Approvals list visible in Custom Agents tab | medium |

### 1.24 Digital Twins — Extended (4 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-DT-01 | Digital Twins API returns list | high |
| AS-DT-02 | Avaliar button opens EvaluateWithTwinModal | high |
| AS-DT-03 | EvaluateWithTwinModal sends POST /digital-twins/:id/evaluate | high |
| AS-DT-04 | Twin card shows accuracy and decision count | medium |

### 1.25 Deploy Dialog (2 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-DEPLOY-01 | Deploy button opens DeployDialog with target options | high |
| AS-DEPLOY-02 | Deploy submit sends POST /custom-agents/:id/deployments | high |

### 1.26 Hardcoded Button Detection (4 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-HBC-01 | Agents tab — ALL buttons intercepted for network calls | critical |
| AS-HBC-02 | Custom Agents tab — ALL buttons intercepted | high |
| AS-HBC-03 | Marketplace tab — ALL buttons intercepted | medium |
| AS-HBC-04 | Search tab — ALL buttons intercepted | medium |

### 1.27 Quality Assessment (5 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-QUAL-01 | Sourcing agent returns candidates with required fields | high |
| AS-QUAL-02 | Custom agent test endpoint returns structured response | high |
| AS-QUAL-03 | WSI screening available for sourcing agent candidates | high |
| AS-QUAL-04 | Custom agent response classified via eval-helpers logic | high |
| AS-QUAL-05 | Sourcing agent approval rate is reasonable (0-100%) | medium |

### 1.28 Report Generation (1 teste)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-RPT-01 | Generate consolidated HTML audit report | low |

---

## 2. Bugs Documentados

### Bugs Confirmados (pré-existentes na aplicação)

| Bug ID | Severidade | Componente | Descrição | Testes Afetados |
|--------|------------|------------|-----------|-----------------|
| BUG-001 | critical | Templates API | `GET /api/backend-proxy/agent-templates/sectors` retorna erro ou dados incompletos. Templates de setor (Tecnologia, Saúde, Varejo, etc.) não renderizam na UI. | AS-TPL-01, AS-TPL-02, AS-TPL-05, AS-SRC-02 a AS-SRC-06 |
| BUG-002 | critical | Next.js Proxy Routing | `GET /api/backend-proxy/sourcing-agents/[id]/calibration-candidates` retorna 404. O Next.js catch-all `[...path]/route.ts` não consegue resolver sub-caminhos com o pattern `[id]`. | AS-CAL-01 a AS-CAL-05, AS-CAL-EXT-01, AS-CAL-EXT-02, AS-ACT-01, AS-ACT-02 |
| BUG-003 | critical | Multi-Strategy Search | Execução de busca multi-estratégia causa crash da aplicação. Componente quebra no render após submissão de query. | AS-SEARCH-04 |
| BUG-004 | high | Calibration Props | Prop `onStartCalibration` não está conectada no `AgentCard`. Botão "Recalibrar" não abre o modal de calibração. | AS-ACT-03, AS-CAL-01 a AS-CAL-05, AS-CAL-EXT-03 |
| BUG-005 | high | Navigation Props | Props `onNavigateToJob` e `onNavigateToPool` não estão conectadas nos AgentCards. Botão "Ver" não navega para a vaga/pool vinculada. | AS-ACT-04, AS-JOB-02, AS-POOL-02 |
| BUG-006 | medium | Accessibility | Faltam `aria-describedby` em seções-chave da página Agent Studio. | AS-A11Y-03 |

### Bugs Potenciais (detectáveis durante execução)

| Bug ID | Severidade | Componente | Descrição | Teste |
|--------|------------|------------|-----------|-------|
| BUG-SRC-001 | high | Sourcing API | `GET /agent-templates/sectors` retorna status 0 ou falha de rede | AS-SRC-01 |
| BUG-SRC-002 | high | Sourcing API | `GET /sourcing-agents` retorna HTTP != 200 | AS-SRC-10 |
| BUG-CA-001 | high | Custom Agents API | `DELETE /custom-agents/:id` falha | AS-CA-08 |
| BUG-CA-002 | high | Custom Agents API | `GET /custom-agents` retorna HTTP != 200 | AS-CA-11 |
| BUG-CA-003 | medium | Custom Agents API | `GET /custom-agents/available-tools` retorna HTTP != 200 | AS-CA-12 |
| BUG-MKT-* | medium | Marketplace API | Endpoints de marketplace podem não estar implementados | AS-MKT-02 a AS-MKT-08 |

---

## 3. Problemas Encontrados no Spec (Code Review)

Os seguintes problemas foram identificados na revisão de código do spec e precisam ser corrigidos:

### 3.1 CRITICO: Hardcoded Button Detection sempre registra PASS

**Arquivo:** `agent-studio-audit.spec.ts` linhas 2130, 2159, 2187
**Problema:** Testes `AS-HBC-02`, `AS-HBC-03` e `AS-HBC-04` registram `record(..., 'PASS', ...)` independentemente de quantos botões hardcoded foram encontrados. Apenas `AS-HBC-01` usa lógica condicional correta.
**Impacto:** Botões sem chamada API passam silenciosamente como OK.
**Correção necessária:** Usar `hardcoded.length === 0 ? 'PASS' : 'WARN'` como já feito em AS-HBC-01.

### 3.2 CRITICO: Validações de API aceitam qualquer status > 0

**Arquivo:** `agent-studio-audit.spec.ts` linhas 970, 1190, 1233, 1309, 1340, 1366, 1450, 1846, 1885, 1967, 2053
**Problema:** 11 testes usam `status > 0 ? 'PASS' : 'WARN'` para validar respostas de API. Isso significa que HTTP 400, 404, 500 são considerados PASS.
**Impacto:** Falhas de API são mascaradas como sucesso.
**Correção necessária:** Substituir por `status >= 200 && status < 300 ? 'PASS' : 'FAIL'` (ou pelo menos `status === 200 || status === 201`).

### 3.3 ALTO: Calibration_v não verifica incremento real

**Arquivo:** `agent-studio-audit.spec.ts` linhas 1742-1759
**Problema:** Teste `AS-CAL-EXT-04` lê `calibration_v` do agente mas registra PASS sem fazer comparação before/after. Não chama a API de calibração e depois verifica se o valor mudou.
**Impacto:** O teste sempre passa se existir um agente, sem validar a funcionalidade.
**Correção necessária:** Fazer POST de calibração, depois GET novamente e comparar `calibration_v` antes vs depois.

### 3.4 ALTO: Quality Assessment usa regex inline ao invés de eval-helpers

**Arquivo:** `agent-studio-audit.spec.ts` linhas 2305-2320
**Problema:** Teste `AS-QUAL-04` implementa classificação com regex ad-hoc em vez de importar e usar `classifyResponse()` do `eval-helpers.ts`. O import está no topo do arquivo mas não é utilizado.
**Impacto:** Resultados de classificação podem divergir do padrão da plataforma. Regex inline é menos completa (falta detecção de recusa ética, clarificação adequada, etc.).
**Correção necessária:** Substituir bloco de regex por chamada `classifyResponse(responseText)`.

### 3.5 MEDIO: Falta fluxo Agent ↔ Listas

**Problema:** Não existe cobertura para o fluxo de agentes integrados com Listas (criar lista, popular com candidatos, associar agente a lista, verificar consistência).
**Impacto:** Funcionalidade de listas não auditada no roteiro E2E.
**Correção necessária:** Adicionar nova seção de testes com:
- Verificar se endpoint `/api/backend-proxy/candidate-lists` existe
- Criar lista via POST
- Vincular agente a lista
- Verificar candidatos filtrados pela lista

### 3.6 MEDIO: Falta archive/duplicate/version para Custom Agents

**Problema:** Ciclo de vida de Custom Agents não testa: arquivar agente, duplicar agente, e verificar incremento de versão após edit.
**Impacto:** Funcionalidades de lifecycle incompletas na auditoria.
**Correção necessária:** Adicionar testes:
- POST /custom-agents/:id/archive
- POST /custom-agents/:id/duplicate
- Verificar que campo `version` incrementa após PATCH de edição

---

## 4. Plano de Ação — O Que Precisa Ser Feito

### Prioridade 1 — Correções no Spec (Bloqueantes)

| # | Ação | Linhas | Esforço |
|---|------|--------|---------|
| P1.1 | Corrigir AS-HBC-02/03/04: usar `hardcoded.length === 0 ? 'PASS' : 'WARN'` | 2130, 2159, 2187 | 5 min |
| P1.2 | Substituir `status > 0` por `status >= 200 && status < 300` em 11 testes | 970, 1190, 1233, 1309, 1340, 1366, 1450, 1846, 1885, 1967, 2053 | 10 min |
| P1.3 | Reescrever AS-CAL-EXT-04 com lógica before/after real | 1742-1759 | 15 min |
| P1.4 | Substituir regex inline por `classifyResponse()` em AS-QUAL-04 | 2305-2320 | 5 min |

### Prioridade 2 — Cobertura Faltante

| # | Ação | Testes Novos | Esforço |
|---|------|-------------|---------|
| P2.1 | Adicionar seção 29: Agent ↔ Listas (CRUD + associação) | ~4 testes | 30 min |
| P2.2 | Adicionar testes de archive/duplicate/version em seção 18 | ~3 testes | 20 min |

### Prioridade 3 — Bugs da Aplicação (Dev Team)

| # | Bug | Ação do Time de Dev | Impacto |
|---|-----|---------------------|---------|
| P3.1 | BUG-001 | Verificar endpoint `/agent-templates/sectors` no backend e corrigir resposta | Desbloqueia 7 testes |
| P3.2 | BUG-002 | Corrigir rota Next.js `[...path]/route.ts` para resolver sub-caminhos com `[id]` | Desbloqueia 8 testes |
| P3.3 | BUG-003 | Investigar crash no componente de busca multi-estratégia | Desbloqueia 1 teste |
| P3.4 | BUG-004 | Conectar prop `onStartCalibration` no `AgentCard` ao `CalibrationModal` | Desbloqueia 6 testes |
| P3.5 | BUG-005 | Conectar props `onNavigateToJob` e `onNavigateToPool` no `AgentCard` | Desbloqueia 3 testes |
| P3.6 | BUG-006 | Adicionar `aria-describedby` em seções-chave | 1 teste WARN→PASS |

### Prioridade 4 — Melhorias de Profundidade E2E

| # | Ação | Descrição |
|---|------|-----------|
| P4.1 | Usar `authenticatedPage` fixture em vez de `{ page }` | Atualmente o spec não usa autenticação, limitando cobertura em ambientes protegidos |
| P4.2 | Adicionar fluxo UI-driven completo (click → preencher → submit → verificar resultado) | Vários testes validam apenas presença de texto ou disponibilidade de API |
| P4.3 | Adicionar assertions de side-effects reais | Após criação, verificar que GET retorna o novo item; após delete, verificar que item sumiu |
| P4.4 | Implementar cleanup/teardown | Agentes criados durante teste devem ser removidos no afterEach |

### 1.29 Agent ↔ Listas (4 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-LIST-01 | GET /candidate-lists endpoint responds | medium |
| AS-LIST-02 | POST create candidate list | medium |
| AS-LIST-03 | Associate agent to candidate list | medium |
| AS-LIST-04 | Verify filtered candidates for agent list | medium |

### 1.30 Custom Agent Lifecycle (3 testes)
| ID | Teste | Severidade |
|----|-------|------------|
| AS-LIFE-01 | Archive custom agent via API | medium |
| AS-LIFE-02 | Duplicate custom agent via API | medium |
| AS-LIFE-03 | Version increment on custom agent update | medium |

---

## 5. Artefatos Gerados pelo Spec

| Artefato | Caminho | Descrição |
|----------|---------|-----------|
| HTML Report | `e2e/evidence/agent-studio-audit-report.html` | Relatório visual com tabelas PASS/FAIL/WARN por área, lista de bugs, seção de botões hardcoded |
| JSON Results | `e2e/evidence/agent-studio-audit-results.json` | Dados brutos de todos os testes em formato JSON |
| Screenshots | `e2e/evidence/AS-*.png` | Capturas de tela de evidência por cenário |

---

## 6. Como Executar

```bash
cd plataforma-lia
npx playwright test e2e/tests/agent-studio-audit.spec.ts --reporter=html
```

Os artefatos serão gerados automaticamente em `e2e/evidence/` ao final da execução.
