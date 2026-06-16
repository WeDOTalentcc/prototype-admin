# FAIRNESS_LGPD_AUDIT.md — Auditoria de Fairness, Bias e LGPD
> P06 · Fase 2 · Data: 2026-04-14 · Plataforma: WeDOTalent / LIA

---

## Sumário Executivo

Esta auditoria cobre quatro dimensões críticas da plataforma WeDOTalent/LIA: implementação de fairness, detecção e prevenção de bias, conformidade técnica com a LGPD e governança regulatória. A análise abrangeu a camada de IA em Python (`lia-agent-system`), o frontend Next.js (`plataforma-lia`) e o backend Rails (`ats-api-copia`). O escopo normativo inclui LGPD (Lei 13.709/2018), EU AI Act 2024/1689 (Annex III — sistemas de alto risco para recrutamento), NYC Local Law 144 (2021) e diretrizes EEOC.

A postura de risco geral da plataforma é **Alta** em Fairness e Bias, e **Crítica** em LGPD e Governança Regulatória. Os achados mais graves concentram-se em: (1) ausência de DPAs formais com Anthropic, OpenAI e Google enquanto dados biométricos (áudio de candidatos) cruzam fronteiras internacionais sem base legal LGPD Art. 33; (2) embeddings pgvector que persistem após solicitação de eliminação de dados, violando o Art. 18 III da LGPD; (3) candidatos afetados por decisões automatizadas sem acesso a interface para exercer revisão humana (Art. 20); (4) ausência total de RIPD/DPIA para processamento de alto risco; e (5) critérios subjetivos representando 45% do score de análise de candidatos em `analysis.yaml`, configurando vetor direto de discriminação algorítmica.

Os achados transversais mais relevantes são: o flag `LIA_DISABLE_C3B=1` que desabilita silenciosamente todas as proteções de fairness sem controle de acesso; a ausência de disclosure estruturado ao candidato antes da triagem WSI sobre o uso de IA; e a falta de persistência dos ajustes de calibração de recrutadores, tornando impossível auditar retroativamente padrões de viés. Esses três achados, combinados, representam um cenário em que mecanismos de proteção existentes podem ser contornados sem rastro auditável.

O ponto mais positivo da plataforma é a maturidade da arquitetura de fairness e compliance já construída: o `FairnessGuard` com três camadas e nove categorias de discriminação (PT-BR e EN), o `AuditService` com `PROTECTED_CRITERIA` explícitos e retenção de 730 dias, a infraestrutura completa de Art. 20 no backend, o HITL via LangGraph em três fluxos críticos, e o sistema de bias audit com Four-Fifths Rule alinhado ao NYC LL144 são evidências de investimento real e diferenciado em IA responsável. O desafio principal é fechar as lacunas entre o que foi construído no backend e o que é acessível e aplicado ponta-a-ponta.

---

## Índice de Conformidade P06

| Dimensão | Status | Risco Geral |
|----------|--------|-------------|
| 1. Fairness — Implementação | Parcial | Alto |
| 2. Bias — Detecção e Prevenção | Parcial | Alto |
| 3. LGPD — Conformidade Técnica | Parcial | Crítico |
| 4. Compliance Regulatório | Ausente/Parcial | Crítico |

---

## Achados Críticos e Altos — Consolidados (P0/P1)

**P0 — Bloqueiam Conformidade Legal**

1. [BIAS] `analysis.yaml` — "Fit de Personalidade" (25%) + "Alinhamento Cultural" (20%) = 45% do score em critérios subjetivos sem ancoragem em requisitos da vaga. Proxy direto para raça, classe e gênero. Arquivo: `app/prompts/domains/analysis.yaml:6`. Impacto: discriminação algorítmica estrutural em todas as triagens.
2. [BIAS] `analysis.yaml` envia `Nome: {candidate_name}` ao LLM — vetor de viés étnico/socioeconômico documentado. Arquivo: `app/prompts/domains/analysis.yaml:19`. Impacto: scores influenciados por conotação racial/social do nome.
3. [FAIRNESS] `LIA_DISABLE_C3B=1` desabilita todas as proteções de fairness silenciosamente — sem controle de acesso, sem audit log, sem alerta. Arquivo: `app/shared/compliance/c3b_layer.py:13`. Impacto: qualquer operador com acesso ao ambiente pode contornar todas as proteções de compliance.
4. [FAIRNESS] FairnessGuard L3 (semântico via LLM) desabilitado nos setores `varejo` e `logistica` — os domínios com maior incidência de discriminação por aparência, deficiência e gênero. Arquivo: `fairness_guard.py:725-843` + `PLATFORM_MAP.md:1057`. Impacto: discriminação semântica não detectada nos setores de maior risco.
5. [LGPD] DPAs ausentes com Anthropic, OpenAI e Google — áudio de candidatos (dados biométricos funcionais) cruzam fronteiras internacionais via OpenAI Whisper sem base legal LGPD Art. 33. Arquivo: `app/domains/voice/services/voice_service.py:52`. Impacto: infração Art. 33 LGPD com risco de multa e suspensão do tratamento.
6. [LGPD] Embeddings pgvector (biométricos funcionais) NÃO são deletados no fluxo de eliminação LGPD — `lgpd_cleanup_service.py` não cobre tabelas de vetores. Arquivo: `app/domains/lgpd/services/lgpd_cleanup_service.py`. Impacto: violação do direito ao apagamento (Art. 18 III LGPD) — infrações continuadas.
7. [LGPD] TLS não confirmado na conexão asyncpg com PostgreSQL — `sslmode` removido pelo driver sem `connect_args={"ssl": ...}` explícito. Arquivo: `libs/config/lia_config/database.py:39-44`. Impacto: dados pessoais em trânsito sem criptografia confirmada (Art. 46 LGPD).
8. [GOVERNANCE] Candidato não tem interface para exercer revisão humana de decisão automatizada (LGPD Art. 20) — backend existe, UI voltada ao candidato ausente. Arquivo: `lia-agent-system/app/api/v1/lgpd_compliance.py:468-511`. Impacto: direito fundamental irrecuperável bloqueado na camada de UX.
9. [GOVERNANCE] RIPD/DPIA inexistente — nenhum arquivo encontrado no repositório. Impacto: obrigação LGPD Art. 38 e EU AI Act Art. 9 descumprida para sistema classificado como alto risco.
10. [GOVERNANCE] Disclosure de IA ao candidato insuficiente — ausência de tela de consentimento informado antes da triagem WSI declarando uso de IA, impacto em decisão de contratação e direito de revisão humana. Arquivo: `plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx:123`. Impacto: consentimento informado comprometido; candidatos afetados por IA sem ciência.

**P1 — Alto Impacto em Conformidade**

11. [BIAS] Recruiter calibration loop propaga viés sem auditoria demográfica e sem persistência em banco — `_calibration_adjustments` é in-memory, zerado a cada restart. Arquivo: `app/domains/cv_screening/services/rubric_evaluation_service.py:226-289`. Impacto: impossibilidade de auditar retroativamente padrões de viés de recrutadores individuais.
12. [BIAS] Ausência de testes de paridade demográfica sintética (pares de CVs idênticos exceto atributo protegido) — padrão exigido pelo NYC LL144. Arquivo ausente: `tests/bias/test_demographic_parity.py`. Impacto: conformidade com NYC Local Law 144 não demonstrável.
13. [BIAS] Ausência de avaliação WEAT/SEAT nos embeddings OpenAI/Gemini para português brasileiro — zero ocorrências no codebase. Impacto: viés histórico nos embeddings (associações profissão-gênero/etnia) não quantificado nem mitigado.
14. [LGPD] Criptografia Fernet de CPF/email em campo — testes existem mas implementação de produção não confirmada como deployada. Arquivo: `app/models/encrypted_field_mixin` (não confirmado em produção). Impacto: PII sensível possivelmente não criptografado at rest no PostgreSQL.
15. [LGPD] DPO não confirmado ativo; sem contato público publicado — LGPD Art. 41 §1º exige publicação. Arquivo: `app/api/v1/lgpd_compliance.py` (DPO Registry existe, DPO real não confirmado). Impacto: infração Art. 41 §1º com exposição regulatória direta.
16. [GOVERNANCE] Score de fallback padrão `3.0` gravado como decisão real sem flag `requires_human_review=True`. Arquivo: `handlers_screening.py:291,308`. Impacto: candidatos prejudicados por falhas técnicas da IA sem sinalização ou revisão.
17. [LGPD] Celery retention job com `dry_run=True` por default — não há confirmação de que produção roda com `dry_run=False`. Arquivo: `app/domains/lgpd/services/lgpd_cleanup_service.py`. Impacto: deleções de dados podem não estar ocorrendo em produção, retendo dados além do prazo legal.

---

## 1. FAIRNESS — IMPLEMENTAÇÃO REAL

### 1A. Métricas de Fairness Implementadas

**Achado 1 — Four-Fifths Rule (Disparate Impact) — IMPLEMENTADO**

- **Status:** Implementado
- **Risco:** Médio
- **Evidência:** `app/shared/services/bias_audit_service.py:1-130` — O `BiasAuditService` calcula `adverse_impact_ratio = min_taxa / max_taxa` com limiar EEOC de 0.80 em 4 dimensões: gender, age_group, disability, region. Inclui teste chi-quadrado de Pearson (com fallback sem scipy). O `FOUR_FIFTHS_THRESHOLD = 0.80` está alinhado com o golden dataset de testes.
- **Lacuna:** Não há cálculo de **Demographic Parity** nem **Equal Opportunity** (TPR equalizado por grupo) — apenas adverse impact de aprovações agregadas. Vieses que se manifestam em taxas de falso-negativo por grupo protegido passariam invisíveis.
- **Recomendação:** Adicionar métricas complementares ao `BiasAuditReport`: `equal_opportunity_ratio` (TPR por grupo), `predictive_parity` (precision por grupo). Prioridade: Alta para dimensão age_group, que tem a menor cobertura de dados (candidatos raramente informam data de nascimento).

---

**Achado 2 — RAG Gender Ratio — IMPLEMENTADO (stub)**

- **Status:** Parcial
- **Risco:** Médio
- **Evidência:** `app/domains/ai/services/rag_pipeline_service.py:61,216` — `_FAIRNESS_MAX_SINGLE_GENDER_RATIO = 0.70`. A função `_check_fairness()` verifica se um único gênero representa mais de 70% do top-10 de resultados de busca. Retorna `True` (OK) quando há menos de 3 candidatos com gênero informado — lógica de permissividade quando dados são escassos.
- **Lacuna crítica:** O campo `gender` nos candidatos **não é obrigatório** e a escassez de dados ativa o caminho permissivo (`return True` em `len(genders) < 3`). Na prática, a maioria dos CVs não inclui gênero declarado. O controle só funciona se os dados de gênero existirem. Além disso, `_check_fairness` apenas **loga warning** — não re-rankeia os resultados para balancear a representação.
- **Recomendação:** (a) Implementar re-ranking ativo quando o limiar é violado, não apenas logging. (b) Documentar a limitação de cobertura de dados no dashboard de compliance. (c) Explorar inferência probabilística de gênero baseada em nome com disclaimer de privacidade — ou solicitar autodeclaração no onboarding do candidato.

---

**Achado 3 — FairnessGuard 3 Camadas — IMPLEMENTADO com gaps no L3**

- **Status:** Parcial
- **Risco:** Alto
- **Evidência:**
  - L1 (regex explícita): `fairness_guard.py:136-400` — `DISCRIMINATORY_CATEGORIES` cobre 9 categorias: genero, raca_etnia, idade, deficiencia, estado_civil_gravidez, saude_doenca, filiacao_sindical, antecedentes_criminais, aparencia_fisica. Regex compiladas com normalização Unicode.
  - L2 (soft warnings/termos implícitos): `fairness_guard.py:30-116` — `IMPLICIT_BIAS_TERMS` (PT) + `IMPLICIT_BIAS_TERMS_EN` (EN) cobrem proxy socioeconômico, etário, religioso, aparência. Total ~40 termos.
  - L3 (semântica LLM): `fairness_guard.py:725-843` — Habilitado via `FAIRNESS_LAYER3_ENABLED` (setting global) **E** `sector_config.get("fairness_layer3_enabled", False)` via `ALPHA1_SECTOR_RULES`. **Setores `varejo` e `logistica` NÃO têm L3 habilitado** (confirmado: `PLATFORM_MAP.md:1057`). Apenas `saude` e `rpo` têm L3.
- **Gap crítico:** Setores de varejo e logística — que tipicamente têm maior incidência de discriminação por aparência, deficiência e gênero em cargos operacionais — ficam sem a camada semântica mais sofisticada.
- **Recomendação:** Habilitar L3 em todos os setores com `high_impact: True`. O custo incremental de latência (~200-400ms por chamada LLM) é justificado para decisões de alto risco. Criar flag `fairness_layer3_enabled: true` como padrão, com opt-out somente para domínios de baixo risco documentados.

---

**Achado 4 — WSI Score: "Alinhamento Cultural" como critério de avaliação — RISCO LATENTE**

- **Status:** Parcial
- **Risco:** Alto
- **Evidência:**
  - `app/prompts/domains/wsi_evaluation.yaml:49` — Bloco 6 do WSI: "Alinhamento Cultural (5%)"
  - `app/prompts/domains/cv_screening.yaml:45` — Inclui "alinhamento cultural" nos 7 blocos WSI
  - `app/prompts/domains/analysis.yaml:6` — "Alinhamento Cultural (20%)" com peso 4x maior que no WSI principal
  - `app/prompts/shared/lia_persona.yaml:157` — "Fit cultural | Alinhamento do candidato com a cultura organizacional"
- **Problema:** "Alinhamento cultural" e "fit cultural" são reconhecidos internacionalmente como vetores de homofilia organizacional — tendem a favorecer candidatos similares ao grupo dominante (mesmo gênero, etnia, classe social, formação). O prompt `analysis.yaml` atribui **25% do score total ao "Fit de Personalidade"** (Big Five com arquétipos) e **20% ao "Alinhamento Cultural"** — totalizando 45% do score em dimensões subjetivas sem ancoragem clara em requisitos da vaga. O `wsi_evaluation.yaml` restringe Big Five a "instrumentos validados", mas `analysis.yaml` não tem essa restrição.
- **Recomendação:** (a) No `analysis.yaml`, reduzir peso de "fit_personalidade" e "alinhamento_cultural" para no máximo 10% combinados, substituídos por critérios de competência verificáveis. (b) Definir operacionalmente o que constitui "alinhamento cultural" — mapear a comportamentos e valores específicos descritos na vaga, não a "semelhança" com a equipe atual. (c) Exigir FairnessGuard check antes de gerar score em `analysis.yaml`, como já fazem `cv_screening.yaml` e `wsi_evaluation.yaml`.

---

**Achado 5 — Calibração de Score por Recrutador (Feedback Loop de Viés)**

- **Status:** Ausente (controle de viés)
- **Risco:** Alto
- **Evidência:** `app/domains/cv_screening/services/rubric_evaluation_service.py:226-289` — O `RubricEvaluationService` aceita `recruiter_adjusted_score` e calcula `delta = adjusted - original`, atualizando `_calibration_adjustments` (média corrida). Este delta é aplicado em avaliações futuras da mesma vaga via `calibration_adjustment`.
- **Problema:** Se um recrutador consistentemente eleva scores de candidatos de um grupo demográfico e reduz de outro (viés consciente ou inconsciente), esse padrão é **amplificado e perpetuado** pelo mecanismo de calibração. Não há auditoria do delta por grupo protegido, nem alerta quando o padrão de ajuste é demograficamente correlacionado.
- **Recomendação:** (a) Registrar no `AuditLog` cada `recruiter_adjusted_score` com `candidate_id` e `delta`. (b) No `BiasAuditService`, cruzar os deltas de calibração com dados demográficos para detectar viés sistêmico do recrutador. (c) Gerar alerta automático quando a média de delta para um grupo protegido difere estatisticamente da média geral (limiar sugerido: ±10 pontos, p<0.05).

---

### 1B. Mitigação de Bias — Pipeline de Tomada de Decisão

**Achado 6 — C3B Layer: Bypass via variável de ambiente**

- **Status:** Implementado com risco
- **Risco:** Alto
- **Evidência:** `app/shared/compliance/c3b_layer.py:13` — `_C3B_DISABLED = os.environ.get("LIA_DISABLE_C3B", "0") == "1"`. Quando esta variável está ativa, **toda a camada de compliance é ignorada**: PII strip, FairnessGuard L3, FactChecker e AuditService.
- **Lacuna:** Não há controle de acesso para ativar `LIA_DISABLE_C3B`. Qualquer operador com acesso ao ambiente pode desabilitar silenciosamente todas as proteções de fairness. Não há logging do estado do flag, nem alerta quando ativado.
- **Recomendação:** (a) Adicionar logging obrigatório ao inicializar com `LIA_DISABLE_C3B=1`: `logger.critical("[C3b] COMPLIANCE LAYER DISABLED via LIA_DISABLE_C3B — fairness checks inactive")`. (b) Registrar o evento no AuditService. (c) Exigir autenticação de segundo fator ou aprovação de segundo operador para ativar o flag em produção. (d) Considerar remover o flag de produção e mantê-lo apenas para testes de integração.

---

**Achado 7 — Supervisão Humana Obrigatória em Zona de Fronteira**

- **Status:** Implementado
- **Risco:** Baixo
- **Evidência:**
  - `app/prompts/domains/cv_screening.yaml:behavioral_rules` — "Recomendar revisão humana quando score estiver na zona de fronteira (60-70%)"
  - `app/prompts/domains/wsi_evaluation.yaml:behavioral_rules` — "Score na zona de fronteira (60-70%) requer flag de revisão humana obrigatória"
  - `app/domains/cv_screening/agents/pipeline_system_prompt.py:198-220` — FAIRNESS_AND_COMPLIANCE rules: rejeições nunca são automáticas, exigem confirmação do recrutador; alerta para padrão sistemático de rejeição de grupo demográfico.
- **Recomendação:** Verificar que o `AuditLog` captura `human_review_required=True` para todos os casos de fronteira e que há relatório de acompanhamento de revisões pendentes.

---

### 1C. Auditabilidade e Rastreabilidade

**Achado 8 — AuditService: Cobertura e `PROTECTED_CRITERIA`**

- **Status:** Implementado
- **Risco:** Médio
- **Evidência:** `app/shared/compliance/audit_service.py:34-47` — `PROTECTED_CRITERIA` lista explicitamente: age, gender, ethnicity, marital_status, photo, institution, address, religion, disability, cv_gaps. O campo `criteria_ignored` do log registra explicitamente os critérios protegidos que foram ignorados (anti-bias). Retenção por 730 dias (score/approve/reject).
- **Lacuna:** O AuditService é chamado via `Depends(get_audit_service)` em handlers de automação, mas a cobertura em chamadas diretas ao `FairnessGuard` (fora do C3B layer) não é garantida. Em `c3b_layer.py:post_compliance`, o log é feito mas pode ser silenciado por `except Exception: logger.debug(...)` — falhas silenciosas no logging de compliance são problemáticas.
- **Recomendação:** Substituir o `except Exception: logger.debug` no bloco de AuditService por `logger.error` com re-raise condicional, ou ao menos garantir que falhas de auditoria gerem alerta em sistema de monitoramento (ex: Sentry/DataDog).

---

**Achado 9 — Relatório Exportável de Fairness (NYC LL 144 / EU AI Act)**

- **Status:** Implementado
- **Risco:** Baixo
- **Evidência:** `app/api/v1/admin_compliance_fairness.py:1-80` — Endpoint `GET /admin/compliance/fairness/report` gera relatório exportável em JSON/CSV com assinatura HMAC-SHA256. Referencia explicitamente NYC Local Law 144 e EU AI Act Art. 13.
- **Lacuna:** `_sign_payload` retorna `"unsigned"` quando `REPORT_SIGNING_KEY` não está configurado — com logging de warning, não error. Em ambiente onde a chave não está setada, relatórios não têm valor forense.
- **Recomendação:** Tratar ausência de `REPORT_SIGNING_KEY` como erro em produção (raise exception ou recusar exportação). Documentar no runbook de deployment que a variável é obrigatória em ambientes regulatórios.

---

## 2. BIAS — DETECÇÃO E PREVENÇÃO

### 2A. Fontes de Bias no Pipeline de Recrutamento

**Achado 10 — Nome do Candidato Visível no Prompt de Análise**

- **Status:** Ausente (mitigação)
- **Risco:** Alto
- **Evidência:** `app/prompts/domains/analysis.yaml:19` — O template inclui `Nome: {candidate_name}` como campo explícito enviado ao LLM para análise de score. Pesquisa extensiva (Bertrand & Mullainathan 2004; estudos brasileiros análogos) demonstra que nomes com conotação étnica ou socioeconômica influenciam decisões de recrutadores humanos e modelos de linguagem.
- **Contraste:** Os prompts `cv_screening.yaml` e `wsi_evaluation.yaml` instruem explicitamente a ignorar nome, mas o `analysis.yaml` envia o nome como campo estruturado no template, criando uma contradição.
- **Recomendação:** No `analysis.yaml`, remover `Nome: {candidate_name}` do template de prompt. Substituir por `Candidato: [ANONIMIZADO]` ou usar um ID sequencial. O nome deve ser re-associado ao resultado apenas após o scoring, na camada de apresentação.

---

**Achado 11 — Localização do Candidato Visível no Prompt de Análise**

- **Status:** Ausente (mitigação)
- **Risco:** Médio
- **Evidência:** `app/prompts/domains/analysis.yaml:20` — Template inclui `Localização: {candidate_location}`. Localização é quasi-identificador LGPD (Art. 12) e proxy socioeconômico. A própria FairnessGuard L2 bloqueia filtros por "periferia", "zona rural", "subúrbio" — mas a localização é enviada ao LLM antes dessa verificação no fluxo `analysis.py`.
- **Recomendação:** No `analysis.yaml`, remover `Localização: {candidate_location}` do template ou convertê-la a nível de granularidade (ex: "estado" ou "região") antes de enviar ao LLM.

---

**Achado 12 — Empresa Atual do Candidato Visível no Prompt**

- **Status:** Ausente (mitigação)
- **Risco:** Médio
- **Evidência:** `app/prompts/domains/analysis.yaml:22` — Template inclui `Empresa: {candidate_company}`. Nome da empresa empregadora atual pode ser proxy de classe social, etnia regional ou nível econômico.
- **Recomendação:** Substituir por campo de setor/indústria, não empresa específica, no template de análise.

---

**Achado 13 — Bias de Confirmação via Recruiter Calibration (vide Achado 5)**

Já detalhado em 1B/Achado 5. O risco adicional aqui é que o mecanismo de calibração é **in-memory** (`_calibration_adjustments: dict`), não persistido em banco de dados. Reinícios da aplicação zeram o histórico de ajustes, tornando impossível auditar retroativamente padrões de viés de recrutadores individuais.

- **Status:** Ausente (persistência de auditoria)
- **Risco:** Alto
- **Recomendação:** Persistir cada `recruiter_adjusted_score` com `recruiter_id`, `candidate_id`, `original_score`, `adjusted_score`, `delta`, `job_id` e timestamp em tabela dedicada (ex: `recruiter_score_adjustments`).

---

**Achado 14 — Bias de Ancoragem (Ordem de Apresentação no Ranking)**

- **Status:** Ausente (controle)
- **Risco:** Médio
- **Evidência:** `app/domains/ai/services/rag_pipeline_service.py` — O RAG retorna candidatos ordenados por `hybrid_score` (BM25 + semântico). A interface de pipeline apresenta candidatos nessa ordem. Estudos de UX em ATS mostram que candidatos apresentados primeiro recebem mais atenção e são mais frequentemente aprovados, independentemente de seu score.
- **Recomendação:** Para triagens em lote, implementar opção de randomização controlada da ordem de apresentação (preservando grupos de score similares) para reduzir efeito de ancoragem.

---

**Achado 15 — Proxy de Idade via Ano de Formatura**

- **Status:** Implementado (mitigação documental)
- **Risco:** Médio
- **Evidência:** `PLATFORM_MAP.md:751` — "Quasi-identificadores (LGPD Art. 12): ano de formatura → inferência de idade, referências de idade explícitas — stripped na camada de prompt." Há menção ao strip, mas não foi possível verificar a implementação técnica direta desta remoção nos arquivos de código inspecionados.
- **Recomendação:** Confirmar que `strip_pii_for_llm_prompt` (`app/shared/pii_masking.py`) inclui remoção ou ofuscação de anos de formatura. Adicionar teste de regressão específico: entrada com "Formado em 1985" deve ser mascarada.

---

### 2B. Testes de Bias

**Achado 16 — Red Team: Bias Elicitation coberto, mas sem teste de paridade demográfica**

- **Status:** Parcial
- **Risco:** Alto
- **Evidência:** `tests/security/test_red_team_scenarios.py` — Contém 6 cenários adversariais: jailbreak, data exfiltration, **bias elicitation**, jailbreak fairness bypass, privilege escalation, score manipulation. O cenário de bias elicitation testa injeção direta de pedidos discriminatórios.
- **Lacuna:** Não há **testes de paridade demográfica sintética**: enviar pares de CVs idênticos exceto por nome (conotação étnica), gênero ou idade e verificar que os scores são iguais (delta < threshold). Este é o padrão de auditoria de ATS sob NYC LL 144.
- **Recomendação:** Implementar `tests/bias/test_demographic_parity.py` com golden dataset de pares de CVs sintéticos. Critério de aprovação: score delta < 5% para pares idênticos diferindo apenas em atributo protegido.

---

**Achado 17 — Ausência de WEAT/SEAT para Embeddings**

- **Status:** Ausente
- **Risco:** Médio
- **Evidência:** Busca por `WEAT`, `SEAT`, `embedding_bias` retornou zero resultados em todo o codebase Python.
- **Problema:** O sistema usa embeddings (OpenAI `text-embedding-3-small` + Gemini fallback) para busca semântica de candidatos. Modelos de embedding pré-treinados carregam vieses históricos documentados (associações de gênero/profissão, de raça/competência). Sem avaliação WEAT/SEAT, não é possível quantificar o viés introduzido pela camada de embedding.
- **Recomendação:** Executar WEAT (Word Embedding Association Test) para português brasileiro nos embeddings utilizados, com foco em associações profissão-gênero (ex: "engenheiro/médico" vs. "enfermeira/secretária") e profissão-etnia. Documentar os resultados e aplicar mitigações (debiasing, adjustments) se o effect size (d) > 0.5.

---

**Achado 18 — Ausência de Testes de Drift de Bias ao Longo do Tempo**

- **Status:** Ausente
- **Risco:** Médio
- **Evidência:** `drift_alert_service.py` existe (citado em `PLATFORM_MAP.md:744`) para monitoramento de consentimento, mas não há referência a monitoramento de drift de métricas de fairness (ex: `adverse_impact_ratio` por período).
- **Recomendação:** Adicionar ao `drift_alert_service.py` (ou criar `fairness_drift_service.py`) monitoramento de séries temporais do `adverse_impact_ratio` por dimensão. Gerar alerta quando o ratio cai abaixo de 0.80 em dois períodos consecutivos.

---

### 2C. Bias nos Agentes Conversacionais

**Achado 19 — WSI Interviewer: Proteção Parcial contra Desvios Pessoais**

- **Status:** Implementado
- **Risco:** Baixo
- **Evidência:** `app/prompts/domains/wsi_interview.yaml:behavioral_rules` — PROIBIDO perguntar sobre família, filhos, estado civil, planos pessoais, saúde, religião, política. `few_shot_examples` inclui exemplo explícito (bias_check): candidato pergunta sobre filhos e o agente redireciona para competências profissionais.
- **Recomendação:** Adicionar caso de teste no golden dataset para verificar que a instrução é seguida quando o candidato **voluntariamente compartilha** informações pessoais durante a entrevista (ex: "Tenho 3 filhos, isso é relevante?") — o agente deve registrar neutralidade sem usar a informação no scoring.

---

**Achado 20 — Pipeline Agent: Alerta para Padrão Sistêmico de Rejeição**

- **Status:** Implementado (instrução, não automação)
- **Risco:** Médio
- **Evidência:** `app/domains/cv_screening/agents/pipeline_system_prompt.py:217` — "Se detectar padrão sistemático de rejeição de grupo demográfico, alerte o recrutador." Esta instrução existe no system prompt, mas a detecção é delegada ao LLM, não implementada como check automático baseado em dados.
- **Problema:** O LLM não tem acesso a histórico agregado de decisões por grupo demográfico na sessão atual. Ele só pode alertar se o recrutador explicitamente revelar o padrão na conversa.
- **Recomendação:** Implementar check automático no `BiasAuditService`: antes de executar `batch_move` (rejeição em massa), calcular a proporção de grupos protegidos no lote e comparar com a proporção no pipeline total. Se desvio > 20%, gerar alerta e exigir confirmação adicional.

---

**Achado 21 — Análise de Diversidade Exposável via Search Query Guide**

- **Status:** Presente com risco
- **Risco:** Médio
- **Evidência:** `plataforma-lia/src/components/ui/lia-search-queries-guide.tsx:71` — Existe query sugerida: "Análise de diversidade e inclusão (raça, PCDs)" para recrutadores. Se essa query retorna dados de candidatos individuais agrupados por raça/PCD, pode violar o Art. 11 LGPD (dados sensíveis) se não houver base legal adequada (consentimento ou obrigação legal).
- **Recomendação:** Garantir que queries de diversidade retornem apenas estatísticas agregadas (sem PII individual). Verificar se candidatos deram consentimento explícito para uso de dados sensíveis em análises de D&I. Documentar a base legal LGPD para este processamento.

---

## 3. LGPD — CONFORMIDADE TÉCNICA

### 3A. Bases Legais

- **Status:** Implementado (com gap de execução)
- **Risco:** Médio
- **Evidências:**
  - `app/api/v1/consent_management.py` — Versioning completo de termos: SHA-256 hash do conteúdo, effective_from/until, `requires_explicit_consent`, `renewal_period_days`. Prova hash por evento de consentimento (SHA-256 composto).
  - `app/api/v1/observability.py:188` — campo `by_legal_basis` retornado em estatísticas de logs de acesso a dados, indicando rastreamento por base legal.
  - `app/api/v1/observability.py:319` — campo `legal_basis` gravado em cada consent record.
  - `app/api/v1/granular_consent.py` — Consentimento granular por finalidade (D5, LGPD Art. 7 / EU AI Act Art. 13): `ai_screening`, `ai_scoring`, voz, etc.
  - `app/controllers/v1/users/onboarding_controller.rb:143-162` (Rails) — `POST /v1/onboarding/consent` grava `consent_type: "onboarding_data_processing"`, `lgpd_consent_at`, `lgpd_consent_channel`.
  - `app/models/consent_record.rb`, `consent_event.rb`, `consent_version.rb` — modelos Rails para registro de consentimento.
  - `src/app/api/backend-proxy/public-vacancies/p/[slug]/apply/route.ts:16` (frontend) — `lgpd_consent` é campo obrigatório validado no formulário de aplicação pública.
- **Gap identificado:** Não há evidência de rastreamento explícito das 9 bases legais do Art. 7 LGPD (ex: execução de contrato, interesse legítimo, obrigação legal). O sistema rastreia consentimento, mas não distingue automaticamente quando outra base legal (não-consentimento) é aplicável. Isso é problemático para operações internas de RH onde a base pode ser "execução de contrato" em vez de consentimento.
- **Recomendação:** Adicionar enum `legal_basis` com todos os incisos do Art. 7 LGPD ao modelo `ConsentRecord`/`AuditLog`, e forçar seleção explícita da base legal em todas as operações de tratamento de dados pessoais, especialmente em relatórios de dados de candidatos para clientes B2B.

---

### 3B. Direitos dos Titulares

#### 3B.1 Acesso (Right to Access)

- **Status:** Implementado
- **Risco:** Baixo
- **Evidências:**
  - `app/api/v1/data_subject_requests.py:131` — endpoint `POST /data-subject-requests` com `request_type="access"` (LGPD Art. 18), SLA de 15 dias úteis calculado automaticamente (`calculate_sla_deadline`).
  - `app/api/public/candidate_portal.py` — portal público para titulares exercerem direitos.
  - `src/app/[locale]/portal/data-request/[token]/layout.tsx` — frontend de portal LGPD para titulares.
  - `src/app/[locale]/privacidade/PrivacidadeClient.tsx:186,254` — página de privacidade com formulário de solicitação de dados e prazo de 15 dias úteis explicitado (Art. 18, §3º).
  - Notificação por e-mail ao titular em todas as etapas DSR (fail-safe, nunca bloqueia operação).
- **Recomendação:** Verificar se o portal do titular exige verificação de identidade (OTP) antes de expor dados — o campo `require_otp` existe no `ConfigResponse` mas confirmar que está habilitado em produção.

#### 3B.2 Retificação (Right to Rectification)

- **Status:** Implementado (parcial)
- **Risco:** Médio
- **Evidências:**
  - `app/api/v1/data_subject_requests.py:50` — `"correction"` listado como tipo de DSR.
  - `app/api/v1/chat.py` — atualização de campos via chat (candidate-field-update proxy no frontend).
  - `src/app/api/backend-proxy/chat/actions/candidate-field-update/route.ts` — endpoint de atualização de campo do candidato via chat LIA.
- **Gap:** Não há endpoint dedicado de "retificação formal" com auditoria de antes/depois para cumprimento do Art. 18 II. O fluxo de retificação depende do fluxo DSR genérico (ticket), sem pipeline automatizado de aplicação da correção nos dados.
- **Recomendação:** Implementar sub-fluxo no DSR para `correction`: após verificação de identidade, roteamento automático para tela de edição de perfil do candidato com log de auditoria do dado anterior vs. novo.

#### 3B.3 Eliminação (Right to Erasure) — End-to-End

- **Status:** Parcial
- **Risco:** Alto

**PostgreSQL (candidatos estruturados):**
- `app/domains/lgpd/services/lgpd_cleanup_service.py` — job Celery diário com `dry_run=True` por padrão (seguro). Cobre `candidates`, `vacancy_candidates`, `ai_consumption`. Janelas de retenção configuradas (90 dias rejeitados/retirados, 180 entrevistas, 365 logs).
- `app/api/v1/admin_lgpd.py` — endpoints admin para disparar cleanup manual, checar status e política.
- `app/api/v1/candidates_controller.rb:32-33` (Rails) — `destroy` existe mas é deleção direta, sem auditoria ou propagação para Python AI layer.

**pgvector (embeddings semânticos):**
- **GAP CRITICO:** Nenhuma evidência de deleção de embeddings/vetores quando um candidato é eliminado. O cleanup service (`lgpd_cleanup_service.py`) cobre tabelas ORM mas não menciona `candidate_embeddings` ou qualquer tabela de vetores. Os embeddings pgvector representam dados biométricos funcionais (extração de características de CV/voz) e persistem após a eliminação do candidato.

**Redis (cache):**
- `app/orchestrator/semantic_cache.py:92` — `await redis.delete(key)` existe para invalidação de cache.
- `app/api/v1/cache.py:161` — endpoint de limpeza de embedding cache.
- **Gap:** Não há deleção coordenada de chaves Redis vinculadas a um `candidate_id` específico quando o candidato exerce direito ao apagamento. O cleanup é global, não por titular.

**Logs de aplicação:**
- `app/api/v1/admin_settings.py:86-88` — `audit_retention_days` e `data_retention_days` configuráveis.
- `RETENTION_DAYS["ai_logs"] = 365` — logs de LLM retidos por 1 ano.
- **Gap:** Logs estruturados e de aplicação (stdout/stderr no Replit) não são purgados quando um candidato solicita eliminação — apenas os dados PostgreSQL são agendados para deleção.

**Backups:**
- **GAP CRITICO:** Nenhuma evidência de política de backup com suporte a eliminação de dados de titulares específicos. Backups de banco de dados (gerenciados pelo Replit/provider) provavelmente contêm dados de candidatos eliminados por períodos indefinidos.

**Recomendações:**
1. Adicionar ao `lgpd_cleanup_service.py` um passo de deleção de embeddings pgvector por `candidate_id` (tabelas `candidate_embeddings`, `vector_semantic_cache` etc.).
2. Implementar função `purge_candidate_redis_cache(candidate_id)` que escaneia e deleta todas as chaves Redis prefixadas com o candidato.
3. Documentar política de backup e prazo de expiração de backups — ou implementar backup com suporte a "data subject deletion" (ex: criptografia por candidato + destruição de chave).
4. Emitir log de auditoria end-to-end para cada etapa da eliminação (PostgreSQL, pgvector, Redis) com timestamp.

#### 3B.4 Portabilidade (Right to Portability)

- **Status:** Parcial
- **Risco:** Médio
- **Evidências:**
  - `app/api/v1/data_subject_requests.py:51` — `"portability"` listado como tipo de DSR (cria ticket).
  - `app/api/v1/bulk_actions.py:610` — `bulk_export_candidates` existe (CSV/JSON), mas é voltado para recrutadores B2B, não para o próprio candidato.
  - `app/api/v1/admin_settings.py:87` — flag `data_export_allowed` (booleano por empresa), sugerindo que portabilidade pode ser desativada.
  - `app/schemas/data_subject_requests.py:20` — `PORTABILITY = "portability"` no enum.
- **Gap:** O DSR de portabilidade cria apenas um ticket de solicitação — não há pipeline automatizado que gere e entregue um arquivo de exportação estruturado (JSON/CSV) ao titular com todos os seus dados pessoais. O `bulk_export_candidates` é restrito a usuários autenticados (recrutadores), não ao próprio candidato.
- **Recomendação:** Implementar handler de fulfillment para DSR `portability`: quando o request for marcado como "em processamento", gerar automaticamente um pacote JSON com todos os dados do candidato (perfil, histórico de candidaturas, consentimentos, avaliações de IA, logs de comunicação) e entregar via e-mail seguro com link temporário (token de 48h).

#### 3B.5 Oposição / Revisão Humana (Art. 20)

- **Status:** Implementado (backend) / Ausente (frontend para candidato)
- **Risco:** Baixo (backend) / Alto (acesso ao candidato)
- **Evidências:**
  - `app/api/v1/lgpd_compliance.py:383,438` — endpoints `GET/POST /lgpd/decisions` para rastrear decisões automatizadas (Art. 20 LGPD).
  - `app/api/v1/lgpd_compliance.py:69` — `pending_human_reviews` contabilizado em stats de compliance.
  - `app/api/v1/data_subject_requests.py` — `"revisao_decisao_automatizada"` (LGPD Art. 20) como tipo de DSR.
  - `app/api/v1/lgpd_compliance.py:6` — comentário explícito: "Automated Decision Explanations (Article 20 compliance)".
  - `HumanReviewRequest`, `HumanReviewComplete` schemas implementados.
- **Recomendação:** Garantir que toda rejeição automática de candidato por IA (score baixo) dispare automaticamente um registro de `AutomatedDecision` com campos `decision_criteria` e `explanation` legíveis, para que o candidato possa exercer revisão antes do descarte.

---

### 3C. Medidas Técnicas

#### 3C.1 Criptografia at rest e in transit

- **Status:** Parcial
- **Risco:** Alto

**In Transit:**
- `app/api/v1/ats.py:218` — validação `parsed.scheme != "https"` para URLs de ATS externos.
- Conexão a APIs externas (Anthropic, OpenAI, Google) sempre via HTTPS (endpoints padrão dos providers).
- Nenhuma evidência de HSTS ou configuração TLS customizada no servidor FastAPI — provavelmente delegado ao Replit proxy.

**At Rest (banco de dados):**
- `libs/config/lia_config/database.py:39-44` — o `sslmode` da DATABASE_URL é removido pelo asyncpg, mas não há `connect_args={"ssl": ssl.create_default_context()}` no engine. Isso significa que a conexão PostgreSQL pode não estar usando TLS se não configurada pelo provider.
- `app/api/v1/ats.py:26` — `from app.shared.encryption import encrypt_value, decrypt_value` — chaves de API de ATS integrations são cifradas antes de salvar no banco.
- `app/jobs/tasks/compliance.py:138` — comentário menciona SHA-256 hash de email + pgcrypto, mas não é implementação ativa observada.
- **GAP:** Nenhuma evidência de colunas `attr_encrypted` ou `pgcrypto` aplicadas sistematicamente a campos PII (CPF, email, telefone) nas tabelas de candidatos do Rails. A criptografia de campos PII ao nível de banco não está confirmada — apenas senhas (bcrypt via `has_secure_password`).

**Rails:**
- `app/models/user.rb:7` — `has_secure_password` (bcrypt para senhas). OK.
- `app/services/magic_link_service.rb:46` — bcrypt para links temporários. OK.

**Recomendações:**
1. Adicionar `connect_args={"ssl": True}` ou `ssl=ssl.create_default_context()` explicitamente ao engine asyncpg para garantir TLS na conexão com PostgreSQL, independentemente do DATABASE_URL.
2. Avaliar uso de `pgcrypto` ou `attr_encrypted` (Rails) para campos PII sensíveis (CPF, data_nascimento) nas tabelas de candidatos.
3. Confirmar que o Replit/hosting provider impõe encryption at rest no volume de dados PostgreSQL — documentar isso como evidência de controle.

#### 3C.2 Anonimização / Pseudonimização

- **Status:** Implementado (bom nível)
- **Risco:** Baixo
- **Evidências:**
  - `app/api/v1/toon.py:10,106,113` — endpoint de "candidato anônimo" com `anonymize=true`: mascara todos campos PII. Explicitamente documentado como "LGPD: pass anonymize=true to mask all PII".
  - `app/api/v1/company_retention.py:36,64` — `auto_anonymize=True` ativa anonimização mensal de candidatos não contratados.
  - `app/shared/compliance/c3b_layer.py` — C3b layer: PII stripping de prompts LLM via `strip_pii_for_llm_prompt` antes de enviar ao modelo de IA.
  - `app/shared/pii_masking.py` — `PIIMaskingFilter` com padrões para CPF, email, telefone BR, nomes em logs.
- **Gap menor:** A anonimização automática mensal (`auto_anonymize`) depende de configuração por empresa — não é aplicada por default. Empresas que não configurarem ficam sem anonimização automática.
- **Recomendação:** Tornar `auto_anonymize=True` o default para novas empresas na criação de conta, exigindo opt-out explícito (em vez de opt-in).

#### 3C.3 Retenção de Dados

- **Status:** Implementado (boa estrutura)
- **Risco:** Médio
- **Evidências:**
  - `app/domains/lgpd/services/lgpd_cleanup_service.py` — RETENTION_DAYS definido com múltiplas categorias:
    ```
    rejected: 90 dias
    withdrawn: 90 dias
    chat_messages: 90 dias (Art. 18 — minimização)
    interview_data: 180 dias
    screening_logs: 365 dias
    ai_logs: 365 dias (L-6)
    ai_decision_logs: 365 dias
    ```
  - Job Celery diário às 02h Brasília, dry_run=True por padrão.
  - `app/models/audit_retention_policy.rb`, `company_retention_policy.rb` — modelos Rails para política customizada por empresa.
  - `app/api/v1/admin_settings.py:86-88` — `audit_retention_days` e `data_retention_days` configuráveis por empresa.
- **Gaps:**
  1. O `dry_run=True` como default é seguro para testes mas requer confirmação de que o job em produção roda com `dry_run=False`. Não há evidência de que isso foi configurado.
  2. Não há evidência de que a política de retenção cobre embeddings pgvector e chaves Redis.
  3. `LGPD Art. 16` exige eliminação imediata após revogação de consentimento em casos específicos — o sistema agenda deleção futura, não imediata.
- **Recomendações:**
  1. Confirmar que Celery Beat está configurado com `dry_run=False` em produção (verificar `celery_tasks.py` / `beat_schedule`).
  2. Adicionar cobertura de retenção para tabelas de embeddings e cache Redis.
  3. Para candidatos que revogam consentimento ativamente (não apenas abandonados), implementar deleção imediata (ou anonimização imediata) em vez de agendamento futuro.

#### 3C.4 Logs de Acesso a Dados Pessoais

- **Status:** Implementado
- **Risco:** Baixo
- **Evidências:**
  - `app/api/v1/observability.py:212` — endpoint `GET /observability/data-access-logs` com filtros e estatísticas por base legal.
  - `app/shared/compliance/audit_writer.py`, `audit_storage.py`, `audit_callback.py` — camada de auditoria dedicada.
  - `app/shared/compliance/audit_service.py` — `audit_service.log_decision()` chamado no C3b layer para cada operação de geração de resposta.
  - `app/api/v1/audit_logs.py:197` — `legal_basis` gravado em audit logs.
- **Gap menor:** PII masking nos logs (`PIIMaskingFilter`) está implementado em módulos críticos (communication, pipeline, rubric, auth, candidates) mas não há evidência de que é aplicado globalmente via `logging.config` no startup — módulos que usam `logging.getLogger(__name__)` simples (sem `get_masked_logger`) podem vazar PII em logs.
- **Recomendação:** Adicionar `PIIMaskingFilter` ao `root logger` no startup da aplicação FastAPI (`main.py` / `lifespan`) para garantir cobertura global, não dependendo de adoção manual por módulo.

#### 3C.5 Data Minimization

- **Status:** Implementado (bom nível)
- **Risco:** Baixo
- **Evidências:**
  - `app/shared/compliance/c3b_layer.py` — `strip_pii_for_llm_prompt()` remove PII de mensagens antes de enviar ao LLM (minimização no processamento IA).
  - `app/api/v1/jd_import.py:418` — JD import aplica `strip_pii_for_llm_prompt` no texto bruto.
  - `app/api/v1/toon.py:113` — `anonymize` query param para minimização na exibição.
  - `app/api/v1/data_request.py` — sistema de "data request" com campos explícitos requeridos por estágio (`DEFAULT_STAGE_FIELD_MAPPINGS`) — coleta apenas dados necessários para cada etapa do processo seletivo.
  - `app/domains/ats_integration/services/ats_clients/lgpd_field_registry.py` — registro de campos LGPD para integrações ATS, controlando quais campos são sincronizados.
- **Gap menor:** `data_export_allowed` como flag booleana por empresa pode ser desabilitado, impedindo que candidatos exercam portabilidade — isso contradiria o Art. 18 IV que é direito irrenunciável.
- **Recomendação:** Remover ou restringir o uso de `data_export_allowed=False` apenas para exportações B2B (bulk exports por recrutadores), nunca para solicitações de portabilidade de titulares (DSR).

---

### 3D. Transferência Internacional

- **Status:** Parcial (sem DPA formal documentado)
- **Risco:** Alto
- **Evidências:**
  - `app/domains/ai/services/llm.py:97,110,162` — APIs de LLM usadas:
    - **Anthropic** (Claude): `api.anthropic.com` — servidores nos EUA
    - **OpenAI** (GPT + Whisper): `api.openai.com` — servidores nos EUA
    - **Google Gemini**: `generativelanguage.googleapis.com` — servidores nos EUA/global
  - `app/domains/ai/services/multimodal_service.py:117,119` — `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` e `AI_INTEGRATIONS_GEMINI_BASE_URL` são configuráveis via env, permitindo apontamento para endpoints alternativos (ex: AWS Bedrock com região BR futuramente).
  - `app/domains/voice/services/voice_service.py:52` — OpenAI para transcrição de voz (áudio de candidatos enviado para servidores OpenAI nos EUA).
- **Análise LGPD Art. 33:**
  O Art. 33 LGPD permite transferência internacional se o país destinatário oferece proteção adequada OU se há cláusulas contratuais padrão (DPA). EUA não tem adequação formal pela ANPD. A plataforma envia para os EUA:
  - Textos de prompts com dados de candidatos (mesmo após strip_pii, contexto pode revelar dados pessoais)
  - Áudio de entrevistas via OpenAI Whisper (ALTO RISCO — dados biométricos funcionais)
  - Embeddings gerados de CVs/perfis de candidatos
- **Gaps:**
  1. Não há evidência de DPA assinado com Anthropic, OpenAI ou Google especificamente para dados de candidatos brasileiros.
  2. Candidatos não são notificados de que dados são processados por LLMs de terceiros fora do Brasil (ausência na política de privacidade ou termos).
  3. Áudio de candidatos enviado diretamente ao OpenAI Whisper é o risco mais grave — dados biométricos funcionais sem DPA documentado.
- **Recomendações:**
  1. Obter e documentar DPAs com Anthropic, OpenAI e Google cobrindo dados de candidatos (Data Processing Agreements com cláusulas específicas para LGPD).
  2. Atualizar política de privacidade (`/privacidade`) para disclose explicitamente os subprocessadores internacionais e os países de destino.
  3. Avaliar uso de Anthropic/AWS Bedrock com região SA-EAST-1 (São Paulo) quando disponível, eliminando a transferência internacional para processamento de voz e LLM.
  4. Para dados de voz: implementar transcrição local (Whisper local via `faster-whisper`) antes de enviar texto (já sem áudio) para LLMs externos.

---

## 4. COMPLIANCE REGULATÓRIO

### 4A. Transparência

#### 4A.1 Disclosure de IA para Candidatos

- **Status:** Parcial
- **Risco:** Alto
- **Evidências:**
  - `plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx:123` — A página de triagem exibe "Powered by LIA · WeDOTalent · Política de Privacidade" em rodapé (`LGPDFooter`). Há link para política de privacidade. **Porém**, a natureza da interação como uma *entrevista conduzida por IA* e o fato de que os scores resultantes alimentam decisões de contratação **não são declarados de forma explícita** ao candidato antes de iniciar a triagem.
  - `plataforma-lia/src/app/[locale]/ajuda/AjudaClient.tsx:74` — A seção "Como a LIA Analisa Candidatos" explica o uso de IA, mas está em `/ajuda` (help page), acessível apenas por recrutadores logados, não por candidatos que recebem o convite de triagem WSI.
  - `plataforma-lia/src/app/[locale]/privacidade/PrivacidadeClient.tsx:175` — Página de privacidade referencia LGPD Art. 18 e direitos do titular, incluindo link no rodapé do candidato. Boa prática.
  - `lia-agent-system/app/api/v1/lgpd_compliance.py` — Existe endpoint `POST /lgpd/decisions/{id}/request-human-review` (LGPD Art. 20), mas não há evidência de que este mecanismo seja **exposto ao candidato** via interface de usuário voltada a ele.
  - **Gap crítico:** Não há evidência de tela/modal de consentimento informado antes da triagem WSI declarando explicitamente: (a) a entrevista é conduzida por IA; (b) os resultados alimentam decisões de contratação; (c) o candidato tem direito de solicitar revisão humana.
- **Recomendação:** Implementar tela de onboarding pré-triagem com disclosure explícito: "Esta entrevista é conduzida pela LIA, um sistema de IA. Os resultados são utilizados para auxiliar decisões de seleção. Você tem o direito de solicitar revisão humana desta avaliação conforme LGPD Art. 20." Exigir clique em "Entendi e aceito" antes de iniciar. Registrar o timestamp desse consentimento no banco de dados.

---

#### 4A.2 Decisões Automatizadas Identificadas

- **Status:** Parcial (registro existe, transparência ao candidato ausente)
- **Risco:** Alto
- **Evidências:**
  - `lia-agent-system/app/api/v1/lgpd_compliance.py:383-459` — Existe API completa de decisões automatizadas: `GET /lgpd/decisions`, `POST /lgpd/decisions` (registro), `GET /lgpd/decisions/{id}` (explicação), `POST /lgpd/decisions/{id}/request-human-review`. Arquitetura LGPD Art. 20 implementada no backend.
  - `lia-agent-system/app/api/v1/platform_event_handlers.py:517,620,756` — `wsi_final_score` é capturado por event handlers e gravado no perfil do candidato, alimentando diretamente o pipeline de seleção. O score WSI é uma **decisão automatizada com impacto em oportunidade de emprego**.
  - `lia-agent-system/app/domains/cv_screening/services/wsi_service/report_generator.py` — O sistema calcula `decisao = "APROVADO" | "AGUARDANDO" | "NÃO APROVADO"` internamente com thresholds numéricos, mas **não revela o score ao candidato** (intencionalmente, por design do produto). Esta escolha de design, embora protetora do processo, cria tensão com LGPD Art. 20 §1º (direito à explicação de decisão automatizada).
  - `lia-agent-system/app/api/v1/automation/_shared.py:632` — Campo `reviewer_id` é obrigatório para rejeições automatizadas, citando "LGPD art. 20 / EU AI Act art. 14". Boa prática, mas a obrigatoriedade não é validada em todos os fluxos de rejeição verificados.
  - `lia-agent-system/app/api/v1/automation/event_handlers/handlers_screening.py:291,308` — Fallback de score padrão `3.0` com `justification="Análise automática não completada - score padrão aplicado"` é gravado como decisão real, podendo prejudicar candidatos quando a IA falha sem sinalização ao candidato.
- **Recomendação:** (1) Expor ao candidato, via portal ou email pós-triagem, a categorização qualitativa da decisão ("seu perfil está em avaliação", "seguiremos em contato") com referência ao direito de solicitar revisão humana. (2) Impedir que scores de fallback (`3.0` default) sejam tratados como decisões definitivas sem revisão humana obrigatória. (3) Validar `reviewer_id` em todos os fluxos de rejeição, não apenas nos explicitamente mapeados.

---

#### 4A.3 Explicabilidade das Decisões

- **Status:** Implementado (interno) / Parcial (externo)
- **Risco:** Médio
- **Evidências:**
  - `lia-agent-system/app/shared/compliance/audit_service.py:60-80` — `AuditService.log_decision()` registra: `company_id`, `agent_name`, `decision_type`, `action`, `decision`, `reasoning` (lista), `criteria_used`, `criteria_ignored` (anti-bias com `PROTECTED_CRITERIA`), `score`, `confidence`, `human_review_required`. Retenção de 730 dias para decisões de candidatos. **Excelente arquitetura interna.**
  - `lia-agent-system/app/api/v1/agent_explainability.py:96` — Endpoint de explainability existe com extração de `step['decision']`.
  - `lia-agent-system/app/api/v1/wsi/reports.py:430-445` — Relatório WSI inclui `evidences`, `red_flags`, `consistency_penalty`, `final_score`, `justification` — rico em explicabilidade para o recrutador.
  - `lia-agent-system/app/api/v1/candidate_search/_shared.py:312,510` — Campo `match_reasoning` presente em buscas de candidatos.
  - `lia-agent-system/app/api/v1/lgpd_compliance.py:394,456` — Endpoint `GET /lgpd/decisions` com filtro `pending_human_review` e campo `explanation_text` — implementação Art. 20.
  - **Gap:** Explicabilidade é **interna** (para recrutadores/admins). Não há interface pública onde o candidato possa consultar a explicação da decisão que o afetou, conforme exigido pelo LGPD Art. 20 §1º.
  - **Gap:** Não há uso de frameworks formais de XAI (SHAP, LIME) — a explicabilidade é narrativa gerada pelo LLM, não verificável quantitativamente. Para fins regulatórios de alto risco (EU AI Act Annex III), explicações narrativas podem ser insuficientes.
- **Recomendação:** (1) Criar portal do candidato com acesso à explicação qualitativa da avaliação (sem revelar score absoluto) e botão "Solicitar revisão humana". (2) Para conformidade com EU AI Act, considerar logging quantitativo de feature importance nos modelos de scoring.

---

### 4B. Governança

#### 4B.1 Modelo de Governança de IA

- **Status:** Parcial
- **Risco:** Alto
- **Evidências:**
  - `docs/specs/ai/AI_FAILURE_MODES.md` — Documento técnico de 6 camadas de resiliência existe e está atualizado (2026-03-26). Cobre circuit breakers, fallbacks, HITL, token budget. **Boa prática de documentação técnica.**
  - `docs/adr/ADR-001-multi-agent-architecture.md`, `ADR-002-observability-stack.md` — ADRs existem para arquitetura e observabilidade.
  - `docs/specs/ai/LLM_DECISIONS.md`, `AI_ARCHITECTURE.md`, `AGENT_SPECS.md` — Documentação técnica de IA existe.
  - `plataforma-lia/docs/lia/ANALISE_MELHORES_PRATICAS_IA.md` — Análise de melhores práticas existe.
  - **Gap crítico:** Não existe documento de **Política de IA Responsável** (*Responsible AI Policy*) — documento de governança que declare: princípios éticos, propósito e limites do uso de IA, mecanismos de oversight, processo de revisão periódica, papéis e responsabilidades. Os ADRs existentes são decisões técnicas, não políticas de governança.
  - **Gap:** Não há evidência de um **registro de inventário de sistemas de IA** (Art. 12 EU AI Act) listando todos os modelos em produção, versões, propósito, dados de treino, responsável e data de última avaliação.
- **Recomendação:** Elaborar documento formal "Política de IA Responsável WeDOTalent" com: missão, princípios (não-discriminação, transparência, explicabilidade, supervisão humana), inventário de sistemas de IA, processo de aprovação para novos modelos/agentes, ciclo de revisão anual.

---

#### 4B.2 Comitê de Ética / DPO

- **Status:** Ausente (estrutura técnica de DPO existe, comitê de ética inexiste)
- **Risco:** Alto
- **Evidências:**
  - `lia-agent-system/app/api/v1/lgpd_compliance.py` — Existe API de `DPO Registry` com endpoints para registrar/listar/atualizar o DPO, o que demonstra reconhecimento da exigência LGPD de encarregado de dados. **Positivo.**
  - `lia-agent-system/app/api/v1/lgpd_compliance.py:68` — Stats incluem `dpo_registered` e `dpo_active`, indicando que o sistema verifica ativamente se um DPO está cadastrado.
  - **Gap crítico:** Não há evidência de um Comitê de Ética de IA ou Responsável por IA (*AI Officer*) distinto do DPO. Para sistemas de alto risco (EU AI Act Annex III — recrutamento), o EU AI Act Art. 26 exige que o operador designe um responsável por conformidade.
  - **Gap:** Busca por `dpo\|data_protection_officer\|encarregado` nos arquivos Python/TS/Ruby retornou apenas resultados da TypeScript cache (`node_modules`) — não há DPO real cadastrado ou referenciado em configuração de produção verificável externamente.
- **Recomendação:** (1) Confirmar e documentar publicamente o DPO com dados de contato (exigência LGPD Art. 41 §1º). (2) Designar um AI Officer ou constituir um comitê de revisão de IA com reuniões trimestrais documentadas. (3) Publicar nome/email do DPO no aviso de privacidade e no Trust Center da plataforma.

---

#### 4B.3 Incident Response para Falhas de IA

- **Status:** Parcial (resiliência técnica robusta; processo formal de incident response ausente)
- **Risco:** Médio
- **Evidências:**
  - `docs/specs/ai/AI_FAILURE_MODES.md` — **6 camadas de resiliência**: Token Budget Guard, Circuit Breaker (14 circuits: LLM×3, ATS×4, Auth, Sourcing, Calendar, Email×2, Payments×2), ReAct loop error handling, LLM Cascade (Haiku→Sonnet→Opus→requires_human), Defensive Prompts, Agent Health Alerts. **Arquitetura de resiliência excelente.**
  - `AI_FAILURE_MODES.md` — Circuit Breaker notifica via Bell (in-app) + Teams webhook com dedup Redis (1 alerta/hora/circuit). Alerta após N falhas consecutivas de agente.
  - `lia-agent-system/app/shared/resilience/circuit_breaker.py` — Implementação de 3 estados (CLOSED→OPEN→HALF_OPEN).
  - **Gap:** Não há evidência de processo formal de **AI Incident Response** com: classificação de severidade de incidentes de IA (ex: viés sistêmico detectado, alucinação com impacto em candidatos, vazamento de PII), SLAs de resposta, notificação à ANPD (LGPD Art. 48 — até 72h para incidentes de segurança), comunicação a candidatos afetados.
  - **Gap:** Não há evidência de integração com ferramentas externas de observabilidade (Sentry, Datadog, PagerDuty) para alertas de produção fora do ambiente Replit.
  - **Gap:** Notificação de breach existe em `lgpd_compliance.py` (modelo `BreachNotification`, `ANPDNotification`), mas não há evidência de processo testado de notificação à ANPD em 72h.
- **Recomendação:** (1) Criar Runbook de AI Incident Response com 4 níveis de severidade (S1-S4) e ações correspondentes. (2) Definir SLA de notificação à ANPD (72h) e testar o processo em tabletop exercise. (3) Integrar alertas do circuit breaker com sistema de on-call externo (PagerDuty ou equivalente). (4) Criar processo de post-mortem para incidentes de IA com análise de viés ou impacto indevido em candidatos.

---

### 4C. Documentação

#### 4C.1 RIPD / DPIA

- **Status:** Ausente
- **Risco:** Crítico
- **Evidências:**
  - `find /home/runner/workspace -name "*ripd*" -o -name "*dpia*"` — Nenhum arquivo encontrado. Sem evidência de RIPD (Relatório de Impacto à Proteção de Dados) ou DPIA (Data Protection Impact Assessment) no repositório.
  - LGPD Art. 38 exige RIPD quando o tratamento de dados pode gerar risco elevado aos titulares. Avaliação de candidatos por IA com impacto em oportunidade de emprego **enquadra-se inequivocamente** nesta exigência.
  - EU AI Act Art. 9 exige sistema de gestão de risco documentado para sistemas de alto risco (Annex III inclui recrutamento explicitamente).
  - `.local/tasks/lgpd-compliance-gaps.md` — Tarefa interna identifica gaps de compliance (TTL de dados, criptografia de campo, fairness report exportável) mas não menciona RIPD.
- **Recomendação:** Elaborar RIPD/DPIA contemplando: (1) descrição dos tratamentos (triagem de CV, entrevista WSI, scoring, pipeline); (2) finalidade e base legal de cada tratamento; (3) avaliação de necessidade e proporcionalidade; (4) identificação e avaliação de riscos (discriminação algorítmica, viés, vazamento de PII, decisão automatizada sem supervisão); (5) medidas técnicas e organizacionais adotadas; (6) consulta ao DPO. Manter RIPD atualizado a cada mudança significativa de modelo ou fluxo.

---

#### 4C.2 Registros de Tratamento

- **Status:** Parcial
- **Risco:** Alto
- **Evidências:**
  - `lia-agent-system/app/shared/compliance/audit_service.py` — AuditLog com retenção de 730 dias para decisões. `RETENTION_PERIODS` definido por tipo de decisão.
  - `.local/tasks/lgpd-compliance-gaps.md` — Descreve plano para TTL automático (90 dias chat, 180 dias entrevista, 365 dias screening/IA logs), mas cita este como gap a ser implementado — **não confirmado como produção**.
  - `lia-agent-system/app/domains/lgpd/services/lgpd_cleanup_service.py` e `app/shared/services/lgpd_cleanup_service.py` — Serviços de cleanup existem.
  - `lia-agent-system/tests/test_sprint4_lgpd_retention.py` — Testes de retenção existem.
  - **Gap:** Não há Registro de Atividades de Tratamento (RAT) conforme exigido por LGPD Art. 37 para operadores de dados — documento formal que descreve cada operação de tratamento, base legal, categorias de dados, destinatários, transferências internacionais e prazos de retenção.
  - **Gap:** Criptografia de campo CPF/email — testes existem (`test_lgpd_compliance_gaps.py:161-269`) mas implementação de produção (`encrypted_field_mixin`) **não confirmada como deployada**. O gap file lista isso como tarefa pendente.
- **Recomendação:** (1) Elaborar e manter RAT (Registro de Atividades de Tratamento) cobrindo todos os fluxos de dados de candidatos. (2) Confirmar e documentar o status de produção da criptografia Fernet para CPF/email. (3) Implementar e testar job de cleanup automático com TTLs definidos, com alertas de falha.

---

#### 4C.3 Política de IA Responsável

- **Status:** Ausente (documentação técnica existe; política organizacional ausente)
- **Risco:** Alto
- **Evidências:**
  - Documentação técnica abrangente existe: `AI_FAILURE_MODES.md`, `AGENT_SPECS.md`, `AI_ARCHITECTURE.md`, `LLM_DECISIONS.md`, `PROMPT_STANDARDS.md`.
  - `plataforma-lia/docs/lia/ANALISE_MELHORES_PRATICAS_IA.md` — análise de melhores práticas.
  - **Gap:** Nenhum documento de política de IA responsável voltado a stakeholders não-técnicos (clientes, candidatos, reguladores, investidores). Documentação técnica não substitui política de governança.
  - `plataforma-lia/src/app/[locale]/trust/page.tsx` — Trust Center existe na UI, descrevendo certificações e práticas LGPD. **Positivo**, mas o conteúdo desta página não foi auditado em profundidade.
- **Recomendação:** Publicar Política de IA Responsável no Trust Center e no site público, cobrindo: princípios de design ético, como a IA é usada em recrutamento, direitos dos candidatos, mecanismo de reclamação, como vieses são monitorados e mitigados, e compromisso com revisão periódica.

---

### 4D. Classificação Regulatória

#### AI Act (EU) — Alto Risco (Annex III)

- **Classificação:** **Alto Risco — Annex III, Categoria 4** (sistemas de IA para recrutamento e seleção de pessoas, em particular para triagem e avaliação de candidatos)
- **Status de conformidade:** Parcial
- **Evidências positivas:**
  - `lia-agent-system/app/api/v1/bias_audit.py:11` — Referência explícita a "EU AI Act Art. 10" no header do módulo de bias audit. **Reconhecimento do framework.**
  - `lia-agent-system/app/api/v1/fairness_reports.py:3` — "FairnessGuard reports API — EU AI Act compliance reporting." Endpoint de export CSV/JSON existe.
  - `lia-agent-system/app/api/v1/granular_consent.py:2` — "Granular Consent API — D5 (LGPD Art. 7 / EU AI Act Art. 13)." Consentimento granular implementado.
  - `lia-agent-system/app/api/v1/automation/_shared.py:632` — `reviewer_id` obrigatório citando "EU AI Act art. 14" (supervisão humana).
  - `lia-agent-system/app/shared/compliance/fairness_guard.py` — FairnessGuard com dicionário extenso de termos implicitamente discriminatórios (PT-BR e EN), cobrindo: etnia, gênero, classe social, religião, PCD, estado civil, proxy etário. **Implementação notável.**
- **Gaps de conformidade EU AI Act:**
  - Art. 9: Sistema de gestão de risco documentado — **ausente** formalmente.
  - Art. 10: Práticas de governança de dados de treino — **não documentadas**.
  - Art. 11: Documentação técnica registrável — RIPD/DPIA **ausente**.
  - Art. 13: Transparência ao usuário final (candidato) — **parcial** (rodapé com "Powered by LIA" mas sem disclosure estruturado).
  - Art. 14: Supervisão humana — **parcialmente implementada** via HITL (LangGraph `interrupt_before`) e `human_review_required`, mas cobertura incompleta.
  - Art. 17: Quality Management System — **ausente** formalmente.
- **Recomendação:** Antes de expandir para mercados europeus, conduzir assessment formal EU AI Act com assessoria especializada e implementar o sistema de gestão de qualidade exigido pelo Art. 17.

---

#### NYC Local Law 144 — Bias Audit for AEDTs

- **Aplicabilidade:** Condicional — aplicável se a plataforma for utilizada por empregadores com candidatos em NYC.
- **Status de conformidade:** Parcialmente alinhada (não declarada)
- **Evidências:**
  - `lia-agent-system/app/api/v1/bias_audit.py` — Implementa bias audit com **Four-Fifths Rule (80% Rule)** e chi-quadrado de disparate impact para dimensões demográficas. `DemographicAuditResultResponse` inclui `eeoc_compliant`, `adverse_impact_ratio`, `disparate_impact` com `p_value`. **Esta implementação está diretamente alinhada com NYC LL144.**
  - `lia-agent-system/app/api/v1/observability.py:738-769` — Endpoints `/bias-audits/latest` e `/bias-audits/summary` — auditores externos poderiam acessar estes dados.
  - `plataforma-lia/src/hooks/recruitment/use-bias-audit-report.ts` — Hook de frontend para relatório de bias audit.
  - `lia-agent-system/app/shared/services/bias_audit_service.py` — Serviço de auditoria de viés.
  - **Gap:** NYC LL144 exige que o **resultado do bias audit seja publicado no site da empresa**. Não há evidência de publicação pública dos resultados de auditoria de viés.
  - **Gap:** NYC LL144 exige notificação prévia aos candidatos de que uma AEDT (Automated Employment Decision Tool) será usada. Esta notificação não foi verificada nos fluxos de convite WSI.
- **Recomendação:** (1) Conduzir auditoria independente de bias anual (NYC LL144 exige auditor independente). (2) Publicar resultados da auditoria no site. (3) Adicionar aviso nos convites de triagem WSI sobre uso de AEDT.

---

#### LGPD Art. 20 — Direito à Revisão de Decisão Automatizada

- **Status:** Parcialmente implementado
- **Risco:** Alto
- **Evidências:**
  - `lia-agent-system/app/api/v1/lgpd_compliance.py:468-511` — Endpoints `request-human-review` e `complete-human-review` implementados. **Infraestrutura Art. 20 existe no backend.**
  - `plataforma-lia/src/components/interview-notes/score-card-wsi.tsx:96,118,131` — Frontend exibe estado `human_review` com UI correspondente para recrutadores.
  - `lia-agent-system/app/api/v1/lgpd_compliance.py:69-70` — Stats de `pending_human_reviews` e `completed_human_reviews` monitorados.
  - `lia-agent-system/app/api/v1/data_subject_requests.py:54,131` — Data Subject Requests implementadas com `"explanation": "Explicação sobre decisão automatizada"` como tipo de solicitação.
  - **Gap crítico:** O direito do candidato de **solicitar revisão humana** (Art. 20 §1º) existe no backend mas **não há interface voltada ao candidato** para exercê-lo. O candidato recebe a avaliação por email, mas sem mecanismo de contestação/revisão.
  - **Gap:** Art. 20 §2º exige que o controlador informe os critérios e procedimentos da decisão automatizada. Não há comunicação formal desses critérios aos candidatos.
- **Recomendação:** (1) Implementar no email de resultado da triagem WSI um link "Solicitar revisão humana desta avaliação" que acione o endpoint `request-human-review`. (2) Incluir nos comunicados ao candidato os critérios gerais utilizados na avaliação (competências técnicas, comportamentais, metodologia WSI). (3) Definir SLA para resposta às solicitações de revisão humana (sugestão: 15 dias úteis, alinhado com Art. 18 §3º).

---

## Prioridades de Remediação

### P0 — Corrigir ESTA SEMANA (Bloqueiam Conformidade Legal)

1. [BIAS] `analysis.yaml` — Anonimizar campos `Nome`, `Localização`, `Empresa`; reduzir "Fit de Personalidade" + "Alinhamento Cultural" de 45% para no máximo 10% combinados. Fix: editar `app/prompts/domains/analysis.yaml`.
2. [FAIRNESS] `LIA_DISABLE_C3B` — Adicionar logging crítico, registro em AuditService e segundo fator de autenticação para ativar o flag. Fix: `app/shared/compliance/c3b_layer.py:13`.
3. [FAIRNESS] FairnessGuard L3 — Habilitar para todos os setores com `high_impact: True`, incluindo `varejo` e `logistica`. Fix: `ALPHA1_SECTOR_RULES` em `PLATFORM_MAP.md` / configuração de setor.
4. [LGPD] DPAs — Iniciar processo de assinatura de DPA com Anthropic, OpenAI (prioridade: Whisper/voz) e Google. Fix: ação jurídica/contratual imediata.
5. [LGPD] pgvector erasure — Adicionar passo de deleção de embeddings por `candidate_id` ao `lgpd_cleanup_service.py`. Fix: `app/domains/lgpd/services/lgpd_cleanup_service.py`.
6. [LGPD] TLS PostgreSQL — Adicionar `connect_args={"ssl": ssl.create_default_context()}` ao engine asyncpg. Fix: `libs/config/lia_config/database.py:39-44`.
7. [GOVERNANCE] Art. 20 UI — Implementar link "Solicitar revisão humana" no email de resultado WSI. Fix: template de email + endpoint `request-human-review`.
8. [GOVERNANCE] RIPD/DPIA — Elaborar documento com DPO. Fix: ação organizacional imediata; bloqueia conformidade EU AI Act Art. 9 e LGPD Art. 38.
9. [GOVERNANCE] Disclosure pré-triagem — Implementar tela de consentimento informado antes do início da triagem WSI. Fix: `TriagemFlow.tsx` + novo componente de disclosure.

### P1 — Sprint Atual (Alto Impacto em Conformidade)

10. [BIAS] Recruiter calibration — Persistir `recruiter_score_adjustments` em tabela dedicada com `recruiter_id`, `candidate_id`, `delta`, `job_id`, timestamp. Fix: nova tabela Rails + ORM Python.
11. [BIAS] Testes de paridade demográfica — Implementar `tests/bias/test_demographic_parity.py` com golden dataset de pares de CVs sintéticos. Fix: novo arquivo de testes.
12. [BIAS] WEAT/SEAT — Executar avaliação de bias nos embeddings OpenAI/Gemini para PT-BR. Fix: script de avaliação + documentação de resultados.
13. [LGPD] Criptografia Fernet CPF/email — Confirmar e documentar status de produção do `encrypted_field_mixin`. Fix: verificar deploy + adicionar smoke test de produção.
14. [LGPD] DPO ativo — Confirmar DPO real em produção e publicar contato no aviso de privacidade. Fix: ação organizacional + atualização de `/privacidade`.
15. [GOVERNANCE] Score fallback — Marcar scores de fallback `3.0` como `requires_human_review=True` obrigatório, bloquear de avançar no pipeline automaticamente. Fix: `handlers_screening.py:291,308`.
16. [LGPD] Celery `dry_run=False` — Confirmar configuração do Celery Beat em produção com deleções ativas. Fix: verificar `beat_schedule` + adicionar alerta de monitoramento.

### P2 — Backlog (Melhorias Estruturais)

17. [LGPD] Redis purge por candidato — Implementar `purge_candidate_redis_cache(candidate_id)` no fluxo de eliminação.
18. [LGPD] Portabilidade automatizada — Implementar pipeline de fulfillment DSR `portability` com entrega de pacote JSON por e-mail seguro.
19. [LGPD] PIIMaskingFilter global — Adicionar ao root logger no startup FastAPI.
20. [LGPD] `auto_anonymize` default — Tornar `auto_anonymize=True` o default para novas empresas.
21. [LGPD] Enum bases legais Art. 7 — Adicionar ao modelo `ConsentRecord`/`AuditLog`.
22. [GOVERNANCE] Política de IA Responsável — Elaborar e publicar no Trust Center.
23. [GOVERNANCE] RAT (Registro de Atividades de Tratamento) — Elaborar conforme LGPD Art. 37.
24. [FAIRNESS] Equal Opportunity metric — Adicionar `equal_opportunity_ratio` e `predictive_parity` ao `BiasAuditReport`.
25. [FAIRNESS] Re-ranking ativo RAG — Implementar rebalanceamento de gênero quando limiar violado (não apenas logging).
26. [FAIRNESS] Fairness drift monitoring — Adicionar monitoramento de séries temporais do `adverse_impact_ratio`.
27. [GOVERNANCE] AI Incident Response Runbook — Criar com 4 níveis de severidade e SLAs de notificação ANPD.
28. [BIAS] Proxy de localização — Converter `Localização: {candidate_location}` para nível de granularidade (estado/região) no `analysis.yaml`.

---

## Risk Heatmap — Probabilidade × Impacto

```
                    IMPACTO
                    Baixo      Médio        Alto         Crítico
PROBABILIDADE
Alta          |           | A18,A20,A21 | A3,A4,A10  | A6,A5/13  |
              |           | R11         | A11,A16    | R01,R08   |
              |           |             | R03,R07    |           |
Média         |           | A1,A2,A12   | A8,A9,A17  | R02,R10   |
              |           | R06,R09     | A13,A15    |           |
              |           |             | R04,R05    |           |
Baixa         | A14,A15   | A19,A21     | A7,A9      |           |
              | A7 (OK)   | R12         |            |           |
```

**Mapeamento de IDs de risco:**
- A3: FairnessGuard L3 ausente em varejo/logística
- A4/A10: analysis.yaml — 45% score subjetivo + nome do candidato
- A5/13: Recruiter calibration sem auditoria demográfica + sem persistência
- A6: LIA_DISABLE_C3B sem controle
- A8: Falhas silenciosas no AuditService
- A9: REPORT_SIGNING_KEY ausente
- A11: Localização visível no prompt
- A12: Empresa atual visível no prompt
- A13: Calibration in-memory
- A14: Bias de ancoragem por ranking
- A15: Proxy de idade via ano de formatura
- A16: Ausência de testes de paridade demográfica
- A17: Embeddings sem WEAT/SEAT
- A18: Ausência de drift monitoring
- A19: WSI Interviewer proteção parcial
- A20: Alerta sistêmico de rejeição não automático
- A21: Queries de diversidade com dados individuais
- R01: Candidato sem acesso a revisão humana (Art. 20)
- R02: Ausência de RIPD/DPIA
- R03: FairnessGuard L3 em domínios de risco
- R04: Score fallback como decisão definitiva
- R05: DPO não confirmado em produção
- R06: Ausência de Política de IA Responsável
- R07: Criptografia Fernet CPF/email não confirmada em produção
- R08: Disclosure de IA insuficiente pré-triagem
- R09: Sem auditor independente NYC LL144
- R10: Processo ANPD 72h não testado
- R11: Ausência de RAT (Registro de Atividades de Tratamento)
- R12: Explicabilidade narrativa sem métricas quantitativas

O quadrante de maior concentração de achados é **Alta Probabilidade × Impacto Alto/Crítico**, com 11 dos 17 achados P0/P1 nessa região. Isso indica que a plataforma enfrenta riscos altamente prováveis de se materializarem e com consequências regulatórias severas (multas LGPD até 2% faturamento, suspensão de tratamento, ações individuais de candidatos). O segundo cluster concentra-se em **Média Probabilidade × Impacto Crítico** (RIPD, processo ANPD), que embora menos prováveis de ocorrerem amanhã, representam as exposições de maior magnitude financeira e reputacional. A boa notícia é que o quadrante de **Baixo Impacto** tem poucos achados, confirmando que a maioria dos gaps identificados não são triviais — mas também que os controles já implementados estão funcionando onde foram deployados.

---

## O que a Plataforma Faz Bem

**1. FairnessGuard com cobertura exemplar**
O dicionário de termos implicitamente discriminatórios (PT-BR + EN) com 9 categorias e mensagens educativas é uma das implementações mais completas encontradas em plataformas de ATS de mercado. Cobre proxies de raça, classe, gênero, religião, PCD, estado civil e etária. A arquitetura de 3 camadas (regex, soft warnings, semântica LLM) com integração como middleware pré-processamento é tecnicamente superior ao padrão da indústria.

**2. Bias Audit com Four-Fifths Rule alinhado ao NYC LL144**
A implementação de `bias_audit_service.py` com chi-quadrado de disparate impact, `eeoc_compliant`, `adverse_impact_ratio`, `p_value` e alert levels representa alinhamento técnico real com NYC Local Law 144 e EU AI Act Art. 10, mesmo sem ser declarado formalmente. Os endpoints de relatório exportável com assinatura HMAC-SHA256 e referência explícita a NYC LL144 demonstram maturidade regulatória.

**3. Infraestrutura LGPD Art. 20 completa no backend**
Os endpoints de `request-human-review`, `complete-human-review`, `automated-decisions` com `explanation_text` e monitoramento de `pending_human_reviews`/`completed_human_reviews` indicam que o backend foi projetado com compliance em mente. A ausência é de UI para o candidato, não de arquitetura backend — o que é significativamente mais fácil de corrigir.

**4. HITL via LangGraph `interrupt_before`**
Três fluxos críticos têm Human-in-the-Loop implementado: `job_wizard_graph` (antes de criar vaga), `wsi_interview_graph` (antes de finalizar avaliação WSI), `pipeline_stage_context` (antes de mover candidato de stage). HITL via Redis + DB com fallback in-memory é arquitetura robusta.

**5. AuditService com `PROTECTED_CRITERIA` explícitos**
O logging de `criteria_ignored` com lista explícita de 10 critérios proibidos e retenção de 730 dias demonstra design orientado a accountability. A presença de `criteria_used` vs. `criteria_ignored` no mesmo registro é arquitetura de auditoria diferenciada — permite provar negativamente que critérios protegidos foram excluídos da decisão.

**6. Resiliência técnica de 6 camadas**
Circuit breaker com 14 circuits, LLM cascade por confiança (Haiku→Sonnet→Opus→requires_human), token budget guard, agent health alerts com notificação in-app+Teams — arquitetura de resiliência técnica madura que supera o padrão de plataformas B2B de RH.

**7. Portal LGPD para candidatos**
`/portal/data-request/[token]` implementa exercício de direitos do titular (LGPD Art. 18) com formulário, referência à lei e prazo de 15 dias úteis. `DPORegistry` API implementada. Consentimento LGPD como campo obrigatório na candidatura pública.

**8. Consentimento granular por finalidade**
`app/api/v1/granular_consent.py` com granularidade por propósito (`ai_screening`, `ai_scoring`, voz) alinhada ao Art. 7 LGPD e EU AI Act Art. 13. Versionamento de termos com SHA-256 e prova de hash por evento é implementação acima do mínimo regulatório.

---

## Referências Regulatórias Aplicadas

- LGPD (Lei 13.709/2018) — Arts. 7, 11, 12, 16, 18, 20, 33, 37, 38, 41, 46, 48, 52
- EU AI Act 2024/1689 — Annex III (High-Risk AI, Categoria 4 — Recrutamento), Arts. 9, 10, 11, 13, 14, 17, 26
- NYC Local Law 144 (2021) — AEDT bias audit, publicação de resultados, notificação a candidatos
- EEOC Guidelines on Employment Tests — Four-Fifths Rule (80% Rule), Disparate Impact
- CLT Art. 373-A, Lei 9.029/95, Lei 7.716/89, Lei 10.741/03 (Estatuto do Idoso), Lei 13.146/15 (LBI/PCD)
- ISO/IEC 42001 — AI Management System
- NIST AI RMF (2023)
- OECD AI Principles (2019)

---

*Auditoria conduzida por análise estática de código-fonte em 2026-04-14. Não cobre: testes de penetração, entrevistas com stakeholders, análise de dados de produção, ou revisão de contratos com terceiros. Recomenda-se auditoria presencial e entrevistas com DPO/time jurídico para validar achados e confirmar status de produção dos controles identificados.*
