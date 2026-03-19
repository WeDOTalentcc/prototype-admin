# FRIA — Avaliação de Impacto em Direitos Fundamentais
## WSI Screening System | WeDOTalent v1.0 | 11/03/2026

---

## 1. Sistema sob Avaliação

**Nome do sistema:** WSI — Voice Screening Interview (Entrevista de Triagem por Voz)

**Descrição:** Sistema automatizado de triagem de candidatos via entrevista por voz estruturada em 7 blocos. O candidato responde a perguntas via canal de voz (WhatsApp, telefone ou web widget); o sistema transcreve, analisa e gera pontuação final de 0 a 100.

**Características técnicas:**

| Componente | Tecnologia | Versão |
|-----------|-----------|--------|
| ASR (Reconhecimento de Fala) | Deepgram Nova-2 | API v1 |
| NLP / Avaliação | Claude Sonnet 4.6 (Anthropic) | via LangChain |
| Orquestração | LangGraph ReAct | Graph: `wsi_interview_graph.py` |
| Persistência | PostgreSQL (Neon) + pgvector | SQLAlchemy 2.0 async |
| Cache / Sessão | Redis | TTL configurável |
| Filas | RabbitMQ + Celery | task: `agents.wsi_interview.start` |

**Dimensões avaliadas:**
1. Abertura e apresentação
2. Motivação para a vaga
3. Experiência técnica relevante
4. Soft skills e comunicação
5. Pretensão salarial e benefícios
6. Disponibilidade e logística
7. Fechamento e próximos passos

**Saída do sistema:** Recomendação numérica 0–100 + classificação (Avançar / Revisar / Rejeitar) + justificativa textual por dimensão.

**Classificação EU AI Act:** Sistema de IA de alto risco — Anexo III, ponto 4 (emprego e gestão de trabalhadores).

---

## 2. Fundamentação Legal

### 2.1 EU AI Act
- **Art. 9** — Gestão de riscos: exige processo contínuo de identificação, análise e mitigação de riscos para sistemas de alto risco.
- **Annex III, ponto 4** — "Employment, workers management and access to self-employment": sistemas de IA usados para recrutamento, seleção, promoção ou término de relação de trabalho são classificados como alto risco.
- **Art. 13** — Transparência: candidatos devem ser informados da utilização de sistema de IA.
- **Art. 14** — Supervisão humana: revisão humana obrigatória para decisões adversas.

### 2.2 LGPD (Brasil — Lei 13.709/2018)
- **Art. 20** — Direito de revisão de decisões automatizadas: o titular de dados pode solicitar revisão humana de qualquer decisão tomada exclusivamente por meios automatizados.
- **Art. 6º, IV** — Livre acesso: candidatos têm direito de acesso aos seus dados e ao resultado da avaliação.
- **Art. 6º, X** — Responsabilização: WeDOTalent responde pela adequação do sistema às normas.

### 2.3 BCB 498 (Brasil — Resolução BCB nº 498/2023)
Aplicável a clientes da plataforma que sejam instituições financeiras reguladas pelo Banco Central. Exige:
- Controles de qualidade e validação de modelos de IA usados em processos de crédito e RH.
- Documentação de governança de algoritmos com revisão periódica.
- Trilha de auditoria completa de decisões automatizadas.

---

## 3. Direitos Fundamentais em Risco

| Direito Fundamental | Risco Identificado | Mitigação Implementada | Risco Residual |
|--------------------|-------------------|----------------------|----------------|
| **Dignidade humana** | Avaliação desumanizante por voz sem contexto pessoal | Blocos estruturados com abertura humanizada; candidato informado previamente | Baixo |
| **Não-discriminação** | Viés em ASR para sotaques regionais, gagueira, voz atípica | FairnessGuard 3 camadas; Deepgram treinado em PT-BR multidialetal; Bias Audit mensal Four-Fifths Rule | Médio |
| **Privacidade** | Coleta de dados biométricos (voz), processamento por LLM externo | PII masking via `strip_pii_for_llm_prompt`; retenção 180 dias; anonimização para análise | Baixo |
| **Devido processo** | Decisão adversa sem possibilidade de contestação | HITL path para revisão humana; LGPD Art. 20 endpoint ativo; SLA 15 dias úteis | Baixo |
| **Transparência** | Candidato não sabe que é avaliado por IA | ConsentCheckerService Gate 1 obrigatório antes de iniciar sessão; aviso no início da chamada | Baixo |
| **Equidade de acesso** | Candidatos sem microfone de qualidade penalizados | Score de qualidade de áudio não penaliza resposta; fallback para avaliação textual disponível | Médio |

---

## 4. Análise de Risco por Dimensão WSI

| Bloco | Dimensão Avaliada | Risco Principal | Mitigação | Nível de Risco |
|-------|------------------|----------------|-----------|----------------|
| 1 | Abertura e apresentação | Penalização por dicção/fluência → discriminação por deficiência auditiva | FairnessGuard Camada 1 (regex PROTECTED_CRITERIA) bloqueia avaliação de características físicas | Baixo |
| 2 | Motivação para a vaga | Candidatos de grupos sub-representados podem ter narrativas diferentes | FactChecker valida afirmações; benchmark setorial impede sycophancy | Baixo |
| 3 | Experiência técnica | Viés de gênero em avaliação de competências técnicas (STEM) | FairnessGuard Camada 2 (léxico implícito); Four-Fifths Rule por gênero em Bias Audit | Médio |
| 4 | Soft skills e comunicação | Avaliação subjetiva de "fit cultural" pode codificar preconceito | Critérios objetivos em rubrica; FairnessGuard Camada 3 LLM (opt-in) para revisão | Médio |
| 5 | Pretensão salarial | Candidatos de regiões periféricas com pretensões menores → sinal falso positivo | Benchmark salarial regional injetado no prompt (anti-sycophancy) | Baixo |
| 6 | Disponibilidade | Discriminação indireta por cuidados familiares (maioria mulheres) | PROTECTED_CRITERIA inclui "disponibilidade imediata" como critério protegido | Baixo |
| 7 | Fechamento | Ansiedade no fim da chamada pode distorcer score geral | Score por bloco independente; agregação ponderada não supervaloriza bloco final | Baixo |

---

## 5. Salvaguardas Implementadas

### 5.1 FairnessGuard — 3 Camadas

**Camada 1 — Filtro Regex (40+ patterns):**
- Arquivo: `app/services/fairness_guard_service.py`
- Detecta e bloqueia referências a: gênero, raça, etnia, orientação sexual, deficiência, religião, região, idade, estado civil, aparência física, sotaque, voz.
- Aplicação: pré-processamento de todo prompt enviado ao LLM.

**Camada 2 — Léxico Implícito:**
- Detecta codificações indiretas ("candidato dinâmico", "perfil jovem", "disponibilidade integral").
- Lista curada e atualizada mensalmente com base em red team interno.

**Camada 3 — LLM Judge (opt-in):**
- Ativado via `FAIRNESS_LAYER3_ENABLED=true`.
- Claude Sonnet 4.6 revisa output do agente WSI antes de finalizar score.
- Recomendado para clientes em segmentos regulados (financeiro, saúde).

### 5.2 AuditService — PROTECTED_CRITERIA

Critérios protegidos validados em todas as avaliações WSI:
- Gênero, raça, cor, etnia, origem nacional ou regional
- Deficiência física, sensorial ou mental
- Orientação sexual, identidade de gênero
- Religião, convicção política
- Estado civil, maternidade/paternidade
- Situação econômica

### 5.3 PII Masking — strip_pii_for_llm_prompt

- Função: `app/shared/pii_masking.py::strip_pii_for_llm_prompt()`
- Remove CPF, RG, e-mail, telefone, endereço completo, nome completo antes de enviar ao LLM.
- Log mascarado: PIIMaskingFilter instalado em todos os workers Celery.

### 5.4 ConsentCheckerService — Gate 1

- Serviço: `app/services/consent_management.py`
- Checagem obrigatória antes de iniciar qualquer sessão WSI.
- Candidato deve consentir explicitamente com: gravação de voz, processamento por IA, retenção por 180 dias.
- Sem consentimento registrado → sessão bloqueada automaticamente.

### 5.5 HITL — Human Review Path

- Implementação: `app/services/hitl_service.py`
- Casos de acionamento automático:
  - Score entre 40–60 (zona cinzenta)
  - FairnessGuard Camada 2 ou 3 sinaliza risco
  - Candidato solicita revisão (LGPD Art. 20)
  - Qualidade de áudio abaixo do threshold
- Recrutador recebe notificação Bell + Teams com link para revisão.

### 5.6 FactChecker

- Serviço: `app/services/fact_checker_service.py`
- Verifica afirmações do candidato sobre experiência e formação contra dados estruturados disponíveis.
- Previne penalização por candidatos que descrevem experiências de forma não-convencional.

---

## 6. Direito de Revisão Humana (LGPD Art. 20)

### 6.1 Processo de Solicitação

O candidato pode solicitar revisão humana de sua avaliação WSI por qualquer canal:
- Portal do candidato: `/candidato/minha-avaliacao/solicitar-revisao`
- E-mail: `privacidade@wedotalent.com.br`
- WhatsApp: via bot LIA com intent "revisar avaliação"

### 6.2 Endpoint Disponível

```
POST /api/v1/data-subject-requests
{
  "tipo": "revisao_decisao_automatizada",
  "candidate_id": "<id>",
  "job_id": "<id>",
  "motivo": "string opcional"
}
```

Retorno: `{ request_id, status: "pending", sla_dias_uteis: 15 }`

### 6.3 SLA e Processo

| Etapa | Responsável | Prazo |
|-------|------------|-------|
| Recebimento e confirmação ao candidato | Sistema automático | Imediato |
| Atribuição a recrutador humano | Supervisor de RH | 1 dia útil |
| Revisão da avaliação e score | Recrutador sênior | 10 dias úteis |
| Comunicação ao candidato | Recrutador | 15 dias úteis |
| Registro no audit trail | Sistema | Automático |

### 6.4 Garantias ao Candidato

- A solicitação de revisão não prejudica candidatura ativa.
- O candidato recebe explicação legível sobre os critérios avaliados.
- Em caso de revisão favorável, o processo retorna ao estágio anterior.

---

## 7. Plano de Monitoramento

### 7.1 Drift Detection — Mensal

- Serviço: `app/services/model_drift_service.py`
- Triggers monitorados: desvio de score médio, taxa de aprovação por grupo, custo por avaliação, latência P95.
- Agendamento: job Celery Beat diário (`drift.run_batch` às 06h Brasília).
- Alerta automático: Bell + Teams quando 2+ triggers ativos (`drift_alert_service`).

### 7.2 Bias Audit — Four-Fifths Rule

- Serviço: `app/services/bias_audit_service.py`
- Frequência: auditoria mensal automática + snapshot histórico (SOX/ISO 27001).
- Dimensões: gênero, faixa etária, deficiência (PCD), região geográfica.
- Threshold: adverse_impact_ratio >= 0.80 por dimensão.
- Ação se abaixo do threshold: alerta ao DPO + revisão obrigatória do modelo.

### 7.3 Red Team — Semestral

- Execução: equipe interna + auditoria externa independente.
- Escopo: injeção de candidatos fictícios com características protegidas para verificar viés de output.
- Referência: `tests/fairness/test_four_fifths_rule.py` + `tests/fixtures/golden_dataset.py`.
- Resultado documentado em `docs/compliance/red_team_<ano>_<semestre>.md`.

### 7.4 Revisão de Prompts — Trimestral

- Auditoria dos system prompts WSI em `app/domains/cv_screening/agents/system_prompt.py`.
- Verificação de linguagem neutra e ausência de critérios implicitamente discriminatórios.
- Referência: `docs/compliance/AUDITORIA_SYSTEM_PROMPTS_2026_02.md`.

---

## 8. Aprovação e Validade

| Campo | Valor |
|-------|-------|
| **Versão do documento** | 1.1 |
| **Data de emissão** | 11/03/2026 |
| **Última atualização** | 11/03/2026 |
| **Aprovado por** | DPO WeDOTalent |
| **Número RIPD/DPIA** | RIPD-LIA-WSI-2026-001 |
| **Validade** | 12 meses |
| **Próxima revisão obrigatória** | 03/2027 |
| **Gatilhos de revisão antecipada** | Mudança de modelo LLM, novo regulamento EU AI Act, resultado adverso em Bias Audit, incidente de discriminação reportado |

---

## 9. Avaliação de Riscos Residuais

> Riscos remanescentes **após** aplicação de todas as salvaguardas da Seção 5.
> Metodologia: Probabilidade (1–5) × Impacto (1–5) = Score. Aceitável ≤ 9, Tolerável 10–14, Inaceitável ≥ 15.

| # | Risco Residual | Probabilidade | Impacto | Score | Classificação | Responsável |
|---|---------------|:---:|:---:|:---:|---|---|
| R1 | Viés de ASR para sotaques muito específicos (ex: interior Norte/Nordeste) não cobertos pelo treinamento Deepgram | 2 | 4 | **8** | Aceitável | Equipe de IA |
| R2 | Avaliação de soft skills (Bloco 4) com variância alta entre avaliações de mesmo candidato | 2 | 3 | **6** | Aceitável | DPO + Produto |
| R3 | Candidato com dificuldade de fala (gagueira leve) não identificado pelo filtro de qualidade de áudio | 2 | 4 | **8** | Aceitável | Engenharia |
| R4 | Prompt injection via resposta do candidato não detectado por camada 1/2 do FairnessGuard | 1 | 5 | **5** | Aceitável | Segurança |
| R5 | Deriva de modelo LLM (Claude) entre versões sem atualização de rubrica de avaliação | 2 | 3 | **6** | Aceitável | MLOps |
| R6 | Ausência de conteúdo em bloco WSI interpretada como nota baixa (penalização por falha técnica) | 2 | 3 | **6** | Aceitável | Produto |
| R7 | Candidatos sem experiência com entrevistas por voz (primeira vez) com desempenho abaixo do potencial real | 3 | 3 | **9** | Aceitável | Produto |

**Nenhum risco residual classificado como Inaceitável (≥ 15).**

### 9.1 Plano de Tratamento dos Riscos Residuais

| Risco | Ação de Mitigação Adicional | Prazo | Status |
|-------|---------------------------|-------|--------|
| R1 | Ampliar golden dataset de sotaques (Norte/Nordeste) em `tests/fixtures/golden_dataset.py` | Q2 2026 | Planejado |
| R7 | Criar guia de orientação pré-entrevista enviado ao candidato 24h antes via WhatsApp/e-mail | Q2 2026 | Planejado |
| R3 | Adicionar detecção de gagueira leve à camada de qualidade de áudio; ativar HITL automático | Q3 2026 | Planejado |
| R5 | Incluir benchmark de modelo na suite de CI/CD para detectar regressão cross-versão | Q2 2026 | Planejado |

---

## 10. Plano de Resposta a Incidentes de IA

> Conforme **EU AI Act Art. 73** (obrigação de notificação de incidentes graves) e **LGPD Art. 48** (notificação de incidentes de segurança).

### 10.1 Definição de Incidente Grave

Um incidente no sistema WSI é classificado como **grave** se:
- Candidato for eliminado de processo seletivo por decisão automatizada com evidência de discriminação por critério protegido;
- Taxa de adverse impact ratio < 0.65 em qualquer dimensão (abaixo do limiar NYC LL144);
- Falha de segurança com exposição de dados biométricos de voz;
- Score de candidato alterado indevidamente por prompt injection confirmado.

### 10.2 Fluxo de Resposta

```
Detecção (Sistema / Reclamação)
    ↓
T+0h: Registrar incidente em #compliance-incidents (Teams) + criar ticket
    ↓
T+4h: DPO notificado — avaliação de gravidade (grave / não grave)
    ↓
T+24h: Se grave → Contenção imediata (suspender avaliações da empresa afetada)
    ↓
T+72h: Análise de causa raiz (engenharia + IA)
    ↓
T+15 dias: Notificação ao regulador competente (ANPD / autoridade EU AI Act)
    ↓
T+30 dias: Relatório de incidente final + plano de correção
    ↓
T+60 dias: Verificação de eficácia das correções aplicadas
```

### 10.3 Contatos e Responsabilidades

| Papel | Responsabilidade | Canal |
|-------|-----------------|-------|
| DPO | Notificação regulatória, comunicação ao titular | `privacidade@wedotalent.com.br` |
| CISO | Contenção técnica, análise forense | Slack `#security-incidents` |
| Engenharia IA | Análise de causa raiz, correção de modelo | Jira projeto `LIA-COMPLIANCE` |
| Jurídico | Avaliação de responsabilidade civil, regulatória | `juridico@wedotalent.com.br` |

### 10.4 Notificação ao Titular (LGPD Art. 48)

Se o incidente envolver dados de candidatos:
- Notificação individual ao(s) titular(es) afetado(s) em até **5 dias úteis**.
- Canal: e-mail registrado + notificação no portal do candidato.
- Conteúdo obrigatório: natureza dos dados, medidas adotadas, DPO de contato, data do incidente.

### 10.5 Registro de Incidentes

Todos os incidentes (graves e não graves) registrados em:
- `docs/compliance/incidentes/INCIDENTE_<ANO>_<SEQ>.md`
- Banco de dados: tabela `compliance_incidents` (auditável SOX/ISO 27001)

---

## 11. Declaração de Conformidade

> Esta seção constitui a declaração formal de conformidade do sistema WSI com os requisitos aplicáveis.

### 11.1 Declaração

A WeDOTalent declara que o sistema **WSI — Voice Screening Interview**, conforme descrito neste documento, foi projetado, implementado e operado em conformidade com:

- ✅ **EU AI Act** — Arts. 9, 13, 14, 16, 73 e Annex III ponto 4 (sistemas de IA de alto risco em emprego)
- ✅ **LGPD** — Arts. 6º, 20 e 48 (revisão de decisões automatizadas, notificação de incidentes)
- ✅ **BCB 498** — Governança de modelos de IA para clientes de instituições financeiras reguladas
- ✅ **ISO 27001** — Controles de segurança da informação implementados e auditados
- ✅ **NYC LL144** — Requisitos de auditoria de viés (Four-Fifths Rule em 4 dimensões)

### 11.2 Limitações e Condições de Uso

O sistema WSI é aprovado para uso com as seguintes condições obrigatórias:

1. **Consentimento explícito** do candidato deve ser coletado antes de cada sessão (via `ConsentCheckerService`).
2. **HITL ativo**: revisão humana obrigatória para scores em zona cinzenta (40–60) e casos sinalizados pelo FairnessGuard.
3. **Bias Audit mensal**: cliente deve manter frequência de auditoria conforme Seção 7.2.
4. **Não exclusividade**: o score WSI não pode ser o único critério de eliminação de candidatos — deve compor avaliação holística.
5. **Transparência**: candidatos devem ser informados da utilização de sistema de IA no início da sessão.

### 11.3 Assinaturas

| Papel | Nome | Data | Assinatura |
|-------|------|------|-----------|
| Data Protection Officer | _(a preencher)_ | 11/03/2026 | __________ |
| Chief Technology Officer | _(a preencher)_ | 11/03/2026 | __________ |
| Responsável pelo Sistema | _(a preencher)_ | 11/03/2026 | __________ |

> **Nota**: As assinaturas digitais devem ser coletadas via plataforma DocuSign referenciando este documento pelo número RIPD-LIA-WSI-2026-001.

---

*Documento gerado em conformidade com EU AI Act Art. 9, Annex III ponto 4 | LGPD Art. 20 | BCB 498.*
*WeDOTalent — Plataforma LIA | Sistema WSI v1.1 | RIPD-LIA-WSI-2026-001*
