# AI Fact Sheet — Transição de Pipeline (Pipeline Transition)

*Última atualização: 2026-04-23 | Idioma: PT-BR | [English version](./pipeline-transition-fact-sheet-en.md)*

## 1. Propósito

A Transição de Pipeline auxilia o recrutador a mover candidatos entre etapas do pipeline (sourced → screening → interview → offer), extraindo preferências da conversa, consultando dados relevantes e sugerindo sub-status apropriado. Cobre movimentações individuais e em lote, com **validação obrigatória de fairness em rejeições**.

Esta feature **não executa transições autônomas sem confirmação do recrutador** — toda ação que afeta candidato é confirmada explicitamente.

## 2. Inputs

- Mensagem do recrutador (intenção de mover candidato)
- Candidato(s) mencionado(s) — IDs ou nomes
- Etapa atual + etapa destino
- Motivo da transição (especialmente para rejeições)
- Contexto de conversa anterior (memória + entidade atual)

## 3. Outputs

- Confirmação da ação a ser executada (etapa + sub-status)
- Extração de preferências (data, hora, formato, canal, urgência)
- Sugestão de sub-status via `suggest_sub_status`
- Aviso de comunicação automática (se ação disparar mensagem ao candidato)
- Resultado de `check_rejection_fairness` (obrigatório em rejeições)
- Audit trail completo via `audit_service.log_decision`

## 4. Modelo e Arquitetura

- **Modelo LLM base:** `claude-sonnet-4-5` (Anthropic)
- **Domain YAML canônico:** `app/prompts/domains/pipeline_transition.yaml` (98 linhas, versão `3.0.0`, `updated_at: 2026-04-14`)
- **Agent:** `PipelineTransitionAgent` — usa `get_pipeline_system_prompt()` customizado (fora do `SystemPromptBuilder` padrão)
- **Calibração por tamanho de empresa:** tom STARTUP / PME / CORPORAÇÃO ajusta formalidade (campo `company_calibration` do YAML)
- **Learning rules:** `get_recruiter_preferences` consulta padrões do recrutador e oferece sugestões proativas

## 5. Atributos Protegidos — Cobertura

- 14 atributos protegidos via `protected_attributes.yaml` e FairnessGuard L1+L2+L3
- Regra canônica em `pipeline_transition.yaml` (regra 5 de `behavioral_rules`): *"Para rejeições: SEMPRE use check_rejection_fairness ANTES de responder"*
- Regra 8 de `behavioral_rules`: *"Use ferramentas proativamente quando necessário"* — inclui checagem de fairness antes de ações irreversíveis

## 6. Métricas de Acurácia e Fairness

→ Ver seção 6 de `eu-ai-act-technical-documentation-pt.md` — métricas consolidadas. Pipeline Transition monitora todos os 14 atributos em transições com destino `conclusion_rejected` ou `shortlist`. DI ratio alvo ≥ 0.80. Próximo bias audit independente: Q3/2026.

## 7. Limitações Conhecidas

- **Ambiguidade de nomes:** se múltiplos candidatos têm o mesmo primeiro nome, a feature pede desambiguação explícita (não assume).
- **Transições em lote:** máximo de 20 candidatos simultâneos (evita falhas em cascata); acima disso, recrutador deve dividir.
- **Rejeição sem motivo:** feature bloqueia rejeição sem motivo estruturado (evita viés oculto).
- **Comunicação automática:** só é disparada se configurada em `company_settings`; se desligada, recrutador deve comunicar manualmente.

## 8. Supervisão Humana (HITL)

- **Obrigatório:** confirmação explícita em toda ação irreversível (rejeição, movimentação final, oferta)
- **Obrigatório:** `check_rejection_fairness` antes de rejeição em qualquer escala
- **Obrigatório:** `communication_transparency` — se transição disparar mensagem automática, recrutador é informado do que o candidato vai receber e pode editar
- **Obrigatório:** confirmação dupla para transições em lote
- **Escalação automática:** se FairnessGuard detectar padrão sistêmico de rejeição por atributo protegido, alerta é emitido para compliance team

## 9. Direitos do Candidato

- **Notificação de comunicação automática:** quando sistema envia mensagem ao candidato (ex.: rejeição com feedback), a comunicação inclui aviso LGPD Art. 20 + EU AI Act Art. 86.
- **Explicabilidade:** endpoint `/api/v1/candidate/decisions/explain` retorna razão da transição em linguagem simples, critérios objetivos e aviso Art. 86.
- **Revisão humana:** candidato pode solicitar revisão pelo canal formal do cliente-deployer.
- **Contestação:** 30 dias a partir da notificação.

## 10. Contatos

- **Compliance:** compliance@wedotalent.cc
- **Suporte:** support@wedotalent.cc
- **Privacidade (DPO):** dpo@wedotalent.cc

---

*Fonte canônica: `app/prompts/domains/pipeline_transition.yaml` + `app/domains/pipeline_transition/` + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invenção.*
