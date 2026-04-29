# AI Fact Sheet — Triagem de Currículos (CV Screening)

*Última atualização: 2026-04-23 | Idioma: PT-BR | [English version](./cv-screening-fact-sheet-en.md)*

## 1. Propósito

A Triagem de Currículos (CV Screening) analisa currículos de candidatos contra os requisitos objetivos de uma vaga, gerando um score WSI inicial (70% técnico + 30% comportamental) e rankeando candidatos para shortlist. O objetivo é reduzir o esforço inicial do recrutador em volumes altos de candidaturas, **sem substituir** a avaliação humana final.

Esta feature **não toma decisão autônoma de rejeição ou contratação** — toda decisão final de pipeline é do recrutador humano.

## 2. Inputs

- Texto do currículo (colado ou extraído de PDF/DOCX pelo sistema)
- Requisitos da vaga (`job_vacancy`): skills mandatórias, experiência mínima, formação
- Configurações da empresa (`company_settings`): critérios de exclusão, nível de autonomia da LIA

## 3. Outputs

- Score WSI inicial (`wsi_score_initial`, 0-100) — interno, NUNCA exposto ao candidato
- Score breakdown: match técnico (%), score comportamental (%)
- Lista de evidências (critérios atendidos / não atendidos)
- Red flags detectados (gaps, inconsistências de datas) — internos
- Recomendação de triagem: `shortlist` / `revisão humana` / `não aderente`
- Reasoning auditável em `audit_service.log_decision`

## 4. Modelo e Arquitetura

- **Modelo LLM base:** `claude-sonnet-4-5` (Anthropic)
- **Domain YAML canônico:** `app/prompts/domains/cv_screening.yaml` (222 linhas, versão `2.0`, `updated_at: 2026-03-19`)
- **Agent:** `CVScreeningAgent` (em `app/domains/cv_screening/`)
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="cv_screening")`
- **Metodologia de scoring:** Dynamic Cutoff (threshold recalculado após 30-50 candidatos) + Smart Saturation (pipeline pausa se >20 aprovados)

## 5. Atributos Protegidos — Cobertura

- 14 atributos protegidos listados em `app/config/protected_attributes.yaml` (versão 6)
- **FairnessGuard Layer 1 (regex, 19 categorias):** bloqueio determinístico antes de chegar ao LLM
- **FairnessGuard Layer 2 (43 termos PT/EN):** detecção de viés implícito
- **FairnessGuard Layer 3 (LLM semântico, ativo desde 2026-04-23):** classificação semântica para ações de alto impacto
- Regra canônica em `cv_screening.yaml`: *"Nunca rejeitar candidato sem verificar FairnessGuard primeiro"* e *"Ignorar completamente: nome, foto, endereço, estado civil, idade, origem étnica"*

## 6. Métricas de Acurácia e Fairness

→ Ver seção 6 de `eu-ai-act-technical-documentation-pt.md` — métricas consolidadas por feature, com status de disparate impact ratio (DI ratio ≥ 0.80 conforme four-fifths rule do NYC LL144). Próximo bias audit independente: Q3/2026.

## 7. Limitações Conhecidas

- **Dependência de qualidade do texto do CV:** CVs mal formatados, escaneados sem OCR limpo ou em idiomas não suportados reduzem acurácia.
- **Viés de treinamento dos modelos LLM base:** mitigado por FairnessGuard + `compliance_block.yaml`, mas não completamente eliminável — por isso a feature é **assistiva, não decisória**.
- **Dynamic Cutoff:** em volumes pequenos (<30 candidatos), o threshold pode não estar calibrado — revisão humana recomendada.
- **Sem avaliação de portfólio:** links para GitHub, portfolio ou LinkedIn não são acessados automaticamente nesta camada.

## 8. Supervisão Humana (HITL)

- **Obrigatório:** confirmação dupla para rejeição em massa (>1 candidato simultaneamente)
- **Obrigatório:** score na zona 60-74% → recomenda revisão humana explicitamente
- **Obrigatório:** toda rejeição passa por `check_rejection_fairness` antes de ser registrada
- **Obrigatório:** reasoning auditável em `audit_service` para toda decisão
- **Opcional:** recrutador pode sobrescrever qualquer score/recomendação

## 9. Direitos do Candidato

- **Explicabilidade:** endpoint `/api/v1/candidate/decisions/explain` (JWT do candidato) retorna critérios objetivos avaliados + lista dos atributos protegidos IGNORADOS + aviso EU AI Act Art. 86 + LGPD Art. 20.
- **Revisão humana:** candidato pode solicitar revisão pelo canal formal de compliance do cliente-deployer (configurado em `CompanyComplianceSettings.contato_revisao`).
- **Contestação:** prazo recomendado de 30 dias a partir da notificação da decisão (EU AI Act Art. 86 + LGPD Art. 20).
- **Acesso/exclusão de dados:** via `data_subject_request` (LGPD Arts. 18 e 15).

## 10. Contatos

- **Compliance:** compliance@wedotalent.cc
- **Suporte:** support@wedotalent.cc
- **Privacidade (DPO):** dpo@wedotalent.cc

---

*Fonte canônica: `app/prompts/domains/cv_screening.yaml` + `app/domains/cv_screening/` + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invenção.*
