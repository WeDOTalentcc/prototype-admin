---
name: screening-compliance
description: "Compliance de screening e teste de viés na Plataforma LIA conforme Guia v3.3. Use ao criar/modificar pipelines de screening, avaliação WSI, pre-qualification, feedback ao candidato, ou quando precisar verificar fairness, red teaming, model drift ou taxonomia de incidentes. Referência: attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md"
---

# Screening Compliance e Teste de Viés — Guia v3.3

Esta skill define as regras de compliance para pipelines de screening, avaliação WSI, pre-qualification, feedback personalizado, normalização de scores, economia de tokens, teste de viés, red teaming, model drift e taxonomia de incidentes na Plataforma LIA.

> **Skills relacionadas:** wedo-governance, dei-fairness, lgpd-data-protection

## Quando Usar

- Ao criar ou modificar pipelines de screening (WSI, pre-qualification, feedback)
- Ao implementar ou alterar lógica de scoring, thresholds ou calibração
- Ao criar/editar prompts de avaliação de candidatos
- Ao implementar feedback ao candidato (rejeição, parcial, construtivo)
- Ao verificar fairness, viés ou discriminação em qualquer etapa
- Ao configurar red teaming, model drift detection ou alertas automáticos

---

## 1. Pipeline de Screening WSI

### Os 7 Blocos Canônicos (Guia Part III)

| # | Bloco | O que avalia | Framework de referência |
|---|-------|-------------|------------------------|
| 1 | **Competências Técnicas** | Hard skills, certificações, domínio de stack | Extração do CV + perguntas técnicas direcionadas |
| 2 | **Competências Comportamentais** | Soft skills, traços de personalidade, padrões de colaboração | Big Five / OCEAN + metodologia STAR |
| 3 | **Experiência Profissional** | Trajetória de carreira, senioridade, progressão | Modelo Dreyfus de proficiência |
| 4 | **Fit Cultural** | Alinhamento com valores da empresa e estilo de trabalho | Perguntas contextuais + perfil cultural da empresa |
| 5 | **Potencial de Crescimento** | Agilidade de aprendizado, adaptabilidade, curiosidade | Taxonomia de Bloom (profundidade cognitiva) |
| 6 | **Formação Acadêmica** | Educação formal, certificações, idiomas | Extração do CV com mapeamento de equivalência |
| 7 | **Alinhamento com a Vaga** | Correspondência entre requisitos do JD e capacidades demonstradas | Comparação estruturada JD vs. perfil |

**Princípio de scoring:** Scoring quantitativo = determinístico (algoritmo). Avaliação qualitativa (nuances nas respostas) = IA. Score final combina ambos com metodologia visível para o recrutador.

Cada bloco produz score independente (0-10 via BARS). Score global = média ponderada com **pesos configuráveis por empresa**.

Thresholds: >= 7.0 Recomendado | 4.0-6.9 Em análise (revisão humana obrigatória) | < 4.0 Não recomendado (feedback construtivo).

Atributos protegidos mascarados antes do LLM avaliar.

### 1.1.1 Dimensões Canônicas WSI — 4 Dimensões com Pesos Padrão

O código usa 4 dimensões canônicas (fonte: `app/domains/cv_screening/constants/wsi_constants.py` → `WSI_DIMENSION_LABELS`):

| Chave | Label canônico | Peso padrão | Correspondência no Guia |
|-------|---------------|:-----------:|------------------------|
| `technical` | Competências Técnicas | **50%** | Hard skills, stack, certificações técnicas |
| `behavioral` | Competências Comportamentais | **20%** | Soft skills, Big Five, CBI |
| `gap_analysis` | Experiência Profissional | **15%** | Trajetória, Dreyfus, progressão |
| `contextual` | Fit Cultural e Alinhamento | **15%** | Fit cultural, alinhamento com vaga |

> **Simplificação deliberada:** O Guia v3.3 descreve 7 dimensões de avaliação. A implementação consolida em 4 para scoring, movendo *Formação Acadêmica* para pré-qualificador pass/fail separado (ver abaixo).

### 1.1.2 Formação Acadêmica — Pré-qualificador Sem Pontuação

`FormacaoPreQualifierResult` (`app/schemas/screening.py`) é **pass/fail**, não entra no score WSI:

```python
FormacaoPreQualifierResult(
    required_certifications=["OAB"],   # exigências legais da vaga
    candidate_certifications=["OAB"],  # extraídas do CV
    passes=True,                        # True = atende todas as exigências legais
    note="",                            # observação contextual livre (verificada por FairnessGuard)
)
```

**Regra:** Somente certificações com requisito legal obrigatório (OAB, CREA, CRM...) justificam eliminação via pré-qualificador. Nunca usar para discriminar por instituição ou tipo de formação.

### ⚠️ Bloco 6 — Formação Acadêmica: Alto Risco de Viés

Este é o bloco de **maior risco de viés** do WSI. Deve ser calibrado com atenção:

**O que PODE ser avaliado (objetivo e verificável):**
- Certificações obrigatórias por lei (OAB, CREA, CRM, CFC...)
- Certificações técnicas verificáveis (AWS, PMP, CPA, Azure...)
- Proficiência em idiomas quando exigido pela vaga
- Grau mínimo onde há requisito legal real

**O que NÃO deve ser avaliado (fonte de discriminação):**
- Prestígio da instituição (USP vs. UNINOVE — não é skill, é privilégio de acesso)
- Tipo de educação (presencial vs. EAD vs. bootcamp)
- Grau acadêmico para vagas que não exigem legalmente

**Regra de equivalência:** `bootcamp = diploma onde aplicável` — o que importa é a competência demonstrada, não o caminho percorrido para adquiri-la.

**Orientação de peso:** Para vagas sem requisito legal de formação, o peso deste bloco deve ser baixo (ou zero), compensado por Competências Técnicas e Potencial de Crescimento. O peso é configurável por empresa via `PreQualificationThresholds`.

### 1.2 Score Normalization

Normaliza scores WSI produzidos por diferentes versões de perguntas para garantir comparabilidade entre candidatos.

**Gatilho:** `needs_normalization = (max_score - min_score) > 0.05` — ativado quando variância entre versões de perguntas excede 5%.

**Fator de normalização:** `0.7 ≤ factor ≤ 1.3` (clampado para evitar distorções extremas)

```
normalized_score = clamp(raw_score × normalization_factor, 0.0, 10.0)
```

**Exemplo concreto:**

| Candidato | Score Bruto | Versão da Pergunta | Fator | Score Normalizado |
|-----------|-------------|-------------------|-------|------------------|
| A | 7.8 | v2 (mais difícil) | 1.15 | 8.97 |
| B | 8.2 | v1 (padrão) | 1.00 | 8.20 |

Sem normalização, o Candidato A seria injustamente penalizado por ter respondido a uma versão mais difícil. O fator é calculado por `ScoreNormalizationService` com base em amostras históricas por versão de pergunta.

---

### 1.3 Calibração por Senioridade (4 Etapas)

`CalibrationService` — calibra o score WSI considerando área, localização, antiguidade da tecnologia e sinal salarial.

**Etapa 1 — Área de Atuação:**

| Área | Perfil Base | Observação |
|------|------------|------------|
| `software_engineering` | Strong coding + system design | Stack age factor aplicado |
| `data_science` | Python/SQL + comunicação de resultados | Ferramentas evoluem rápido |
| `legal` | Formação regulatória + raciocínio jurídico | Certificação OAB como requisito |
| `product_management` | Visão de produto + stakeholder alignment | Sem stack tecnológica fixa |

**Etapa 2 — Fator Geográfico:**

| Região | Multiplicador | Base de comparação |
|--------|--------------|-------------------|
| São Paulo (Capital) | 1.00 | Referência |
| Rio de Janeiro | 0.97 | −3% |
| Outras capitais | 0.92 | −8% |
| Interior / Remoto | 0.88 | −12% |

**Etapa 3 — Tech Age Factor (Antiguidade da Tecnologia):**

| Classificação | Exemplos | Fator |
|---------------|---------|-------|
| `very_new` (< 2 anos) | Rust estável, Bun, HTMX | 1.30 — raridade na oferta |
| `new` (2-5 anos) | FastAPI, Next.js 13+, Prisma | 1.15 |
| `established` (5-15 anos) | Python, React, PostgreSQL | 1.00 — baseline |
| `legacy` (> 15 anos) | COBOL, Delphi, VB6 | 0.85 — pool maior, demanda menor |

**Etapa 4 — Validação por Sinal Salarial:**

Score de senioridade validado contra faixa salarial de mercado. Discrepância > 30% entre seniority implied score e salary signal → flag para revisão humana.

**Mapeamento Dreyfus × Bloom × Senioridade:**

| Seniority | Dreyfus | Bloom | Score WSI mínimo esperado |
|-----------|---------|-------|--------------------------|
| Estágio / Junior | Novato | Lembrar / Entender | 3.0–5.0 |
| Pleno | Competente | Aplicar / Analisar | 5.0–7.0 |
| Sênior | Proficiente | Avaliar | 7.0–8.5 |
| Staff / Principal | Especialista | Criar | 8.5+ |

**Saída:** `CalibrationResult(area_profile, geo_multiplier, tech_age_factor, salary_validation_ok, rationale)` — campo `rationale` obrigatório para auditabilidade e conformidade com EU AI Act (decisões explicáveis).

---

### 1.4 BARS — Behaviorally Anchored Rating Scale

`RubricEvaluationService` — cada dimensão WSI tem âncoras comportamentais explícitas por nível (1–5), eliminando subjetividade na avaliação LLM.

**Estrutura por nível (exemplo — Competências Técnicas / Python):**

| Nível | Score | Âncora Comportamental |
|-------|-------|----------------------|
| **5 — Expert** | 9.0–10.0 | Contribuiu para libs open-source Python, otimizou GIL/async em produção, mentora equipes |
| **4 — Proficiente** | 7.0–8.9 | Escreve código idiomático com generators, decorators, context managers; resolve problemas de performance |
| **3 — Competente** | 5.0–6.9 | Desenvolve features standalone, entende OOP, usa libs padrão sem ajuda |
| **2 — Iniciante Avançado** | 3.0–4.9 | Executa tarefas estruturadas com supervisão, entende sintaxe básica e fluxo de controle |
| **1 — Novato** | 1.0–2.9 | Conhecimento teórico sem aplicação prática, requer orientação em tarefas simples |

**Regra de ouro:** O LLM compara a resposta do candidato contra as âncoras e justifica o nível atribuído. Score nunca é gerado sem `rationale`. `RubricEvaluationService` retorna: `{level, score, rationale, confidence}`.

---

## 2. Pre-Qualification Pipeline

4 Níveis: Alinhado (>= 70%), Parcial (50-69%), Distante (30-49%), Muito Distante (< 30%).

NUNCA revelar porcentagem ou score numérico ao candidato. Candidato SEMPRE tem opção de continuar.

---

## 3. Personalized Feedback

Tom warm, profissional e encorajador. NUNCA revelar score numérico. Sempre destacar pontos fortes. Sugerir áreas de desenvolvimento concretas.

---

## 4. Economia de Tokens

Budget default por empresa: $500/mês. Alertas em 80% e 100%. Usar modelo mais barato possível para cada tarefa.

---

## 5. Framework de Teste de Viés (4 Níveis)

Nível 1 Pre-Deployment: Golden Dataset, Four-Fifths Rule.
Nível 2 Post-Deployment: A/B Testing, Shadow Scoring.
Nível 3 Contínuo: fairness_audit_logs, alertas automáticos.
Nível 4 Externo: auditoria trimestral independente.

---

## 6. Red Teaming

6 cenários obrigatórios: prompt injection, data exfiltration, bias elicitation, jailbreak, escalação de privilégios, manipulação de score.

Critérios: jailbreak < 1%, data leak = 0%, bypass mascaramento = 0%.

---

## 7. Model Drift Detection

Triggers: score WSI varia > 0.5 em 30 dias, taxa aprovação varia > 10%, custo aumenta > 20%, latência P95 aumenta > 50%.

---

## 8. Taxonomia de Incidentes de IA

6 Categorias: Viés Discriminatório (P0), Vazamento de Dados (P0), Alucinação com Impacto (P1), Falha de Mascaramento (P1), Drift de Qualidade (P2), Custo Anômalo (P3).

---

## 9. LLM Evaluation Framework — RAGAS

Avalia a qualidade das respostas geradas pelo LLM em avaliações WSI usando 5 métricas RAGAS. Executado como parte do pipeline de regression testing antes de qualquer deploy de modelo ou versão de prompt.

### Métricas RAGAS

| Métrica | O que mede | Meta |
|---------|-----------|------|
| **Faithfulness** | Respostas factuais ancoradas no contexto — sem alucinação | ≥ 0.90 |
| **Answer Relevance** | Resposta pertinente à pergunta feita | ≥ 0.85 |
| **Context Precision** | Contexto recuperado é relevante, sem ruído | ≥ 0.80 |
| **Context Recall** | Toda informação necessária foi recuperada | ≥ 0.75 |
| **Answer Semantic Similarity** | Similaridade semântica com resposta de referência | ≥ 0.80 |

### Regression Testing Protocol

**Golden Set:** 100 candidatos representativos (25 por quartil de score) — inclui candidatos com diferentes trajetórias de formação (universitária, bootcamp, autodidata) para detectar drift de viés nas dimensões DEI.

**Thresholds de alerta:**

| Condição | Ação |
|----------|------|
| Drift em qualquer métrica RAGAS > 0.10 | Suspender deploy e investigar |
| Variância de aprovação por grupo de formação > 3% | Re-executar testes DEI completos |
| Drift de score WSI > 0.5 em 30 dias | Acionar Model Drift Detection (Seção 7) |
| Qualquer violação de bias audit (ratio < 0.80) | Bloquear deploy — revisão obrigatória |

**Frequência:** A cada deploy de novo modelo ou versão de prompt → regression completa obrigatória **antes** de ativação em produção.

**⚠️ Formação Acadêmica no regression gate:** testes de equivalência bootcamp/diploma fazem parte do golden set. Variância de aprovação entre trajetórias de formação > 3% bloqueia o deploy. Termos como "universidades de primeira linha" em qualquer output do LLM são tratados como falha crítica (Camada 2 do FairnessGuard).

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/screening-compliance` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/screening-compliance.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/screening-compliance/SKILL.md` |

**Quando ativar:**
- Ao criar ou modificar pipelines de screening, scoring WSI ou pre-qualification
- Ao implementar feedback ao candidato
- Ao configurar thresholds, calibração ou normalização de scores
- Ao verificar fairness ou executar red teaming
