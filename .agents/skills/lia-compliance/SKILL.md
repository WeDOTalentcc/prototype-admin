---
name: lia-compliance
description: "Compliance unificado da Plataforma LIA — Governanca WeDO (13 Crencas, 8 Inegociaveis, 18 Production Readiness), Screening/WSI (pipeline, calibracao, BARS), DEI/Fairness (FairnessGuard 3 camadas, Bias Audit, Four-Fifths Rule) e LGPD/Protecao de Dados (6 pilares, PII Masking, DSR, EU AI Act). Referencia: attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md"
---

# LIA Compliance — Governanca, Fairness, LGPD e Screening

Skill unificada de compliance. 4 secoes navegaveis por contexto.

> **Referencia canonica:** `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md`

## Quando ativar

- Ao criar feature, agente IA ou integracao externa nova (PARTE 1: Governanca — 13 Crencas, 8 Inegociaveis)
- Ao mexer em pipeline de screening, scoring WSI, calibracao ou BARS (PARTE 2)
- Ao criar/alterar logica de avaliacao, ranking ou filtragem de candidatos (PARTE 3: DEI/Fairness — Four-Fifths Rule, FairnessGuard 3 camadas)
- Ao manipular dados pessoais, consentimento, retencao, anonimizacao ou DSR (PARTE 4: LGPD — 6 pilares, PII Masking)
- Antes de deploy para producao (Production Readiness Gate, PARTE 1 secao 6 — 18 itens)
- Quando o usuario disser "passa pelas 13 crencas", "checa fairness", "audita LGPD", "valida WSI" ou "tem PII aqui?"
- Ao revisar prompt que toma decisao sobre candidato (anti-vies, calibracao BARS)
- Ao integrar provedor LLM novo (OpenAI, Anthropic, Gemini) — verificar retencao, residencia de dados, EU AI Act

## Quando NAO ativar

- Mudanca puramente visual sem dados de candidato -> `design-standardize`
- Bug isolado sem implicacao etica/legal/regulatoria -> `canonical-fix`
- Refactor mecanico de tipos sem mudanca de comportamento -> sem skill especifica
- Componente de UI interna que nao toca dados pessoais nem decisoes IA

---

## PARTE 1: Governanca WeDO Talent

### As 13 Crencas (Resumo)

| # | Crenca | Verificacao rapida |
|---|--------|-------------------|
| 01 | Humano em Primeiro Lugar | Existe caminho de escalacao humana? |
| 02 | Justa e Nao-Discriminatoria | FairnessGuard ativo? Atributos protegidos mascarados? |
| 03 | Transparente e Explicavel | "Por que fui rejeitado?" e respondivel? |
| 04 | Segura e Respeitosa com Privacidade | PII masking ativo? TLS 1.3+? |
| 05 | Construida por Humanos, Para Humanos | Feedback loop cliente -> produto existe? |
| 06 | Em Melhoria Continua | Metricas visiveis? Post-mortems em incidentes? |
| 07 | Resiliente por Design | Circuit Breaker? Multi-provider LLM? Rate limiting? |
| 08 | Observavel e Rastreavel | Structured logging? Monitoramento ativo? |
| 09 | Consciente de Custos | TokenTrackingService? Budget por empresa? |
| 10 | Inteligencia vs Determinismo | Decisao que rejeita tem guarda deterministico? |
| 11 | Anti-Bajulacao | IA nunca concorda silenciosamente com pedidos que comprometem qualidade |
| 12 | Autonomia Progressiva | Empresa nova comeca como assistente? |
| 13 | Acessivel e Inclusiva | WCAG 2.1 AA? aria-labels? Contraste 4.5:1? |

### 8 Inegociaveis

| # | Inegociavel |
|---|------------|
| 1 | Nenhum candidato rankeado sem WSI explicavel |
| 2 | Nenhuma rejeicao automatica sem review gate |
| 3 | FairnessGuard ativo em 100% das decisoes de screening/ranking |
| 4 | PII masking em todos os logs |
| 5 | Consent antes de qualquer processamento |
| 6 | Dados deletados quando solicitado (SLA 15 dias) |
| 7 | Human override sempre disponivel |
| 8 | WCAG 2.1 AA em todas as interfaces |

### Governanca de Agentes IA

**ConfidencePolicyService:**

| Acao | Confianca | Comportamento |
|------|-----------|---------------|
| APPLY_SILENT | >= 0.85 | Aplica sem notificar |
| APPLY_NOTIFY | 0.70-0.84 | Aplica e notifica recrutador |
| ASK_USER | < 0.70 | Sugere, pede confirmacao |

**LLM Fallback Chain:** Claude -> Gemini -> OpenAI -> Erro critico (503)

**Circuit Breaker (7 circuitos):** ANTHROPIC, OPENAI, GEMINI, PEARCH, WORKOS, MERGE, GOOGLE_CALENDAR. Cada integracao nova DEVE ter circuito registrado.

**Rate Limiting:**
- HTTP: 600/min/usuario, 3000/min/empresa
- Tokens: 60 chamadas LLM/min, $500/mes/empresa

### 5 Perguntas Antes de Implementar

1. **E justo?** Testamos para vies?
2. **E necessario?** Melhora fairness, seguranca ou experiencia?
3. **E transparente?** Conseguimos explicar para candidatos e reguladores?
4. **Conseguimos medir?** Temos metricas? Detectamos regressoes?
5. **E resiliente?** O que acontece quando dependencia falha?

### Production Readiness Gate (18 Criterios)

| # | Criterio | Categoria |
|---|----------|-----------|
| 1 | Circuit Breaker em servicos externos | Resiliencia |
| 2 | LLM fallback chain testada e2e | Resiliencia |
| 3 | PII Masking ativo em todos os logs | Seguranca |
| 4 | Rate Limiting por tenant | Seguranca |
| 5 | Dead Letter Queue ativa | Resiliencia |
| 6 | Token budget por company | Custos |
| 7 | Consent management ativo | Compliance |
| 8 | FairnessGuard em todas as interacoes | Fairness |
| 9 | Bias audit baseline estabelecido | Fairness |
| 10 | Health check endpoint | Operacoes |
| 11 | Error alerting (P0/P1) | Operacoes |
| 12 | Backup de dados verificado | Operacoes |
| 13 | Rollback procedure documentado | Operacoes |
| 14 | Load test (P95 < 5s) | Performance |
| 15 | Security scan limpo | Seguranca |
| 16 | LGPD checklist aprovado | Compliance |
| 17 | WCAG 2.1 AA verificado | Acessibilidade |
| 18 | PII Masking global em loggers | Seguranca |

---

## PARTE 2: Screening e WSI

### 4 Dimensoes WSI com Pesos Padrao

| Chave | Label | Peso |
|-------|-------|:----:|
| `technical` | Competencias Tecnicas | 50% |
| `behavioral` | Competencias Comportamentais | 20% |
| `gap_analysis` | Experiencia Profissional | 15% |
| `contextual` | Fit Cultural e Alinhamento | 15% |

Scoring: BARS (Behaviorally Anchored Rating Scale) com ancoras por nivel 1-5. Score global = media ponderada. Pesos configuraveis por empresa.

**Thresholds:** >= 7.0 Recomendado | 4.0-6.9 Em analise (revisao humana) | < 4.0 Nao recomendado (feedback construtivo)

### Calibracao por Senioridade (4 Etapas)

1. **Area de atuacao** — perfil base por area
2. **Fator geografico** — SP=1.00, RJ=0.97, outras capitais=0.92, interior=0.88
3. **Tech Age Factor** — very_new=1.30, new=1.15, established=1.00, legacy=0.85
4. **Validacao por sinal salarial** — discrepancia >30% = flag revisao humana

### Score Normalization

Ativado quando variancia entre versoes > 5%. Fator: 0.7 <= factor <= 1.3.
```
normalized_score = clamp(raw_score * factor, 0.0, 10.0)
```

### Pre-Qualification

4 niveis: Alinhado (>=70%), Parcial (50-69%), Distante (30-49%), Muito Distante (<30%).
NUNCA revelar porcentagem ao candidato. Candidato SEMPRE tem opcao de continuar.

### Feedback Personalizado

Tom warm, profissional, encorajador. NUNCA revelar score numerico. Sempre destacar pontos fortes. Sugerir areas concretas de desenvolvimento.

### Economia de Tokens

Budget default: $500/mes/empresa. Alertas em 80% e 100%. CascadedRouter: Memory cache > Fast router > LLM fallback.

---

## PARTE 3: DEI e Fairness

### FairnessGuard — 3 Camadas

**Camada 1 — Regex (40+ patterns):** BLOCK_AND_WARN
- Genero, raca/etnia, idade, religiao, orientacao sexual, estado civil, deficiencia, nacionalidade

**Camada 2 — Lexico implicito (15+ termos):** soft_warning
- "boa aparencia", "universidades de primeira linha", "jovem e dinamico", "boa familia", "native speaker"

**Camada 3 — LLM Semantico:** analise contextual profunda quando camadas 1 e 2 nao sao conclusivas

**Cobertura obrigatoria:**

| Ponto | Metodo |
|-------|--------|
| Endpoints REST | `guard.check()` no handler |
| Output avaliador WSI | `_fairness_guard.check()` antes de LiaOpinion |
| Parecer candidato | `guard.check()` em secoes 3, 4, 6 |
| Feedback rejeicao | `guard.check()` antes de status pending_approval |
| Campos texto livre (Pydantic) | `model_validator` com `check_implicit_bias()` |

### Dimensoes de Diversidade Testadas

Meta: variancia < 3% entre grupos.

| Dimensao | Grupos |
|----------|--------|
| Genero | M, F, NB, Prefiro nao responder |
| Idade | 25-35, 35-50, 50+ |
| Formacao | Universidade, Bootcamp, Autodidata |
| Regiao | SP/RJ, Outras capitais, Interior |
| Deficiencia | PCD, Sem deficiencia |

### Bias Audit Dashboard

Rota: `admin/compliance/auditoria/bias`

| Ratio | Status | Acao |
|-------|--------|------|
| >= 0.80 | OK | Monitorar |
| 0.60-0.79 | Investigar | Analise de causa raiz |
| < 0.60 | Acao imediata | Suspender e corrigir |

### Formacao Academica — Alto Risco de Vies

**O que PODE avaliar:** certificacoes legais (OAB, CREA), certificacoes tecnicas (AWS, PMP), proficiencia em idiomas.
**O que NAO avaliar:** prestigio da instituicao, tipo de educacao (presencial vs EAD vs bootcamp), grau academico sem requisito legal.
**Regra:** `bootcamp = diploma onde aplicavel`

### Criterios Afirmativos

PCD, Mulheres, Pessoas Negras, LGBTQIA+, 50+, Indigena, Trans.
MANTEM como preferencia positiva. NAO PENALIZA outros. NAO EXCLUI.

---

## PARTE 4: LGPD e Protecao de Dados

### 6 Pilares LGPD

| Pilar | O que garante |
|-------|---------------|
| Consentimento | Granular, versionado, prova SHA256, revogavel |
| Minimizacao | Apenas dados necessarios |
| PII Masking | PIIMaskingFilter global: CPF, email, telefone, nomes |
| Criptografia | Fernet (at-rest) + TLS 1.3 (in-transit) |
| Retencao | Exclusao automatizada por tipo |
| Auditoria | Trilha imutavel append-only |

### Retencao Automatizada

| Tipo de Dado | Retencao |
|--------------|----------|
| Candidatos rejeitados | 90 dias |
| Notas de entrevista / CVs | 180 dias |
| Logs de screening | 365 dias |
| Logs de IA | 365 dias |
| Contratados — contrato | 7 anos |
| Contratados — CV | 1 ano |

### Direitos do Titular (DSR) — LGPD Art. 18

7 direitos com SLA 15 dias uteis: confirmacao, acesso, correcao, anonimizacao, eliminacao, portabilidade, revogacao (imediata).

### EU AI Act

IA em recrutamento = **alto risco** (Art. 6 + Anexo III). FRIA obrigatorio antes do deploy.
ConfidencePolicyService implementa 3 niveis exigidos para sistemas de alto risco.

### Compliance Multi-Framework

| Framework | Cobertura |
|-----------|-----------|
| LGPD | Consentimento, PII masking, DSR, retencao, DPO |
| EU AI Act | FRIA, ConfidencePolicyService, human oversight |
| SOC-2 | Controles seguranca, audit logs |
| SOX | Trilha auditoria imutavel |
| ISO-27001 | Criptografia, gestao incidentes |
| BCB-498 | Controles instituicoes financeiras |

---

## Teste de Vies — 4 Niveis

1. **Pre-Deployment:** Golden Dataset, Four-Fifths Rule
2. **Post-Deployment:** A/B Testing, Shadow Scoring
3. **Continuo:** fairness_audit_logs, alertas automaticos
4. **Externo:** auditoria trimestral independente

## Red Teaming — 6 Cenarios

Prompt injection, data exfiltration, bias elicitation, jailbreak, escalacao privilegios, manipulacao de score.
Criterios: jailbreak < 1%, data leak = 0%, bypass mascaramento = 0%.

## Model Drift Detection

Triggers: score WSI varia > 0.5 em 30 dias, taxa aprovacao varia > 10%, custo > 20%, latencia P95 > 50%.

## RAGAS — Metricas de Qualidade LLM

| Metrica | Meta |
|---------|------|
| Faithfulness | >= 0.90 |
| Answer Relevance | >= 0.85 |
| Context Precision | >= 0.80 |
| Context Recall | >= 0.75 |
| Semantic Similarity | >= 0.80 |

## Checklist DEI para Novas Features

- [ ] Linguagem neutra
- [ ] Sem proxies discriminatorios
- [ ] FairnessGuard integrado
- [ ] Atributos protegidos mascarados
- [ ] Acessivel via teclado e screen reader
- [ ] Candidato informado sobre IA
- [ ] Opt-out disponivel
- [ ] Feedback personalizado
- [ ] Resultado explicavel
- [ ] Logs de auditoria
