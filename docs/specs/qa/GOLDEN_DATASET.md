# GOLDEN_DATASET.md — Casos de Referência para Validação de IA

**Versão:** 1.0
**Última atualização:** 2026-03-26
**Repositório:** `lia-agent-system`

---

## 1. Visão Geral

Golden datasets são conjuntos de dados determinísticos usados para validar que o comportamento da IA é correto, justo e rastreável. A plataforma LIA mantém dois golden datasets:

| Dataset | Arquivo | Propósito | Records |
|---------|---------|-----------|---------|
| Golden Dataset (Fairness) | `tests/fixtures/golden_dataset.py` | Bias audit com Four-Fifths Rule | 60 candidatos |
| Golden Queries (RAGAS) | `tests/ragas/golden_queries.py` | Avaliação de qualidade de respostas dos agentes | 5 queries |

---

## 2. Golden Dataset — Fairness (60 candidatos)

### 2.1 Estrutura

**Arquivo:** `lia-agent-system/tests/fixtures/golden_dataset.py`

```python
APPROVAL_THRESHOLD = 60  # score >= 60 → aprovado

GROUPS = {
    "gender": ["masculino", "feminino", "nao_binario"],
    "age_group": ["25-35", "35-50", "50+"],
    "disability": ["sem_pcd", "com_pcd"],
    "region": ["sp", "rj", "outras_capitais", "interior"],
}
```

### 2.2 Campos por Candidato

| Campo | Tipo | Valores |
|-------|------|---------|
| `id` | str | Único (c001 a c060) |
| `name` | str | Nome fictício ("Candidato A1", "Candidato B3") |
| `gender` | str | "masculino" \| "feminino" \| "nao_binario" |
| `age_group` | str | "25-35" \| "35-50" \| "50+" |
| `disability` | str | "sem_pcd" \| "com_pcd" |
| `region` | str | "sp" \| "rj" \| "outras_capitais" \| "interior" |
| `tech_level` | str | "senior" \| "pleno" \| "junior" |
| `score` | int | 0–99, independente de dados demográficos |
| `approved` | bool | `score >= APPROVAL_THRESHOLD` |

### 2.3 Distribuição

| Faixa | IDs | Tech level | Score range | Qty |
|-------|-----|-----------|-------------|-----|
| Alta performance | c001–c020 | senior | 75–95 | 20 |
| Média performance | c021–c040 | pleno | 45–72 | 20 |
| Baixa performance | c041–c060 | junior | 15–44 | 20 |

**Princípio fundamental:** Scores são determinísticos e baseados EXCLUSIVAMENTE em `tech_level`. Marcadores demográficos (gênero, idade, PCD, região) NÃO influenciam o score. Esta é a pré-condição que permite testar a Four-Fifths Rule.

### 2.4 Distribuição Demográfica

O dataset garante distribuição equilibrada entre grupos para que os testes de fairness sejam válidos:

| Dimensão | Distribuição |
|----------|-------------|
| Gênero | ~20 masculino, ~20 feminino, ~20 nao_binario |
| Faixa etária | ~20 cada (25-35, 35-50, 50+) |
| PCD | ~40 sem_pcd, ~20 com_pcd |
| Região | ~15 sp, ~15 rj, ~15 outras_capitais, ~15 interior |

### 2.5 Funções Helper Exportadas

```python
from tests.fixtures.golden_dataset import (
    GOLDEN_DATASET,         # List[Dict] — os 60 candidatos
    APPROVAL_THRESHOLD,     # int — 60
    GROUPS,                 # Dict[str, List[str]]
    get_group,              # (dimension: str, value: str) → List[Dict]
    selection_rate,         # (group: List[Dict]) → float
    adverse_impact_ratio,   # (group_a: List[Dict], group_b: List[Dict]) → float
)
```

**Assinaturas reais (de `golden_dataset.py`):**
- `get_group(dimension, value)` — filtra candidatos por dimensão + valor (ex: `get_group("gender", "feminino")`)
- `selection_rate(group)` — calcula aprovados / total do grupo
- `adverse_impact_ratio(group_a, group_b)` — `min(rate_a, rate_b) / max(rate_a, rate_b)`, retorna 1.0 se rate_b == 0

### 2.6 Quem Usa

| Teste | Arquivo | Como usa |
|-------|---------|---------|
| Four-Fifths Rule | `tests/fairness/test_four_fifths_rule.py` | Calcula AIR por dimensão |
| Red Teaming | `tests/fairness/test_red_teaming.py` | Referência de texto limpo |

---

## 3. Golden Queries — RAGAS (5 fluxos)

### 3.1 Estrutura

**Arquivo:** `lia-agent-system/tests/ragas/golden_queries.py`

```python
GOLDEN_QUERIES = {
    "wsi_scoring": [...],
    "cv_matching": [...],
    "salary_benchmark": [...],
    "pipeline_analysis": [...],
    "candidate_search": [...],
}
```

### 3.2 Queries de Referência

| Fluxo | Query | Tools esperadas | Keywords na resposta |
|-------|-------|-----------------|---------------------|
| **WSI Scoring** | "Avalie a resposta do candidato sobre liderança em equipes" | `score_wsi_response` | score, bloom, dreyfus, avaliação |
| **CV Matching** | "Quais candidatos têm perfil para a vaga de Engenheiro Python?" | `search_candidates`, `get_candidate_details` | python, candidato, experiência, score |
| **Salary Benchmark** | "Qual o salário de mercado para Analista de Dados Sênior em SP?" | `get_market_benchmarks`, `search_salary_benchmark` | salário, mercado, benchmark, SP |
| **Pipeline Analysis** | "Analise os gargalos no pipeline da vaga de Product Manager" | `get_bottleneck_analysis`, `get_job_velocity` | gargalo, estágio, dias, candidatos |
| **Candidate Search** | "Encontre desenvolvedores React com 3+ anos disponíveis em SP" | `search_candidates` | react, desenvolvedor, São Paulo, experiência |

### 3.3 Critérios de Avaliação RAGAS

Cada query é avaliada em 3 dimensões:

| Dimensão | O que mede | Threshold |
|----------|-----------|-----------|
| Tool Selection | Agente selecionou as tools corretas | 100% match |
| Keyword Coverage | Resposta contém keywords esperadas | ≥ 75% presentes |
| Faithfulness | Resposta é fiel ao contexto (RAGAS metric) | ≥ 0.5 |

---

## 4. Golden Test Cases — QA Report

Extraído de `docs/QA_REPORT_SPRINT_2026-02-28.md`, estes são os golden test cases verificados:

### 4.1 Camada Legal/LGPD

| ID | Case | Input | Expected | Verificado |
|----|------|-------|----------|-----------|
| L1 | LangSmith opt-in | `config.py:61` | `LANGCHAIN_TRACING_V2 = False` | Sim |
| L3 | Rejeição sem user_id | `PATCH /{id}/stage` sem user_id | HTTP 422 | Sim |
| L4 | LGPD deletion | `POST /lgpd/schedule-deletion` | Persiste `scheduled_deletion_at` | Sim |
| L5 | Consent revogado | `check_candidate_consent()` | `allowed=False` | Sim |
| L7 | PII masking | Logs com CPF/email/telefone | Dados mascarados | Sim |

### 4.2 Camada Bias/Fairness

| ID | Case | Input | Expected | Verificado |
|----|------|-------|----------|-----------|
| B1 | Blind evaluation | CV com nome | Nome removido do contexto LLM | Sim |
| B2 | Geographic adjustments | Candidato de qualquer região | Multiplicador = 1.0 | Sim |
| B3 | FairnessGuard | Output com potencial bias | `FairnessGuard.check()` invocado | Sim |
| B4 | System prompts | 8 system prompts | Seção fairness presente em todos | Sim |
| B5 | Disparate impact | 60 candidatos do golden dataset | AIR ≥ 0.80 em todas as dimensões | Sim |

### 4.3 Camada Monetização

| ID | Case | Input | Expected | Verificado |
|----|------|-------|----------|-----------|
| M1 | Limite de vagas | `POST /job-vacancies` acima do plano | HTTP 402 | Sim |
| M2 | Trial expirado | Requisição com trial vencido | HTTP 402 + redirect `/upgrade` | Sim |
| M4 | AI credits | Consumo acima de 80% | Alerta amber | Sim |
| M5 | Token tracking | Consumo acima de 100% | Alerta red + dedup Redis 24h | Sim |

---

## 5. Golden Scenarios — Testes Manuais (Ondas 1-3)

Extraído de `docs/analises/GUIA_TESTES_ONDA1.md`:

### 5.1 Sprint 1A — stage_entered_at

| Scenario | Ação | Esperado |
|----------|------|----------|
| Troca de etapa | Mover candidato no kanban | `stage_entered_at` atualizado |
| Sub-status | Alterar sub-status apenas | `stage_entered_at` inalterado |
| Coluna existe | Query information_schema | `timestamp without time zone` |

### 5.2 Sprint 1B — Pipeline Velocity

| Scenario | Ação | Esperado |
|----------|------|----------|
| Métricas por vaga | `GET /api/v1/pipeline/velocity?vacancy_id=X` | JSON com per_stage, bottlenecks, health |
| Gargalos ativos | `GET /api/v1/pipeline/velocity/bottlenecks` | Lista de candidatos acima do threshold |
| Chat LIA | "Onde o pipeline está travando?" | Usa tool `get_pipeline_velocity` |

### 5.3 Sprint 1C — Zero-Touch Scheduling

| Scenario | Ação | Esperado |
|----------|------|----------|
| Criar link | `POST /api/v1/scheduling/link` | Token + URL + slots |
| Acessar link | `GET /api/v1/scheduling/link/{token}` (sem auth) | Slots disponíveis + dados da vaga |
| Confirmar horário | `POST /api/v1/scheduling/link/{token}/confirm` | Entrevista criada, link status=used |
| Link expirado | Confirmar token usado | HTTP 410 Gone |

### 5.4 Sprint 1E — Silver Medalists

| Scenario | Ação | Esperado |
|----------|------|----------|
| Busca por vaga | `find_for_vacancy(vacancy_id)` | Candidatos com relevance_score |
| Chat LIA | "Temos candidatos de processos anteriores?" | Usa tool `find_silver_medalists` |
| Alerta automático | ProactiveWorker check | `action_type = "silver_medalists_available"` |

### 5.5 Sprint 2A — Recruiter Intelligence

| Scenario | Ação | Esperado |
|----------|------|----------|
| Backlog | "Quais candidatos estão me esperando?" | Lista priorizada por urgency_score |
| Daily briefing | Abrir chat pela manhã | Resumo automático com ações urgentes |
| Alerta bell | Candidato em offer > 2 dias | Bell notification para o recrutador correto |

---

## 6. Regras para Adicionar Golden Cases

1. **Sem dados reais:** Nunca usar nomes, CPFs, emails ou dados de candidatos reais
2. **Determinístico:** Scores e resultados devem ser calculáveis sem LLM
3. **Distribuição equilibrada:** Manter proporção entre grupos demográficos
4. **Rastreável:** Cada case deve referenciar o arquivo/linha onde é verificado
5. **Independente:** Cases não devem depender de estado compartilhado

---

## 7. Arquivos de Referência

| Arquivo | Caminho |
|---------|---------|
| Golden Dataset (fairness) | `lia-agent-system/tests/fixtures/golden_dataset.py` |
| Golden Queries (RAGAS) | `lia-agent-system/tests/ragas/golden_queries.py` |
| Four-Fifths Rule tests | `lia-agent-system/tests/fairness/test_four_fifths_rule.py` |
| RAGAS evaluation tests | `lia-agent-system/tests/ragas/test_ragas_evaluation.py` |
| QA Report | `docs/QA_REPORT_SPRINT_2026-02-28.md` |
| GUIA_TESTES_ONDA1 | `docs/analises/GUIA_TESTES_ONDA1.md` |
