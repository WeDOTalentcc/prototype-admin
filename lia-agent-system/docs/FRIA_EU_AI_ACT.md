# FRIA — Avaliação de Impacto de IA de Alto Risco (EU AI Act)

**Plataforma:** LIA — WeDOTalent
**Versão:** 1.0 | **Data:** 2026-03-15 | **ACH-031**
**Referência:** EU AI Act (Regulamento UE 2024/1689) — Artigos 9, 10, 13, 14, 15, Anexo III

---

## 1. Identificação do Sistema de IA

| Campo | Valor |
|-------|-------|
| **Nome do sistema** | LIA (Learning Intelligence Assistant) |
| **Versão avaliada** | v3.0 (Sprint I–V completos) |
| **Fornecedor** | WeDOTalent (Brasil) |
| **Finalidade** | Triagem, avaliação e seleção de candidatos para emprego |
| **Usuários previstos** | Recrutadores e gestores de RH (B2B) |
| **Pessoas afetadas** | Candidatos a emprego |
| **Data de implantação** | 2025 (produção ativa) |

---

## 2. Classificação de Risco (Anexo III EU AI Act)

### 2.1 Determinação de Risco

O sistema LIA utiliza IA para:
- **Triagem automática de CVs** (rubric_evaluation_service, WSI)
- **Pontuação e ranking de candidatos** (FairnessGuard, bias audit)
- **Recomendações de contratação** (ReAct agents, HITL)

**Classificação: ⚠️ ALTO RISCO (Art. 6 + Anexo III, Ponto 4)**

> *"Sistemas de IA destinados a ser utilizados para recrutamento ou seleção de pessoas físicas, nomeadamente para publicitar postos de trabalho, analisar e filtrar candidaturas, e avaliar candidatos."* — Anexo III, (4)(a)

### 2.2 Obrigações Aplicáveis

| Obrigação | Artigo | Status LIA |
|-----------|--------|-----------|
| Sistema de gestão de riscos | Art. 9 | ✅ Drift Detection + FairnessGuard |
| Governança de dados de treino | Art. 10 | ✅ Golden Dataset + bias baseline |
| Documentação técnica | Art. 11 | ✅ `docs/architecture/` |
| Rastreabilidade (logs) | Art. 12 | ✅ `audit_service.log_decision()` |
| Transparência para usuários | Art. 13 | ✅ UI + system prompts |
| Supervisão humana (HITL) | Art. 14 | ✅ HITLService em 3 domínios |
| Precisão e robustez | Art. 15 | ⚠️ RAGAS pendente (ACH-027) |

---

## 3. Gestão de Riscos (Art. 9)

### 3.1 Riscos Identificados

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|--------------|---------|-----------|
| R-01 | Discriminação por gênero em triagem | Médio | Alto | FairnessGuard 3 camadas + Four-Fifths Rule |
| R-02 | Discriminação por idade | Médio | Alto | FairnessGuard regex + léxico implícito |
| R-03 | Discriminação por raça/etnia | Baixo | Alto | FairnessGuard + bias audit |
| R-04 | Discriminação por deficiência | Baixo | Alto | FairnessGuard + bias audit (PCD) |
| R-05 | Proxy discrimination (região/CEP) | Médio | Alto | Four-Fifths Rule por região |
| R-06 | Hallucination em avaliações | Médio | Médio | FactChecker + anti-sycophancy |
| R-07 | Drift de modelo ao longo do tempo | Médio | Alto | Drift Detection + Celery batch |
| R-08 | Falta de transparência para candidato | Baixo | Alto | Gate feedback + LGPD portal |
| R-09 | Prompt injection por candidatos | Baixo | Alto | PromptInjectionGuard (SEG-1) |
| R-10 | Perda de dados PII | Baixo | Crítico | strip_pii_for_llm_prompt() + encryption |

### 3.2 Medidas de Mitigação Ativas

#### FairnessGuard (3 Camadas)
- **Camada 1**: 40+ padrões regex — bloqueia discriminação explícita
- **Camada 2**: Léxico implícito — detecta linguagem codificada
- **Camada 3**: LLM semântico (Haiku, opt-in) — bias sutil em contexto
- **Ativação seletiva**: `wsi_score`, `rejection`, `shortlist` (ações de alto impacto)
- **Fallback**: fail-safe — falha na Camada 3 não bloqueia o processo

#### Four-Fifths Rule (Bias Audit)
- Verificação automática em 4 dimensões: gênero, faixa etária, PCD, região
- `adverse_impact_ratio >= 0.80` (threshold EEOC/EU)
- Snapshot histórico com retenção de 3 anos (SOX/EU AI Act)
- API: `GET /api/v1/bias-audit/job/{job_id}`

#### Model Drift Detection
- 4 triggers: score médio, taxa de aprovação, custo/call, latência P95
- Alerta Bell + Teams quando drift detectado (1 trigger=WARNING, 2+=URGENT)
- Job diário: `drift-run-batch-daily` às 06h Brasília

---

## 4. Qualidade e Governança dos Dados (Art. 10)

### 4.1 Dados de Treino/Validação

| Dataset | Registros | Proteções | Localização |
|---------|-----------|-----------|-------------|
| Golden Dataset (fairness) | 60 candidatos | Sintéticos — sem PII | `tests/fixtures/golden_dataset.py` |
| Bias baseline | Distribuição por gênero/idade/PCD/região | Agregado LGPD-safe | `bias_audit_service.py` |
| Prompts few-shot | 3-5 exemplos por domínio | Revisados por humano | `system_prompt.py` de cada agente |

### 4.2 PII em Processamento LLM

- `strip_pii_for_llm_prompt()` aplicado antes de enviar CVs para LLM
- Remove: CPF, email, telefone, RG, CNPJ, endereço, idade explícita, ano de formatura
- 3 callers adicionais protegidos: `analysis_service`, `voice_screening_analysis`, `candidate_comparison_service`

---

## 5. Transparência e Informação (Art. 13)

### 5.1 Para Recrutadores (Usuários B2B)

- Sistema prompts informam explicitamente que é IA
- Pontuações apresentadas com reasoning explicável
- FairnessGuard warnings visíveis quando ativados
- Indicador de confiança em cada avaliação

### 5.2 Para Candidatos (Pessoas Afetadas)

- Gate feedback com explicação de resultado (4 gates)
- LGPD portal: direito de acesso, correção, exclusão (`/data_subject_requests`)
- Consentimento explícito para triagem por IA (`ai_screening` consent flag)
- Avaliação humana garantida via HITL antes de decisões finais de rejeição

---

## 6. Supervisão Humana (Art. 14)

### 6.1 HITL (Human-in-the-Loop) Implementado

| Domínio | Agente | Ação Bloqueada | Aprovação por |
|---------|--------|---------------|--------------|
| Job Wizard | `job_wizard_graph` | Publicação de vaga | Recrutador |
| CV Screening | `wsi_interview_graph` | Feedback final Gate 1 | Recrutador |
| Pipeline | `pipeline_transition_agent` | Movimentação de estágio | Recrutador |
| Sourcing | `sourcing_react_agent` | Envio de abordagem (outreach) | Recrutador |
| Communication | `communication_react_agent` | Envio de rejection/offer | Recrutador |

### 6.2 Decisões Sempre Humanas

- Contratação final: 100% decisão humana (LIA só recomenda)
- Exclusão de candidatos PCD: revisão obrigatória
- Alterações de política de contratação: aprovação de gestor

---

## 7. Precisão, Robustez e Cibersegurança (Art. 15)

### 7.1 Métricas de Qualidade

| Métrica | Meta | Status |
|---------|------|--------|
| Precision@10 (triagem) | > 0.75 | ⚠️ Medição via RAGAS pendente |
| Fairness (Four-Fifths) | AIR ≥ 0.80 | ✅ Verificado por job |
| Drift detection | < 0.3 score drift | ✅ Monitoramento ativo |
| Latência P95 agentes | < 5s | ✅ Prometheus |
| Uptime | > 99.5% | ✅ Circuit breakers |

### 7.2 Robustez contra Adversários

- `PromptInjectionGuard` — detecção high/medium severity em WebSocket
- `bandit` scan — CI verifica vulnerabilidades Python
- Separação de tenants: `company_id` em todos os modelos e queries
- RLS (Row-Level Security) via `company_id` em queries críticas

---

## 8. Registro e Rastreabilidade (Art. 12)

### 8.1 Audit Trail

Todas as decisões de IA são registradas em `audit_decisions` via `audit_service.log_decision()`:

```json
{
  "domain": "cv_screening",
  "agent_name": "wsi_interview_graph",
  "decision_type": "wsi_final_evaluation",
  "decision": "rejected",
  "candidate_id": "<UUID>",
  "company_id": "<UUID>",
  "criteria_ignored": ["gender", "age", "race", ...],
  "metadata": {"final_score": 4.2, "recommendation": "reprovado"}
}
```

### 8.2 Retenção

- Logs de decisão: 7 anos (SOX + BCB 498)
- Logs de acesso: 6 meses (ISO 27001)
- Snapshots bias audit: 3 anos (EU AI Act)

---

## 9. Conformidade com Regulamentos Brasileiros

| Regulamento | Requisito | Implementação |
|-------------|-----------|--------------|
| LGPD (Lei 13.709/2018) | Base legal + direitos do titular | `data_subject_requests.py` + consent |
| BCB 498/2021 | Audit trail + explicabilidade | `audit_service` + reasoning |
| ISO 27001 | ISMS + controles de acesso | `compliance_controls.py` + WorkOS |

---

## 10. Pendências e Plano de Remediação

| Item | Descrição | Prazo |
|------|-----------|-------|
| ACH-007 | WCAG 2.1 AA — contraste e acessibilidade keyboard | Q2 2026 |
| ACH-027 | RAGAS — avaliação contínua de qualidade LLM | Q2 2026 |
| ACH-028 | Red teaming framework — 6 categorias de ataque | Q2 2026 |
| Registro EU AI Act | Notificação à autoridade competente (se operação na UE) | Antes de expansão EU |

---

## 11. Aprovações

| Papel | Nome | Data | Assinatura |
|-------|------|------|-----------|
| CTO / Responsável Técnico | — | 2026-03-15 | Pendente |
| DPO (Proteção de Dados) | — | 2026-03-15 | Pendente |
| Compliance Officer | — | 2026-03-15 | Pendente |

---

*Documento gerado automaticamente com base no estado da plataforma em 2026-03-15.*
*Próxima revisão obrigatória: antes de lançamento de nova funcionalidade de IA classificada como alto risco.*
*Referência: `docs/compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md`*
