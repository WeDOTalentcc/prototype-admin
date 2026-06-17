# SPEC_TEMPLATE.md — Template para Specs de Features Novas

**Versão:** 1.0
**Última atualização:** 2026-03-26

---

## Instruções

Copie este template ao criar uma spec para uma feature nova. Preencha cada seção. Remova as instruções em itálico antes de submeter para review.

---

# [NOME_DA_FEATURE] — Spec

**Autor:** [Nome]
**Data:** [YYYY-MM-DD]
**Status:** Draft | Review | Approved | Implemented
**Ticket:** [LIA-XXXX]

---

## 1. Resumo

*Uma frase descrevendo o que a feature faz e por que é necessária.*

---

## 2. Contexto e Motivação

*Por que essa feature existe? Qual problema resolve? Quem pediu? Há dados que justificam?*

---

## 3. User Stories

*Liste as user stories no formato "Como [persona], quero [ação] para [benefício]".*

| # | Persona | Ação | Benefício |
|---|---------|------|-----------|
| US-1 | | | |
| US-2 | | | |

---

## 4. Requisitos Funcionais

*Liste os requisitos objetivos e testáveis.*

| # | Requisito | Prioridade | Critério de aceite |
|---|-----------|-----------|-------------------|
| RF-1 | | Must | |
| RF-2 | | Should | |
| RF-3 | | Could | |

---

## 5. Requisitos Não-Funcionais

| # | Requisito | Métrica |
|---|-----------|---------|
| RNF-1 | Performance | P95 < Xms |
| RNF-2 | Disponibilidade | 99.9% uptime |
| RNF-3 | Segurança | Multi-tenant, PII masking |

---

## 6. Arquitetura

### 6.1 Componentes Impactados

*Liste os arquivos/módulos que serão criados ou modificados.*

| Componente | Ação | Arquivo |
|-----------|------|---------|
| | Criar / Modificar | |

### 6.2 Diagrama de Fluxo

*Descreva o fluxo principal da feature.*

```
[Passo 1] → [Passo 2] → [Passo 3]
```

### 6.3 API (se aplicável)

| Método | Endpoint | Auth | Request Body | Response |
|--------|----------|------|-------------|----------|
| | | | | |

### 6.4 Modelo de Dados (se aplicável)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| | | | |

---

## 7. Design / UX (se aplicável)

*Descreva as telas, componentes UI, estados e interações.*

| Componente | Estado | Comportamento |
|-----------|--------|--------------|
| | | |

---

## 8. Integração com IA (se aplicável)

### 8.1 Agente/Domínio

*Qual domínio de agente é impactado? Qual tool será adicionada/modificada?*

### 8.2 System Prompt

*Mudanças no system prompt? Nova seção de few-shot examples?*

### 8.3 Fairness

*Como essa feature garante que não introduz bias? FairnessGuard necessário?*

---

## 9. Plano de Testes

| Camada | O que testar | Arquivo esperado |
|--------|-------------|-----------------|
| Unit | | `tests/unit/test_xxx.py` |
| Contract | | `tests/contract/test_xxx.py` |
| Integration | | `tests/integration/test_xxx.py` |
| Fairness | | `tests/fairness/test_xxx.py` (se impacta scoring) |

---

## 10. Checklist de Compliance

- [ ] Multi-tenant: todas as queries filtram por company_id
- [ ] PII masking: logs não contêm dados pessoais
- [ ] LGPD: consentimento verificado antes de processar dados
- [ ] FairnessGuard: outputs que impactam candidatos passam pelo guard
- [ ] Blind evaluation: dados demográficos não incluídos no contexto LLM
- [ ] Anti-sycophancy: prompts instruídos a dar feedback honesto
- [ ] Prompt injection: inputs sanitizados

---

## 11. Rollout

*Como será o rollout? Feature flag? A/B test? Gradual?*

| Fase | Escopo | Critério de avanço |
|------|--------|-------------------|
| 1 | | |
| 2 | | |

---

## 12. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| | | | |

---

## 13. Referências

*Links para specs relacionados, docs externos, designs.*

| Referência | Link |
|-----------|------|
| | |
