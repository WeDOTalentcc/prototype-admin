# Canônicos da Plataforma LIA — Organizados por Tema

> **WeDOTalent** lia-agent-system | Gerado em 2026-04-23
>
> Lista de referência para o time de desenvolvimento replicar a infraestrutura declarativa em outro produto.
> Cada arquivo é identificado pelo caminho relativo a `lia-agent-system/`, tamanho em linhas e responsabilidade canônica.
>
> **Uso:** ler o conteúdo de cada arquivo canônico e replicar o texto declarativo (docstrings, schemas, configurações) no produto alvo. A lógica de negócio é WeDOTalent-específica — a arquitetura e os contratos de interface são replicáveis.

---

## Como usar estes documentos

Este arquivo é o **índice master**. Ele lista todos os canônicos por tema com caminhos e responsabilidades.
Para replicar a infraestrutura completa em outro produto, use os **4 guias de reconstrução**:

```
CANONICAL_FILES_BY_THEME.md                       ← este arquivo (índice rápido por tema)
│
├── responsible-ai/                               ← NOVO 2026-04-23 (publicação pública pendente)
│   ├── eu-ai-act-technical-documentation-pt.md  ← Documentação técnica Art. 11 em PT-BR
│   │                                               (13 seções + 4 apêndices + benchmark + roadmap)
│   ├── eu-ai-act-technical-documentation-en.md  ← English version
│   └── fact-sheets/                              ← 5 AI Fact Sheets × 2 idiomas + README
│       ├── README.md
│       ├── cv-screening-fact-sheet-{pt,en}.md
│       ├── wsi-evaluation-fact-sheet-{pt,en}.md
│       ├── pipeline-transition-fact-sheet-{pt,en}.md
│       ├── ranking-shortlist-fact-sheet-{pt,en}.md
│       └── sourcing-boolean-fact-sheet-{pt,en}.md
│
├── operations/
│   └── FAIRNESS_LAYER3_RUNBOOK.md                ← NOVO 2026-04-23 — runbook da flag L3 em prod
│
├── reconstruction-guides/
│   ├── LIA_PERSONA_RECONSTRUCTION_GUIDE.md       ← Persona + Prompts + LangGraph + Camada Completa
│   │   Temas cobertos: persona YAML, guardrails YAML, compliance YAML, SystemPromptBuilder,
│   │                   LangGraphReActBase, ciclo de 8 passos de reconstrução.
│   │                   Parte 9 (2026-04-23): agent_prompts.yaml verbatim (11 agent_types),
│   │                   defensive.yaml, anti_sycophancy_block.py, interaction_patterns.py,
│   │                   intelligence_floor.yaml, ordem real de injeção de 9 passos, mapa
│   │                   dos 24 domain YAMLs, arquitetura candidate_portal.py + candidate_self_service.
│   │                   §9.11: verbatim dos 5 YAMLs Formato C/D pequenos + wsi_layer2_extraction
│   │                   (Formato E — extração LLM determinística) + seções singulares do Formato B
│   │                   (counter_argumentation, escalation, company_calibration, learning_rules,
│   │                   communication_transparency, config_blocks, reasoning_rules)
│
├── COMPLIANCE_RECONSTRUCTION_GUIDE.md            ← Fairness + LGPD + C3B + Segurança + PII + Auditoria Enterprise + Plano de Ação
│   Temas cobertos: FairnessGuard (3 camadas), AuditService, PII masking, prompt injection,
│                   C3B Layer, tenant guard, protected_attributes YAML, fairness_post_check YAML.
│                   Seção 10 (2026-04-23): auditoria exaustiva vs. EU AI Act / LGPD / NIST AI RMF,
│                   benchmark enterprise (Workday, HiPeople, Eightfold, LinkedIn), arquitetura
│                   de defesa em 8 camadas (C1-C8), matriz de cobertura dos 22 domain YAMLs.
│                   Seção 11 (2026-04-23): plano de ação estruturado para P0.1 (endpoint Art. 86
│                   ✅ IMPLEMENTADO), P1.1 (FAIRNESS_LAYER3_ENABLED ✅ ATIVADO),
│                   P1.2 (bias audit independente 9 semanas - deferido Q3/2026),
│                   P1.3 (5 AI Fact Sheets ✅ PUBLICADAS PT+EN), P2.1 (documentação técnica
│                   Art. 11 ✅ PUBLICADA PT+EN em docs/responsible-ai/)
│
├── INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md        ← Agentes + Tools + Orquestração + LLM
│   Temas cobertos: AgentType enum, @tool_handler decorator, Observability facade,
│                   tool_permissions YAML, domain_routing YAML, LLMProviderFactory,
│                   CascadedRouter (8 tiers), MainOrchestrator (4 fases), ChatResponse schema
│
└── RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md   ← Resiliência + Aprendizado + Mensageria
    Temas cobertos: CircuitBreaker (3 estados, 20 circuitos), LearningLoopService,
                    BrokerInterface (Redis/RabbitMQ/PubSub), PlatformEvent, UnifiedEventPublisher
```

### Hierarquia de dependência para reconstrução

```
1. COMPLIANCE (implementar primeiro — todas as camadas dependem)
      ↓
2. INFRASTRUCTURE (agentes + orquestrador precisam de compliance já disponível)
      ↓
3. RESILIENCE (circuit breakers e learning loop envolvem orquestrador + LLM factory)
      ↓
4. PERSONA (system prompts referenciam compliance + ferramentas já criadas)
```

### Quando usar este índice vs os guias

| Necessidade | Documento a usar |
|------------|-----------------|
| "Quero saber quais arquivos existem no tema X" | Este índice |
| "Quero replicar fairness/LGPD do zero" | `COMPLIANCE_RECONSTRUCTION_GUIDE.md` |
| "Quero entender como o orquestrador funciona" | `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` |
| "Quero implementar circuit breakers" | `RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md` |
| "Quero replicar a persona e os prompts da LIA" | `LIA_PERSONA_RECONSTRUCTION_GUIDE.md` |
| "Preciso do código exato de um arquivo específico" | Abrir o arquivo canônico diretamente em `lia-agent-system/` |

> **Nota de fidelidade:** todo o conteúdo dos guias de reconstrução foi extraído diretamente dos
> arquivos canônicos com leitura via Read tool — nenhum conteúdo foi inventado ou inferido.
> Se houver divergência entre um guia e o código atual, o código em `lia-agent-system/` é a fonte de verdade.

### Atualizações canônicas aplicadas em 2026-04-23 (Audit Compliance)

Fixes P0/P1 aplicados direto nos arquivos canônicos em `lia-agent-system/app/prompts/`
como resultado da auditoria documentada em `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10:

| Arquivo | Tipo de fix | Severidade |
|---------|------------|-----------|
| `app/prompts/domains/autonomous.yaml` | Adicionado `behavioral_rules` + `scope_in/out` + `hitl_escalation` + `compliance_integration` | **P0** |
| `app/prompts/shared/compliance_block.yaml` | Adicionada seção `right_to_contest` (EU AI Act Art. 86 + LGPD Art. 20) em variantes `decision` e `communication` | **P0** |
| `app/prompts/domains/culture_analysis.yaml` | Injetado bloco `<compliance_hr>` dentro do `system_prompt` (fairness + HITL + LGPD Art. 11 + audit) | P1 |
| `app/prompts/domains/orchestrator.yaml` | Injetado prologue de compliance no `system_prompt` (prompt_security + multi_tenancy + direito de contestação) | P1 |

Gaps P0/P1 ainda em aberto (exigem mudança de código ou endpoint, fora do escopo puro de prompts):
- Endpoint/fluxo técnico de explicação ao candidato (validar `decision_explanation.py`)
- Flag `FAIRNESS_LAYER3_ENABLED=True` em produção
- Bias audit independente publicado (disparate impact ratio por grupo protegido)
- AI Fact Sheet por feature (CV screening, WSI)
- Formalização de classificação EU AI Act Anexo III

Rastreamento completo: `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.8.

### Bundles de YAMLs Canônicos (2026-04-24)

> Entregues como fonte verbatim para replicação offline + context file para
> Claude Code / Cursor. Zero paráfrase — cada byte lido direto de
> `lia-agent-system/` no Replit.

| Bundle | YAMLs | Tamanho | Arquivo |
|--------|:-----:|:-------:|---------|
| **LIA** (persona + especialização) | 30 | 224K (4.583L) | `LIA_YAMLS_CANONICAL_BUNDLE.md` |
| **Compliance** (protected_attributes + fairness_post_check) | 2 | 12K (284L) | `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md` |
| **Infrastructure** (tool_permissions + domain_routing) | 2 | 28K (737L) | `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md` |
| **Total** | **34** | **264K** | (3 arquivos) |

Alinhamento 1:1 com os cards Jira: cada card anexa o bundle correspondente
(Card 1 → LIA, Card 2 → Compliance, Card 3 → Infrastructure). Card 4
(Resilience) e Card 5 (Frontend) não têm bundle — Resilience é 100% código
Python; Frontend não consome YAMLs diretamente.

Cada bundle contém:
- Cabeçalho com instruções de uso em Claude Code (via `CLAUDE.md`) e
  Cursor (via `.cursor/rules/*.mdc`)
- Índice tabular com path canônico / linhas / versão / updated_at / formato
- Verbatim de cada YAML em bloco ```yaml
- Cross-references para os bundles irmãos

### Execução Plano P0/P1 concluída em 2026-04-23

Todos os itens do plano `esse-front-end-rustling-lollipop.md` foram executados em uma única janela:

| Fase | Entrega | Artefato | Local |
|------|---------|----------|-------|
| 1 | Ativação FairnessGuard Layer 3 em produção | `.env` + `FAIRNESS_LAYER3_RUNBOOK.md` | `lia-agent-system/.env` + `docs/operations/` |
| 2 | Parte 9 do LIA_PERSONA ampliada com YAMLs pequenos + formato E + seções singulares Formato B | `LIA_PERSONA_RECONSTRUCTION_GUIDE.md` §9.11 | `docs/reconstruction-guides/` |
| 3 | Endpoint EU AI Act Art. 86 direto-ao-candidato implementado e validado | `candidate_portal_explanation.py` + `explain_candidate_decision.py` + YAML regra 8 + teste | `app/api/v1/` + `app/domains/candidate_self_service/` |
| 4 | Documentação técnica EU AI Act Art. 11 completa (PT + EN) | `eu-ai-act-technical-documentation-pt.md` + `-en.md` | `docs/responsible-ai/` |
| 5 | 5 AI Fact Sheets (PT + EN) + README | `fact-sheets/*.md` (11 arquivos) | `docs/responsible-ai/fact-sheets/` |

**Descobertas importantes durante a execução:**
- O suposto gap P0 do `PolicyAgent` estava incorreto — o agente real em `app/domains/policy/agents/agent.py` já tem FairnessGuard implementado. O P0 real era `autonomous.yaml` (corrigido).
- LIA **já tinha** 80% da infraestrutura candidate-facing (`candidate_portal.py` + `candidate_self_service.yaml` + `CandidateStatusService`). O que faltava era apenas a ponte entre `decision_explanation.py` (operador-facing) e o candidato — resolvida pelo novo endpoint + tool.
- `FAIRNESS_LAYER3_ENABLED=true` já estava recomendado em `.env.production.example` — só faltava aplicar.
- Score de compliance WeDOTalent subiu de 6/10 (pré-2026-04-23) para 7/10 após esta janela.

**Ainda pendente (deferido pelo Paulo):**
- Item 2c — bias audit independente com publicação (Q3/2026, 9 semanas, 3 sprints em COMPLIANCE §11.3)
- Revisão jurídica externa dos docs `responsible-ai/` antes de publicação pública
- Frontend + rota final em `wedotalent.cc/responsible-ai/`
- Certificação ISO/IEC 42001:2023 (roadmap 2027)
- Registro no EU AI Act database (pós 02/08/2026)

---

## Índice Rápido por Tema

| # | Tema | Arquivos | Prioridade |
|---|------|---------|-----------|
| 1 | [Fairness & Bias](#tema-1--fairness--bias) | 5 canônicos | 🔴 Crítico — toda plataforma de triagem |
| 2 | [LGPD & Privacidade](#tema-2--lgpd--privacidade) | 5 canônicos | 🔴 Crítico — Brasil + EU AI Act |
| 3 | [Compliance Gates (C3B + Audit)](#tema-3--compliance-gates-c3b--audit) | 5 canônicos | 🔴 Crítico — toda decisão sobre candidato |
| 4 | [Segurança & PromptInjection](#tema-4--segurança--promptinjection) | 4 canônicos | 🔴 Crítico — LLM em produção |
| 5 | [Observabilidade](#tema-5--observabilidade) | 9 canônicos | 🟡 Alta — MLOps + drift detection |
| 6 | [Infraestrutura de Agentes](#tema-6--infraestrutura-de-agentes) | 6 canônicos | 🟡 Alta — base para todos os agentes |
| 7 | [Orquestração & Roteamento](#tema-7--orquestração--roteamento) | 8 canônicos | 🟡 Alta — performance + cascata LLM |
| 8 | [Provedores LLM (tenant-aware)](#tema-8--provedores-llm-tenant-aware) | 5 canônicos | 🟡 Alta — multi-tenant LLM |
| 9 | [Resiliência & Circuit Breaker](#tema-9--resiliência--circuit-breaker) | 4 canônicos | 🟡 Alta — produção 24/7 |
| 10 | [Multi-tenancy & Tool Permissions](#tema-10--multi-tenancy--tool-permissions) | 6 canônicos | 🟡 Alta — SaaS B2B |
| 11 | [Aprendizado & Inteligência](#tema-11--aprendizado--inteligência) | 6 canônicos | 🟢 Média — otimização contínua |
| 12 | [Comunicação & Eventos](#tema-12--comunicação--eventos) | 5 canônicos | 🟢 Média — mensageria async |

---

## Tema 1 — Fairness & Bias

> **Objetivo:** Garantir que nenhuma decisão automatizada sobre candidatos contenha viés discriminatório.
> Fundamental para LGPD Art. 20, EU AI Act, e qualquer plataforma de RH.

---

### 1.1 `app/shared/compliance/fairness_guard.py`
**Tamanho:** ~1.014 linhas | **Tipo:** Serviço canônico central

**Responsabilidade:**
Sistema de 3 camadas para detecção e bloqueio de viés em conteúdo processado por IA:
- **Layer 1 (computacional):** keyword matching contra lista de atributos protegidos
- **Layer 2 (ML):** modelo de classificação de bias embutido
- **Layer 3 (LLM-judge, opt-in):** Claude Sonnet como árbitro para casos ambíguos — ativado via `FAIRNESS_LAYER3_ENABLED`

**Interface principal:**
```python
class FairnessGuard:
    async def check(self, text: str, action_type: str = "general") -> FairnessCheckResult
    async def check_with_layer3(self, text: str, action_type: str) -> FairnessCheckResult
    async def log_check(self, result: FairnessCheckResult, context: str, company_id: str) -> None

class FairnessCheckResult:
    is_blocked: bool
    category: str          # qual atributo protegido foi detectado
    confidence: float
    educational_message: str  # mensagem para exibir ao usuário/recrutador
    layer_triggered: int   # 1, 2, ou 3
```

**Atributos protegidos verificados:** gênero, raça, etnia, religião, estado civil, idade (fora critério profissional), orientação sexual, deficiência, origem nacional, dados de saúde.

**Como replicar:** importar padrão de 3 camadas. Layer 1 é puro Python. Layer 2 exige modelo treinado ou regras heurísticas. Layer 3 exige LLM com prompt de juiz de fairness.

---

### 1.2 `app/shared/compliance/fairness_guard_middleware.py`
**Tamanho:** ~194 linhas | **Tipo:** Middleware FastAPI

**Responsabilidade:**
Intercepta automaticamente todas as requisições HTTP que passam por rotas de triagem (`/screening`, `/ranking`, `/scoring`) e aplica FairnessGuard antes de chegarem ao handler. Evita que cada endpoint precise chamar FairnessGuard explicitamente.

**Interface principal:**
```python
class FairnessGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response
    
SCREENING_ROUTES = ["/api/v1/candidates", "/api/v1/screening", "/api/v1/ranking"]
```

**Como replicar:** middleware genérico. Configurar lista de rotas sensíveis. Retornar 422 com `educational_message` quando bloqueado.

---

### 1.3 `app/shared/compliance/protected_attributes.py`
**Tamanho:** ~107 linhas | **Tipo:** Configuração declarativa

**Responsabilidade:**
Lista canônica de atributos protegidos, sinônimos, e variantes linguísticas (PT-BR + EN). Usada por FairnessGuard L1.

**Estrutura:**
```python
PROTECTED_ATTRIBUTES = {
    "gender": ["gênero", "sexo", "gender", "feminino", "masculino", ...],
    "race": ["raça", "cor", "etnia", "race", "ethnicity", ...],
    "religion": ["religião", "crença", "religion", "faith", ...],
    "age": ["idade", "age", "anos de experiência" (se usado como proxy), ...],
    # ... 10+ categorias
}

SEVERITY_WEIGHTS = {
    "race": 1.0,     # máxima severidade
    "gender": 0.9,
    "religion": 0.9,
    "age": 0.7,      # mais comum em JDs — requer contexto
}
```

**Como replicar:** arquivo de configuração puro. Adaptar lista para idioma e legislação do país alvo.

---

### 1.4 `app/services/bias_audit_service.py`
**Tamanho:** ~521 linhas | **Tipo:** Serviço de auditoria

**Responsabilidade:**
Implementa o método **Four-Fifths Rule (80% Rule)** para detecção de disparate impact em processos seletivos. Calcula taxa de aprovação por grupo demográfico e alerta quando um grupo tem taxa < 80% de outro.

**Interface principal:**
```python
class BiasAuditService:
    async def run_four_fifths_audit(self, job_id: str, company_id: str) -> BiasAuditReport
    async def get_audit_history(self, job_id: str) -> list[BiasAuditSnapshot]
    async def schedule_periodic_audit(self, job_id: str, frequency_days: int) -> None

class BiasAuditReport:
    job_id: str
    company_id: str
    selection_rates: dict[str, float]   # por grupo demográfico
    disparate_impact_ratios: dict       # taxa comparativa
    alerts: list[BiasAlert]
    recommendations: list[str]
    four_fifths_passed: bool
```

**Endpoint:** `GET /api/v1/bias-audit/job/{job_id}`

**Como replicar:** a matemática da Four-Fifths Rule é padrão EEOC (EUA) e equivalente em outros países. Adaptar grupos demográficos para legislação local.

---

### 1.5 `app/models/bias_audit_snapshot.py`
**Tamanho:** ~89 linhas | **Tipo:** Modelo SQLAlchemy

**Responsabilidade:**
Persiste snapshots de auditoria de bias para histórico e relatórios de compliance. Cada execução de `BiasAuditService` gera um snapshot imutável.

**Schema:**
```python
class BiasAuditSnapshot(Base):
    id: UUID
    job_id: UUID
    company_id: UUID
    audit_date: datetime
    four_fifths_passed: bool
    selection_rates: JSON      # {group: rate}
    disparate_impact: JSON     # {comparison: ratio}
    alerts_count: int
    report_json: JSON          # relatório completo serializado
    created_by: str            # "system" ou user_id
```

**Endpoint histórico:** `GET /api/v1/bias-audit/job/{job_id}/history`

---

## Tema 2 — LGPD & Privacidade

> **Objetivo:** Conformidade com LGPD (Lei 13.709/2018), GDPR equivalência, e proteção de dados pessoais de candidatos.

---

### 2.1 `app/shared/pii_masking.py`
**Tamanho:** ~220 linhas | **Tipo:** Utilitário global

**Responsabilidade:**
Mascaramento automático de PII (Personally Identifiable Information) em logs, respostas e dados em trânsito. Instalado globalmente no startup da aplicação.

**Interface principal:**
```python
def install_global_pii_masking() -> None:
    """Instalar interceptor global no logging + Celery workers."""

def mask_pii(text: str) -> str:
    """Mascarar CPF, CNPJ, email, telefone, RG em texto arbitrário."""

PII_PATTERNS = {
    "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"(\+55\s?)?(\(?\d{2}\)?[\s\-]?)?\d{4,5}[\s\-]?\d{4}",
    "rg": r"\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]",
}

MASK_REPLACEMENT = {
    "cpf": "***.***.***-**",
    "email": "***@***.***",
    "phone": "(**.)*****-****",
}
```

**Uso no startup:**
```python
# main.py
from app.shared.pii_masking import install_global_pii_masking
install_global_pii_masking()
```

**Como replicar:** adaptar `PII_PATTERNS` para documentos do país alvo (ex: CPF → SSN para EUA). Instalar no startup é o padrão — não depende de cada endpoint chamar explicitamente.

---

### 2.2 `app/services/data_request.py`
**Tamanho:** ~312 linhas | **Tipo:** Serviço DSR (Data Subject Request)

**Responsabilidade:**
Portal de titular de dados — implementa os direitos LGPD Art. 18:
- Acesso (portabilidade dos dados)
- Correção
- Exclusão (direito ao esquecimento)
- Revogação de consentimento

**Interface principal:**
```python
class DataRequestService:
    async def submit_access_request(self, candidate_id: str, company_id: str) -> DataRequest
    async def submit_deletion_request(self, candidate_id: str, reason: str) -> DataRequest
    async def process_deletion(self, request_id: str) -> DeletionResult
    async def export_candidate_data(self, candidate_id: str) -> CandidateDataExport
    async def get_request_status(self, request_id: str) -> DataRequestStatus
```

**Como replicar:** esquema de request + processamento assíncrono (deletar dados leva tempo, especialmente em backups). O padrão de soft-delete + hard-delete programado é fundamental.

---

### 2.3 `app/services/consent_management.py`
**Tamanho:** ~287 linhas | **Tipo:** Serviço de consentimento

**Responsabilidade:**
Gerenciamento granular de consentimento por finalidade de uso dos dados:
- Triagem automática por IA
- Compartilhamento com terceiros
- Armazenamento além do processo seletivo
- Comunicações de marketing

**Interface principal:**
```python
class ConsentManagementService:
    async def record_consent(self, candidate_id: str, purposes: list[ConsentPurpose]) -> Consent
    async def revoke_consent(self, candidate_id: str, purpose: ConsentPurpose) -> None
    async def check_consent(self, candidate_id: str, purpose: ConsentPurpose) -> bool
    async def get_consent_history(self, candidate_id: str) -> list[ConsentEvent]
```

**Endpoint granular:** `GET/POST /api/v1/consent/granular/{candidate_id}`

---

### 2.4 `app/services/granular_consent_service.py`
**Tamanho:** ~198 linhas | **Tipo:** Extensão de consentimento granular

**Responsabilidade:**
Camada estendida sobre `consent_management.py` com UI-friendly responses e agrupamento de finalidades por contexto (triagem vs. marketing vs. analytics).

---

### 2.5 `app/shared/encryption/encrypted_field_mixin.py`
**Tamanho:** ~142 linhas | **Tipo:** Mixin SQLAlchemy

**Responsabilidade:**
Criptografia transparente de campos sensíveis no banco de dados (AES-256). Campos marcados com `EncryptedField` são automaticamente criptografados na escrita e descriptografados na leitura.

**Interface:**
```python
class EncryptedFieldMixin:
    """Mixin para modelos SQLAlchemy com campos sensíveis."""
    
class EncryptedField(TypeDecorator):
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect) -> str  # encrypt on write
    def process_result_value(self, value, dialect) -> str  # decrypt on read
```

**Como replicar:** padrão de TypeDecorator SQLAlchemy. Chave de criptografia via env var (`FIELD_ENCRYPTION_KEY`). Nunca hardcoded.

---

## Tema 3 — Compliance Gates (C3B + Audit)

> **Objetivo:** Garantir que toda entrada e saída do sistema passe por verificação de compliance, e que toda decisão seja rastreável.

---

### 3.1 `app/shared/compliance/c3b_layer.py`
**Tamanho:** ~126 linhas | **Tipo:** Gateway de compliance

**Responsabilidade:**
Implementa o padrão **C3B (Compliance, Consent, Context, Block)** — camada de verificação pré e pós-processamento para qualquer operação que afeta candidatos.

**Interface principal:**
```python
class ComplianceContext:
    company_id: str
    domain: str
    user_id: str | None = None

class ComplianceResult:
    fairness_blocked: bool
    block_reason: str | None
    pii_detected: bool
    consent_valid: bool
    audit_trail_id: str

async def pre_compliance(
    payload_summary: str,
    company_id: str,
    domain: str,
) -> ComplianceResult:
    """Verificar antes de processar — fairness + consent."""

async def post_compliance(
    response: Any,
    context: ComplianceContext,
) -> Any:
    """Mascarar PII na saída + log final."""
```

**Padrão de uso (referência: `agent_chat_sse.py`):**
```python
_pre = await pre_compliance(summary, company_id=ctx.company_id, domain="chat")
if _pre.fairness_blocked:
    raise HTTPException(422, detail=_pre.block_reason)

# ... processar ...

response = await post_compliance(raw_response, ComplianceContext(company_id=..., domain=...))
```

**Como replicar:** padrão decorator/gateway. O segredo é ser chamado em TODA fronteira de entrada/saída, não só nos agentes. Middleware ou explicit call — ambos válidos.

---

### 3.2 `app/shared/compliance/audit_service.py`
**Tamanho:** ~598 linhas | **Tipo:** Serviço de auditoria canônico

**Responsabilidade:**
Trilha auditável imutável de todas as decisões sobre candidatos. Implementa requisitos SOX, ISO 27001, e LGPD Art. 20 (explicabilidade de decisões automatizadas).

**Interface principal:**
```python
class AuditService:
    async def log_decision(
        self,
        company_id: str,
        agent_name: str,
        decision_type: str,           # "cv_screening", "ranking", "auto_reject", etc.
        action: str,                  # descrição da ação
        decision: str,                # "approved", "rejected", "escalated"
        reasoning: list[str] = [],    # lista de critérios aplicados
        criteria_used: list[str] = [],
        subject_id: str | None = None,
        subject_ids: list[str] = [],
        metadata: dict = {},
    ) -> AuditEntry
    
    async def get_decision_history(
        self,
        subject_id: str,
        company_id: str,
        decision_type: str | None = None,
    ) -> list[AuditEntry]
    
    async def generate_compliance_report(
        self,
        company_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> ComplianceReport

# Singleton global
audit_service = AuditService()
```

**Como replicar:** padrão write-once append-only. Nunca atualizar ou deletar entradas. Index em `company_id + decision_type + created_at` para queries de compliance.

---

### 3.3 `app/shared/compliance/domain_validators.py`
**Tamanho:** ~142 linhas | **Tipo:** Validadores por domínio

**Responsabilidade:**
Validações específicas por domínio que vão além do schema Pydantic. Exemplos: verificar se uma vaga tem requisitos legalmente permitidos, se critérios de triagem são objetivos, se SLA de resposta ao candidato está sendo respeitado.

---

### 3.4 `app/shared/security/fact_checker.py`
**Tamanho:** ~476 linhas | **Tipo:** Verificador de fatos

**Responsabilidade:**
Verificação de claims factuais em respostas do LLM antes de enviar ao candidato/recrutador. Evita hallucinations sobre requisitos legais, benefícios ou obrigações contratuais.

**Interface:**
```python
class FactChecker:
    async def check_response(self, response: str, context: dict) -> FactCheckResult
    
class FactCheckResult:
    passed: bool
    suspicious_claims: list[str]
    confidence: float
    flagged_for_review: bool
```

---

### 3.5 `app/repositories/guardrail_repository.py`
**Tamanho:** ~224 linhas | **Tipo:** Repositório de guardrails

**Responsabilidade:**
Persiste e gerencia as regras de guardrail configuradas por tenant — quais tipos de conteúdo são bloqueados, quais ações requerem aprovação humana (HITL), e limites de automação por domínio.

---

## Tema 4 — Segurança & PromptInjection

> **Objetivo:** Proteger a plataforma contra ataques específicos de LLM em produção.

---

### 4.1 `app/shared/prompt_injection.py`
**Tamanho:** ~112 linhas | **Tipo:** Guard canônico

**Responsabilidade:**
Detecção e bloqueio de prompt injection attacks antes que o input do usuário chegue ao LLM. Cobre: jailbreaks, role-playing override, instruction hijacking, delimiter attacks.

**Interface principal:**
```python
class PromptInjectionGuard:
    def check(self, user_input: str) -> InjectionCheckResult
    async def check_async(self, user_input: str) -> InjectionCheckResult

class InjectionCheckResult:
    is_injection: bool
    attack_type: str | None      # "jailbreak", "role_override", "delimiter", etc.
    confidence: float
    cleaned_input: str | None    # input sanitizado (se possível)
```

**Padrões detectados (exemplos):**
- `"Ignore previous instructions and..."` → instruction hijacking
- `"You are now DAN..."` → role-play override
- `"---\nSYSTEM: ..."` → delimiter injection
- `"[INST] <<SYS>>"` → format injection

**Como replicar:** usar biblioteca `rebuff` ou implementar regex + ML classifier. A lista de padrões é frequentemente atualizada — ter um sistema de update sem deploy é essencial.

---

### 4.2 `app/shared/security/security_patterns.py`
**Tamanho:** ~473 linhas | **Tipo:** Biblioteca de padrões de segurança

**Responsabilidade:**
Coleção central de patterns de segurança: validação de inputs, sanitização, detecção de strings maliciosas, whitelist de formatos aceitos por tipo de campo.

---

### 4.3 `app/shared/security/response_filter.py`
**Tamanho:** ~363 linhas | **Tipo:** Filtro de saída

**Responsabilidade:**
Filtro de pós-processamento nas respostas do LLM. Remove: dados sensíveis que vazaram, hallucinations de PII, conteúdo inapropriado para contexto de RH.

**Interface:**
```python
class ResponseFilter:
    async def filter(self, response: str, context: FilterContext) -> FilteredResponse
    
class FilteredResponse:
    content: str
    was_modified: bool
    modifications: list[str]   # log de o que foi removido/modificado
```

---

### 4.4 `app/shared/middleware/tenant_guard.py`
**Tamanho:** ~74 linhas | **Tipo:** Guard de isolamento tenant

**Responsabilidade:**
Garante que `company_id` usado em qualquer operação vem da sessão JWT autenticada, nunca do payload da requisição. Previne tenant boundary violations.

**Interface:**
```python
def require_company(current_user: User = Depends(get_current_user)) -> str:
    """FastAPI dependency — retorna company_id validado da sessão."""
    if not current_user.company_id:
        raise HTTPException(403, "Tenant context missing")
    return current_user.company_id

# Uso em endpoint:
@router.get("/candidates")
async def list_candidates(
    company_id: str = Depends(require_company),
    db: AsyncSession = Depends(get_db),
):
    # company_id sempre da sessão — nunca do query param
```

**Regra inviolável:** `company_id` NUNCA do payload/query param em operações de leitura/escrita. Sempre do JWT via `require_company`.

---

## Tema 5 — Observabilidade

> **Objetivo:** Visibilidade completa de agentes em produção — traces, logs estruturados, drift de modelos, saúde de agentes.

---

### 5.1 `app/shared/observability/__init__.py`
**Tamanho:** facade de 19 exports | **Tipo:** Facade unificado

**Responsabilidade:**
Ponto de entrada único para toda infraestrutura de observabilidade. Exporta 19 símbolos de 7 módulos distintos — elimina imports dispersos.

**Exports:**
```python
# Tracing
from app.shared.observability import (
    trace_agent_call,        # decorator para rastrear chamadas de agente
    get_tracer,              # OpenTelemetry tracer
    
    # Structured logging
    get_structured_logger,   # logger com campos JSON
    log_agent_event,         # evento de agente padronizado
    
    # Model drift
    ModelDriftService,       # detecção de drift em modelos ML
    DriftAlert,              # alerta de drift
    
    # Agent monitoring
    AgentMonitoringService,  # saúde e métricas de agentes
    AgentHealthAlert,        # alerta de saúde
    
    # WSI observability
    WSIObservabilityService, # métricas específicas de entrevistas WSI
    
    # Golden signals
    GoldenDriftMonitor,      # latência, erros, saturação, tráfego
    
    # Monitoring loop
    start_monitoring_loop,   # background task de monitoramento
    stop_monitoring_loop,
)
```

**Como replicar:** pattern de facade é a parte mais valiosa. Centralizar todos os imports de observabilidade em um `__init__.py` evita que novos devs importem de módulos internos arbitrários.

---

### 5.2 `app/shared/observability/tracing.py`
**Tamanho:** ~481 linhas | **Tipo:** OpenTelemetry integration

**Responsabilidade:**
Integração com OpenTelemetry para distributed tracing de chamadas de agente. Cada step do LangGraph gera um span rastreável end-to-end.

---

### 5.3 `app/shared/observability/structured_logging.py`
**Tamanho:** ~115 linhas | **Tipo:** Logging canônico

**Responsabilidade:**
Logger estruturado (JSON) com campos obrigatórios: `company_id`, `agent_name`, `trace_id`, `timestamp`. Integra com Prometheus e sistemas de log aggregation.

**Campos obrigatórios em todo log:**
```json
{
  "company_id": "UUID",
  "agent_name": "string",
  "trace_id": "UUID",
  "timestamp": "ISO8601",
  "level": "INFO|WARNING|ERROR",
  "event": "string",
  "duration_ms": "number"
}
```

---

### 5.4 `app/services/model_drift_service.py`
**Tamanho:** ~427 linhas | **Tipo:** MLOps — drift detection

**Responsabilidade:**
Detecta quando modelos de ML (scoring, classificação de bias) começam a divergir do comportamento esperado. Monitora distribuição de scores, taxa de bloqueio do FairnessGuard, e performance de prompts.

---

### 5.5 `app/services/drift_alert_service.py`
**Tamanho:** ~159 linhas | **Tipo:** Alertas de drift

**Responsabilidade:**
Envia alertas quando drift é detectado. Integra com sistema de notificações (email, Teams, in-app).

---

### 5.6 `app/services/agent_monitoring_service.py`
**Tamanho:** ~580 linhas | **Tipo:** Monitoramento de agentes

**Responsabilidade:**
Métricas de saúde de cada agente: latência média, taxa de erro, uso de tokens, custo por operação, taxa de escalada HITL.

---

### 5.7 `app/services/agent_health_alert_service.py`
**Tamanho:** ~208 linhas | **Tipo:** Alertas de saúde

**Responsabilidade:**
Alerta quando agentes excedem thresholds: latência > SLA, erro rate > limite, custo de tokens acima do orçamento por tenant.

---

### 5.8 `app/shared/observability/monitoring_loop.py`
**Tamanho:** ~491 linhas | **Tipo:** Background monitoring

**Responsabilidade:**
Loop de monitoramento em background (Celery beat) que coleta métricas periodicamente: golden signals (latência, erros, saturação, tráfego), health checks de agentes, verificação de drift.

---

### 5.9 `app/shared/observability/golden_drift_monitor.py`
**Tamanho:** ~274 linhas | **Tipo:** Golden signals

**Responsabilidade:**
Implementa os 4 golden signals do Google SRE para agentes IA: Latency, Traffic, Errors, Saturation. Dashboard-ready output.

---

## Tema 6 — Infraestrutura de Agentes

> **Objetivo:** Base classes e executores que todos os agentes herdam — garantindo compliance por herança.

---

### 6.1 `app/agents/base_agent.py`
**Tamanho:** ~189 linhas | **Tipo:** Canonical base class

**Responsabilidade:**
Define os tipos e contratos fundamentais de todos os agentes da plataforma.

**Exports canônicos:**
```python
class AgentType(Enum):
    WIZARD = "wizard"
    PIPELINE = "pipeline"
    SOURCING = "sourcing"
    TALENT = "talent"
    JOB_MANAGEMENT = "job_management"
    KANBAN = "kanban"
    POLICY = "policy"
    # ... todos os tipos

class TaskPriority(Enum):
    LOW = 1; NORMAL = 2; HIGH = 3; CRITICAL = 4

class TaskStatus(Enum):
    PENDING = "pending"; RUNNING = "running"
    COMPLETED = "completed"; FAILED = "failed"

class AgentTask:
    id: str
    type: AgentType
    priority: TaskPriority
    payload: dict
    company_id: str     # SEMPRE presente

class AgentResponse:
    success: bool
    result: Any
    error: str | None
    audit_trail_id: str  # sempre vinculado ao audit

class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResponse: ...
```

**Shim de compatibilidade:** `app/shared/agents/agent_types.py` re-exporta via `from app.agents.base_agent import *`

---

### 6.2 `app/shared/agents/tool_handler.py`
**Tamanho:** ~115 linhas | **Tipo:** Decorator de tool handler

**Responsabilidade:**
Decorator `@tool_handler(domain)` que substitui `@tool` do LangChain. Adiciona automaticamente: logging, error handling, audit trail, tenant context. Padrão canônico LIA.

**Interface:**
```python
def tool_handler(domain: str):
    """Decorator canônico para handlers de ferramentas LIA.
    
    Uso:
        @tool_handler("hiring_policy")
        async def validate_policy(job_id: str, company_id: str) -> dict:
            ...
    """
```

---

### 6.3 `app/shared/agents/crew_executor.py`
**Tamanho:** ~428 linhas | **Tipo:** Executor de crew

**Responsabilidade:**
Executa "crews" de sub-agentes — grupos de agentes especializados que colaboram para uma tarefa complexa (ex: crew de triagem = CVParser + Scoring + Ranking + FeedbackAgent).

---

### 6.4 `app/shared/agents/agent_bus.py`
**Tamanho:** ~333 linhas | **Tipo:** Message bus para agentes

**Responsabilidade:**
Comunicação assíncrona entre agentes via message bus. Evita acoplamento direto entre agentes — cada um publica eventos, outros assinam.

---

### 6.5 `app/shared/robustness/enhanced_registry.py`
**Tamanho:** ~319 linhas | **Tipo:** Registry com robustez

**Responsabilidade:**
Registry de agentes com `EnhancedAgentMixin` — adiciona retry, circuit breaker, logging, e health tracking a qualquer agente registrado. Usado pelos LangGraph ReAct agents ativos.

---

### 6.6 `app/shared/agents/langgraph_react_base.py`
**Tamanho:** ~estendido via mixin | **Tipo:** Base LangGraph

**Responsabilidade:**
Base class para todos os 12+ agentes ReAct. Herda compliance por padrão: PromptInjection Guard no input, Tenant Isolation via `require_company`, Observability via traces.

---

## Tema 7 — Orquestração & Roteamento

> **Objetivo:** Roteamento inteligente de mensagens para o agente correto, com fallback, cache e hierarquia de LLMs.

---

### 7.1 `app/orchestrator/main_orchestrator.py`
**Tamanho:** ~1.189 linhas | **Tipo:** Orquestrador central

**Responsabilidade:**
Ponto de entrada único para todas as mensagens de chat. Classifica intenção, seleciona agente, gerencia contexto multi-turno, aplica compliance antes de rotear.

**Fluxo:**
```
mensagem → FastRouter (intent) → CascadedRouter (domínio) → Agente → AuditLog → Resposta
```

---

### 7.2 `app/orchestrator/cascaded_router.py`
**Tamanho:** ~793 linhas | **Tipo:** Roteador em cascata

**Responsabilidade:**
Roteamento semântico de mensagens para domínio + agente correto. Implementa hierarquia: regras determinísticas → embedding similarity → LLM fallback. Cada nível só é chamado se o anterior não resolver com confiança suficiente.

---

### 7.3 `app/orchestrator/llm_cascade.py`
**Tamanho:** ~325 linhas | **Tipo:** Cascata de LLMs

**Responsabilidade:**
Fallback hierárquico entre provedores LLM: Claude Sonnet 4.5 (primário) → Claude Haiku (rápido/barato) → GPT-4 (fallback) → Gemini (multimodal). Seleciona automaticamente baseado em latência, custo e disponibilidade.

---

### 7.4 `app/orchestrator/policy_engine.py`
**Tamanho:** ~345 linhas | **Tipo:** Motor de políticas

**Responsabilidade:**
Aplica políticas de hiring configuradas pelo tenant antes de qualquer decisão automatizada. Integra com `PolicySetupAgent` e `hiring_policy` domain.

---

### 7.5 `app/orchestrator/task_planner.py`
**Tamanho:** ~236 linhas | **Tipo:** Planejador de tarefas

**Responsabilidade:**
Decompõe requests complexos em sub-tarefas distribuídas entre agentes especializados. Implementa DAG de dependências e paralelização quando possível.

---

### 7.6 `app/orchestrator/fast_router.py`
**Tamanho:** ~682 linhas | **Tipo:** Roteador rápido (Tier 0)

**Responsabilidade:**
Classificação ultra-rápida de intenção sem chamar LLM — baseada em regex, keywords, e embedding cache. Resolve ~60% dos requests sem custo de LLM.

---

### 7.7 `app/shared/cache/semantic_cache.py`
**Tamanho:** ~112 linhas | **Tipo:** Cache semântico

**Responsabilidade:**
Cache de respostas LLM baseado em similaridade semântica (não string exata). Queries semanticamente similares retornam resposta cacheada sem chamar o LLM.

---

### 7.8 `app/shared/memory/memory_resolver.py`
**Tamanho:** ~386 linhas | **Tipo:** Resolvedor de memória

**Responsabilidade:**
Gerencia contexto multi-turno por sessão de chat. Seleciona quais memórias injetar no contexto do LLM baseado em relevância para a query atual.

---

## Tema 8 — Provedores LLM (tenant-aware)

> **Objetivo:** Roteamento de LLM por tenant — cada empresa pode ter seu próprio provedor/modelo configurado.

---

### 8.1 `app/shared/llm/llm_factory.py`
**Tamanho:** ~544 linhas | **Tipo:** Factory canônica

**Responsabilidade:**
Cria instâncias de LLM configuradas por tenant. Suporta: Anthropic Claude, OpenAI GPT-4, Google Gemini, Deepseek, e modelos locais. Tenant pode ter BYOK (Bring Your Own Key).

**Interface:**
```python
class LLMFactory:
    async def get_provider_for_tenant(
        self,
        company_id: str,
        use_case: str = "general",        # "screening", "chat", "analysis"
        require_vision: bool = False,
        prefer_fast: bool = False,
    ) -> BaseLLM:
        """Retornar instância de LLM configurada para o tenant.
        
        NUNCA hardcodar provider. Sempre usar este método.
        """
    
    async def get_embedding_provider(self, company_id: str) -> Embeddings

# Singleton global
llm_factory = LLMFactory()
```

**Regra inviolável:** `provider="claude"` hardcoded é proibido. Sempre `llm_factory.get_provider_for_tenant(company_id)`.

---

### 8.2 `app/shared/llm/embedding_factory.py`
**Tamanho:** ~263 linhas | **Tipo:** Factory de embeddings

**Responsabilidade:**
Cria provedores de embedding configurados por tenant. Suporta: OpenAI Ada, Voyage AI, Cohere, e modelos locais via Ollama.

---

### 8.3 `app/shared/llm/voice_composite.py`
**Tamanho:** ~414 linhas | **Tipo:** Compositor de voz

**Responsabilidade:**
Orquestra pipeline de voz: STT (Deepgram) → LLM → TTS. Suporta OpenMic.ai para triagem por voz. Tenant-aware — cada empresa pode ter provedor de voz diferente.

---

### 8.4 `app/shared/llm/llm_provider.py`
**Tamanho:** ~111 linhas | **Tipo:** Abstração base

**Responsabilidade:**
Interface `BaseLLMProvider` que todos os provedores implementam. Permite swap de provider sem alterar código de negócio.

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[Message], **kwargs) -> LLMResponse: ...
    @abstractmethod
    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]: ...
    
    company_id: str  # sempre presente — isolamento por tenant
    model_name: str
    cost_per_1k_tokens: float
```

---

### 8.5 `app/shared/llm/tenant_llm_context.py`
**Tamanho:** ~229 linhas | **Tipo:** Contexto de LLM por tenant

**Responsabilidade:**
Gerencia configuração de LLM por tenant: modelo padrão, limites de uso, budget mensal, whitelist de features (BYOK, Layer 3, voice). Persiste no banco e cacheia em Redis.

---

## Tema 9 — Resiliência & Circuit Breaker

> **Objetivo:** Produção 24/7 com degradação graciosa — nunca travar quando LLM externo cai.

---

### 9.1 `app/shared/resilience/circuit_breaker.py`
**Tamanho:** ~1.060 linhas | **Tipo:** Circuit breaker canônico

**Responsabilidade:**
Implementação completa de circuit breaker para todos os serviços externos: LLM providers, APIs externas, banco de dados. Estados: CLOSED → OPEN → HALF-OPEN.

**Interface:**
```python
class CircuitBreaker:
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2,
    )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any
    def get_state(self) -> CircuitState
    def reset(self) -> None

# Registry global
circuit_breaker_registry: dict[str, CircuitBreaker]

# Endpoint admin
# GET /api/v1/admin/circuit-breakers → estado de todos os breakers
```

---

### 9.2 `app/shared/resilience/dlq_service.py`
**Tamanho:** ~326 linhas | **Tipo:** Dead Letter Queue

**Responsabilidade:**
Gerencia mensagens que falharam após todas as retentativas — persiste em DLQ para análise e replay manual. Integra com RabbitMQ DLX.

---

### 9.3 `app/shared/cache/cache_manager_service.py`
**Tamanho:** ~596 linhas | **Tipo:** Gerenciador de cache

**Responsabilidade:**
Cache manager multi-camada: L1 (in-memory LRU), L2 (Redis), L3 (PostgreSQL para dados de longa vida). Invalida automaticamente por tenant quando dados são atualizados.

---

### 9.4 `app/shared/stats/stats_manager.py`
**Tamanho:** ~217 linhas | **Tipo:** Gerenciador de estatísticas

**Responsabilidade:**
Coleta e agrega métricas de runtime para Prometheus. Expõe `/metrics` endpoint para Grafana. Métricas por tenant, por agente, por modelo LLM.

---

## Tema 10 — Multi-tenancy & Tool Permissions

> **Objetivo:** Isolamento total entre tenants + controle granular de quais ferramentas cada agente pode usar.

---

### 10.1 `app/shared/middleware/tenant_guard.py`
*(listado também no Tema 4 — referência cruzada)*

---

### 10.2 `app/shared/agents/tool_handler.py`
*(listado também no Tema 6 — referência cruzada)*

---

### 10.3 `app/tools/tool_permissions_loader.py`
**Tamanho:** ~288 linhas | **Tipo:** Loader de permissões de ferramentas

**Responsabilidade:**
Carrega permissões de ferramentas do arquivo YAML de configuração e expõe API para verificar se um agente pode usar uma ferramenta específica em um contexto.

**Interface:**
```python
class ToolPermissionsLoader:
    def load_permissions(self, config_path: str) -> ToolPermissionConfig
    def is_tool_allowed(self, tool_name: str, agent_type: str, scope: str) -> bool
    def get_tools_for_agent(self, agent_type: str, scope: str) -> list[str]
```

**Arquivo de configuração:** `app/tools/tools_permissions.yaml`

---

### 10.4 `app/tools/scope_config.py`
**Tamanho:** ~304 linhas | **Tipo:** Configuração de escopo

**Responsabilidade:**
Define quais ferramentas estão disponíveis em cada escopo (chat público, admin, internal, screening). Funções `get_tools_for_scope()` e `is_tool_allowed_in_scope()`.

---

### 10.5 `app/tools/tool_registry_loader.py`
**Tamanho:** ~156 linhas | **Tipo:** Loader de registries

**Responsabilidade:**
Carrega e valida tool registries de todos os domínios. Garante que nenhum `ToolDefinition` faltando campos obrigatórios seja registrado.

---

### 10.6 `app/domains/hiring_policy/agents/policy_tool_registry.py`
**Tamanho:** ~1.267 linhas | **Tipo:** Referência de implementação

**Responsabilidade:**
Registry canônico de referência com 13 ferramentas — usa o padrão completo `@tool_handler + ToolDefinition` com FairnessGuard integrado. **Usar como template** para novos tool registries.

**Padrão:**
```python
from app.shared.agents.tool_handler import tool_handler
from app.shared.compliance.fairness_guard import FairnessGuard

@tool_handler("hiring_policy")
async def validate_hiring_criteria(
    job_id: str,
    criteria: list[str],
    company_id: str,
) -> dict:
    fg = FairnessGuard()
    result = await fg.check(" ".join(criteria), action_type="hiring_criteria")
    if result.is_blocked:
        return {"blocked": True, "reason": result.educational_message}
    # ... lógica de negócio

HIRING_POLICY_TOOL_DEFINITIONS = [
    ToolDefinition(
        name="validate_hiring_criteria",
        description="Valida se os critérios de contratação atendem às diretrizes de compliance",
        handler=validate_hiring_criteria,
        parameters={...},  # JSON Schema
    ),
    # ... 12 outros
]
```

---

## Tema 11 — Aprendizado & Inteligência

> **Objetivo:** Melhoria contínua baseada em feedback — modelos aprendem com resultados reais.

---

### 11.1 `app/shared/learning/learning_loop_service.py`
**Tamanho:** ~1.133 linhas | **Tipo:** Loop de aprendizado canônico

**Responsabilidade:**
Coleta feedback de decisões (candidato contratado? avaliação correta?), atualiza pesos de scoring, e melhora prompts baseado em outcomes reais. Multi-tenant — cada empresa tem seu próprio modelo adaptado.

**Interface:**
```python
class LearningLoopService:
    async def record_outcome(
        self,
        decision_id: str,
        outcome: DecisionOutcome,  # "hired", "rejected_correct", "false_positive", etc.
        company_id: str,
    ) -> None
    
    async def get_performance_metrics(self, company_id: str) -> LearningMetrics
    async def trigger_model_update(self, company_id: str) -> UpdateResult
```

---

### 11.2 `app/shared/ab_testing.py`
**Tamanho:** ~232 linhas | **Tipo:** A/B testing de prompts (in-memory)

**Responsabilidade:**
Framework de experimentos para variantes de prompts. Distribui requests entre variantes e mede qual performa melhor (baseado em métricas configuráveis). In-memory — para experimentos rápidos.

**Contexto:** prompts e variantes de agentes (não email templates).

```python
class ExperimentManager:
    def create_experiment(self, name: str, variants: list[PromptVariant]) -> Experiment
    def get_variant(self, experiment_id: str, user_id: str) -> PromptVariant
    def record_conversion(self, experiment_id: str, variant_id: str) -> None
    def get_results(self, experiment_id: str) -> ExperimentResults
```

---

### 11.3 `app/shared/learning/ab_testing_service.py`
**Tamanho:** ~340 linhas | **Tipo:** A/B testing de templates (DB-backed)

**Responsabilidade:**
A/B testing persistente para templates de email/comunicação. Guarda resultados no banco para análise histórica. Diferente do `ab_testing.py` que é in-memory para prompts.

**Contexto:** templates de email e comunicação com candidatos (não prompts de agentes).

---

### 11.4 `app/shared/learning/template_learning_service.py`
**Tamanho:** ~401 linhas | **Tipo:** Aprendizado de templates (job creation)

**Responsabilidade:**
Aprende quais templates de vagas performam melhor (mais candidatos qualificados) e sugere melhorias automáticas. **Contexto:** criação de vagas.

---

### 11.5 `app/shared/intelligence/template_learning/template_learning_service.py`
**Tamanho:** ~176 linhas | **Tipo:** Aprendizado de templates (email)

**Responsabilidade:**
Aprende quais templates de email têm melhor taxa de abertura/resposta. **Contexto:** comunicação com candidatos. Classe renomeada para `EmailTemplateLearningService` para distinguir do template de vagas.

---

### 11.6 `app/domains/cv_screening/services/seniority_resolver.py`
**Tamanho:** ~882 linhas | **Tipo:** Resolvedor de senioridade (canônico)

**Responsabilidade:**
Determina nível de senioridade de candidato usando 5 sinais: tempo de experiência, complexidade de projetos, tamanho de equipe gerenciada, stack técnica, e responsabilidades declaradas. Sistema de pesos configurável com conflict resolution quando sinais divergem.

---

## Tema 12 — Comunicação & Eventos

> **Objetivo:** Mensageria assíncrona confiável — desacoplar produtores de consumidores, garantir delivery.

---

### 12.1 `app/shared/messaging/broker_interface.py`
**Tamanho:** ~334 linhas | **Tipo:** Interface de broker

**Responsabilidade:**
Abstração sobre RabbitMQ — permite trocar de broker sem alterar código de negócio. Implementa: publish, subscribe, acknowledge, reject, dead-letter.

```python
class BrokerInterface(ABC):
    @abstractmethod
    async def publish(self, exchange: str, routing_key: str, message: dict) -> None: ...
    @abstractmethod
    async def subscribe(self, queue: str, handler: Callable) -> None: ...
    @abstractmethod
    async def acknowledge(self, delivery_tag: int) -> None: ...
```

---

### 12.2 `app/shared/messaging/rabbitmq_producer.py`
**Tamanho:** ~185 linhas | **Tipo:** Producer RabbitMQ

**Responsabilidade:**
Implementação concreta de `BrokerInterface` para RabbitMQ. Inclui: connection pooling, retry automático, serialização JSON, headers de tenant.

---

### 12.3 `app/shared/events/unified_event_publisher.py`
**Tamanho:** ~112 linhas | **Tipo:** Publisher unificado

**Responsabilidade:**
Ponto único para publicar eventos de domínio. Garante que todos os eventos incluam `company_id`, `timestamp`, e `trace_id` como campos obrigatórios.

```python
class UnifiedEventPublisher:
    async def publish(
        self,
        event_type: str,
        payload: dict,
        company_id: str,   # obrigatório
        trace_id: str | None = None,
    ) -> None
```

---

### 12.4 `app/shared/events/platform_events.py`
**Tamanho:** ~188 linhas | **Tipo:** Catálogo de eventos

**Responsabilidade:**
Enum e schemas de todos os eventos da plataforma. Fonte de verdade para nomes de eventos — evita strings mágicas dispersas.

```python
class PlatformEvent(Enum):
    CANDIDATE_APPLIED = "candidate.applied"
    CANDIDATE_SCREENED = "candidate.screened"
    CANDIDATE_RANKED = "candidate.ranked"
    JOB_PUBLISHED = "job.published"
    BIAS_ALERT = "bias.alert"
    FAIRNESS_BLOCKED = "fairness.blocked"
    DRIFT_DETECTED = "model.drift_detected"
    # ... 30+ eventos
```

---

### 12.5 `app/shared/messaging/rails_crud_consumer.py`
**Tamanho:** ~170 linhas | **Tipo:** Consumer Rails (CRUD bridge)

**Responsabilidade:**
Consumer RabbitMQ que recebe eventos do sistema Rails (ATS legado) e sincroniza com o banco PostgreSQL do LIA. Bridge entre o mundo Rails (CRUD) e o mundo FastAPI (IA).

---

## Apêndice — Arquivos de Configuração Canônicos

| Arquivo | Tipo | Responsabilidade |
|---------|------|-----------------|
| `app/tools/tools_permissions.yaml` | YAML | Permissões de ferramentas por agente e escopo |
| `app/shared/agents/domain_mappings.py` | Python | Mapeamento intent → domínio → agente |
| `app/shared/agents/domain_routing.yaml` | YAML | Configuração de roteamento de domínios |
| `app/core/config.py` | Python | Configuração central (env vars, feature flags) |
| `app/core/settings.py` | Pydantic | Settings validadas com defaults seguros |
| `scripts/check_c3b_compliance.py` | Lint (G7) | Sensor: C3B em todo agente |
| `scripts/check_tenant_isolation.py` | Lint (G6) | Sensor: require_company em todo endpoint |
| `scripts/check_fairness_consolidation.py` | Lint (G5) | Sensor: FairnessGuard em serviços de scoring |
| `scripts/check_bulk_actions_compliance.py` | Lint (G8) | Sensor: C3B + audit em bulk_* |
| `scripts/check_graph_node_audit.py` | Lint (G9) | Sensor: audit em nós críticos de graphs |

---

## Apêndice — ADRs Arquiteturais Relevantes

| ADR | Arquivo | Decisão |
|-----|---------|---------|
| ADR-001 | `docs/architecture/ADR-001-langchain-vs-langgraph.md` | LangGraph para flows stateful, LangChain apenas para chains simples |
| ADR-002 | `docs/architecture/ADR-002-stategraph-vs-react.md` | StateGraph apenas para flows com estado explícito (Wizard, WSI, Interview) |
| ADR-003 | `docs/architecture/ADR-003-fairness-3-layers.md` | FairnessGuard 3 camadas — Layer 3 opt-in por razões de latência |
| ADR-004 | `docs/architecture/ADR-repo-bifurcation.md` | Bifurcações propositais: auth/user_repository vs company/user_repository |
| ADR-005 | `docs/architecture/ADR-005-apps-microservices.md` | apps/ microservices preparados mas não deployados — monolito por ora |

---

*Lista gerada em 2026-04-23 | 52 canônicos identificados em 12 temas | Atualizar após cada sprint que introduzir novos canônicos.*

---

## Thematic Operational Docs (31 receitas executáveis)

Para cada tema abaixo, existe um doc completo em `themes/` com código verificado, lógica IN/OUT, instruções para Claude Code/Cursor, checklists P0/P1/P2 e testes obrigatórios.

**Índice master:** `themes/README.md` (Mac: `/Users/paulomoraes/Documents/Python/themes/README.md`)

### Compliance Layer (C1-C8)

| Doc | Localização Mac |
|-----|----------------|
| C1 Fairness & Anti-Discrimination | `themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md` |
| C2 LGPD PII & Data Minimization | `themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md` |
| C3 LGPD Consent & Data Subject Rights | `themes/compliance/C3_LGPD_CONSENT_AND_DATA_SUBJECT.md` |
| C4 LGPD Art.20 Right to Contest | `themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md` |
| C5 Multi-tenancy & Isolation | `themes/compliance/C5_MULTI_TENANCY_AND_ISOLATION.md` |
| C6 Prompt Injection & Encryption | `themes/compliance/C6_PROMPT_INJECTION_AND_ENCRYPTION.md` |
| C7 Audit Trail & Compliance Lint | `themes/compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md` |
| C8 Policy Engine & Governance | `themes/compliance/C8_POLICY_ENGINE_AND_GOVERNANCE.md` |

### Infrastructure Layer (I1-I11) | Persona (P1-P4) | Resilience (R1-R4) | Agent Studio (AS1) | Operational (O1-O3)

| Doc | Localização Mac |
|-----|----------------|
| I1-I11 (Infrastructure) | `themes/infrastructure/I{1-11}_*.md` |
| P1-P4 (Persona) | `themes/persona/P{1-4}_*.md` |
| R1-R4 (Resilience) | `themes/resilience/R{1-4}_*.md` |
| AS1 (Custom Agents) | `themes/agent_studio/AS1_CUSTOM_AGENTS.md` |
| O1-O3 (Operational) | `themes/operational/O{1-3}_*.md` |

**Replit:** todos em `docs/reconstruction-guides/themes/` (sincronizados via SCP + MD5 verificado)
