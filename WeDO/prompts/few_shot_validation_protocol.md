# Few-Shot Validation Protocol — LIA Prompts

**Versão:** 1.0 | **Data:** 04/março/2026

---

## Objetivo

Garantir que os exemplos few-shot utilizados nos prompts dos agentes LIA representem fielmente as decisões de um profissional sênior de RH, e não padrões de programador ou defaults de LLM.

---

## Regra Fundamental

> **Todo exemplo few-shot deve ser revisado e aprovado por pelo menos 1 profissional sênior de RH antes de entrar em produção.**

---

## Processo de Validação (por domínio)

### 1. Elaboração dos Exemplos

Antes de submeter à revisão de RH, o engenheiro responsável deve:

1. **Criar 10 exemplos claros** — casos onde o comportamento correto é óbvio e unânime
2. **Criar 10 exemplos ambíguos** — casos onde há interpretação possível, como:
   - "quero ver candidatos" → pode ser Kanban, Sourcing ou CV Screening
   - "mover candidato" → pode ser manual (Pipeline) ou automação (Automation)
   - "avaliar esse candidato" → pode ser triagem rápida ou WSI completo
3. **Incluir casos negativos** — o que o agente NÃO deve fazer (scope_out)
4. **Testar com LLM antes da revisão** — rodar 5 variações de cada exemplo e verificar consistência

### 2. Revisão de RH Sênior

O revisor de RH deve ter:
- Mínimo 5 anos de experiência em recrutamento
- Experiência com o segmento de mercado do cliente-alvo (ex: RPO, varejo, tech)
- Familiaridade com o processo WSI da WeDOTalent

O revisor avalia:
- [ ] A resposta do agente reflete o que um recrutador experiente faria?
- [ ] A linguagem está adequada ao tom de comunicação com candidatos?
- [ ] Os critérios de avaliação são objetivos e auditáveis?
- [ ] Há risco de viés inconsciente em algum exemplo?
- [ ] Os casos ambíguos foram resolvidos da forma mais natural para um RH?

### 3. Critérios de Aprovação

Um exemplo é **APROVADO** quando:
- O revisor de RH concorda com o comportamento esperado sem ressalvas
- Não há linguagem que possa ser interpretada como discriminatória
- O raciocínio é auditável (pode ser explicado a um candidato ou auditoria)

Um exemplo é **REJEITADO** quando:
- O comportamento esperado não é natural para um RH experiente
- Usa linguagem informal, jargão técnico ou não-inclusiva
- Baseia decisão em critérios não auditáveis

---

## Exemplos por Domínio (mínimo exigido)

| Domínio | Exemplos Claros | Exemplos Ambíguos | Status |
|---------|----------------|-------------------|--------|
| sourcing | 10 | 10 | ⬜ Pendente |
| job_management | 10 | 10 | ⬜ Pendente |
| cv_screening | 10 | 10 | ⬜ Pendente |
| communication | 10 | 10 | ⬜ Pendente |
| interview_scheduling | 10 | 10 | ⬜ Pendente |
| pipeline | 10 | 10 | ⬜ Pendente |
| recruiter_assistant | 10 | 10 | ⬜ Pendente |
| analytics | 10 | 10 | ⬜ Pendente |
| automation | 10 | 10 | ⬜ Pendente |

---

## Casos Ambíguos Obrigatórios (cross-domain)

Os seguintes casos DEVEM estar cobertos nos exemplos few-shot de routing (intent_router):

| Frase do Usuário | Pode Ser | Critério de Decisão |
|-----------------|----------|---------------------|
| "quero ver candidatos" | Kanban, Sourcing, CV Screening | Contexto: há vaga ativa? Estágio do processo? |
| "mover candidato" | Pipeline (manual), Automation (regra) | Uma vez ou sempre que X acontecer? |
| "avaliar candidato" | CV Screening (rubrica), Interview (WSI) | CV em mãos? Entrevista agendada? |
| "preciso de mais candidatos" | Sourcing, CV Screening (reabrir pool) | Pipeline escasso (< 5) ou necessidade nova? |
| "criar vaga" | Job Management (nova), Job Management (editar) | Já existe rascunho? |
| "feedback para o candidato" | Communication, Pipeline | Aprovado ou rejeitado? Etapa? |
| "entrevistar candidato" | Interview Scheduling, Sourcing | Candidato já triado? Etapa? |

---

## Onde os Exemplos Ficam no Código

```
app/prompts/
  domains/          ← system_prompt + intent_examples (YAML)
  examples.py       ← FewShotExamples (JOB_EXTRACTION, INTENT_CLASSIFICATION, etc.)
  shared/
    agent_prompts.yaml  ← few-shot exemplos compartilhados entre agentes
```

Para adicionar exemplos validados:

```python
# app/prompts/examples.py
JOB_EXTRACTION_EXAMPLES = FewShotExamples(examples=[
    # ADICIONAR AQUI após aprovação de RH sênior
    {
        "input": "Preciso contratar um dev Python pleno, remoto, até R$ 8k",
        "output": {
            "title": "Desenvolvedor Python Pleno",
            "modality": "remote",
            "salary_max": 8000,
            "seniority": "mid"
        },
        "validated_by": "Nome do revisor",
        "validated_at": "2026-03-XX"
    }
])
```

---

## Checklist de Release

Antes de habilitar novos exemplos few-shot em produção:

- [ ] 10 exemplos claros validados por RH sênior
- [ ] 10 exemplos ambíguos validados por RH sênior
- [ ] Teste de regressão: exemplos existentes não foram afetados
- [ ] Sem linguagem discriminatória (auditado por FairnessGuard Layer 1)
- [ ] Aprovação técnica do engenheiro responsável pelo domínio
- [ ] Documentação: revisor, data, versão do modelo testado

---

## Histórico de Revisões

| Data | Domínio | Revisor | Versão | Mudanças |
|------|---------|---------|--------|----------|
| 04/mar/2026 | — | — | 1.0 | Protocolo inicial criado |
