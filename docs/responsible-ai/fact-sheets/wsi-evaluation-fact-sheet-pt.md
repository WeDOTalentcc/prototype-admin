# AI Fact Sheet — Avaliação WSI (WSI Evaluation)

*Última atualização: 2026-04-23 | Idioma: PT-BR | [English version](./wsi-evaluation-fact-sheet-en.md)*

## 1. Propósito

A Avaliação WSI (Workplace Science Index) aplica metodologias científicas — Bloom Taxonomy, Dreyfus Model e Big Five — a transcrições de entrevistas estruturadas para gerar pareceres técnico-comportamentais, comparações side-by-side entre candidatos e níveis de expertise por competência. Usada após a entrevista (triagem inicial + entrevista WSI via WhatsApp) para apoiar decisão final de contratação pelo recrutador humano.

Esta feature **não toma decisão autônoma de contratação** — toda decisão final é do recrutador humano.

## 2. Inputs

- Transcrição completa da entrevista WSI
- Perguntas WSI (framework definido por vaga + arquétipo)
- Contexto da vaga (requisitos + seniority level)
- Decisões históricas do mesmo recrutador (opcional, para calibração)

## 3. Outputs

- Score WSI final (`wsi_final_score`, 0-100) — interno, NUNCA exposto ao candidato
- Níveis Bloom (1-6) por competência avaliada
- Níveis Dreyfus (1-5) por competência avaliada
- Traços Big Five (O/C/E/A/N) com scores
- Parecer estruturado em linguagem natural (4-6 parágrafos)
- Comparação side-by-side quando múltiplos candidatos avaliados
- Reasoning completo em `audit_service.log_decision`

## 4. Modelo e Arquitetura

- **Modelo LLM base (pontuação):** `claude-sonnet-4-5` (Anthropic)
- **Modelo de extração linguística (Camada 2 — `wsi_layer2_extraction`):** `claude-haiku-4-5-20251001` (Anthropic) — extrai sinais objetivos (paráfrase, 1ª pessoa, quantificação, inflação semântica) para alimentar a Camada 1 determinística
- **Domain YAML canônico:** `app/prompts/domains/wsi_evaluation.yaml` (82 linhas, versão `2.0`, `updated_at: 2026-04-07`) + `wsi_layer2_extraction.yaml` (140 linhas)
- **Agent:** `WSIEvaluatorAgent` (em `app/domains/wsi_evaluation/`)
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="wsi_evaluator")`

## 5. Atributos Protegidos — Cobertura

- Mesma cobertura de 14 atributos protegidos via `protected_attributes.yaml` e FairnessGuard L1+L2+L3
- **Camada 2 de extração** tem regra explícita em `wsi_layer2_extraction.yaml` scope_out: *"NÃO usa nome, idade, gênero, raça, foto, origem (atributos protegidos)"*
- **Detecção de inflação semântica:** claims grandiosos sem evidência são flagados, não premiados
- **Prompt injection detection:** respostas do candidato que tentam manipular avaliação são detectadas e flagadas

## 6. Métricas de Acurácia e Fairness

→ Ver seção 6 de `eu-ai-act-technical-documentation-pt.md` — métricas consolidadas por feature. WSI Evaluation é uma das features monitoradas (grupo: Gênero × Idade). DI ratio alvo ≥ 0.80. Próximo bias audit independente: Q3/2026.

## 7. Limitações Conhecidas

- **Dependência da qualidade da transcrição:** ruídos de áudio, transcrição automática com erros reduzem acurácia.
- **Nível Dreyfus é estimativa:** a classificação de expertise (Novato → Expert) é aproximada — especialistas humanos podem divergir em casos de fronteira.
- **Big Five requer tamanho mínimo de entrevista:** respostas muito curtas (<30 palavras) limitam a detecção de traços comportamentais.
- **Calibração por empresa:** scoring pode ser ajustado por `CalibrationWeight` do tenant — sem calibração, usa pesos padrão (70% técnico / 30% comportamental).

## 8. Supervisão Humana (HITL)

- **Obrigatório:** `FairnessGuard.check()` antes de cada scoring final
- **Obrigatório:** reasoning auditável com `criteria_used`, `score_breakdown`, `subject_id`, `timestamp`
- **Obrigatório:** decisão de contratação é **exclusivamente** humana — a LIA produz parecer, nunca veredito
- **Opcional:** recrutador pode ajustar pesos por vaga (via `CalibrationWeight`)
- **Opcional:** recrutador pode sobrescrever score final

## 9. Direitos do Candidato

- **Explicabilidade:** endpoint `/api/v1/candidate/decisions/explain` retorna critérios objetivos (níveis Bloom demonstrados, competências técnicas avaliadas) + transparência sobre atributos ignorados. **NUNCA** expõe scoring bruto, traços Big Five numéricos, ou níveis Dreyfus detalhados.
- **Revisão humana:** via canal formal de compliance do cliente-deployer.
- **Contestação:** 30 dias a partir da notificação da decisão (EU AI Act Art. 86 + LGPD Art. 20).
- **Acesso/exclusão:** via `data_subject_request`.

## 10. Contatos

- **Compliance:** compliance@wedotalent.cc
- **Suporte:** support@wedotalent.cc
- **Privacidade (DPO):** dpo@wedotalent.cc

---

*Fonte canônica: `app/prompts/domains/wsi_evaluation.yaml` + `wsi_layer2_extraction.yaml` + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invenção.*
