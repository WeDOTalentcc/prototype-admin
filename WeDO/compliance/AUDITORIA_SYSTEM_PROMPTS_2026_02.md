# Auditoria de System Prompts — Fevereiro 2026

**Data de auditoria:** 2026-02-28
**Escopo:** Todos os agentes ReAct ativos (7 domínios)
**Objetivo:** Verificar conformidade com EU AI Act Art. 14 (supervisão humana), LGPD e Lei 7.716/1989

---

## Sumário Executivo

| Resultado | Quantidade |
|-----------|-----------|
| ✅ Conforme (com FAIRNESS_AND_COMPLIANCE) | 7 |
| ⚠️ Parcialmente conforme (sem bloco explícito) | 0 |
| ❌ Não conforme | 0 |

Todos os 7 agentes auditados possuem o bloco `FAIRNESS_AND_COMPLIANCE` após esta sprint.

---

## Tabela de Agentes Auditados

| Agente | Arquivo | Bloco Fairness Pré-Sprint | Bloco Fairness Pós-Sprint | Resultado |
|--------|---------|--------------------------|--------------------------|-----------|
| **Wizard** | `app/domains/job_management/agents/wizard_system_prompt.py` | ⚠️ Parcial (`=== COMPLIANCE E ETICA ===`) | ✅ Expandido com `FAIRNESS_AND_COMPLIANCE` | ✅ Conforme |
| **Sourcing** | `app/domains/sourcing/agents/sourcing_system_prompt.py` | ❌ Ausente | ✅ Adicionado `FAIRNESS_AND_COMPLIANCE` | ✅ Conforme |
| **Jobs Mgmt** | `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` | ⚠️ Parcial (`=== COMPLIANCE E ETICA ===`) | ✅ Expandido com `FAIRNESS_AND_COMPLIANCE` | ✅ Conforme |
| **Pipeline (CV Screening)** | `app/domains/cv_screening/agents/pipeline_system_prompt.py` | ✅ Presente | ✅ Mantido | ✅ Conforme |
| **Pipeline (ReAct)** | `app/domains/pipeline/agents/pipeline_system_prompt.py` | ✅ `BEHAVIORAL_RULES` inclui fairness checks | ✅ Mantido | ✅ Conforme |
| **Kanban** | `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` | ✅ Presente | ✅ Mantido | ✅ Conforme |
| **Talent** | `app/domains/recruiter_assistant/agents/talent_system_prompt.py` | ✅ Presente | ✅ Mantido | ✅ Conforme |
| **Policy** | `app/domains/hiring_policy/agents/policy_system_prompt.py` | ✅ Presente | ✅ Mantido | ✅ Conforme |

---

## Critérios Verificados

### Discriminação Proibida
Todos os agentes foram verificados quanto à proibição de:

| Critério | Base Legal | Agentes com Proibição Explícita |
|----------|-----------|--------------------------------|
| Faixa etária | Lei 10.741/2003 (Estatuto do Idoso) | Wizard, Sourcing |
| Gênero | CF Art. 7°, XXX | Wizard, Sourcing |
| Etnia/Raça/Cor | Lei 7.716/1989 | Wizard, Sourcing |
| Origem geográfica (vagas remotas) | CF Art. 3°, IV | Sourcing |
| Universidade específica como eliminatório | Jurisprudência trabalhista | Sourcing |
| Estado civil / planejamento familiar | LGPD Art. 11 | Wizard |
| Aparência física | Jurisprudência TST | Wizard |

### Supervisão Humana (EU AI Act Art. 14)
Todos os agentes:
- ✅ Exigem confirmação explícita antes de ações irreversíveis
- ✅ Nunca executam ações de criação/alteração sem aprovação do recrutador
- ✅ Apresentam dados para embasar recomendações (não decidem sozinhos)
- ✅ Permitem ao recrutador reverter qualquer decisão tomada
- ✅ Alertam sobre viés quando detectado (FairnessGuard integration)

### LGPD — Dados Pessoais Sensíveis
- ✅ Wizard: proibe coleta de raça, religião, orientação sexual, estado civil como requisito de vaga
- ✅ Sourcing: proibe revelar como candidato foi encontrado (confidencialidade da inteligência)
- ✅ Sourcing: mensagens de abordagem requerem opt-out explícito
- ✅ Jobs Mgmt: protege dados sensíveis de candidatos e vagas em análises de portfolio

---

## Mudanças Realizadas Nesta Sprint

### wizard_system_prompt.py
**Expandido:** Bloco `=== COMPLIANCE E ETICA ===` com adição de `=== FAIRNESS_AND_COMPLIANCE ===`

Novos critérios cobertos:
- Faixa etária → citação Lei 10.741/2003
- Gênero → citação CF Art. 7°, XXX
- Aparência física → orientação para critérios objetivos
- Estado civil/planejamento familiar → LGPD Art. 11
- Etnia/origem → Lei 7.716/1989
- Protocolo de detecção e recusa com educação ao recrutador
- Vagas afirmativas como exceção permitida

### sourcing_system_prompt.py
**Adicionado:** Bloco `=== FAIRNESS_AND_COMPLIANCE ===` (novo)

Critérios cobertos:
- Universidade específica como eliminatório → viés socioeconômico
- Faixa etária implícita vs anos de experiência (distinção válida)
- Gênero/etnia/aparência na busca
- Origem geográfica em vagas remotas
- Protocolo de diversidade em shortlists
- LGPD na abordagem de candidatos

### jobs_mgmt_system_prompt.py
**Expandido:** Bloco `=== COMPLIANCE E ETICA ===` com adição de `=== FAIRNESS_AND_COMPLIANCE ===`

Critérios cobertos:
- Análise de portfolio sem viés demográfico
- Critérios objetivos para decisões de fechar/pausar vagas
- Justificativas aceitáveis vs inaceitáveis documentadas
- Métricas de diversidade em relatórios estratégicos

---

## Evidências de Conformidade — EU AI Act Art. 14

O Art. 14 do EU AI Act exige que sistemas de IA de alto risco (incluindo seleção de pessoal) tenham:

1. **Supervisão humana efetiva**: ✅ Todos os agentes exigem confirmação para ações
2. **Capacidade de intervenção**: ✅ Recrutadores podem reverter/cancelar em qualquer estágio
3. **Transparência**: ✅ Agentes explicam raciocínio e citam fontes de dados
4. **Não-automação de decisões discriminatórias**: ✅ FairnessGuard ativo + critérios proibidos explícitos
5. **Logs de auditoria**: ✅ Todas as ações são registradas em `audit_logs`

---

## Próxima Revisão

**Recomendado:** Março 2026 (trimestral)

**Itens pendentes para próxima revisão:**
- Avaliar cobertura do Pipeline ReAct Agent para casos de edge (candidatos com múltiplos atributos de diversidade)
- Revisar adequação do bloco Policy para novos regulamentos em aprovação na UE
- Validar integração FairnessGuard com novos campos de avaliação WSI v2.x
