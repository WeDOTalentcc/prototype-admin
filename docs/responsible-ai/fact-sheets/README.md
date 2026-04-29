# AI Fact Sheets — WeDOTalent LIA

> **Published:** 2026-04-23
> **Source platform:** WeDOTalent LIA (Learning Intelligence Assistant)
> **Regulatory basis:** EU AI Act Art. 13 + NIST AI RMF Transparency + ISO/IEC 42001 Impact Assessment
> **Status:** Drafted and internal — pending final legal review before public release on `wedotalent.cc/responsible-ai/fact-sheets/`

---

## O que é isto? / What is this?

**PT-BR:** Conjunto de "AI Fact Sheets" — documentos padronizados que descrevem cada feature de IA da plataforma LIA em formato consumível por clientes/deployers, auditores e candidatos. Segue o padrão de ML Fact Sheets da Workday e das fact sheets publicadas por Eightfold, LinkedIn e HiPeople.

**EN:** Set of "AI Fact Sheets" — standardized documents describing each AI feature of the LIA platform in a format consumable by clients/deployers, auditors, and candidates. Follows Workday's ML Fact Sheets pattern and the fact sheets published by Eightfold, LinkedIn, and HiPeople.

---

## Índice das 5 features documentadas / Index of 5 documented features

| Feature | PT-BR | English |
|---------|-------|---------|
| CV Screening | [cv-screening-fact-sheet-pt.md](./cv-screening-fact-sheet-pt.md) | [cv-screening-fact-sheet-en.md](./cv-screening-fact-sheet-en.md) |
| WSI Evaluation | [wsi-evaluation-fact-sheet-pt.md](./wsi-evaluation-fact-sheet-pt.md) | [wsi-evaluation-fact-sheet-en.md](./wsi-evaluation-fact-sheet-en.md) |
| Pipeline Transition | [pipeline-transition-fact-sheet-pt.md](./pipeline-transition-fact-sheet-pt.md) | [pipeline-transition-fact-sheet-en.md](./pipeline-transition-fact-sheet-en.md) |
| Ranking & Shortlist | [ranking-shortlist-fact-sheet-pt.md](./ranking-shortlist-fact-sheet-pt.md) | [ranking-shortlist-fact-sheet-en.md](./ranking-shortlist-fact-sheet-en.md) |
| Sourcing & Boolean Search | [sourcing-boolean-fact-sheet-pt.md](./sourcing-boolean-fact-sheet-pt.md) | [sourcing-boolean-fact-sheet-en.md](./sourcing-boolean-fact-sheet-en.md) |

---

## Estrutura padrão / Standard structure

Todas as fact sheets seguem a mesma estrutura de 10 seções:

1. **Propósito / Purpose** — o que a feature faz e por quê
2. **Inputs** — dados recebidos + fonte
3. **Outputs** — dados retornados + semântica
4. **Modelo e Arquitetura / Model and Architecture** — LLM base + versão do YAML canônico + agent
5. **Atributos Protegidos — Cobertura / Protected Attributes — Coverage** — cobertura FairnessGuard
6. **Métricas de Acurácia e Fairness / Accuracy and Fairness Metrics** — ponteiro para doc consolidado Art. 11
7. **Limitações Conhecidas / Known Limitations** — honesto e explícito
8. **Supervisão Humana (HITL) / Human Oversight (HITL)** — quando exige confirmação humana
9. **Direitos do Candidato / Candidate Rights** — EU AI Act Art. 86 + LGPD Art. 20
10. **Contatos / Contacts** — compliance, suporte, DPO

---

## Documentos relacionados / Related documents

- [`eu-ai-act-technical-documentation-pt.md`](../eu-ai-act-technical-documentation-pt.md) — Documentação técnica Art. 11 (PT-BR) — métricas consolidadas, benchmark de mercado, roadmap público
- [`eu-ai-act-technical-documentation-en.md`](../eu-ai-act-technical-documentation-en.md) — EU AI Act Art. 11 Technical Documentation (EN) — consolidated metrics, market benchmark, public roadmap
- [`COMPLIANCE_RECONSTRUCTION_GUIDE.md`](../../reconstruction-guides/COMPLIANCE_RECONSTRUCTION_GUIDE.md) — auditoria completa + plano de ação P0/P1
- [`LIA_PERSONA_RECONSTRUCTION_GUIDE.md`](../../reconstruction-guides/LIA_PERSONA_RECONSTRUCTION_GUIDE.md) — camada de prompts + 24 domain YAMLs
- [`FAIRNESS_LAYER3_RUNBOOK.md`](../../operations/FAIRNESS_LAYER3_RUNBOOK.md) — operação do FairnessGuard Layer 3

---

## Próximos passos antes da publicação pública / Next steps before public release

1. **Revisão jurídica externa** dos 10 documentos (escritório especializado em AI/LGPD/EU AI Act)
2. **Design HTML** dos fact sheets para renderização em `wedotalent.cc/responsible-ai/fact-sheets/`
3. **Publicação do bias audit independente** (Q3/2026 — plano em COMPLIANCE §11.3) — atualizará a seção 6 de cada fact sheet
4. **Link no menu do produto** e no footer do site institucional
5. **Versionamento:** cada fact sheet terá controle de versão semântico + changelog visível na data "Última atualização"

Responsável por coordenação: Compliance team + Marketing + Legal.
Prazo sugerido: **Q2/2026** (em andamento).

---

## Integridade do conteúdo / Content integrity

Todo o conteúdo destes documentos é embasado em leitura direta dos arquivos canônicos em `lia-agent-system/` (Replit). Zero invenção. Se houver divergência entre fact sheet e código atual, **o código é a fonte de verdade** e a fact sheet deve ser atualizada.

Se detectar divergência, reportar para compliance@wedotalent.cc.

---

*README gerado em 2026-04-23*
