# AI Fact Sheet — Ranking e Shortlist

*Última atualização: 2026-04-23 | Idioma: PT-BR | [English version](./ranking-shortlist-fact-sheet-en.md)*

## 1. Propósito

O Ranking e Shortlist consolida candidatos em uma vaga, apresenta-os em ordem de match (baseado em WSI + calibração do recrutador) e gera insights proativos sobre a saúde do pipeline (pool size, diversidade demográfica agregada, gaps vs. requisitos). A decisão final de quem entra no shortlist é **sempre do recrutador humano** — a LIA organiza e sugere.

## 2. Inputs

- Lista de candidatos na vaga (resultado de sourcing + CV screening)
- Scores WSI atualizados (se disponíveis)
- Calibração do recrutador (`CalibrationWeight`, se configurada)
- Requisitos da vaga (`job_vacancy`)
- Histórico de preferências do recrutador (quando disponível)

## 3. Outputs

- Lista ordenada por score (rank 1..N)
- Narrativa principal do pool (2-3 frases conversacionais)
- Destaques (máx. 5 pontos positivos)
- Preocupações (máx. 5 pontos de atenção) — ex: "pool pequeno", "score médio baixo"
- Recomendações de ação (máx. 4)
- Pergunta proativa antecipando próxima ação
- Métricas agregadas: score médio, pool size, cobertura de contato (telefone, email)

## 4. Modelo e Arquitetura

- **Modelo LLM base:** `claude-sonnet-4-5` (Anthropic)
- **Domain YAML canônico:** combinação de `sourcing.yaml` (96L, versão `2.0`) + `recruiter_assistant.yaml` (187L, versão `2.0`)
- **Variante específica:** `proactive_insights` em `agent_prompts.yaml` — gera narrativa estruturada
- **Agent:** compartilhado entre `RecruiterAssistantAgent` e `SourcingAgent` conforme contexto
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="proactive_insights")`

## 5. Atributos Protegidos — Cobertura

- 14 atributos protegidos via `protected_attributes.yaml` e FairnessGuard L1+L2+L3
- Ranking **nunca usa atributos protegidos como critério** — só competências técnicas e score WSI
- Métricas agregadas de diversidade (% gênero, % raça/etnia) podem ser reportadas **no agregado do pool**, nunca associadas a candidatos individuais no output
- `compliance_block.yaml` seção `decision.bias` tem instrução específica sobre evitar "cultural fit" como proxy em rankings

## 6. Métricas de Acurácia e Fairness

→ Ver seção 6 de `eu-ai-act-technical-documentation-pt.md` — métricas consolidadas. Ranking/Shortlist monitora **representatividade por grupo** (Gênero × Raça/Etnia × Deficiência) para detectar viés sistêmico de ranking (ex: mulheres consistentemente em rank > 10). DI ratio alvo ≥ 0.80. Próximo bias audit independente: Q3/2026.

## 7. Limitações Conhecidas

- **Dependência de qualidade do scoring:** ranking é tão bom quanto o WSI score que o alimenta — se cv_screening falhar, ranking herda o erro.
- **Pool pequeno (<10 candidatos):** insights podem ser enganosos estatisticamente — feature alerta explicitamente.
- **Sem lookup externo:** não busca ativamente novos candidatos (isso é responsabilidade do Sourcing) — trabalha apenas com o pool já existente na vaga.
- **Calibração opcional:** sem `CalibrationWeight`, usa defaults 70% técnico / 30% comportamental — pode não refletir o perfil desejado pela empresa.

## 8. Supervisão Humana (HITL)

- **Obrigatório:** shortlist final é **exclusivamente** decisão humana — LIA sugere, recrutador confirma
- **Obrigatório:** confirmação para compartilhamento de shortlist com gestor
- **Obrigatório:** reasoning auditável por candidato no ranking
- **Recomendado:** se score médio do top-5 < 60%, feature sugere refinamento de busca em vez de shortlist prematura
- **Recomendado:** se pool tem viés sistêmico (representatividade baixa de grupo), feature pede confirmação e sugere expansão

## 9. Direitos do Candidato

- **Notificação de ranking:** candidato **não é notificado de sua posição no ranking** (dado interno de operação). Se for descartado por não entrar no shortlist, recebe comunicação via Pipeline Transition com aviso LGPD + Art. 86.
- **Explicabilidade:** endpoint `/api/v1/candidate/decisions/explain` mostra critérios objetivos avaliados, **sem revelar rank numérico ou scoring bruto**.
- **Revisão humana:** via canal formal do cliente-deployer.
- **Contestação:** 30 dias a partir da notificação de descarte (Art. 86 + LGPD Art. 20).

## 10. Contatos

- **Compliance:** compliance@wedotalent.cc
- **Suporte:** support@wedotalent.cc
- **Privacidade (DPO):** dpo@wedotalent.cc

---

*Fonte canônica: `app/prompts/domains/sourcing.yaml` + `recruiter_assistant.yaml` + `agent_prompts.yaml` (variante `proactive_insights`) + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invenção.*
