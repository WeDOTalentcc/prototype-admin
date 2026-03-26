# WSI — Fluxo Completo Ponta a Ponta
## Guia de Implementação, Metodologia e Referências de Código

> **Versão:** 1.1 — 25/03/2026
> **Audiência:** Time de produto, engenharia e IA da WeDOTalent
> **Documentos relacionados:**
> - Metodologia detalhada: `docs/WSI_METHODOLOGY_COMPLETE_v2.md`
> - Referência resumida: `docs/WSI_METHODOLOGY_REFERENCE.md`
> - Sprint history: `docs/archived/sprint-history.md`

---

## 0. Mapa Geral do Fluxo

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    BLOCO A — CRIAÇÃO DA VAGA                            ║
║                    (feito pelo recrutador, uma vez por vaga)            ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  F1 ──► F2.5 ──► F3 ──► F4 ──► F5                                      ║
║  JD     Big Five  Rank   Sen.   Distribuição                            ║
║  Enrich Extract   Traits Resol. T/B por perfil                          ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                    BLOCO B — TRIAGEM DO CANDIDATO                        ║
║                    (executado por candidato, por triagem)               ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  F6 ──► F7 ──► F8 ──► F9 ──► F10 ──► F11                              ║
║  Gen.   Coleta  Aval.  WSI   Gates  Relatório                          ║
║  Pergs  Resp.   4 cam. Final Decisão + Feedback                        ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### Canais de Execução (F7)

```
                    ┌─ E1: Assíncrono (email/link)
                    │   /wsi/async/{token}  [Redis, TTL 72h]
F6 Perguntas ───────┤
                    ├─ E2: Síncrono (portal web)
                    │   LangGraph WSIInterviewGraph
                    │
                    └─ E3: Voz (telefônico)
                        WSIVoiceOrchestrator + OpenMic.ai
```

---

## 1. BLOCO A — Criação da Vaga

---

### F1 — Enriquecimento do JD e Avaliação de Qualidade

**Objetivo:** Transformar o JD bruto do recrutador em um JD estruturado e enriquecido com mínimos garantidos para o pipeline WSI.

#### Ponto de Entrada no Código

| Arquivo | Classe / Função |
|---------|----------------|
| `app/domains/job_management/services/jd_enrichment_service.py` | `JdEnrichmentService.enrich_job_description()` |
| `app/services/jd_enrichment_service.py` | Alias → domínio acima |
| `app/api/v1/wsi_question_adjust.py` | `POST /wsi/jd-evaluate` |

#### Dependências Internas

```python
JdEnrichmentService
  ├── MarketBenchmarkService       # Glassdoor, LinkedIn — salário e demanda
  ├── SkillsCatalogService         # Catálogo de competências técnicas
  ├── ResponsibilitiesCatalogService
  ├── CompanyConfigurationService
  └── ATSJobHistoryService         # Histórico de vagas da empresa
```

#### Mínimos WSI Verificados (F1.B — Score Determinístico)

```python
# app/domains/job_management/services/jd_enrichment_service.py
MIN_TECHNICAL_SKILLS_FOR_WSI    = 9   # D3: abaixo → aviso de cobertura limitada
MIN_BEHAVIORAL_COMPETENCIES_WSI = 5   # D4: abaixo → aviso
MIN_RESPONSIBILITIES             = 5
```

| Score JD | Nível | Comportamento |
|----------|-------|---------------|
| < 30 | Crítico | `ready_for_processing: false` — bloqueio hard |
| 30–49 | Insuficiente | Aviso — pipeline prossegue com ressalvas |
| 50–69 | Adequado | OK |
| 70–84 | Bom | OK |
| 85–100 | Excelente | OK |

#### F1.C — Prompt de Enriquecimento (LLM)

**Parâmetros:** `temperature=0.3 | max_tokens=4000 | top_p=0.95`
**Modelo:** Claude Sonnet 4.6 (primário)

**Input:** `{jd_raw}`, `{titulo}`, `{senioridade}`, `{departamento}`, `{setor}`, `{tamanho_empresa}`, `{lista_skills}`

**Output Schema** (`app/schemas/jd_enrichment.py` → `EnrichedJobDescription`):

```python
class EnrichedJobDescription(BaseModel):
    titulo_padronizado: str
    senioridade_confirmada: str
    about_role: str
    responsabilidades: List[str]
    skills_obrigatorias: List[{"skill": str, "contexto": str}]
    skills_desejaveis: List[str]
    competencias_comportamentais: List[{
        "competencia": str,
        "contexto": str,
        "trait_big_five": "openness|conscientiousness|extraversion|agreeableness|stability"
    }]
    context_signals: {
        "nivel_autonomia": "baixo|medio|alto",
        "nivel_inovacao": "baixo|medio|alto",
        "nivel_pressao": "baixo|medio|alto",
        "nivel_colaboracao": "baixo|medio|alto"
    }
    alteracoes_realizadas: List[str]
    fairness_corrections: List[str]
    wsi_quality_score: float       # score 0-100 calculado deterministicamente
    wsi_quality_warnings: List[str]
```

**Schemas relevantes:**

```python
# app/schemas/jd_enrichment.py
class TechnicalSkillSuggestion(EnrichedSuggestion):
    proficiency_level: Optional[str]
    market_demand_trend: Literal["rising", "stable", "declining"]

class BehavioralCompetencySuggestion(EnrichedSuggestion):
    big_five_mapping: Optional[str]   # trait OCEAN pré-mapeado
    assessment_methods: List[str]
```

#### F1.D — Apresentação ao Recrutador

O recrutador vê JD original (esquerda) + JD enriquecido (direita) + badge de qualidade (inferior).
**Aprovação obrigatória** → `jd_approved = true` antes de avançar para F2.

#### F1.E — Integração downstream: enriched_jd → Pipeline WSI

Após aprovação do recrutador, o `enriched_jd` vira a fonte canônica para todo o pipeline. Isso impacta diretamente F2.5 e F6.6:

| Campo de `enriched_jd` | Consumido por | Como |
|---|---|---|
| `about_role` + `responsabilidades` | F2.5 `_extract_ocean_scores()` | Texto de contexto limpo (sem ruído do JD bruto) |
| `skills_obrigatorias[{skill, contexto}]` | F6.5 `_generate_cbi_question()` / `_generate_bloom_question()` | Nome + contexto passados no prompt técnico |
| `competencias_comportamentais[{competencia, trait_big_five}]` | F6.6 `_generate_bigfive_question()` | `big_five_mapping` pré-preenchido → seleção por afinidade de trait |
| `context_signals {pressao, autonomia, inovacao}` | Futuro F3 | Calibração do peso dos traits no ranking |

**Bridge de código:**
```python
# app/domains/cv_screening/services/wsi_service.py
# WSIService._build_competencies_from_enriched_jd(enriched_jd, seniority)
#   → converte dict EnrichedJobDescription em List[Competency] com big_five_mapping
#   → retorna também jd_context (about_role + responsabilidades) para F2.5
#
# WSIService._merge_with_enriched(original_comps, enriched_comps)
#   → copia big_five_mapping do enriquecido para competências sem mapeamento
#   → mantém competências originais; adiciona novas do enriquecido
#
# WSIService.generate_screening_questions(..., enriched_jd=enriched_jd)
#   → chama _build_competencies_from_enriched_jd + _merge_with_enriched antes de generate_all()
```

**Fluxo com enriched_jd:**
```
JD bruto ──► F1.C (LLM, temp=0.3) ──► EnrichedJobDescription
                                              │
                     ┌────────────────────────┤
                     │                        │
                     ▼                        ▼
              UI: lado direito          enriched_jd persiste em
              para revisão              job_vacancies.enriched_jd
              recrutador (F1.D)                 │
                                               ▼
                                    WSIService.generate_screening_questions(
                                        competencies=[...],
                                        enriched_jd=enriched_jd  ← NOVO
                                    )
                                        │
                                        ├─▶ _build_competencies_from_enriched_jd()
                                        │     └─▶ Competency.big_five_mapping preenchido
                                        │
                                        ├─▶ job_description = about_role + responsabilidades
                                        │     └─▶ F2.5 usa texto limpo
                                        │
                                        └─▶ generate_all() → F6.6 _select_comp_by_trait()
                                                └─▶ match exato: trait == big_five_mapping
```

#### Conecta com

```
F1 (enriched_jd.about_role + responsabilidades) ──► F2.5 _extract_ocean_scores() — texto limpo
F1 (competencias_comportamentais[trait_big_five]) ──► F6.6 _select_comp_by_trait() — afinidade
F1 (skills_obrigatorias[{skill, contexto}]) ────────► F6.5 prompts técnicos — contexto rico
F1 (context_signals) ───────────────────────────────► Futuro: F3 calibração de pesos
F1 (wsi_quality_score) ─────────────────────────────► Gate de ativação da vaga
```

---

### F2 — Extração do Perfil Big Five do JD

**Objetivo:** Determinar quais dos 5 traits OCEAN a vaga mais exige, com evidências auditáveis.

> **Status de implementação:**
> ✅ Abordagem C (LLM) — única ativa
> ❌ Abordagem A (Léxico/LIWC) — não implementada
> ❌ Abordagem B (Prior O\*NET) — não implementada
> **Fórmula atual:** `score_final = score_C` (sem combinação)

#### F2.5 — Abordagem C: LLM com Rubric NEO-PI-R ✅

**Ponto de Entrada:**

| Arquivo | Método |
|---------|--------|
| `app/domains/cv_screening/services/wsi_service.py` | `WSIQuestionGenerator._extract_ocean_scores()` |

**Parâmetros LLM:** `temperature=0.1 | max_tokens=800`
**Modelo:** Claude Sonnet 4.6

**Assinatura:**
```python
async def _extract_ocean_scores(
    self,
    job_description: str,           # enriched_jd de F1
    behavioral_competencies: Optional[List[str]] = None,  # nomes de F1
) -> List[OceanTraitScore]:
```

**Dataclass de saída** (`wsi_service.py`):
```python
@dataclass
class OceanTraitScore:
    trait: str           # openness|conscientiousness|extraversion|agreeableness|stability
    score: int           # 0-100: intensidade exigida pela vaga
    confidence: str      # high|medium|low — confiança da extração
    evidence: List[str]  # citações literais do JD (requisito EU AI Act)
```

**Rubric de avaliação (5 bandas):**

| Faixa | Significado |
|-------|------------|
| 0–30 | Trait não mencionado ou irrelevante |
| 31–50 | Aparece implicitamente; útil mas não diferenciador |
| 51–70 | Claramente necessário; em responsabilidades/requisitos |
| 71–85 | Central para o papel; múltiplas evidências fortes |
| 86–100 | Absolutamente crítico; vaga inviável sem ele |

**Regras especiais:**
- JD < 50 palavras → `confidence: "low"` em todos os traits
- Sinais contraditórios → prefixo `[SINAL CONTRADITÓRIO]`, score 40-55, `confidence: "medium"`
- Traits sem evidência literal → `evidence: []`, `confidence: "low"`, `score ≤ 30`

**Fallback (LLM failure):**
```python
_FALLBACK = {t: {"score": 60, "evidence": [], "confidence": "low"}
             for t in ["openness", "conscientiousness", "extraversion",
                       "agreeableness", "stability"]}
```

#### ~~Abordagem A — Léxico/LIWC~~ *(Não considerado)*

> Requereria LIWC licenciado ou dicionário OCEAN customizado PT-BR.
> Peso futuro na fórmula: `0.25 × score_A`

#### ~~Abordagem B — Prior O\*NET~~ *(Não considerado)*

> O\*NET é US-centric — inadequado para vagas brasileiras.
> Substituição futura: prior com dados históricos próprios da plataforma.
> Peso futuro na fórmula: `0.35 × score_B`

#### Conecta com

```
F2.5 (List[OceanTraitScore]) ──► F3 _select_traits_by_seniority()
```

---

### F3 — Ranking Ponderado de Traits

**Objetivo:** Ordenar os 5 traits por relevância para a vaga e selecionar os top-N conforme senioridade.

**Ponto de Entrada:**

| Arquivo | Método |
|---------|--------|
| `app/domains/cv_screening/services/wsi_service.py` | `WSIQuestionGenerator._select_traits_by_seniority()` |

**Implementação atual:**
```python
def _select_traits_by_seniority(
    self,
    ranked_traits: List[OceanTraitScore],  # ordenados por score desc (F2.5)
    seniority: str,
) -> List[OceanTraitScore]:
    key = seniority.lower().strip().replace(" ", "_").replace("-", "_")
    n = SENIORITY_BIGFIVE_TOP_N.get(key, 3)
    return ranked_traits[:n]   # top-N traits para geração de perguntas BigFive
```

**Constante `SENIORITY_BIGFIVE_TOP_N`** (wsi_service.py):

| Senioridade | N (traits avaliados) |
|-------------|---------------------|
| estagiario, junior | 2 |
| pleno, senior | 3 |
| lead, principal | 4 |
| diretor, vp_clevel | 5 |

#### ~~Fórmula Completa F3~~ *(Referência futura — não implementada)*

```python
# Quando Abordagens A e B estiverem implementadas:
score_final = score_C * 0.40 + score_B * 0.35 + score_A * 0.25
# Boost por senioridade aplicado após (ver metodologia v2, seção 3.2)
```

**Logs emitidos:**
```python
logger.info(f"WSI F2.5 OCEAN ranked: {[(t.trait, t.score) for t in ranked]}")
logger.info(f"WSI F5 selected ({len(selected_traits)} for '{seniority}'): {[t.trait for t in selected_traits]}")
```

#### Conecta com

```
F3 (List[OceanTraitScore] top-N) ──► F5 → F6.6 _generate_bigfive_question(ocean_trait=trait)
```

---

### F4 — Resolução de Senioridade

**Objetivo:** Determinar a senioridade efetiva da vaga quando não informada explicitamente (multi-signal).

**Ponto de Entrada:**

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/domains/cv_screening/services/seniority_resolver.py` | `resolve_seniority_full()` — motor multi-sinal 100% determinístico |
| `app/domains/cv_screening/services/wsi_screening_pipeline.py` | Chamador — passa todos os sinais e consome o resultado |
| `app/services/seniority_jd_analyzer.py` | Sinal 3 — análise semântica do JD |

**Cinco sinais combinados** (motor determinístico, sem LLM):

| # | Sinal | Peso | Fonte no Request |
|---|-------|------|-----------------|
| 1 | Senioridade explícita do recrutador | 0.50 | `request.seniority` |
| 2 | Palavras-chave no título do cargo | 0.25 | `request.job_title` |
| 3 | Análise semântica do JD | 0.25 | `request.job_description` |
| 4 | Faixa salarial vs. benchmark de mercado | 0.15 | `request.salary_min / salary_max` |
| 5 | Complexidade das skills técnicas | 0.10 | `request.technical_skills` |

> Pesos redistribuídos proporcionalmente quando sinais estão ausentes.

**Output em `WSIScreeningPipelineResponse.seniority_resolution`:**
```json
{
  "resolved": true,
  "source": "multi_signal",
  "effective_level": "senior",
  "confidence": 0.85,
  "agreement": "majority",
  "signals": [{"source": "title_keywords", "level": "senior", "confidence": 0.80, ...}],
  "warnings": [],
  "requires_confirmation": false
}
```

**Regras do motor de combinação:**

| Regra | Condição | Confiança | `agreement` |
|-------|----------|-----------|-------------|
| 1 | Todos concordam | 1.00 | `full` |
| 2 | Maioria (2+ sinais) | 0.85 | `majority` |
| 3 | Conflito explícito vs. inferido | 0.40 | `conflict` → `requires_confirmation: true` |
| 4 | Sinal único | 0.50–0.70 | `single` |
| 5 | Sem sinais | 0.00 | `none` → default `pleno` |

#### Conecta com

```
F4 (effective_seniority) ──► F5 SENIORITY_DISTRIBUTIONS
                         ──► F3 SENIORITY_BIGFIVE_TOP_N
                         ──► F8/F9 SENIORITY_WEIGHTS (técnico/comportamental)
```

---

### F5 — Distribuição Adaptativa de Perguntas por Senioridade

**Objetivo:** Determinar quantas perguntas técnicas vs. comportamentais gerar conforme senioridade e modo.

**Ponto de Entrada:**

| Arquivo | Classe / Constante |
|---------|-------------------|
| `app/domains/cv_screening/constants/wsi_constants.py` | `SENIORITY_DISTRIBUTIONS` — **fonte canônica** da tabela T/B |
| `app/domains/cv_screening/services/wsi_screening_pipeline.py` | `WSIScreeningPipeline.build_pipeline()` — usa distribuição via import |
| `app/domains/cv_screening/services/wsi_service.py` | `WSIQuestionGenerator.generate_all()` — distribuição adaptativa ativa (WSI-8 ✅) |

**Tabela de Distribuição** (`wsi_constants.py → SENIORITY_DISTRIBUTIONS`):

| Senioridade | Compact (7) | Full (12) |
|-------------|-------------|-----------|
| Estagiário | 5T + 2B | 9T + 3B |
| Junior | 5T + 2B | 9T + 3B |
| Pleno | 5T + 2B | 8T + 4B |
| Senior | 4T + 3B | 7T + 5B |
| Lead | 3T + 4B | 7T + 5B |
| Principal | 4T + 3B | 7T + 5B |
| Diretor | 3T + 4B | 7T + 5B |
| Executive/VP | 2T + 5B | 7T + 5B |

**Alocação intra-framework em `generate_all()`** (deduzida deterministicamente de T e B):

| Framework | Compact | Full |
|-----------|---------|------|
| CBI técnico | `max(1, T − has_dreyfus − has_bloom)` | `max(1, T − dreyfus_n − bloom_n)` |
| Dreyfus | 1 se T ≥ 2, senão 0 | `min(2, max(0, T − 3))` |
| Bloom | 1 se T ≥ 3, senão 0 | `min(2, max(0, T − 1 − dreyfus_n))` |
| CBI comportamental | sempre 1 | `max(1, B − 2)` |
| BigFive | `B − 1` | `B − cbi_behav_n` (fixo em 2 para todos os níveis full) |

> Exemplo compact Senior (4T+3B): CBI_tech=2, Dreyfus=1, Bloom=1, CBI_behav=1, BigFive=2
> Exemplo compact Junior (5T+2B): CBI_tech=3, Dreyfus=1, Bloom=1, CBI_behav=1, BigFive=1

**Blocos no Pipeline:**

| Bloco | Conteúdo | Editável |
|-------|----------|---------|
| 0 | Abordagem Inicial | ❌ |
| 1 | Apresentação da Oportunidade | ❌ |
| 2 | Perguntas Padrão da Empresa (elegibilidade) | ✅ |
| 3 | Avaliação Técnica (Bloom/Dreyfus) | ✅ |
| 4 | Comportamental e Fit (BigFive/CBI) | ✅ |
| 5 | Resultado e Encerramento | ❌ |

**Perguntas de Ação Afirmativa** (quando `is_affirmative=True`):

```python
# wsi_screening_pipeline.py → AFFIRMATIVE_QUESTIONS
types = ["pcd", "racial", "gender", "age", "lgbtqia+"]
# Todas NÃO-eliminatórias — candidato informado explicitamente
```

#### Conecta com

```
F5 (distribuição T/B) ──► F6 geração de perguntas por framework
```

---

## 2. BLOCO B — Triagem do Candidato

---

### F6 — Geração de Perguntas WSI

**Objetivo:** Gerar as perguntas calibradas por framework científico (CBI, Bloom, Dreyfus, BigFive), ancorando em skills específicas da vaga.

#### Ponto de Entrada Principal

| Arquivo | Classe / Método |
|---------|----------------|
| `app/domains/cv_screening/services/wsi_service.py` | `WSIQuestionGenerator.generate_all()` |
| `app/domains/cv_screening/services/wsi_screening_pipeline.py` | `WSIScreeningPipeline.build_pipeline()` |
| `app/domains/cv_screening/services/wsi_question_generator.py` | `WSIScreeningQuestionGenerator.generate_questions()` |

#### Assinatura `generate_all()`

```python
async def generate_all(
    self,
    competencies: List[Competency],
    mode: Literal["compact", "full"] = "compact",
    job_description: Optional[str] = None,    # enriched_jd de F1
    seniority: Optional[str] = None,          # para F3/F5
) -> List[WSIQuestion]:
```

#### Frameworks por tipo de pergunta

**F6.5 — Perguntas Técnicas (CBI + Bloom + Dreyfus)**

| Parâmetro | Valor |
|-----------|-------|
| Temperature | 0.7 |
| max_tokens | 200 |
| top_p | 0.95 |
| Método | `_generate_cbi_question()`, `_generate_dreyfus_question()`, `_generate_bloom_question()` |

**F6.6 — Perguntas Comportamentais (BigFive)**

| Parâmetro | Valor |
|-----------|-------|
| Temperature | 0.8 |
| max_tokens | 250 |
| top_p | 0.95 |
| Método | `_generate_bigfive_question(competency, ocean_trait=trait)` |

**Temperatura por framework** (implementada em `wsi_service.py`):

```python
CBI      → temperature=0.7   # _generate_cbi_question()
Dreyfus  → temperature=0.75  # _generate_dreyfus_question()
Bloom    → temperature=0.75  # _generate_bloom_question()
BigFive  → temperature=0.8   # _generate_bigfive_question()
```

#### F6.6 — Mecânica de Seleção: Competência × Trait (WSI-7)

A pergunta Big Five tem **dois inputs distintos** que devem estar alinhados:

| Input | Papel no prompt | Origem |
|---|---|---|
| `competency.name` | Ancora o **conteúdo** — situação real do trabalho | Lista `behavioral` do WSIService |
| `ocean_trait` | Calibra o **foco** — qual trait OCEAN revelar | F2.5 → F3 → F5 pipeline |

**Seleção por afinidade de trait (`_select_comp_by_trait()`):**

```python
# app/domains/cv_screening/services/wsi_service.py
# WSIQuestionGenerator._select_comp_by_trait(trait, behavioral, used_indices)
#
# Estratégia:
# 1. Match exato:  behavioral[i].big_five_mapping == trait → usa esse
# 2. Fallback:     próxima competência não usada (seleção posicional)
# 3. Último recurso: behavioral[0]

# Exemplo — compact mode:
used_bf = set()
trait1 = selected_traits[0].trait   # ex: "conscientiousness"
bigfive_comp1, idx1 = self._select_comp_by_trait(trait1, behavioral, used_bf)
# → retorna competência com big_five_mapping="conscientiousness" (ex: "Organização")
used_bf.add(idx1)

trait2 = selected_traits[1].trait   # ex: "agreeableness"
bigfive_comp2, idx2 = self._select_comp_by_trait(trait2, behavioral, used_bf)
# → retorna competência com big_five_mapping="agreeableness" (ex: "Colaboração")
```

**Exemplo de alinhamento correto:**

| competency.name | ocean_trait | Qualidade |
|---|---|---|
| "Organização" (`big_five_mapping="conscientiousness"`) | "conscientiousness" | ✅ Alinhado |
| "Colaboração" (`big_five_mapping="agreeableness"`) | "agreeableness" | ✅ Alinhado |

**Pré-requisito:** `Competency.big_five_mapping` deve estar preenchido — vem do `enriched_jd` via bridge F1.E ou pode ser passado diretamente na lista de competências.

#### Pipeline F2.5 → F3 → F5 → F6.6 dentro de `generate_all()`

```python
# Quando job_description disponível:
ranked = await self._extract_ocean_scores(job_description, behav_names)
selected_traits = self._select_traits_by_seniority(ranked, seniority)

# F6.6: seleção por afinidade de trait (WSI-7):
used_bf: set = set()
trait1 = selected_traits[0].trait if len(selected_traits) > 0 else None
if trait1 and behavioral:
    bigfive_comp1, idx1 = self._select_comp_by_trait(trait1, behavioral, used_bf)
    used_bf.add(idx1)
else:
    bigfive_comp1 = behavioral[1] if len(behavioral) > 1 else behavioral[0]  # fallback
questions.append(await self._generate_bigfive_question(bigfive_comp1, ocean_trait=trait1))
```

**Labels PT-BR dos traits** (mapeados em `_generate_bigfive_question()`):

```python
_TRAIT_LABELS = {
    "openness":          "Abertura a mudanças — inovação, curiosidade, aprendizado",
    "conscientiousness": "Organização e disciplina — entregas, rigor, método",
    "extraversion":      "Sociabilidade — comunicação, assertividade, energia",
    "agreeableness":     "Cooperação — empatia, colaboração, gestão de stakeholders",
    "stability":         "Estabilidade emocional — resiliência sob pressão",
}
```

**`ocean_trait` salvo em `scoring_criteria`:**
```python
scoring_criteria["ocean_trait"] = ocean_trait   # auditável por pergunta
```

#### Schema da Pergunta Gerada

```python
# app/domains/cv_screening/services/wsi_service.py
class WSIQuestion(BaseModel):
    id: str
    competency: str
    framework: str          # CBI | Bloom | Dreyfus | BigFive
    question_type: str      # contextual | situational | autodeclaration | microcase
    question_text: str
    weight: float
    expected_signals: List[str]
    scoring_criteria: Dict[str, Any]   # inclui ocean_trait quando BigFive
    is_critical: bool = False          # máximo 2 por triagem (Gate G4)
```

#### Ajuste em Linguagem Natural

Recrutadores podem ajustar perguntas via texto livre:

| Arquivo | Classe | Endpoint |
|---------|--------|----------|
| `app/domains/cv_screening/services/wsi_question_adjuster.py` | `WSIQuestionAdjusterService.adjust_questions()` | `POST /wsi/questions/adjust` |

```python
# Limites:
MAX_ITERATIONS_PER_BLOCK = 5
# LLM: Google Gemini 2.0 Flash (iterações rápidas)
```

#### F6.8 — Validação automática pós-geração ✅ WSI-8

Implementado em `wsi_service.py` via `_generate_with_validation()`.
Spec completa: `docs/WSI_METHODOLOGY_COMPLETE_v2.md` §6.8 e §6.8.1.

**Fluxo (até 3 tentativas por pergunta):**

```
gen_fn(competency) → Estágio 1: determinístico → Estágio 2: LLM ancoragem (se JD disponível)
                           ↓ falha                        ↓ falha
                    regenera c/ hint              regenera c/ suggestion do LLM
                           ↓ 3ª falha                     ↓ 3ª falha
                    needs_manual_review=True       needs_manual_review=True
```

**Estágio 1 — `_validate_deterministic(text)` (~0 ms, regex):**

| Critério | Verificação | Flag |
|---|---|---|
| Comprimento | 15–80 palavras | `length_out_of_range` |
| Não hipotética | Ausência de "como você faria se", "imagine que" | `hypothetical_phrasing` |
| Não tendenciosa | Ausência de marcadores de gênero, origem, religião | `bias_marker_detected` |
| Situacional | Presença de verbo situacional (Conte/Descreva/…) | `missing_situational_verb` |

**Estágio 2 — `_validate_jd_anchor()` (LLM, temp=0.0, max_tokens=300):**

Invocado somente se `job_description` foi passado a `generate_all()`.
Verifica ancoragem real no JD — evita perguntas genéricas válidas para qualquer cargo.
Retorna `is_anchored`, `evidence_in_jd`, `anchor_type`, `suggestion` (reformulação se não ancorada).

**Campos no `WSIQuestion` (F6.8):**

```python
needs_manual_review: bool          # True após 3 falhas (qualquer estágio)
validation_flags: Dict[str, Any]   # det. flags ou metadados de ancoragem
```

#### Persistência das Perguntas

```python
# app/api/v1/wsi_question_adjust.py → POST /wsi/questions/save
class ScreeningQuestionSet(Base):     # libs/models/lia_models/screening_question_set.py
    questions_snapshot: JSON          # imutável para auditoria
    questions_hash: str               # SHA256
    version: int                      # versionamento automático
    block_distribution: JSON          # {"block_2": 2, "block_3": 5, "block_4": 3}
```

#### Conecta com

```
F6 (List[WSIQuestion]) ──► F7 canal de coleta selecionado
F6 (questions persisted in ScreeningQuestionSet) ──► audit trail
```

---

### F7 — Coleta de Respostas (Canais)

**Objetivo:** Coletar respostas do candidato pelo canal configurado para a vaga.

#### E1 — Assíncrono (email/link)

| Arquivo | Endpoints |
|---------|-----------|
| `app/api/v1/wsi_async.py` | `POST /wsi/async/invite` → cria token |
| | `GET /wsi/async/{token}` → obtém próxima pergunta |
| | `POST /wsi/async/{token}/answer` → submete resposta |
| | `GET /wsi/async/{token}/complete` → finaliza |

```python
class InviteRequest(BaseModel):
    candidate_id: str
    job_id: str
    company_id: str
    expire_hours: int = 72    # TTL Redis padrão

class AnswerRequest(BaseModel):
    answer: str
```

**Armazenamento:** Redis com TTL 72h (sessão completa)

#### E2 — Síncrono (portal web / LangGraph)

| Arquivo | Classe |
|---------|--------|
| `app/domains/cv_screening/agents/wsi_interview_graph.py` | `WSIInterviewNodes` |

**State Machine LangGraph:**

```python
class WSIInterviewStage(str, Enum):
    INIT           = "init"
    LOAD_CONTEXT   = "load_context"
    GENERATE_QUESTION = "generate_question"
    AWAIT_RESPONSE = "await_response"
    VALIDATE_RESPONSE = "validate_response"
    SCORE_RESPONSE = "score_response"
    ADVANCE        = "advance"
    GENERATE_FEEDBACK = "generate_feedback"
    COMPLETE       = "complete"
    ERROR          = "error"
```

**Por que State Machine e não ReAct?**
- Fluxo sequencial determinístico: pergunta 1 → 2 → N → resultado
- Cada etapa rastreável individualmente (compliance BCB 498, SOX)
- Sem decisão autônoma — transições por regras explícitas
- Auditável: `execution_log` completo em `WSIInterviewState`

**Estado completo da sessão** (`WSIInterviewState`):
```python
@dataclass
class WSIInterviewState:
    session_id: str
    company_id: str
    candidate_id: str
    job_id: str
    interview_level: str           # "quick" | "standard" | "full"
    question_blocks: List[WSIQuestionBlock]
    current_question_index: int
    responses: List[WSIResponseRecord]
    technical_score: float
    behavioral_score: float
    wsi_final_score: Optional[float]
    recommendation: str            # "aprovado" | "aguardando" | "reprovado"
    stage: WSIInterviewStage
    execution_log: List[Dict[str, Any]]  # auditoria completa
```

**Nodes do grafo:**
```python
class WSIInterviewNodes:
    async def load_context(state) -> WSIInterviewState
    async def generate_question(state) -> WSIInterviewState
    async def score_response(state) -> WSIInterviewState
    async def generate_feedback(state) -> WSIInterviewState
```

#### E3 — Voz (telefônico)

| Arquivo | Classe | Integração |
|---------|--------|------------|
| `app/domains/cv_screening/services/wsi_voice_orchestrator.py` | `WSIVoiceOrchestrator` | OpenMic.ai |

**Fluxo de voz:**
```python
async def start_voice_screening(
    candidate_id, job_vacancy_id, competencies,
    candidate_phone, candidate_name,
    job_title, job_description, seniority,
    mode="compact", db=None
) -> VoiceScreeningResult:

    # 1. Gera perguntas WSI
    questions = await wsi_service.generate_screening_questions(
        competencies, mode, job_description=job_description, seniority=seniority
    )

    # 2. Persiste sessão
    INSERT INTO wsi_sessions (id, candidate_id, job_vacancy_id, mode, status, ...)
    INSERT INTO wsi_questions (id, session_id, competency, framework, ...)

    # 3. Cria agente OpenMic + inicia chamada
    agent_id = openmic.create_agent(questions)
    call_id  = openmic.start_call(candidate_phone, agent_id)

async def process_call_completed(call_id, transcript, transcript_object, db):
    # 4. Parse Q/A pairs do transcript
    # 5. Calcula WSI scores (determinístico)
    # 6. Gera feedback
    # 7. Persiste VoiceScreeningCall + VoiceScreeningAnalysis
```

**Modelos de DB:**

```python
# libs/models/lia_models/voice_screening.py
class VoiceScreeningCall(Base):
    __tablename__ = "voice_screening_calls"
    call_id: str      # OpenMic call ID
    candidate_id: str
    job_title: str
    transcript: Text
    transcript_object: JSON    # com timestamps
    processing_status: str     # pending|analyzing|completed|failed
    # OneToOne → VoiceScreeningAnalysis

class VoiceScreeningAnalysis(Base):
    __tablename__ = "voice_screening_analyses"
    tech_score: int            # 0-100
    comm_score: int            # 0-100
    fit_score: int             # 0-100
    overall_score: int         # 0-100 (indexed)
    overall_recommendation: str  # reject|maybe|interview|strong_yes (indexed)
    key_strengths: JSON
    key_concerns: JSON
    full_analysis_payload: JSON   # para debugging/auditoria
```

**Webhook de conclusão:**
```
POST /webhook/openmic/call-completed
  └─► WSIVoiceOrchestrator.process_call_completed()
```

#### Conecta com

```
F7 (respostas coletadas) ──► F8 avaliação por resposta
```

---

### F8 — Avaliação das Respostas (4 Camadas)

**Objetivo:** Calcular score 0-10 por resposta usando 4 camadas em sequência: STAR determinístico → LLM extrator → fórmula tri-componente → output.

#### Camada 1 — STAR Determinístico (SEM LLM)

**Arquivo:** `app/domains/cv_screening/services/wsi_deterministic_scorer.py`

```python
# Detecção por keywords — SEM LLM
STAR_COMPONENT_WEIGHTS = {"S": 0.20, "T": 0.20, "A": 0.40, "R": 0.20}

# star_score = S×0.20 + T×0.20 + A×0.40 + R×0.20 (0.0–1.0)
```

**Outras métricas determinísticas (SEM LLM):**
```python
def extract_autodeclaracao_score(text: str) -> Optional[float]  # escala 1-5 no texto
def calculate_context_score(text, evidences) -> float           # alta/média/baixa qualidade
def calculate_bloom_level(text) -> Tuple[int, str]              # 1-6 (Recordar→Criar)
def calculate_dreyfus_level(years, context_score, ...) -> Tuple[int, str]  # 1-5
```

**Penalidades e Bônus:**
```python
PENALTY_TRIGGERS = {
    "inflation":   -1.0,  # resposta inflada, sem evidência
    "generic":     -0.5,  # resposta genérica sem contexto
    "no_context":  -0.3,  # sem situação específica
}
BONUS_TRIGGERS = {
    "humility":             +0.5,  # demonstra consciência de limitações
    "exceptional_evidence": +0.3,  # evidência concreta excepcional
}
```

#### Camada 2 — LLM Extrator de Sinais (F8.3)

**Parâmetros:** `temperature=0.0 | max_tokens=800 | top_p=1.0`

**Campos extraídos pelo LLM:**
```python
signals_detected: List[str]    # sinais positivos
signals_absent: List[str]      # sinais esperados ausentes
bloom_demonstrated: int        # nível Bloom demonstrado na resposta
dreyfus_demonstrated: int      # nível Dreyfus demonstrado
key_quote: str                 # trecho chave para F11.7
inflation_detected: bool       # estruturado (não string)
_llm_fallback: bool            # True se LLM falhou — aplicado fallback conservador
```

#### Camada 3 — Fórmula Tri-Componente (F8)

**Arquivo:** `app/domains/cv_screening/services/wsi_deterministic_scorer.py`

```python
WSI_FORMULA_WEIGHTS_TECHNICAL = {
    "autodeclaracao":      0.35,
    "evidencias_tecnicas": 0.40,
    "bloom_alinhamento":   0.25,
}

WSI_FORMULA_WEIGHTS_BEHAVIORAL = {
    "star_estrutura":      0.35,
    "sinais_trait":        0.40,
    "bloom_alinhamento":   0.25,
}

# bloom_alinhamento = diferença normalizada entre bloom_demonstrado e bloom_esperado
# star_estrutura = star_score (camada 1)

# Score clampado: max(0.0, min(10.0, score))
```

**Dataclass de resultado:**
```python
@dataclass
class DeterministicWSIResult:
    autodeclaracao_score: float
    context_score: float
    bloom_level: int           # demonstrado
    dreyfus_level: int         # demonstrado
    evidences: List[str]
    red_flags: List[str]
    penalty: float
    bonus: float
    final_score: float         # 0.0–10.0
    formula_applied: str
    formula_version: str = "v2"
    star_components: Optional[Dict[str, bool]]
    star_score: float
    bloom_alignment: float
    flags_structured: Optional[Dict[str, bool]]  # is_inflation, is_generic, is_short
```

#### Camada 4 — Output e Acumulação

**Arquivo:** `app/domains/cv_screening/agents/wsi_interview_graph.py`

```python
# Acumulação por resposta (WSI-1 implementou):
# Running weighted average por peso da competência
# (não mais (old+new)/2 simples)
```

**F8.5.1 — Template Determinístico de Feedback** (WSI-4):
```python
# app/domains/cv_screening/services/personalized_feedback_service.py
# 3 blocos fixos:
# BLOCO_POSITIVO: baseado em score_qualitativo
# BLOCO_DESENVOLVIMENTO: top-2 gaps (maior delta Bloom/Dreyfus)
# BLOCO_NIVEL: mensagem por decisão (APROVADO/EM_AVALIACAO/REPROVADO)
```

#### Conecta com

```
F8 (DeterministicWSIResult por pergunta) ──► F9 composição WSI final
F8 (key_quote, signals, inflation_detected) ──► F11.7 relatório
```

---

### F9 — Composição WSI Final

**Objetivo:** Calcular os scores WSI_técnico, WSI_comportamental e WSI_final ponderados por senioridade.

**Arquivo:** `app/domains/cv_screening/agents/wsi_interview_graph.py`

#### Pesos por Senioridade (SENIORITY_WEIGHTS)

**Arquivo:** `app/domains/cv_screening/services/wsi_deterministic_scorer.py`

```python
SENIORITY_WEIGHTS = {
    "estagiario": {"technical": 0.6875, "behavioral": 0.3125},
    "junior":     {"technical": 0.625,  "behavioral": 0.375},
    "pleno":      {"technical": 0.6875, "behavioral": 0.3125},
    "senior":     {"technical": 0.5625, "behavioral": 0.4375},
    "lead":       {"technical": 0.4375, "behavioral": 0.5625},
    "principal":  {"technical": 0.50,   "behavioral": 0.50},
    "diretor":    {"technical": 0.3125, "behavioral": 0.6875},
    "vp_clevel":  {"technical": 0.25,   "behavioral": 0.75},
}
```

#### Fórmula Final

```python
WSI_final = (WSI_tecnico  × weights["technical"]
           + WSI_comport. × weights["behavioral"])

# WSI_comportamental: ponderado pelos scores dos traits selecionados em F3
# (proporcional ao score_C de cada trait, não média simples)
# ⚠️ Gap F9-1: verificar se implementação atual usa ponderação por trait score
```

#### Conecta com

```
F9 (WSI_final, WSI_tecnico, WSI_comportamental) ──► F10 gates e decisão
```

---

### F10 — Gates e Decisão Final

**Objetivo:** Aplicar gates de exclusão automática e tomar decisão de triagem.

**Arquivo:** `app/api/v1/wsi.py`

#### Gates (G1–G6)

| Gate | Condição | Ação | Status |
|------|----------|------|--------|
| G1 | Questões eliminatórias do Bloco 2 | Exclusão imediata | ✅ |
| G2 | ≥ 1 tentativa de prompt injection | Reprovado automático | ✅ (WSI-3) |
| G3 | WSI_técnico < 4.0/10 | Reprovado automático | ⚠️ Verificar threshold |
| G4 | Score em skill `is_critical` < 3.0/10 | Reprovado automático | ✅ (WSI-3) |
| G5 | ≥ 50% respostas < 30 palavras | Reprovado (qualidade insuficiente) | ⚠️ Verificar |
| G6 | ≥ 3 perguntas com `inflation_detected=True` | Reprovado automático | ⚠️ Gap F10-5 |

> **Gap F10-5:** Apêndice A.2 do methodology doc especifica G6 = ≥ 3 inflações.
> Verificar threshold atual em `wsi.py`.

**Thresholds de Decisão (Apêndice A.2):**

```python
WSI_CUTOFFS = {
    "approved_auto":  7.5,   # ≥ 7.5/10 → APROVADO
    "review_min":     6.0,   # 6.0–7.4 → EM_AVALIACAO
    "rejected_max":   6.0,   # < 6.0   → REPROVADO
}
# Arquivo: wsi_deterministic_scorer.py
```

**`decision.confidence`** ✅ F10-6 — lógica implementada em `_compute_decision_confidence()` (`app/api/v1/wsi.py`):

| Condição | confidence | human_review_required |
|---|---|---|
| G2 ativado, ou ≥2 `_llm_fallback`, ou variância de scores > 2.0 | `baixa` | `True` |
| WSI ≥ 4.5 sem gates | `alta` | `False` |
| Rejeição clara por G1/G3/G4 (sem G5/G6) | `alta` | `False` |
| Zona borderline (3.0–3.74) | `media` | `True` |
| Aprovação sólida (3.75–4.49) sem gates | `media` | `False` |
| Gates apenas G5/G6 (ambíguos) | `media` | `True` |

`confidence = "baixa"` → sempre força `human_review_required: True`.

#### Red Flags (RF-01 a RF-08)

```python
# wsi_deterministic_scorer.py → detect_red_flags()
# Retorna: Dict[str, bool] com is_inflation, is_generic, is_short
# Usado em F10 G6 e F11.7

CONTEXT_INDICATORS = {
    "high_quality":  [...],   # evidências de resposta detalhada
    "medium_quality": [...],
    "low_quality":   [...],
}
```

#### Conecta com

```
F10 (decision: APROVADO|EM_AVALIACAO|REPROVADO) ──► F11 relatório
F10 (failed_gates: List[str]) ──────────────────► F11.7 prompt + F8.5.1 feedback
F10 (human_review_required) ────────────────────► notificação ao recrutador
```

---

### F11 — Relatório Final e Feedback

**Objetivo:** Gerar o relatório completo para o recrutador (F11.7) e o feedback para o candidato (F8.5.1).

#### F11.5 — Perguntas para Entrevista Presencial ✅ WSI-9

**Arquivo:** `app/api/v1/wsi.py` → `_generate_cbi_questions_llm()`
**Parâmetros:** `temperature=0.6 | max_tokens=600 | retry≤3`
**Status:** ✅ Implementado

Gera 2 perguntas CBI aprofundadas baseadas nos maiores gaps identificados em F8, para uso pelo recrutador na entrevista presencial.

#### F11.7 — Geração do Relatório Completo ✅ WSI-9

**Arquivo:** `app/api/v1/wsi.py` → `get_f11_report()` + `app/domains/cv_screening/services/personalized_feedback_service.py`
**Status:** ✅ Implementado — `GET /wsi/f11-report/{session_id}`

**Parâmetros:** `temperature=0.2`
**Regras de ativação (F11-3 ✅ WSI-10):**
- Triagem em andamento → bloquear (`"Triagem não finalizada"`)
- Relatório já gerado (`wsi_results.f11_report_json IS NOT NULL`) → retornar cache com `already_generated: true` (sem LLM)
- JSON inválido → até 3 retries → `needs_manual_review: true`
- `confidence = "baixa"` → `human_review_required: true` (F10-6 ✅ WSI-10)

**Campos adicionados a `F11ReportResponse`:**
- `human_review_required: bool` — calculado por `_compute_decision_confidence()`
- `already_generated: bool` — `True` quando servido do cache
- `confidence = "baixa"` → sempre `human_review_required: true`

**Estrutura JSON de saída (F11.7):**

```python
{
  "report_header": {
    "report_id", "generated_at", "methodology_version": "2.0",
    "vacancy": {...}, "candidate": {...},
    "scores": {"wsi_final": /10, "wsi_technical": /10, "wsi_behavioral": /10},
    "decision": {"result", "confidence", "human_review_required", "gate_triggered"},
    "red_flags": [...], "questions": [...], "big_five_scores": [...]
  },
  "report_sections": {
    "executive_summary": str,      # 2-4 frases, sem scores numéricos, sem atributos pessoais
    "strengths": [str],            # máx 4, só scores ≥ 7.5/10
    "gaps": [{"texto": str, "severidade": "alta|media|baixa"}],  # máx 4, ordenados
    "key_evidence": [str],         # máx 4, citações/paráfrases das respostas
    "recommendation_rationale": str,
    "next_steps": [str],           # 2-4 ações concretas para o recrutador
    "candidate_feedback": {
      "intro": str,      # NÃO revela scores, gates, ranking, metodologia
      "strengths": [str], "development": [str], "tip": str
    }
  },
  "interview_questions": [...],    # 2 perguntas de F11.5
  "generation_metadata": {
    "temperature": 0.2,
    "fairness_check": str,         # confirmação explícita
    "fields_generated_by_llm": [...],
    "fields_deterministic": [...]
  }
}
```

**F11.6 — UI do Relatório (3 Tabs) — `triagem-details-modal.tsx`**

| Tab | Conteúdo | Status |
|-----|----------|--------|
| Tab 1: Respostas | Perguntas + respostas + scores individuais | ⚠️ Parcial |
| Tab 2: Parecer | executive_summary, strengths, gaps, rationale | ⚠️ Parcial |
| Tab 3: Ranking | Pool averages + tabela de ranking com posição, scores, classificação | ✅ WSI-10 |

#### Retenção LGPD (Apêndice A.2)

| Dado | Retenção |
|------|---------|
| Dados do candidato | 2 anos |
| Relatório de scoring | 5 anos |

---

## 3. Infraestrutura

### 3.1 Banco de Dados — Tabelas WSI

```sql
-- Sessões de triagem
wsi_sessions
  id UUID PK, candidate_id, job_vacancy_id
  screening_type (voice|text), mode (compact|full)
  status (in_progress|completed|cancelled)
  question_set_version, question_set_id
  call_id, agent_id
  created_at, updated_at

-- Perguntas de cada sessão
wsi_questions
  id UUID PK, session_id FK
  competency, framework, question_type
  question_text, weight
  expected_signals JSON, scoring_criteria JSONB
  sequence_order

-- Perguntas customizadas da empresa (Bloco 2)
company_screening_questions
  id UUID PK, company_id (indexed)
  question_text, question_type, options JSON
  is_required, is_eliminatory
  category (availability|salary|work_model|logistics|legal|experience|language|custom)
  order, is_active

-- Conjuntos de perguntas versionados (auditoria)
screening_question_sets
  id UUID PK, job_vacancy_id (indexed)
  version INTEGER
  questions_hash VARCHAR(64)  -- SHA256 para detecção de alteração
  questions_snapshot JSON     -- imutável
  block_distribution JSON     -- {"block_2": 2, "block_3": 5, "block_4": 3}
  source (wsi_generation|template|company_custom)
  is_active BOOLEAN
  UNIQUE INDEX (job_vacancy_id, version)

-- Chamadas de voz
voice_screening_calls
  call_id VARCHAR(255) UNIQUE (indexed)  -- OpenMic ID
  candidate_id (indexed), candidate_name (indexed)
  job_title (indexed), required_skills JSON
  transcript TEXT, transcript_object JSON
  processing_status, is_analyzed BOOLEAN
  created_at (indexed)

-- Análises de voz
voice_screening_analyses
  screening_call_id FK UNIQUE
  tech_score, comm_score, fit_score, overall_score (indexed)
  overall_recommendation (indexed)  -- reject|maybe|interview|strong_yes
  key_strengths JSON, key_concerns JSON
  analysis_status
```

**Schemas SQLAlchemy:**

| Modelo | Arquivo |
|--------|---------|
| `CompanyScreeningQuestion` | `libs/models/lia_models/screening_question.py` |
| `ScreeningQuestionSet` | `libs/models/lia_models/screening_question_set.py` |
| `VoiceScreeningCall` | `libs/models/lia_models/voice_screening.py` |
| `VoiceScreeningAnalysis` | `libs/models/lia_models/voice_screening.py` |

---

### 3.2 Agentes LangGraph

| Agente | Arquivo | Tipo | Uso |
|--------|---------|------|-----|
| `WSIInterviewGraph` | `app/domains/cv_screening/agents/wsi_interview_graph.py` | State Machine | Entrevista síncrona E2 |

**Por que State Machine e não ReAct Agent?**
O pipeline WSI é sequencial e determinístico. State machines garantem rastreabilidade de cada transição (BCB 498, SOX, EU AI Act). Agentes ReAct são usados para tarefas de raciocínio aberto; entrevistas WSI seguem fluxo definido.

**Outros agentes do domínio `cv_screening`:**

```
app/domains/cv_screening/agents/
├── wsi_interview_graph.py      ← State machine WSI
└── [outros agentes do domínio de triagem]
```

---

### 3.3 Endpoints WSI Completos

| Método | Path | Arquivo | Descrição |
|--------|------|---------|-----------|
| POST | `/api/v1/wsi/generate-questions` | `wsi.py` | Gera perguntas Bloom+Dreyfus |
| POST | `/wsi/generate` | `wsi_questions.py` | Gera com Gemini LLM |
| POST | `/wsi/regenerate` | `wsi_questions.py` | Regenera por competências |
| POST | `/wsi/screening-pipeline` | `wsi_screening_pipeline_endpoint.py` | Pipeline unificado (blocos 2,3,4) |
| POST | `/wsi/async/invite` | `wsi_async.py` | Cria sessão assíncrona (E1) |
| GET | `/wsi/async/{token}` | `wsi_async.py` | Obtém próxima pergunta |
| POST | `/wsi/async/{token}/answer` | `wsi_async.py` | Submete resposta |
| GET | `/wsi/async/{token}/complete` | `wsi_async.py` | Finaliza sessão |
| POST | `/wsi/questions/adjust` | `wsi_question_adjust.py` | Ajuste em linguagem natural |
| POST | `/wsi/jd-evaluate` | `wsi_question_adjust.py` | Avalia qualidade do JD |
| POST | `/wsi/questions/save` | `wsi_question_adjust.py` | Persiste perguntas |
| GET | `/wsi/questions/{job_id}` | `wsi_question_adjust.py` | Recupera perguntas salvas |
| GET | `/wsi-observability/{company_id}/correlation` | `wsi_observability.py` | Score vs Hiring Outcome |
| GET | `/wsi-observability/{company_id}/block-accuracy` | `wsi_observability.py` | Acurácia por bloco |
| GET | `/wsi-observability/{company_id}/distribution` | `wsi_observability.py` | Distribuição de scores |
| GET | `/wsi-observability/{company_id}/threshold-analysis` | `wsi_observability.py` | Análise de thresholds |
| GET | `/wsi-observability/{company_id}/summary` | `wsi_observability.py` | KPIs de observabilidade |

---

### 3.4 Integrações Externas

| Integração | Uso no WSI | Arquivo |
|-----------|-----------|---------|
| **Claude Sonnet 4.6** | LLM primário: F1.C, F2.5, F6.5, F6.6, F8.3, F11.7 | `app/services/llm.py → llm_service` |
| **Google Gemini 2.0 Flash** | Question adjustment, fallback | `wsi_question_adjuster.py`, `wsi_questions.py` |
| **OpenMic.ai** | Voice agent + call initiation | `wsi_voice_orchestrator.py` |
| **Deepgram** | STT (integrado no OpenMic) | Indireto |
| **Redis** | Sessões E1 (TTL 72h) | `wsi_async.py` |
| **PostgreSQL + pgvector** | Persistência principal | Todos os serviços |

---

### 3.5 Compliance e Fairness no Pipeline WSI

| Mecanismo | Onde | Arquivo |
|-----------|------|---------|
| **Consent Gate (SEG-4)** | Antes de iniciar triagem | `app/shared/fairness/` |
| **PII Masking** | F1.C e F2.5 — antes de enviar ao LLM | `app/shared/pii_masking.py` |
| **FairnessGuard** | Avaliação de respostas | `app/shared/fairness/fairness_guard.py` |
| **Bias Audit** | Four-Fifths rule | `app/services/bias_audit_service.py` |
| **Audit Log** | Cada nó do WSIInterviewGraph | `WSIInterviewState.execution_log` |
| **HITL Gate** | Decisões com baixa confiança | `app/services/hitl_service.py` |
| **Perguntas Afirmativas** | Vagas de ação afirmativa | `wsi_screening_pipeline.py → AFFIRMATIVE_QUESTIONS` |

**Regras de fairness embutidas em todos os prompts LLM:**
- Linguagem neutra em gênero: "a pessoa candidata", "você"
- 8 atributos protegidos nunca mencionados: gênero, raça, etnia, origem, religião, orientação sexual, estado civil, deficiência
- 12 termos de viés implícito proibidos: "boa aparência", "jovem e dinâmico", "native speaker", etc.
- `candidate_feedback` nunca revela: scores, gates, ranking, metodologia interna

---

## 4. Índice Completo de Arquivos WSI

### Backend — Serviços

```
lia-agent-system/app/domains/cv_screening/services/
├── wsi_service.py ★                # WSIQuestionGenerator, WSIService, OceanTraitScore
│   Funções: generate_all(), _extract_ocean_scores(), _select_traits_by_seniority(),
│            _generate_cbi_question(), _generate_dreyfus_question(),
│            _generate_bloom_question(), _generate_bigfive_question(),
│            _select_comp_by_trait(),                        ← WSI-7: seleção por afinidade de trait
│            generate_screening_questions(enriched_jd=...),  ← WSI-7: aceita enriched_jd opcional
│            _build_competencies_from_enriched_jd(),         ← WSI-7: bridge F1.C → WSI
│            _merge_with_enriched()                          ← WSI-7: mescla big_five_mapping
│   Import: SENIORITY_DISTRIBUTIONS ← de wsi_constants.py  ← WSI-8: distribuição adaptativa F5
│
├── seniority_resolver.py ★         # Motor multi-sinal de resolução de senioridade (F4)
│   Funções: resolve_seniority_full(), resolve_seniority_simple(), resolve_seniority()
│   Classes: SenioritySignal, SeniorityResolution
│   Sinais: explicit(0.50), title_keywords(0.25), jd_analysis(0.25),
│           salary_range(0.15), skills_complexity(0.10)
│
├── wsi_deterministic_scorer.py ★   # Scoring 100% determinístico
│   Funções: calculate_wsi_deterministic(), calculate_final_wsi_score(),
│            detect_red_flags(), extract_autodeclaracao_score(),
│            calculate_bloom_level(), calculate_dreyfus_level()
│   Constantes: SENIORITY_WEIGHTS, BIG_FIVE_RECRUITER_LABELS,
│               WSI_FORMULA_WEIGHTS_TECHNICAL, WSI_FORMULA_WEIGHTS_BEHAVIORAL,
│               WSI_CUTOFFS, STAR_COMPONENT_WEIGHTS
│
├── wsi_question_generator.py       # WSIScreeningQuestionGenerator
│   Constantes: SENIORITY_TO_DREYFUS, SENIORITY_TO_BLOOM, BIG_FIVE_QUESTIONS,
│               TECHNICAL_QUESTION_TEMPLATES
│
├── wsi_voice_orchestrator.py ★     # WSIVoiceOrchestrator
│   Funções: start_voice_screening(enriched_jd=...),  ← WSI-7: aceita enriched_jd opcional
│            process_call_completed()
│
├── wsi_screening_pipeline.py ★     # WSIScreeningPipeline
│   Funções: build_pipeline(), apply_screening_policy(), get_screening_policy()
│   Constantes: MODEL_DISTRIBUTIONS, AFFIRMATIVE_QUESTIONS
│   Import: SENIORITY_DISTRIBUTIONS ← de wsi_constants.py (F4+F5: sinais completos + distribuição)
│
├── wsi_question_adjuster.py        # WSIQuestionAdjusterService
│   Funções: adjust_questions(), evaluate_job_description()
│   Constantes: WSI_BLOCKS, MAX_ITERATIONS_PER_BLOCK
│
└── personalized_feedback_service.py  # Feedback F8.5.1
    Funções: send_approval_feedback(), send_review_feedback()
```

### Backend — Agentes

```
lia-agent-system/app/domains/cv_screening/agents/
└── wsi_interview_graph.py ★       # LangGraph State Machine
    Classes: WSIInterviewStage, WSIQuestionBlock, WSIResponseRecord,
             WSIInterviewState, WSIInterviewNodes
```

### Backend — Schemas

```
lia-agent-system/app/domains/cv_screening/schemas/
└── screening.py
    Classes: BigFiveProfile, UnifiedScreeningQuestion,
             WSIScreeningPipelineRequest, WSIScreeningPipelineResponse,
             WSIBlockSummary

lia-agent-system/app/schemas/
└── jd_enrichment.py
    Classes: EnrichedJobDescription, TechnicalSkillSuggestion,
             BehavioralCompetencySuggestion, EnrichedSuggestion,
             SuggestionSource, SuggestionImpactLevel
```

### Backend — Constantes

```
lia-agent-system/app/domains/cv_screening/constants/
└── wsi_constants.py                              ← Fonte canônica de constantes WSI
    Constantes: WSI_DIMENSION_LABELS, WSI_DIMENSION_WEIGHTS_DEFAULT,
                WSI_BLOCK_NAMES,
                SENIORITY_DISTRIBUTIONS           ← F5: tabela T/B por senioridade e modo
```

### Backend — Endpoints

```
lia-agent-system/app/api/v1/
├── wsi.py                               # POST /api/v1/wsi/generate-questions
│                                        #   GenerateQuestionsRequest (sem enriched_jd — versão legada)
├── wsi_questions.py                     # POST /wsi/generate, /wsi/regenerate
├── wsi_async.py                         # /wsi/async/* (E1 assíncrono)
├── wsi_question_adjust.py               # /wsi/questions/adjust, /wsi/jd-evaluate
├── wsi_observability.py                 # /wsi-observability/*
└── wsi_screening_pipeline_endpoint.py   # POST /wsi/screening-pipeline

lia-agent-system/app/api/
└── wsi_endpoints.py ★                  # POST /api/wsi/generate-questions  ← WSI-7
    Classes: GenerateQuestionsRequest(enriched_jd: Optional[Dict] = None)
             └── enriched_jd: campo WSI-7 — repassa para WSIService.generate_screening_questions()
```

### Backend — Modelos DB

```
lia-agent-system/libs/models/lia_models/
├── screening_question.py    # CompanyScreeningQuestion
├── screening_question_set.py # ScreeningQuestionSet
└── voice_screening.py       # VoiceScreeningCall, VoiceScreeningAnalysis

lia-agent-system/app/models/ (aliases → libs/models/lia_models/)
├── screening.py
├── screening_question.py
├── screening_question_set.py
└── voice_screening.py
```

### Backend — Job Management

```
lia-agent-system/app/domains/job_management/services/
└── jd_enrichment_service.py  # JdEnrichmentService (F1)

lia-agent-system/app/services/ (aliases)
└── jd_enrichment_service.py  → app/domains/job_management/services/
```

### Documentação

```
docs/
├── WSI_FLOW_PONTA_A_PONTA.md          ← ESTE DOCUMENTO
├── WSI_METHODOLOGY_COMPLETE_v2.md     # Metodologia científica completa
├── WSI_METHODOLOGY_REFERENCE.md       # Referência resumida
└── archived/sprint-history.md         # Histórico de sprints WSI-1 a WSI-6
```

### Testes

```
lia-agent-system/tests/unit/
├── test_wsi1_scoring_engine.py    # Fórmula tri-componente, acumulação ponderada
├── test_wsi2_jd_quality.py        # D3/D4 thresholds, question counts
├── test_wsi3_gates.py             # Gates G2, G4, G6
├── test_wsi4_feedback.py          # Template F8.5.1, 3 paths de feedback
└── test_wsi6_bigfive_pipeline.py  # F2.5, F3, F5, F6.6 — Big Five pipeline
    ├── TestF66TraitAffinity        ← WSI-7: _select_comp_by_trait() — match exato + fallback
    └── TestF1CBridge               ← WSI-7: _build_competencies_from_enriched_jd() + _merge_with_enriched()
```

---

## 5. Gaps e Roadmap de Implementação

### Gaps por Fase

| ID | Fase | Descrição | Prioridade | Sprint |
|----|------|-----------|-----------|--------|
| ~~F1-1~~ | ~~F1~~ | ~~Temperature F1.C = 0.3 explícita~~ | ~~🟡~~ | ✅ WSI-7 |
| ~~F1-2~~ | ~~F1~~ | ~~`context_signals` no schema de output~~ | ~~🟡~~ | ✅ WSI-7 |
| ~~F1-3~~ | ~~F1~~ | ~~Hard-block JD Quality < 30~~ | ~~🟠~~ | ✅ WSI-7 |
| F2-1 | F2 | Abordagem A (léxico LIWC/PT-BR) | 🟠 | Futura |
| F2-2 | F2 | Abordagem B (prior O\*NET / dados próprios) | 🟠 | Futura |
| ~~F6-W7~~ | ~~F6~~ | ~~`Competency.big_five_mapping` — novo campo + `_select_comp_by_trait()`~~ | ~~🔴~~ | ✅ WSI-7 |
| ~~F1-W7~~ | ~~F1~~ | ~~Bridge F1.C → WSI: `_build_competencies_from_enriched_jd()` + `_merge_with_enriched()`~~ | ~~🔴~~ | ✅ WSI-7 |
| ~~API-W7~~ | ~~API~~ | ~~`GenerateQuestionsRequest.enriched_jd` em `wsi_endpoints.py`~~ | ~~🔴~~ | ✅ WSI-7 |
| ~~E3-W7~~ | ~~E3~~ | ~~`WSIVoiceOrchestrator.start_voice_screening()` aceita `enriched_jd`~~ | ~~🔴~~ | ✅ WSI-7 |
| ~~F4-1~~ | ~~F4~~ | ~~Sinais salary/skills não passados ao resolver (silenciosos)~~ | ~~🟠~~ | ✅ WSI-8 parcial |
| ~~F5-1~~ | ~~F5~~ | ~~Distribuição T/B em `generate_all()` por senioridade~~ | ~~🟠~~ | ✅ WSI-8 parcial |
| ~~F6-1~~ | ~~F6~~ | ~~Validação de comprimento: 15–80 palavras, 3 retries~~ | ~~🟠~~ | ✅ WSI-8 |
| ~~F6-2~~ | ~~F6~~ | ~~Ancoragem no JD (temp=0.0, max_tokens=300)~~ | ~~🟠~~ | ✅ WSI-8 |
| ~~F6-5~~ | ~~F6~~ | ~~`is_critical` máximo 2 por triagem~~ | ~~🟠~~ | ✅ WSI-8 |
| ~~F8-1~~ | ~~F8~~ | ~~Temperature Camada 2 = 0.0 explícita~~ | ~~🔴~~ | ✅ WSI-7 |
| ~~F8-3~~ | ~~F8~~ | ~~Flag `_llm_fallback: true` em falha/timeout~~ | ~~🟠~~ | ✅ WSI-7 |
| ~~F8-5~~ | ~~F8~~ | ~~Campo `key_quote` por resposta~~ | ~~🟠~~ | ✅ WSI-7 |
| ~~F8-6~~ | ~~F8~~ | ~~`inflation_detected: bool` estruturado~~ | ~~🟠~~ | ✅ WSI-7 |
| ~~F9-1~~ | ~~F9~~ | ~~WSI_comportamental ponderado por trait scores F3~~ | ~~🟠~~ | ✅ WSI-8 |
| ~~F10-2~~ | ~~F10~~ | ~~G3 WSI_técnico ≥ 4.0 — verificar threshold~~ | ~~🟠~~ | ✅ WSI-7 |
| ~~F10-3~~ | ~~F10~~ | ~~G4 skill crítica ≥ 3.0 — verificar threshold~~ | ~~🟠~~ | ✅ WSI-7 |
| ~~F10-4~~ | ~~F10~~ | ~~G5 ≥ 50% respostas < 30 palavras~~ | ~~🟠~~ | ✅ WSI-7 |
| ~~F10-5~~ | ~~F10~~ | ~~G6 ≥ 3 inflações (verificar threshold atual)~~ | ~~🔴~~ | ✅ WSI-7 |
| F10-6 | F10 | `decision.confidence` alta/media/baixa | 🟡 | WSI-9 |
| ~~F11-1~~ | ~~F11~~ | ~~F11.5 prompt (perguntas entrevista presencial)~~ | ~~🟠~~ | ✅ WSI-9 |
| ~~F11-2~~ | ~~F11~~ | ~~F11.7 prompt completo (relatório JSON)~~ | ~~🟠~~ | ✅ WSI-9 |
| ~~F11-3~~ | ~~F11~~ | ~~`already_generated: true` check — evitar re-geração desnecessária~~ | ~~🟡~~ | ✅ WSI-10 |
| ~~F10-6~~ | ~~F10~~ | ~~`decision.confidence` (alta/media/baixa) — lógica de cálculo~~ | ~~🟡~~ | ✅ WSI-10 |
| ~~F11-6~~ | ~~F11~~ | ~~Tab 3 (Ranking) — comparativo entre candidatos ≥ 2~~ | ~~🟡~~ | ✅ WSI-10 |

### Sprints Planejados

| Sprint | Escopo | Prioridade |
|--------|--------|-----------|
| ~~**WSI-7**~~ | ~~F8-1 (temp=0.0), F10-5 (G6≥3), F1-3 (hard-block), G3/G4/G5, flags estruturadas~~ + **`Competency.big_five_mapping`, `_select_comp_by_trait()`, bridge F1.C→WSI, `enriched_jd` em endpoint+orquestrador** | ✅ **Implementado** |
| **WSI-8** | ~~F4 sinais salary/skills~~ ✅ + ~~F5 distribuição adaptativa~~ ✅ + ~~F6 validação comprimento~~ ✅ + ~~F6.8.1 ancoragem~~ ✅ + ~~F6-5 is_critical max 2~~ ✅ + ~~F9-1 ponderação por trait~~ ✅ | ✅ Concluído |
| ~~**WSI-9**~~ | ~~F11.5 + F11.7 prompts completos~~ ✅ + F11-3 already_generated + candidate_feedback pipeline | 🟠 (F11.5+F11.7 done) |
| ~~**WSI-10**~~ | ~~F10-6 (decision.confidence)~~ ✅ + ~~F11-3 (already_generated)~~ ✅ + ~~F11-6 (Tab 3 Ranking)~~ ✅ | ✅ Concluído |
| **WSI-11** | Abordagens A+B (lexical LIWC + prior O*NET) + fórmula F3 completa + boost por senioridade | 🟡 futura |

---

## 6. Fluxo de Dados: Input → Output por Fase

```
RECRUITER INPUT
  job_title, seniority, department, skills[], competencies[], description
        │
        ▼
F1 JdEnrichmentService.enrich_job_description()
  OUTPUT: EnrichedJobDescription {
    titulo_padronizado, senioridade_confirmada,
    skills_obrigatorias[{skill, contexto}],        ← alimenta F6 perguntas técnicas
    competencias_comportamentais[{competencia,      ← alimenta F2.5 behavioral_competencies
                                  trait_big_five,    ← pré-mapeia trait para F6.6
                                  contexto}],
    context_signals{autonomia, inovacao, pressao, colaboracao},
    wsi_quality_score, ready_for_processing
  }
        │
        ▼
F2.5 _extract_ocean_scores(enriched_jd, behavioral_competencies)
  OUTPUT: List[OceanTraitScore] ordenado desc {
    trait, score(0-100), confidence(high|med|low), evidence[citações literais]
  }
        │
        ▼
F3 _select_traits_by_seniority(ranked, seniority)
  OUTPUT: List[OceanTraitScore] top-N (2-5 conforme senioridade)
        │
        ▼
F5 SENIORITY_DISTRIBUTIONS[seniority][mode]
  OUTPUT: {technical: N, behavioral: M, total: 7 ou 12}
        │
        ▼
F6 generate_all(competencies, mode, job_description, seniority)
  OUTPUT: List[WSIQuestion] {
    id, competency, framework(CBI|Bloom|Dreyfus|BigFive),
    question_type, question_text, weight,
    expected_signals[], scoring_criteria{ocean_trait?}
  }
        │
        ├─────────── E1/E2/E3 ────────────────────────────────────────────────────
        │                                                                         │
        ▼ (candidato responde)                                                   │
F7 Respostas coletadas                                                           │
  OUTPUT: List[{question_id, candidate_response, transcript_segment?}]           │
        │
        ▼
F8 calculate_wsi_deterministic() × por pergunta
  Camada 1 (deterministic): star_score, bloom_level, dreyfus_level, autodeclaracao
  Camada 2 (LLM temp=0.0):  signals_detected, inflation_detected, key_quote
  Camada 3 (fórmula):       final_score(0-10), penalty, bonus
  OUTPUT: List[DeterministicWSIResult] {
    final_score, star_score, bloom_level, dreyfus_level,
    red_flags, flags_structured{is_inflation, is_generic, is_short},
    key_quote, _llm_fallback
  }
        │
        ▼
F9 WSI_final = WSI_tecnico × w_tech + WSI_comport × w_behav
  OUTPUT: {
    wsi_final(0-10), wsi_technical(0-10), wsi_behavioral(0-10),
    weight_technical, weight_behavioral
  }
        │
        ▼
F10 Gates G1-G6 + Thresholds (7.5/6.0)
  OUTPUT: {
    result: APROVADO|EM_AVALIACAO|REPROVADO,
    confidence: alta|media|baixa,
    human_review_required: bool,
    gate_triggered: str|null,
    failed_gates: List[str]
  }
        │
        ▼
F11 Relatório + Feedback
  F11.5 (temp=0.6): 2 perguntas CBI para entrevista presencial
  F11.7 (temp=0.2): JSON completo com 7 seções para recrutador
  F8.5.1:           Feedback LGPD-compliant para candidato
  OUTPUT: {report_header, report_sections, interview_questions, generation_metadata}
```

---

*Última atualização: 25/03/2026 — WSI-10 CONCLUÍDO: F10-6 confidence ✅ + F11-3 cache ✅ + F11-6 Tab 3 Ranking ✅*
*Próxima sprint WSI-11: F2-1 (LIWC/PT-BR) + F2-2 (prior O\*NET) — planejadas para futuro*
*Arquivos impactados nesta atualização: `wsi_constants.py`, `wsi_screening_pipeline.py`, `wsi_service.py`*
