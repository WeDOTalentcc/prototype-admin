---
name: dei-fairness
description: "Princípios de Diversidade, Equidade e Inclusão (DEI) e Fairness na Plataforma LIA conforme Guia v3.3. Use ao criar/modificar funcionalidades de screening, avaliação, ranking, perguntas de entrevista, ou qualquer componente que possa impactar candidatos de forma desigual. Cobre FairnessGuard (3 camadas), Bias Audit Dashboard, Affirmative Criteria e Acessibilidade como DEI. Referência: attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md"
---

# DEI e Fairness — Princípios e Implementação na Plataforma LIA

Skill de referência para garantir que toda funcionalidade que toca avaliação, ranking, filtragem ou comunicação com candidatos respeite os princípios de Diversidade, Equidade e Inclusão definidos no Guia WeDO Talent v3.3.

> **Skills relacionadas:** wedo-governance, screening-compliance, lgpd-data-protection

## 1. Quando Usar

Ative esta skill ao trabalhar em qualquer funcionalidade que avalie, pontue, classifique, filtre, ordene ou exclua candidatos.

---

## 2. FairnessGuard — 3 Camadas de Proteção

`app/shared/compliance/fairness_guard.py`

### Camada 1 — Regex Patterns (40+ patterns, 8 categorias)

Ação: `BLOCK_AND_WARN` — bloqueia e notifica o recrutador com mensagem educativa.

| Categoria | Exemplos de patterns detectados | Base legal |
|-----------|--------------------------------|------------|
| **Gênero** | "apenas homens", "sexo masculino", "preferência por mulheres" | Art. 5º CLT, LGPD |
| **Raça/Etnia** | "apenas brancos", "raça branca", "excluir negros" | CF Art. 5º, Lei 7.716/89 |
| **Idade** | "jovens apenas", "idade máxima 35", "velho demais" | Estatuto do Idoso (Lei 10.741/03) |
| **Religião** | "apenas cristãos", "excluir muçulmanos" | CF Art. 5º, VI |
| **Orientação Sexual** | "apenas heterossexuais", "excluir gays" | ADO 26 (STF) |
| **Estado Civil** | "apenas solteiros", "excluir casados" | CLT |
| **Deficiência** | "excluir deficientes", "sem PCD", "excluir PCD" | Lei 8.213/91, Lei 13.146/15 |
| **Nacionalidade** | "apenas brasileiros", "excluir estrangeiros" | CF Art. 5º |

### Camada 2 — Léxico Implícito (15+ termos de viés sutil)

Ação: `soft_warning` — apresenta alerta educativo sem bloquear, sugere reformulação.

| Termo detectado | Tipo de viés | Sugestão educativa |
|-----------------|-------------|-------------------|
| "boa aparência" | Discriminação estética | Referenciar critérios objetivos de apresentação profissional |
| "apresentação pessoal" | Discriminação estética | Definir critérios objetivos mensuráveis |
| "bairros nobres" / "região nobre" | Discriminação socioeconômica | Usar critérios de disponibilidade ou mobilidade |
| "universidades de primeira linha" / "faculdade de ponta" | **Elitismo acadêmico** | Focar em competências e resultados demonstráveis |
| "escola particular" | Discriminação socioeconômica | Avaliar formação e competências, não instituição |
| "perfil adequado" | Viés vago | Definir competências objetivas |
| "morar próximo" | Discriminação socioeconômica | Avaliar disponibilidade ou opção de trabalho remoto |
| "boa família" | Discriminação de origem | Usar critérios exclusivamente profissionais |
| "clube social" | Discriminação de classe | Remover critérios de classe social |
| "jovem e dinâmico" | Viés de idade (implícito) | Descrever competências objetivas sem referência a idade |
| "native speaker" | Viés de sotaque/nacionalidade | Especificar nível de proficiência real exigido |
| "recém-formado" | Viés de idade | Definir anos de experiência verificáveis |

> **Atenção:** Termos como "universidades de primeira linha" são detectados como viés implícito de elitismo acadêmico — alinhado ao princípio de que **formação acadêmica deve ser avaliada por competências, não por prestígio institucional** (ver Seção 7).

### Camada 3 — LLM Semântico

Análise contextual profunda para textos longos onde regex e léxico não capturam nuances. Custo: tokens + ~2s de latência. Acionado apenas quando Camadas 1 e 2 não são conclusivas.

### Escopo de Cobertura do FairnessGuard

O FairnessGuard NÃO cobre apenas endpoints de API. A cobertura obrigatória inclui:

| Ponto de verificação | Arquivo | Método |
|---------------------|---------|--------|
| Endpoints REST (triagem, notas) | `app/api/v1/interview_notes.py`, `rubric_evaluation.py` | `guard.check()` no handler |
| Output do avaliador WSI | `app/domains/cv_screening/agents/avaliador_wsi_agent.py` | `_fairness_guard.check()` antes de criar `LiaOpinion` |
| Parecer do candidato | `app/domains/analytics/services/candidate_report_service.py` | `guard.check()` em seções 3, 4, 6 |
| Feedback de rejeição | `app/domains/cv_screening/services/personalized_feedback_service.py` | `guard.check()` antes de `status = "pending_approval"` |
| Campos livres de schema | `app/schemas/screening.py` → `FormacaoPreQualifierResult.note` | `model_validator` com `check_implicit_bias()` |

**Padrão para campos de texto livre em schemas Pydantic:**
```python
@model_validator(mode="after")
def _check_note_fairness(self) -> "Self":
    if self.note:
        warnings = FairnessGuard().check_implicit_bias(self.note)
        if warnings:
            logger.warning("FairnessGuard: implicit bias detectado", extra={"warnings": warnings})
    return self
```

> **Regra:** Todo campo `str` que aceita texto gerado por IA ou inserido livremente por recrutador **deve** passar por `check_implicit_bias()`. Campos estruturados (IDs, datas, scores) são isentos.

---

## 3. Dimensões de Diversidade Testadas

Meta: variância < 3% entre grupos em todas as dimensões.

| Dimensão | Grupos testados |
|----------|----------------|
| **Gênero** | Masculino, Feminino, Não-binário, Prefiro não responder |
| **Idade** | 25-35, 35-50, 50+ |
| **Formação** | Universidade, Bootcamp, Autodidata ← alto risco (ver Seção 7) |
| **Região** | SP/RJ, Outras capitais, Interior |
| **Deficiência** | Com deficiência (PCD), Sem deficiência |
| **Proficiência linguística** | Nativo, Não-nativo |
| **Trajetória** | Formal, Bootcamp, Autodidata, Carreira em transição |

---

## 4. Bias Audit Dashboard

Rota: `admin/compliance/auditoria/bias`

**Métricas calculadas por dimensão:**

| Métrica | Fórmula | Meta |
|---------|---------|------|
| `selection_rate` | (aprovados do grupo / total do grupo) × 100 | Variância < 3% |
| `adverse_impact_ratio` | selection_rate(minoritário) / selection_rate(referência) | ≥ 0.80 (Regra dos 4/5) |

**Interpretação do ratio:**

| Ratio | Status | Ação |
|-------|--------|------|
| ≥ 0.80 | ✅ OK | Monitorar |
| 0.60–0.79 | ⚠️ Investigar | Análise de causa raiz |
| < 0.60 | ❌ Ação imediata | Suspender e corrigir |

**Compliance regulatório do dashboard:**

| Framework | Requisito | Como atendemos |
|-----------|-----------|----------------|
| **NYC Local Law 144** | Auditoria anual de viés em AEDT | Auditoria mensal interna + trimestral externa |
| **EU AI Act** | Avaliação de conformidade, supervisão humana | FairnessGuard ativo + logs de auditoria |
| **LGPD Art. 6º** | Não-discriminação; Art. 20 — revisão de decisões automatizadas | Mascaramento de atributos + direito a revisão humana |

---

## 5. Critérios Afirmativos

Patterns afirmativos detectados pelo `IntentClassifier`: PCD, Mulheres, Pessoas Negras, LGBTQIA+, 50+, Indígena, Pessoas Trans.

**Regras:**
- **MANTÉM** como preferência positiva — aumenta visibilidade do grupo
- **NÃO PENALIZA** candidatos fora do grupo
- **NÃO EXCLUI** — critérios afirmativos são inclusivos, nunca excludentes

---

## 6. Acessibilidade como DEI

WCAG 2.1 AA obrigatório (Crença #13 do Manifesto). Radix UI primitives, `aria-labels`, `sr-only`, `focus-visible`, `prefers-reduced-motion`. Contraste mínimo 4.5:1.

---

## 7. ⚠️ Formação Acadêmica como Dimensão de Alto Risco de Viés

A dimensão **Formação** é a de **maior risco de viés socioeconômico** no WSI. O Bias Audit Dashboard monitora explicitamente a disparidade entre: Universidade, Bootcamp e Autodidata.

**O que nunca deve ser avaliado:**
- Prestígio da instituição ("USP > UNINOVE" não é competência, é privilégio de acesso)
- Tipo de educação (presencial vs. EAD vs. bootcamp)
- Grau acadêmico quando não há requisito legal

**O que pode ser avaliado:**
- Certificações obrigatórias por lei (OAB, CREA, CRM)
- Certificações técnicas verificáveis (AWS, PMP, CPA)
- Proficiência em idiomas quando a vaga exige
- Competências demonstráveis, independente de onde foram adquiridas

**Regra de equivalência:** `bootcamp = diploma onde aplicável`

**Sinais de alerta no FairnessGuard:** termos como "universidades de primeira linha", "faculdade de ponta", "escola particular" são detectados como viés implícito de elitismo acadêmico (Camada 2).

---

## 7. Checklist DEI para Novas Features

Linguagem neutra, sem proxies discriminatórios, FairnessGuard integrado, atributos protegidos mascarados, acessível via teclado e screen reader, candidato informado sobre IA, opt-out disponível, feedback personalizado, resultado explicável, logs de auditoria.

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/dei-fairness` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/dei-fairness.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/dei-fairness/SKILL.md` |

**Quando ativar:**
- Ao criar funcionalidades que avaliam, pontuam, classificam, filtram ou excluem candidatos
- Ao implementar ou modificar linguagem de interface voltada a candidatos
- Ao configurar critérios afirmativos ou políticas de diversidade
- Ao auditar viés em algoritmos existentes
