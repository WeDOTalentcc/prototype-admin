# Playbook de Auditoria Profunda — Plataforma LIA (WeDO Talent)

## O QUE É ESTE DOCUMENTO

Este documento é um conjunto completo e AUTO-CONTIDO de instruções para executar uma auditoria profunda de código, prompts de IA, agentes, arquitetura, compliance, governança, DEI e proteção de dados da Plataforma LIA (WeDO Talent). Ele consolida critérios de 8 frameworks de análise e contém TODAS as regras, definições, thresholds, patterns e checklists necessários — nenhum arquivo externo é necessário para executar a auditoria.

**Origem:** Construído a partir de auditoria real executada sobre os 6 prompts/assistentes de IA da plataforma, aplicando: feature-audit (14 dimensões), feature-impact (12 dimensões), wedo-governance (13 Crenças + 8 Inegociáveis + 18 Production Readiness), code_review, screening-compliance, dei-fairness e lgpd-data-protection.

**Uso:** Cole este documento como instrução/prompt ao iniciar uma sessão de auditoria com qualquer agente IA (Claude Code, Replit Agent, Cursor, ChatGPT, etc.). O agente deve seguir cada seção na ordem e gerar o relatório no formato definido ao final.

---

## INSTRUÇÕES GERAIS PARA O AGENTE

Você é um auditor sênior de arquitetura de IA e produto. Sua missão é executar uma auditoria profunda e completa da Plataforma LIA, cobrindo TODAS as dimensões abaixo. Para cada dimensão, você deve:

1. **Investigar o código real** — não aceitar suposições; ler os arquivos, buscar patterns, verificar implementações
2. **Classificar cada item** como: OK, PARCIAL, FALHA, AUSENTE ou N/A
3. **Documentar evidências** — com caminhos de arquivo e linhas quando relevante
4. **Propor correções** priorizadas por impacto (P0 crítico → P3 futuro)
5. **Gerar relatório estruturado** no formato definido na seção final

**IMPORTANTE:** Este playbook contém TODAS as regras e critérios necessários. Você NÃO precisa de arquivos externos de skills ou guias. Todo o conteúdo necessário está aqui.

---

# PARTE I: FUNDAMENTOS — REGRAS DE GOVERNANÇA WEDO TALENT

Estes são os fundamentos normativos da plataforma. Toda auditoria deve verificar conformidade com estas regras. Estão aqui definidos na íntegra para que o auditor saiba exatamente o que verificar.

---

## 1. AS 13 CRENÇAS DO MANIFESTO WEDO TALENT

A plataforma é governada por 13 Crenças que devem ser respeitadas em toda feature, agente, prompt e integração:

### Crença 01 — Humano em Primeiro Lugar
- IA RECOMENDA, humanos DECIDEM
- Decisões de alto impacto (rejeitar candidato, enviar comunicação, mover etapa) NUNCA são automatizadas sem aprovação humana
- Deve existir caminho de escalação humana em toda interação com IA
- O recrutador SEMPRE pode reverter/sobrescrever qualquer decisão da IA

### Crença 02 — Justa e Não-Discriminatória
- Teste de viés obrigatório em todo pipeline que avalia candidatos
- Atributos protegidos (nome, gênero, idade, etnia, foto, orientação sexual, estado civil, deficiência, nacionalidade, religião) MASCARADOS antes de enviar ao LLM
- FairnessGuard ativo em 100% das decisões de screening/ranking (ver seção FairnessGuard abaixo)

### Crença 03 — Transparente e Explicável
- Candidato sabe que está sendo avaliado por IA
- Opt-out disponível
- "Por que fui rejeitado?" é SEMPRE respondível com raciocínio rastreável
- System prompts versionados para auditoria

### Crença 04 — Segura e Respeitosa com Privacidade
- Dados do candidato são confiança sagrada
- Coleta mínima (apenas dados necessários para a finalidade)
- LGPD inegociável (ver seção LGPD abaixo)
- PII masking ativo em todos os logs
- Secrets fora do código (vault/env vars)
- TLS 1.3+ para dados em trânsito

### Crença 05 — Construída por Humanos, Para Humanos
- Todo engenheiro entende o impacto de suas decisões sobre candidatos
- Auditorias trimestrais obrigatórias
- Red teaming contínuo
- Feedback loop cliente → produto deve existir

### Crença 06 — Em Melhoria Contínua
- Métricas visíveis e monitoradas
- Post-mortems em todo incidente
- Nenhuma dívida técnica que comprometa fairness ou segurança

### Crença 07 — Resiliente por Design
- Nenhum ponto único de falha
- Multi-provider LLM com fallback chain testada
- Circuit breakers obrigatórios em TODAS as integrações externas
- Rate limiting ativo

### Crença 08 — Observável e Rastreável
- Toda saída de agente logada em formato estruturado (nunca print)
- Trilha de auditoria persistente e imutável
- Monitoramento e alertas ativos

### Crença 09 — Consciente de Custos
- Budget de tokens por interação e por empresa
- Limites por tenant configurados
- Cascata de modelo mais barato para mais caro (resolver no nível mais barato possível)
- Pre-call budget check ANTES de cada invocação LLM (não apenas após)

### Crença 10 — Inteligência vs Determinismo
- IA usada onde agrega inteligência (análise, recomendação, conversação)
- Código determinístico onde precisa de garantia (rejeição, movimentação, compliance)
- Decisão que rejeita candidato deve ter guarda determinística (não apenas LLM)
- ConfidencePolicyService com 3 níveis: APPLY_SILENT (>= 0.85), APPLY_NOTIFY (0.70-0.84), ASK_USER (< 0.70)

### Crença 11 — Anti-Bajulação (Anti-Sycophancy)
- IA NUNCA concorda silenciosamente com pedidos que comprometam qualidade
- Deve contra-argumentar com dados e benchmarks quando o recrutador faz pedidos problemáticos
- 8 benchmarks setoriais de referência: ABRH, GPTW, Gupy, Robert Half, LinkedIn Economic Graph, Glassdoor, IBGE/PNAD, MTE/CAGED
- Divergências documentadas formalmente na trilha de auditoria
- **TODOS os prompts devem ter seções de anti-sycophancy e contra-argumentação. Sem exceção.**

### Crença 12 — Autonomia Progressiva
- Nível de automação configurável por empresa
- Empresa nova começa como assistente (nível mínimo de autonomia)
- Autonomia cresce com confiança demonstrada (baseada em volume de dados)
- Autonomia NUNCA concedida por padrão

### Crença 13 — Acessível e Inclusiva
- WCAG 2.1 AA obrigatório
- Acessibilidade é direito, não feature
- aria-labels em componentes interativos
- sr-only para textos de screen reader
- focus-visible com ring
- Contraste mínimo 4.5:1 (texto normal), 3:1 (texto grande)
- prefers-reduced-motion respeitado

---

## 2. OS 8 INEGOCIÁVEIS

Pré-condições para QUALQUER feature. Se qualquer um falha, a feature NÃO pode ser entregue. Sem exceções, sem "consertamos depois", sem bypass manual.

| # | Inegociável | Regra |
|---|------------|-------|
| 1 | Nenhum candidato rankeado sem WSI explicável | Score WSI deve ter raciocínio rastreável de input a output |
| 2 | Nenhuma rejeição automática sem review gate | Toda rejeição passa por humano ou gate de revisão configurado |
| 3 | FairnessGuard ativo em 100% das decisões de screening/ranking | Guard intercepta AUTOMATICAMENTE todas as decisões com log de intervenções |
| 4 | PII masking em todos os logs | PIIMaskingFilter no root logger; CPF, email, telefone, nomes mascarados |
| 5 | Consent antes de qualquer processamento | Nenhum candidato entra no pipeline sem consentimento registrado |
| 6 | Dados deletados quando solicitado (SLA 15 dias) | DSR funcional com fluxo de exclusão |
| 7 | Human override sempre disponível | Recrutador pode reverter/sobrescrever qualquer decisão da IA |
| 8 | WCAG 2.1 AA em todas as interfaces | Navegação por teclado, contraste, aria-labels, screen reader |

---

## 3. PRODUCTION READINESS GATE (18 Critérios)

Todo deploy para produção deve passar 18/18. Sem exceções.

| # | Critério | Categoria |
|---|----------|-----------|
| 1 | Circuit Breaker configurado em todos os serviços externos | Resiliência |
| 2 | LLM fallback chain testada end-to-end (Provider1 → Provider2 → Provider3 → Erro 503) | Resiliência |
| 3 | PII Masking ativo em todos os logs | Segurança |
| 4 | Rate Limiting configurado por tenant (HTTP + tokens) | Segurança |
| 5 | Dead Letter Queue ativa para mensagens falhadas | Resiliência |
| 6 | Token budget configurado por company | Custos |
| 7 | Consent management ativo para novos candidatos | Compliance |
| 8 | FairnessGuard ativo em todas as interações | Fairness |
| 9 | Bias audit baseline estabelecido | Fairness |
| 10 | Health check endpoint respondendo | Operações |
| 11 | Error alerting configurado (P0/P1) | Operações |
| 12 | Backup de dados verificado | Operações |
| 13 | Rollback procedure documentado | Operações |
| 14 | Load test executado (P95 < 5s) | Performance |
| 15 | Security scan limpo (0 critical/high) | Segurança |
| 16 | LGPD compliance checklist aprovado | Compliance |
| 17 | WCAG 2.1 AA compliance verificado | Acessibilidade |
| 18 | PII Masking global ativo em todos os loggers (root + por app) | Segurança |

---

## 4. REFERÊNCIA RÁPIDA DE DECISÃO

Antes de aprovar qualquer feature, responder 5 perguntas:

1. **É justo?** Testamos para viés? Discrimina mesmo inadvertidamente?
2. **É necessário?** Genuinamente melhora fairness, segurança ou experiência?
3. **É transparente?** Conseguimos explicar para candidatos e reguladores?
4. **Conseguimos medir?** Temos métricas? Detectamos regressões?
5. **É resiliente?** O que acontece quando uma dependência falha?

**Se todas = SIM: Construa. Se qualquer = NÃO: Reconsidere ou redesenhe.**

---

# PARTE II: FAIRNESSGUARD — PROTEÇÃO CONTRA DISCRIMINAÇÃO

O FairnessGuard é o componente central de proteção contra discriminação. Opera em 3 camadas e deve interceptar AUTOMATICAMENTE (como middleware) todas as decisões que afetam candidatos.

## Camada 1 — Regex Patterns (40+ patterns, 8 categorias)

Ação: **BLOCK_AND_WARN** — bloqueia a operação e notifica o recrutador com mensagem educativa.

| Categoria | Exemplos de patterns que devem ser detectados | Base legal |
|-----------|-----------------------------------------------|------------|
| **Gênero** | "apenas homens", "sexo masculino", "preferência por mulheres" | Art. 5º CLT, LGPD |
| **Raça/Etnia** | "apenas brancos", "raça branca", "excluir negros" | CF Art. 5º, Lei 7.716/89 |
| **Idade** | "jovens apenas", "idade máxima 35", "velho demais" | Estatuto do Idoso (Lei 10.741/03) |
| **Religião** | "apenas cristãos", "excluir muçulmanos" | CF Art. 5º, VI |
| **Orientação Sexual** | "apenas heterossexuais", "excluir gays" | ADO 26 (STF) |
| **Estado Civil** | "apenas solteiros", "excluir casados" | CLT |
| **Deficiência** | "excluir deficientes", "sem PCD", "excluir PCD" | Lei 8.213/91, Lei 13.146/15 |
| **Nacionalidade** | "apenas brasileiros", "excluir estrangeiros" | CF Art. 5º |

## Camada 2 — Léxico Implícito (15+ termos de viés sutil)

Ação: **soft_warning** — alerta educativo sem bloquear, sugere reformulação.

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

## Camada 3 — LLM Semântico

Análise contextual profunda para textos longos onde regex e léxico não capturam nuances. Custo: tokens + ~2s de latência. Acionado apenas quando Camadas 1 e 2 não são conclusivas.

## Escopo Obrigatório do FairnessGuard

O FairnessGuard NÃO cobre apenas endpoints de API. A cobertura obrigatória inclui:

| Ponto de verificação | O que verificar |
|---------------------|-----------------|
| Endpoints REST | Triagem, notas de entrevista, avaliações |
| Output do avaliador de candidatos | Antes de criar opinião/parecer |
| Parecer do candidato | Seções qualitativas do relatório |
| Feedback de rejeição | Antes de enviar ao candidato |
| Campos livres de schema | Todo campo `str` que aceita texto gerado por IA ou inserido por recrutador |
| **Input de TODOS os agentes** | FairnessGuard como middleware automático, não chamada manual |

**REGRA CRÍTICA:** FairnessGuard deve ser middleware automático (intercepta todas as interações). NÃO deve depender de cada agente chamar manualmente. Se cada agente precisa "lembrar" de chamar o guard, haverá falhas.

---

# PARTE III: DEI — DIVERSIDADE, EQUIDADE E INCLUSÃO

## Dimensões de Diversidade Testadas

Meta: variância < 3% entre grupos em TODAS as dimensões:

| Dimensão | Grupos testados |
|----------|----------------|
| **Gênero** | Masculino, Feminino, Não-binário, Prefiro não responder |
| **Idade** | 25-35, 35-50, 50+ |
| **Formação** | Universidade, Bootcamp, Autodidata ← **ALTO RISCO** |
| **Região** | SP/RJ, Outras capitais, Interior |
| **Deficiência** | PCD, Sem deficiência |
| **Proficiência linguística** | Nativo, Não-nativo |
| **Trajetória** | Formal, Bootcamp, Autodidata, Transição de carreira |

## Bias Audit Dashboard

Métricas calculadas por dimensão:

| Métrica | Fórmula | Meta |
|---------|---------|------|
| `selection_rate` | (aprovados do grupo / total do grupo) x 100 | Variância < 3% entre grupos |
| `adverse_impact_ratio` | selection_rate(minoritário) / selection_rate(referência) | >= 0.80 (Regra dos 4/5) |

Interpretação:
- Ratio >= 0.80 → OK, monitorar
- Ratio 0.60-0.79 → Investigar causa raiz
- Ratio < 0.60 → Ação imediata, suspender e corrigir

Compliance regulatório:
- **NYC Local Law 144**: Auditoria anual de viés em AEDT — plataforma deve fazer auditoria mensal interna + trimestral externa
- **EU AI Act**: Avaliação de conformidade + supervisão humana obrigatória
- **LGPD Art. 6º**: Não-discriminação + Art. 20 (revisão de decisões automatizadas)

## Formação Acadêmica — Dimensão de ALTO RISCO de Viés

A dimensão Formação é a de MAIOR RISCO de viés socioeconômico:

**O que NUNCA deve ser avaliado:**
- Prestígio da instituição ("USP > UNINOVE" não é competência, é privilégio de acesso)
- Tipo de educação (presencial vs. EAD vs. bootcamp)
- Grau acadêmico quando não há requisito legal

**O que PODE ser avaliado:**
- Certificações obrigatórias por lei (OAB, CREA, CRM, CFC)
- Certificações técnicas verificáveis (AWS, PMP, CPA, Azure)
- Proficiência em idiomas quando a vaga exige
- Competências demonstráveis, independente de onde foram adquiridas

**Regra de equivalência:** `bootcamp = diploma onde aplicável` — o que importa é a competência demonstrada.

**Sinais de alerta:** Termos como "universidades de primeira linha" em qualquer output do LLM são tratados como falha crítica (Camada 2 do FairnessGuard).

## Critérios Afirmativos

Patterns afirmativos detectados: PCD, Mulheres, Pessoas Negras, LGBTQIA+, 50+, Indígena, Pessoas Trans.

Regras:
- **MANTÉM** como preferência positiva — aumenta visibilidade do grupo
- **NÃO PENALIZA** candidatos fora do grupo
- **NÃO EXCLUI** — critérios afirmativos são inclusivos, nunca excludentes

## Checklist DEI para Novas Features

- [ ] Linguagem neutra (sem vieses implícitos)
- [ ] Sem proxies discriminatórios
- [ ] FairnessGuard integrado
- [ ] Atributos protegidos mascarados antes do LLM
- [ ] Acessível via teclado e screen reader
- [ ] Candidato informado sobre IA
- [ ] Opt-out disponível
- [ ] Feedback personalizado (sem score numérico)
- [ ] Resultado explicável
- [ ] Logs de auditoria

---

# PARTE IV: LGPD, EU AI ACT E PROTEÇÃO DE DADOS

## Os 6 Pilares LGPD

| Pilar | O que garante | Como verificar |
|-------|---------------|---------------|
| **Consentimento** | Granular, versionado, com prova SHA256, revogável a qualquer momento | 7 tipos: personal_data, sensitive_data, data_sharing, marketing, cookies, analytics, third_party. Hash SHA256 em cada evento. HTTP 451 quando consent obrigatório ausente. |
| **Minimização** | Apenas dados necessários para a finalidade declarada | Verificar se campos coletados são justificados |
| **PII Masking** | PIIMaskingFilter global em todos os loggers antes de persistir | Máscara: CPF (***CPF***), email (***EMAIL***), telefone (***PHONE***), nomes (***NAME***). NUNCA logar dados pessoais em texto claro. NUNCA incluir PII em mensagens de erro. |
| **Criptografia** | Fernet (at-rest) + TLS 1.3 (in-transit) | Verificar se dados sensíveis são criptografados em repouso e em trânsito |
| **Retenção** | Exclusão automatizada por tipo de dado | Ver tabela de retenção abaixo |
| **Auditoria** | Trilha de auditoria imutável append-only | Todo tratamento de dado pessoal logado |

## Tabela de Retenção

| Tipo de Dado | Retenção | Critério |
|--------------|----------|---------|
| Candidatos rejeitados/desistentes | 90 dias | scheduled_deletion_at |
| Notas de entrevista / CVs | 180 dias | Data de upload/criação |
| Logs de screening | 365 dias | Data de execução |
| Logs de IA (consumo) | 365 dias | scheduled_deletion_at |
| Candidatos contratados — contrato/onboarding | 7 anos | Exigência legal trabalhista |
| Candidatos contratados — CV | 1 ano | Referência interna |

## DSR — Direitos do Titular (LGPD Art. 18)

7 direitos que devem ser suportados com SLA de 15 dias úteis:

| # | Direito | SLA |
|---|---------|-----|
| 1 | Confirmação de Existência | 15 dias úteis |
| 2 | Acesso aos Dados | 15 dias úteis |
| 3 | Correção de Dados | 15 dias úteis |
| 4 | Anonimização ou Bloqueio | 15 dias úteis |
| 5 | Eliminação de Dados | 15 dias úteis |
| 6 | Portabilidade (export) | 15 dias úteis |
| 7 | Revogação de Consentimento | Imediato |

## EU AI Act — Sistema de Alto Risco

IA em recrutamento = sistema de **alto risco** (Art. 6 + Anexo III). Requisitos:

- **FRIA (Fundamental Rights Impact Assessment)** obrigatório antes do deploy
- **ConfidencePolicyService** com 3 níveis: APPLY_SILENT (>= 0.85), APPLY_NOTIFY (0.70-0.84), ASK_USER (< 0.70)
- **Human oversight** garantido
- **Decisões explicáveis** (rationale obrigatório em toda avaliação)
- Não é permitido decidir sobre candidatos sem supervisão humana

## Compliance Multi-Framework

| Framework | Cobertura |
|-----------|-----------|
| **LGPD** | Consentimento granular, PII masking, DSR, retenção, DPO |
| **EU AI Act** | FRIA, ConfidencePolicy, human oversight, auditabilidade |
| **SOC-2** | Controles de segurança, audit logs, acesso restrito |
| **SOX** | Trilha de auditoria imutável, segregação de funções |
| **ISO-27001** | Criptografia, gestão de incidentes, continuidade |
| **BCB-498** | Controles para instituições financeiras reguladas |

---

# PARTE V: SCREENING COMPLIANCE

## Pipeline WSI (Weighted Scoring Index)

### 4 Dimensões Canônicas

| Chave | Label | Peso padrão |
|-------|-------|:-----------:|
| `technical` | Competências Técnicas | 50% |
| `behavioral` | Competências Comportamentais | 20% |
| `gap_analysis` | Experiência Profissional | 15% |
| `contextual` | Fit Cultural e Alinhamento | 15% |

### BARS — Behaviorally Anchored Rating Scale

Cada dimensão WSI deve ter âncoras comportamentais explícitas por nível, eliminando subjetividade:

| Nível | Score | O que significa |
|-------|-------|----------------|
| 5 — Expert | 9.0-10.0 | Contribuições de referência, mentoria, solução de problemas complexos |
| 4 — Proficiente | 7.0-8.9 | Código/trabalho idiomático, resolve problemas de performance |
| 3 — Competente | 5.0-6.9 | Desenvolve features standalone, entende fundamentos |
| 2 — Iniciante Avançado | 3.0-4.9 | Executa tarefas com supervisão |
| 1 — Novato | 1.0-2.9 | Conhecimento teórico sem aplicação prática |

**Regra:** Score NUNCA é gerado sem `rationale` (justificativa textual). O LLM compara a resposta do candidato contra as âncoras e justifica o nível atribuído.

### Thresholds de Decisão

- >= 7.0: Recomendado
- 4.0-6.9: Em análise (revisão humana obrigatória)
- < 4.0: Não recomendado (feedback construtivo obrigatório)

### Formação Acadêmica como Pré-qualificador

Formação acadêmica é **pass/fail** (não entra no score WSI):
- Somente certificações com requisito legal obrigatório (OAB, CREA, CRM) justificam eliminação
- NUNCA usar para discriminar por instituição ou tipo de formação

### Score Normalization

Normaliza scores WSI entre versões de perguntas:
- Gatilho: variância entre versões > 5%
- Fator: 0.7 <= factor <= 1.3 (clampado)
- Fórmula: `normalized_score = clamp(raw_score x normalization_factor, 0.0, 10.0)`

### Calibração por Senioridade

4 etapas: Área de Atuação → Fator Geográfico → Tech Age Factor → Validação por Sinal Salarial.

Mapeamento Dreyfus x Bloom:
| Seniority | Dreyfus | Bloom | Score WSI mínimo |
|-----------|---------|-------|:----------------:|
| Estágio / Junior | Novato | Lembrar/Entender | 3.0-5.0 |
| Pleno | Competente | Aplicar/Analisar | 5.0-7.0 |
| Sênior | Proficiente | Avaliar | 7.0-8.5 |
| Staff / Principal | Especialista | Criar | 8.5+ |

## Feedback ao Candidato

- Tom warm, profissional e encorajador
- NUNCA revelar score numérico
- SEMPRE destacar pontos fortes
- Sugerir áreas de desenvolvimento concretas

## Framework de Teste de Viés (4 Níveis)

| Nível | Quando | O que faz |
|-------|--------|-----------|
| 1 — Pre-Deployment | Antes do deploy | Golden Dataset (100 candidatos, 25 por quartil) + Four-Fifths Rule |
| 2 — Post-Deployment | Após deploy | A/B Testing + Shadow Scoring |
| 3 — Contínuo | Em produção | fairness_audit_logs + alertas automáticos |
| 4 — Externo | Trimestral | Auditoria independente |

## Red Teaming (6 Cenários Obrigatórios)

| Cenário | Critério de Aprovação |
|---------|----------------------|
| Prompt injection | Não executa comandos injetados |
| Data exfiltration | Vazamento de dados = 0% |
| Bias elicitation | Não produz output discriminatório |
| Jailbreak | Taxa < 1% |
| Escalação de privilégios | Não acessa dados de outro tenant |
| Manipulação de score | Score não é alterável por input malicioso |

## Model Drift Detection

Triggers de alerta:
- Score WSI varia > 0.5 em 30 dias
- Taxa de aprovação varia > 10%
- Custo de IA aumenta > 20%
- Latência P95 aumenta > 50%

## RAGAS Evaluation Framework

| Métrica | O que mede | Meta |
|---------|-----------|:----:|
| Faithfulness | Respostas factuais sem alucinação | >= 0.90 |
| Answer Relevance | Resposta pertinente à pergunta | >= 0.85 |
| Context Precision | Contexto recuperado é relevante | >= 0.80 |
| Context Recall | Toda informação necessária recuperada | >= 0.75 |
| Answer Semantic Similarity | Similaridade com resposta de referência | >= 0.80 |

Golden Set: 100 candidatos representativos (25 por quartil) incluindo diferentes trajetórias (universitária, bootcamp, autodidata). Variância de aprovação entre trajetórias > 3% bloqueia deploy.

## Taxonomia de Incidentes de IA

| Categoria | Prioridade | Exemplo |
|-----------|:----------:|---------|
| Viés Discriminatório | P0 | FairnessGuard falhou em detectar discriminação |
| Vazamento de Dados | P0 | PII apareceu em log ou output |
| Alucinação com Impacto | P1 | IA inventou qualificação de candidato |
| Falha de Mascaramento | P1 | Atributo protegido passou para LLM |
| Drift de Qualidade | P2 | Scores mudaram sem motivo aparente |
| Custo Anômalo | P3 | Budget estourado sem explicação |

---

# PARTE VI: ARQUITETURA TÉCNICA — O QUE AUDITAR

## Governança de Agentes IA

### Circuit Breaker (3 Estados)

Estados: CLOSED (normal) → N falhas → OPEN (rejeitando) → recovery_timeout → HALF_OPEN (testando) → sucesso → CLOSED / falha → OPEN

Cada integração externa DEVE ter circuit breaker. Verificar se cada circuito tem: `failure_threshold`, `recovery_timeout`, `timeout_request`, `fallback` definidos.

### LLM Fallback Chain

1. Provider Primário → 2. Primeiro Fallback → 3. Segundo Fallback → 4. Erro crítico (log P0 + alerta + HTTP 503)

Verificar se a fallback chain é testada end-to-end e se existe alerta quando todos os providers falham.

### Caching Semântico (3 Camadas)

| Camada | Tipo | Latência |
|--------|------|----------|
| Session | In-memory, hash O(1) | Sub-ms |
| Redis | Distribuído, compartilhado | ~1ms |
| PostgreSQL | Persistente longo prazo | ~10ms |

Verificar se TTLs estão configurados por domínio e se existe cache busting quando dados mudam.

### Dead Letter Queue

- Retry com backoff exponencial: delay = 60s x (2^retry_count)
- Max 3 tentativas antes de DLQ
- Alerta ops quando mensagem vai para DLQ
- Max delay: 3600s (cap de segurança)

### Rate Limiting (2 Níveis)

**Nível 1 — HTTP:**
- 600 req/min/usuário, 20.000 req/hora/usuário
- 3.000 req/min/empresa, 60.000 req/hora/empresa

**Nível 2 — Tokens:**
- 60 chamadas LLM/min/usuário
- 100.000 tokens/hora/usuário, 500.000 tokens/dia/usuário
- 5.000.000 tokens/dia/empresa, $500/mês/empresa
- Alertas: 80% budget → alerta suave | 100% → bloqueio

### Token Tracking e Budget

Cada chamada LLM deve registrar: user_id, company_id, agent_type, intent, input_tokens, output_tokens, model, latency_ms.

Budget por empresa com check_limits() ANTES de cada chamada (não apenas após).

### CascadedRouter (Economia de Cascata)

Resolver intenções na camada mais barata possível:
1. Memory cache (O(1)) — busca em memória/cache
2. Fast router (regex/keyword) — patterns conhecidos (< 5ms)
3. LLM Router — apenas quando fast falha, com fallback

Manter estatísticas: memory_hits, fast_hits, llm_hits, total.

### Multi-Tenant Isolation

- `company_id` em TODAS as queries
- Cross-tenant prevention com erro explícito
- Scope-based tool access por contexto
- Isolamento em tool calls

### HITL — Human-In-The-Loop

Ações que DEVEM requerer aprovação humana:
- Rejeitar candidato
- Mover candidato entre etapas
- Enviar email/WhatsApp ao candidato
- Operações em batch (bulk move, bulk email)
- Disparar triagem (WSI)
- Qualquer ação irreversível

Para cada prompt: a lista de ações HITL deve ser EXPLÍCITA (não depender de fallback genérico).

### Framework de Aprendizado Contínuo

4 tipos de memória de longo prazo:
| Tipo | Descrição |
|------|-----------|
| `pattern` | Padrões recorrentes ("Empresa X sempre contrata CLT, nunca PJ") |
| `preference` | Preferências do recrutador ("Prefere listar 5 candidatos, não 10") |
| `learning` | Aprendizados de correções ("Faixa salarial Dev Senior SP: R$18-22k") |
| `outcome` | Resultados de contratações ("Vagas Python preenchem em 35 dias") |

Verificar: FeedbackLearningService, OutcomeTracker, RecruiterPreferencesLearning, CompanySkillPromotion, LearningExtractor.

---

# PARTE VII: PROCEDIMENTO DE AUDITORIA

## FASE 1: MAPEAMENTO DA ARQUITETURA

Antes de auditar, mapeie a arquitetura completa:

### 1.1 Identificação dos Prompts/Assistentes

Localize TODOS os prompts/assistentes de IA do sistema. Para cada um, documente:
- Nome e contexto
- Arquivo do system prompt (path completo)
- Scope
- Frontend que o consome
- API routes

### 1.2 Stack Completo por Prompt

Para CADA prompt, monte uma tabela com:

| Camada | Componente | Arquivo |
|:---|:---|:---|
| Agente (classe) | Nome | Path |
| Domínio | Nome | Path |
| System Prompt | Constante | Path |
| Reasoning Prompt | (se houver) | Path |
| Tool Registry | Registry | Path |
| Tool Implementations | Tools | Path |
| Serviços vinculados | Serviços | Path |
| Compliance integrado | Guards | Path |
| Frontend — Página | Componente | Path |
| Frontend — Hooks | Hooks | Path |
| Frontend — Chat/Panel | Chat | Path |
| API Proxy | Rota | Backend |

### 1.3 Componentes Compartilhados

Documente os componentes centrais que TODOS os prompts utilizam:
- Orquestração (Orchestrator, Router, TaskPlanner, PolicyEngine, StateManager, DomainRegistry)
- Provedores LLM (Factory, providers, fallback chain)
- Serviços Compartilhados (ConversationMemory, ResponseCache, SemanticCache, FairnessGuard, AuditService, FactChecker, GuardrailRepository, ToolRegistry, ScopeConfig)
- Frontend Compartilhado (FloatProvider, ChatButton, streaming hooks, navigation hooks, HITL components)

### 1.4 Mapa de Tools por Scope

Para cada scope, liste:
- Tools de query (somente leitura)
- Tools de action (modificam dados)
- Quais estão IMPLEMENTADOS vs DECLARADOS (stubs)
- Quais têm HITL/guardrail enforcement

---

## FASE 2: AUDITORIA POR PROMPT (14 Dimensões)

Para CADA prompt/assistente, aplique as 14 dimensões:

### DIMENSÃO 1: Integração (Wiring)

- [ ] Todo hook criado está sendo importado e chamado por pelo menos um componente?
- [ ] Todo endpoint backend tem proxy frontend E hook que o chama?
- [ ] Todo componente que recebe props está recebendo dados REAIS?
- [ ] Todo modal criado tem trigger acessível ao usuário?
- [ ] Todo evento do usuário (click, drag, submit) produz efeito visível?

### DIMENSÃO 2: Fluxo de Dados

- [ ] Dados fluem do banco → backend → proxy → hook → componente → UI?
- [ ] Componente usa dados reais (da API) ou estado local/mock?
- [ ] Após ação do usuário, os dados na tela atualizam sem recarregar?
- [ ] Dado é persistido no banco ou só no estado local?
- [ ] Existe estado de loading e fallback de erro?

### DIMENSÃO 3: UI/UX + Design System

- [ ] Regra 90/10 monocromática: 90% grayscale, 10% acento (cores de acento apenas em badges, status, brain icon)
- [ ] Botão primário: bg escuro (preto), NUNCA colorido
- [ ] Tipografia: família principal para UI geral + família complementar para dados/tabelas
- [ ] Espaçamento base 4px
- [ ] Sombras: subtle para cards, média para elevados, forte apenas para modais/dropdowns (nunca dramáticas)
- [ ] Bordas: arredondadas moderadas (6px inputs, 8px cards, 12px modais)
- [ ] Motion: fade/slide/scale sutil (nunca bounce/elastic)
- [ ] Brain Icon IA: cor cyan, com estados (idle, thinking, success, error)
- [ ] Acessibilidade WCAG 2.1 AA: aria-labels, contraste 4.5:1, focus ring, sr-only
- [ ] Funciona em todas as visões do produto (ex: Kanban E Tabela se aplicável)

### DIMENSÃO 4: Backend e API

- [ ] Endpoint existe e responde com formato correto?
- [ ] Modelo de dados (tabela/coluna) existe no banco?
- [ ] Validação com schemas tipados?
- [ ] Proxy frontend configurado e headers propagados?
- [ ] Resposta inclui TODOS os campos que o frontend precisa?

### DIMENSÃO 5: Tipos e Contratos

- [ ] Interfaces/Types atualizados entre frontend e backend?
- [ ] Props obrigatórias passadas em todos os lugares?
- [ ] Enums/constantes alinhados entre frontend e backend?
- [ ] Sem coerção de tipo desnecessária (`as any`)?
- [ ] Verificação de tipos limpa (0 erros)?

### DIMENSÃO 6: Fluxo do Usuário

Para cada funcionalidade, simule:
1. Ponto de entrada — como o usuário inicia?
2. Caminho feliz — o que acontece se tudo der certo?
3. Resultado visível — o que o usuário VÊ?
4. Caminhos alternativos — cancelar, campo vazio, perda de conexão?
5. Estado pós-ação — dado persiste ao recarregar?

### DIMENSÃO 7: Consistência

- [ ] Segue mesmo padrão de componentes similares existentes?
- [ ] Sem duplicação de lógica?
- [ ] Imports consistentes?
- [ ] Nomenclatura padrão (hooks: kebab-case, componentes: PascalCase, backend: snake_case)?

### DIMENSÃO 8: Documentação

- [ ] Docs de arquitetura atualizados?
- [ ] Lógica complexa tem comentários de decisão (não óbvios)?
- [ ] TODO/FIXME rastreados com contexto?

### DIMENSÃO 9: Arquitetura de Agentes

- [ ] Domínio herda de base abstrata com métodos obrigatórios?
- [ ] Workflow segue pipeline padrão (classify → route → prepare → execute → validate → format → respond)?
- [ ] Router em cascata funciona (cache → fast → LLM)?
- [ ] Registry com auto-discovery e metadata completa?
- [ ] Tools com schema tipado e tenant scoping?
- [ ] Memória de conversa persistida com summarization?

### DIMENSÃO 10: Qualidade LLM

**10.1 Anti-Sycophancy:**
- [ ] Tem seção de prevenção de sycophancy no system prompt?
- [ ] Tem seção de contra-argumentação?
- [ ] Referencia benchmarks setoriais?
- [ ] Documenta divergências na trilha de auditoria?
- [ ] NUNCA concorda silenciosamente com pedidos problemáticos?

**REGRA: TODOS os prompts devem ter anti-sycophancy. Sem exceção.**

**10.2 Detecção de Intent:**
- [ ] Implementa negation detection? ("não quero ranking" ≠ "ranking")
- [ ] Confiança é REAL? (não usa fórmula artificial tipo `max(0.6, min(X*3, 0.95))`)
- [ ] Fallback para LLM quando confiança baixa?
- [ ] Intents mutuamente exclusivos?

**REGRA: negation detection deve existir em TODOS os prompts que usam keywords.**

**10.3 Structured Output:**
- [ ] Output do LLM parseado com modelo tipado (não regex manual)?
- [ ] Fallback para texto puro se parsing falhar?

**10.4 ConfidencePolicy:**
- [ ] APPLY_SILENT >= 0.85?
- [ ] APPLY_NOTIFY 0.70-0.84?
- [ ] ASK_USER < 0.70?

### DIMENSÃO 11: Serviços e Integrações IA

- [ ] WSI scoring com raciocínio rastreável?
- [ ] Feedback personalizado sem revelar score numérico?
- [ ] Score normalization ativa quando variância > 5%?
- [ ] Calibração por senioridade?
- [ ] RAGAS evaluation configurado?

### DIMENSÃO 12: Governança e Resiliência IA

**12.1 FairnessGuard:**
- [ ] Ativo em 100% das decisões de screening/ranking?
- [ ] Como middleware automático (não chamada manual por agente)?
- [ ] 3 camadas funcionando: Regex → Léxico → LLM?
- [ ] Audit log de intervenções?

**12.2 HITL:**
- [ ] Toda ação destrutiva requer aprovação humana?
- [ ] Lista de ações HITL EXPLÍCITA em cada tool registry?
- [ ] Recrutador pode reverter qualquer decisão da IA?

**12.3 Circuit Breaker:**
- [ ] Em todas as integrações externas?
- [ ] 3 estados: CLOSED → OPEN → HALF_OPEN?
- [ ] Fallback chain testada?
- [ ] Circuit breaker direto nas chamadas LLM dos agentes?

**12.4 Token Budget:**
- [ ] Token tracking ativo?
- [ ] Pre-call budget check ANTES de cada invocação LLM?
- [ ] Budget por empresa?
- [ ] Alertas em 80% e 100%?

### DIMENSÃO 13: Segurança e Proteção de Dados

**13.1 PII Masking:**
- [ ] PIIMaskingFilter global instalado no startup?
- [ ] Máscara CPF, email, telefone, nomes?
- [ ] strip_pii antes de enviar ao LLM?
- [ ] Secrets fora do código?

**13.2 Consent Management:**
- [ ] Consent check antes de processar dados?
- [ ] Hard block quando consent revogado?
- [ ] 7 tipos de consentimento granular com prova SHA256?

**13.3 DSR (Data Subject Request):**
- [ ] 7 direitos suportados?
- [ ] SLA 15 dias automático?
- [ ] Verificação de identidade antes de fulfillment?

**13.4 Multi-Tenant:**
- [ ] company_id em TODAS as queries?
- [ ] Cross-tenant prevention?

**13.5 LGPD:**
- [ ] 6 pilares cobertos?
- [ ] Retenção automatizada por tipo?
- [ ] Criptografia at-rest + in-transit?

**13.6 EU AI Act:**
- [ ] Sistema classificado como alto risco?
- [ ] ConfidencePolicy com 3 níveis?
- [ ] Human oversight garantido?
- [ ] Decisões explicáveis?

### DIMENSÃO 14: Performance e Escalabilidade

- [ ] Tarefas longas em fila assíncrona (não bloqueiam request)?
- [ ] Cache patterns definidos?
- [ ] Migrations rodam sem downtime?
- [ ] Health check endpoints respondendo?
- [ ] Load test executado (P95 < 5s)?

---

## FASE 3: ANÁLISE COMPARATIVA DE CAPACIDADES

### 3.1 Mapa de Capacidades

Monte tabela com TODOS os prompts nas colunas e capacidades nas linhas. Marque: SIM, NÃO, PARCIAL, DECLARADO MAS NÃO USADO, N/A.

**Capacidades a mapear:**

**ANÁLISE:** Ranking/scoring, Comparação lado-a-lado, Análise de perfil, KPIs/métricas, Skills gap, Diversidade, Market insights, Gargalos, SLA, Performance

**PREDITIVO:** Predict dropout risk, Pipeline forecast, ML predictions, Conversion patterns, Smart alerts, At-risk candidates

**AÇÕES:** Mover candidato, Batch move, Rejeitar, Shortlist, Email/WhatsApp, Triagem, Entrevista, Criar/editar vaga, Salvar política/draft

**PROATIVO:** Daily briefing, Pending actions, Sugestões proativas, Alertas SLA

**RELATÓRIOS:** Gerar relatório, Exportar dados

**CHAT/CONVERSA:** Histórico de conversas, Novo chat / Limpar chat, Memória entre turnos, Anti-sycophancy, Negation detection

### 3.2 Identificar Padrões a Padronizar

**NÍVEL 1 — PADRÃO PARA TODOS OS PROMPTS (sem exceção):**
- Anti-sycophancy (contra-argumentar com dados)
- FairnessGuard no input (middleware automático)
- Negation detection (onde usa keywords)
- Confiança real (sem fórmula artificial)

**NÍVEL 2 — PADRÃO PARA PROMPTS OPERACIONAIS (exceto configuracionais):**
- Gerar relatórios do seu domínio
- Histórico de conversas (listar, retomar, criar novo, limpar)
- Capacidade preditiva (dropout risk, forecast, alerts)
- Identificar problemas e listar pendências
- Sugestões proativas
- Funcionar como assistente completo ("o que preciso fazer?", "me dê um resumo", "o que está em risco?")

**NÍVEL 3 — ESPECÍFICO POR TIPO:**
- Prompts configuracionais (ex: Policy): relatório de status sim, histórico de chat não faz sentido
- Prompts de criação (ex: Wizard): histórico por entidade, não por chat genérico

### 3.3 Tools Declarados vs Usados

Para cada prompt:
- Tools no scope mas NÃO usados ativamente
- Tools referenciados no prompt mas NÃO existem ou são stubs
- Oportunidades de ativação

---

## FASE 4: ANÁLISE DE IMPACTO SISTÊMICO (12 Dimensões)

Para features novas ou ajustes identificados, mapear impacto em:

| # | Dimensão | O que verificar |
|---|----------|----------------|
| 1 | Frontend | Páginas, componentes, hooks, rotas proxy, estados loading/error |
| 2 | Backend API | Endpoints, schemas, rate limiting, auth multi-tenant |
| 3 | Backend Services | Serviços, lógica de negócio, fallbacks |
| 4 | Banco de Dados | Tabelas, campos, migrations, índices, multi-tenant |
| 5 | Camada IA / Agentes | Agentes, tools, prompts, state machine, memória |
| 6 | Comunicações | Templates email/WhatsApp/Teams, preferências |
| 7 | Integrações Externas | Auth, Calendar, Search, Transcription, ATS, CRM, Billing |
| 8 | Compliance/LGPD | PII, consentimento, auditoria, SOC-2, ISO-27001 |
| 9 | Segurança/Multi-Tenant | company_id isolation, roles/scopes, vulnerabilidades |
| 10 | Infraestrutura/Async | Filas, cache, migrations sem downtime |
| 11 | Observabilidade | Logs estruturados, métricas, traces, alertas |
| 12 | Testes/Qualidade | Unitários, integração, edge cases, rollback plan |

---

# PARTE VIII: FORMATO DO RELATÓRIO — GUIA COMPLETO DE GERAÇÃO

> **Este é o guia definitivo para gerar o relatório de auditoria profunda.** Cada seção do relatório final está conectada aos procedimentos específicos do playbook (DP, CI, RM) que o auditor deve executar para preencher cada parte. O relatório final terá 8 seções obrigatórias + 2 anexos.

---

## VISÃO GERAL: ESTRUTURA DO RELATÓRIO FINAL

O relatório final DEVE conter estas seções na seguinte ordem:

| # | Seção do Relatório | Procedimentos Fonte | Resultado Esperado |
|---|-------------------|--------------------|--------------------|
| 0 | Resumo Executivo | Todas as seções | 1-2 páginas com achados críticos |
| 1 | Mapeamento da Arquitetura | DP-01, DP-02, DP-03 | Inventário + stack + tools |
| 2 | Análise Detalhada por Prompt | DP-04, DP-05, DP-06, DP-07 | 1 bloco por prompt |
| 3 | Auditoria Multi-Dimensional | DP-09.1 a DP-09.11 | Matrizes transversais |
| 4 | Análise Comparativa de Capacidades | DP-08, DP-10, DP-11, DP-12 | Mapa + padronização |
| 5 | Análise de Funcionalidades Transversais | DP-13, DP-14 | Histórico, relatórios |
| 6 | Prioridades de Correção | DP-15, DP-16 | Achados P0-P3 + arquivos |
| 7 | Resumo Executivo de Esforço | DP-15, DP-16 | Tabela para sprint planning |
| A | Anexo: Arquivos-Chave | DP-16 | Índice completo de arquivos |
| B | Anexo: Referência Cruzada Runbooks | DP-20, RM-01..RM-44 | Mapa problema → solução |

---

## SEÇÃO 0: RESUMO EXECUTIVO

**Procedimentos fonte:** Consolidação de todas as seções.

**Quando escrever:** APÓS completar todas as outras seções (é a última a ser escrita, primeira a ser lida).

**Template obrigatório:**

```markdown
# RELATÓRIO DE AUDITORIA PROFUNDA — PLATAFORMA LIA
**Data:** [DD/MM/AAAA]
**Auditor(es):** [nomes]
**Versão do código:** [commit hash ou tag]
**Escopo:** [N] prompts/assistentes, [M] agentes, [K] domínios

## Resumo Executivo

### Números-Chave
- **Prompts auditados:** [N]
- **Achados totais:** [X] (P0: [a], P1: [b], P2: [c], P3: [d])
- **Dimensões avaliadas:** 14
- **Tools verificados:** [T] (implementados: [I], stubs: [S], ausentes: [A])

### Status Geral por Prompt
| Prompt | Achados P0 | Achados P1 | Status Geral |
|--------|-----------|-----------|-------------|
| P1 [Nome] | [n] | [n] | SAUDÁVEL / EM RISCO / CRÍTICO |
| P2 [Nome] | [n] | [n] | |
| ... | | | |

### Top 5 Achados Críticos
1. **[ACH-XXX]** — [Título] — Impacto: [descrição em 1 linha]
2. ...

### Recomendação Principal
[1-2 parágrafos com a recomendação mais importante para o CTO/Head de Engenharia]
```

---

## SEÇÃO 1: MAPEAMENTO DA ARQUITETURA

**Procedimentos fonte:** DP-01 (Inventário), DP-02 (Stack), DP-03 (Tools)

**Passos para o auditor:**

1. Executar **DP-01** → Produz a tabela de inventário de prompts
2. Executar **DP-02** para cada prompt → Produz N tabelas de stack (14 camadas)
3. Executar **DP-03** para cada scope → Produz N tabelas de tools (query/action)

### 1.1 Componentes Compartilhados da Arquitetura

Antes dos stacks individuais, listar os componentes que são compartilhados por TODOS os prompts:

```markdown
### Componentes Compartilhados

| Componente | Classe/Módulo | Arquivo | Usado por |
|-----------|--------------|---------|-----------|
| Orquestrador | Orchestrator | lia-agent-system/app/orchestrator/orchestrator.py | Todos (via Float) |
| Router | CascadedRouter | lia-agent-system/app/orchestrator/cascaded_router.py | Float |
| Intent Classifier | IntentRouter | lia-agent-system/app/orchestrator/intent_router.py | Float |
| FairnessGuard | FairnessGuard | lia-agent-system/app/shared/compliance/fairness_guard.py | Policy, Wizard (parcial) |
| PII Masking | PIIMaskingFilter | lia-agent-system/app/shared/pii_masking.py | Todos |
| Audit Callback | AuditCallback | lia-agent-system/libs/audit/lia_audit/audit_callback.py | Todos |
| ReAct Loop | ReActLoop | lia-agent-system/libs/agents-core/lia_agents_core/react_loop.py | Todos os ReAct agents |
| Enhanced Mixin | EnhancedAgentMixin | lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py | Todos os agents |
| Token Tracking | TokenTrackingService | lia-agent-system/app/services/token_tracking_service.py | Todos |
| Conversation Memory | ConversationMemory | lia-agent-system/app/services/conversation_memory.py | Float, Kanban |
| LLM Factory | LLMFactory | lia-agent-system/app/shared/providers/llm_factory.py | Todos |
| Circuit Breaker | CircuitBreaker | lia-agent-system/app/shared/resilience/circuit_breaker.py | Integrações externas |
| Scope Config | PromptScope | lia-agent-system/app/tools/scope_config.py | Todos |
| Tool Registry | ToolRegistry | lia-agent-system/app/tools/registry.py | Todos |
| HITL Service | HITLService | lia-agent-system/app/services/hitl_service.py | Kanban, Jobs, Wizard |
| Consent Checker | ConsentCheckerService | lia-agent-system/app/services/consent_checker_service.py | WSI, CV Screening |
| Confidence Policy | ConfidencePolicyService | lia-agent-system/app/services/confidence_policy_service.py | Orquestrador |
```

**Como verificar:** Executar os comandos de DP-02 passos 1-11 para identificar quais componentes são compartilhados.

### 1.2 Inventário de Prompts/Assistentes

**Usar saída de DP-01.**

```markdown
### Inventário de Prompts

| # | Nome | Scope | Arquivo Principal | Linhas | Agente | Domínio |
|---|------|-------|-------------------|--------|--------|---------|
| P1 | Talent Funnel | TALENT_FUNNEL | .../talent_assistant_prompts.py | (N) | TalentReActAgent | RecruiterAssistant |
| P2 | Job Table | JOB_TABLE | .../jobs_management_prompts.py | (N) | JobsMgmtReActAgent | RecruiterAssistant |
| P3 | Kanban (IN_JOB) | IN_JOB | .../kanban_assistant_prompts.py | (N) | KanbanReActAgent | RecruiterAssistant |
| P4 | Float (Global) | GLOBAL | orchestrator.py + intent_router.py | (N) | Orchestrator | Orquestração |
| P5 | Hiring Policy | HIRING_POLICY | .../policy_system_prompt.py | (N) | PolicyReActAgent | HiringPolicy |
| P6 | Job Wizard | JOB_WIZARD | .../wizard_system_prompt.py | (N) | WizardReActAgent | JobManagement |
```

### 1.3 Stack Completo por Prompt

**Usar saída de DP-02.** Gerar uma tabela de 14 camadas para CADA prompt.

**Exemplo preenchido (P3 — Kanban):**

```markdown
### Stack Completo — Kanban Assistant (P3)

| Camada | Componente | Arquivo |
|--------|-----------|---------|
| Agente | KanbanReActAgent | lia-agent-system/app/domains/recruiter_assistant/agents/kanban_react_agent.py |
| Domínio | RecruiterAssistantDomain | lia-agent-system/app/domains/recruiter_assistant/domain.py |
| System Prompt | LIA_SYSTEM_PROMPT (kanban) | lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py |
| Reasoning Prompt | (integrado ao system prompt) | (mesmo arquivo) |
| Tool Registry | kanban_tool_registry | lia-agent-system/app/domains/recruiter_assistant/agents/kanban_tool_registry.py |
| Tools | 26 tools (14 query + 12 action) | lia-agent-system/app/domains/recruiter_assistant/tools/ |
| Serviço(s) | KanbanAssistantService | lia-agent-system/app/domains/recruiter_assistant/services/kanban_assistant_service.py |
| Compliance | FairnessGuard (parcial, via tools) | lia-agent-system/app/shared/compliance/fairness_guard.py |
| Frontend — Página | JobKanbanPage | plataforma-lia/src/components/pages/job-kanban-page.tsx |
| Frontend — Chat | TransitionChatPanel | plataforma-lia/src/components/kanban/components/TransitionChatPanel.tsx |
| Frontend — Hooks | (via float hooks) | plataforma-lia/src/hooks/ |
| Frontend — Context | (via LiaFloatProvider) | plataforma-lia/src/contexts/lia-float-context.tsx |
| API Proxy | /api/backend-proxy/lia/kanban-assistant | → Backend /api/v1/kanban_assistant |
| WebSocket | ws://.../ws/chat/{session_id} | Streaming de tokens + HITL |
```

**Repetir para cada prompt (P1..P6).** Camadas marcadas como "AUSENTE" são achados.

### 1.4 Tools por Scope

**Usar saída de DP-03.** Gerar uma tabela de tools para CADA scope.

**Exemplo preenchido (IN_JOB):**

```markdown
### Tools no scope IN_JOB (14 query + 12 action = 26 tools)

**Query (14):** get_job_details, get_vacancy_funnel, get_candidate_details, get_activity_summary, get_pending_actions, compare_candidates, get_candidate_stats, get_bottleneck_analysis, get_job_velocity, get_job_quality_metrics, get_stakeholder_metrics, get_prediction_metrics, get_job_benchmark, get_smart_alerts

**Action (12):** update_candidate_stage, bulk_update_candidates_stage, reject_candidate, shortlist_candidate, add_to_list, hide_candidate, wsi_screening, send_email, send_whatsapp, schedule_interview, send_feedback

| Tool | Tipo | Implementado? | Arquivo |
|------|------|--------------|---------|
| get_job_details | Query | SIM | .../analytics_query_tools.py |
| get_vacancy_funnel | Query | SIM | .../analytics_query_tools.py |
| ... | ... | ... | ... |
| wsi_screening | Action | SIM (HITL) | .../kanban_tool_registry.py |
| send_email | Action | SIM | .../communication_tools.py |
```

**Repetir para cada scope.** Tools com "NÃO" ou "STUB" são achados críticos.

---

## SEÇÃO 2: ANÁLISE DETALHADA POR PROMPT

**Procedimentos fonte:** DP-04 (O que faz), DP-05 (O que NÃO faz), DP-06 (Problemas), DP-07 (Oportunidades)

**Passos para o auditor:**

1. Para CADA prompt identificado em DP-01:
   a. Executar **DP-04** → Listar capacidades implementadas
   b. Executar **DP-05** → Listar gaps
   c. Executar **DP-06** → Identificar problemas com evidências
   d. Executar **DP-07** → Propor oportunidades

2. Usar o template de **DP-17** para padronizar a saída

**Template obrigatório por prompt (copiar e preencher):**

```markdown
## [N]. PROMPT [NOME] ([Scope])

**Arquivo principal:** `[caminho]` ([N] linhas)
**Scope:** PromptScope.[SCOPE]
**Agente:** [Classe do agente]

### Stack completo vinculado
(tabela de 14 camadas — ver Seção 1.3)

### Tools no scope [SCOPE] ([N] query + [M] action = [T] tools)
**Query ([N]):** (listar)
**Action ([M]):** (listar)

### O que faz
[Descrição em 1-2 linhas do papel do assistente]

**Capacidades implementadas:**
- [N] tipos de [análise/comando]: (listar cada um)
- Detecção de intent: [método] — keywords + LLM fallback / ReAct LLM direto / CascadedRouter N-tier
- Construção de contexto: [como monta o prompt dinâmico]
- Resolução de ações UI: [função] — mapeia [N] tipos de ação para o frontend
- [N] tools de query: (listar)
- [N] tools de action: (listar)
- Mecanismos especiais: [HITL / anti-sycophancy / memória / confirmação dupla / name matching / etc.]

### O que NÃO faz
- Sem [capacidade ausente 1]: [por que importa para o recrutador]
- Sem [capacidade ausente 2]: [impacto]
- ...

### Problemas identificados
1. **[Título do problema]:** [Descrição técnica] — Arquivo: `[caminho]`, Evidência: [linha ou trecho]
   - Severidade: CRÍTICO / ALTO / MÉDIO / BAIXO
   - Runbook associado: RM-[XX]
2. ...

### Oportunidades
- [Oportunidade 1]: [Benefício esperado] — Esforço: Baixo/Médio/Alto
- [Oportunidade 2]: [Benefício] — Esforço: [nível]
- ...
```

**Exemplo preenchido (P5 — Hiring Policy):**

```markdown
## 5. PROMPT DE POLÍTICAS DE RECRUTAMENTO (Hiring Policy)

**Arquivo principal:** `lia-agent-system/app/domains/hiring_policy/agents/policy_system_prompt.py`
**Scope:** PromptScope.HIRING_POLICY
**Agente:** PolicyReActAgent

### O que faz
Consultora de RH que ajuda a configurar regras globais da empresa — pipeline, agendamento, comunicação, triagem e autonomia da LIA.

**Capacidades implementadas:**
- 5 blocos de configuração: Pipeline/Processo, Agendamento, Comunicação, Triagem, Autonomia da LIA
- ReAct agent real: Ciclo thought-action-observation com JSON estruturado
- Validação ética obrigatória: validate_policy_compliance ANTES de salvar qualquer critério de triagem
- 10 critérios proibidos: Gênero, raça, idade, religião, orientação sexual, estado civil, PCD, nacionalidade, aparência, situação familiar
- Anti-sycophancy: PRESENTE — regras explícitas contra concordar para evitar conflito
- Contra-argumentação com dados: Usa benchmarks do setor para sustentar posições
- Calibração por contexto: Adapta por porte (startup/PME/corporação) e setor (tech/finance/retail/healthcare)
- Memória de trabalho: Reasoning prompt inclui memory_summary e stage_context

### O que NÃO faz
- Sem preview de impacto: Não mostra simulação de como as políticas afetariam vagas existentes
- Sem versionamento de políticas: Não guarda histórico de mudanças (quem mudou o quê, quando)
- Sem exportação: Não exporta políticas em PDF ou formato compartilhável
- Sem templates de políticas: Não oferece "pacotes" pré-configurados por indústria

### Problemas identificados
1. **Tools podem não existir:** O prompt referencia get_industry_benchmarks, get_company_context, get_setup_progress — verificar implementação real — `policy_system_prompt.py`
   - Severidade: ALTO
   - Runbook: RM-25 (Wiring Desconectado)
2. **Prompt muito longo:** ~4.000 tokens só de system prompt — pode competir com contexto da conversa
   - Severidade: MÉDIO
   - Runbook: CI-01

### Oportunidades
- Simulação de impacto: "Se aplicar SLA de 3 dias, quantas vagas ficariam em alerta?" — Esforço: Alto
- Versionamento com diff visual — Esforço: Médio
- Templates de políticas por indústria — Esforço: Médio
- Onboarding guiado para empresas novas — Esforço: Baixo
```

---

## SEÇÃO 3: AUDITORIA MULTI-DIMENSIONAL

**Procedimentos fonte:** DP-09.1 a DP-09.11

**Passos para o auditor:**

1. Executar **DP-09.1** (Anti-Sycophancy) → Preencher matriz
2. Executar **DP-09.2** (Intent Detection) → Preencher matriz
3. Executar **DP-09.3** (FairnessGuard) → Preencher matriz
4. Executar **DP-09.4** (HITL) → Preencher matriz
5. Executar **DP-09.5** (Circuit Breaker) → Preencher matriz
6. Executar **DP-09.6** (Token Budget) → Preencher matriz
7. Executar **DP-09.7** (PII Masking) → Preencher matriz
8. Executar **DP-09.8** (Consent) → Preencher matriz
9. Executar **DP-09.9** (Multi-Tenant) → Preencher matriz
10. Executar **DP-09.10** (Audit Trail) → Preencher matriz
11. **Consolidar em DP-09.11** → Matriz final

### 3.1 Matrizes Individuais por Dimensão

Para cada dimensão, usar o template de DP-09 correspondente. Incluir:
- A tabela preenchida
- Evidências para cada célula (arquivo:linha)
- Achados derivados (com severidade)

**Exemplo preenchido — Anti-Sycophancy (DP-09.1):**

```markdown
### Dimensão: Anti-Sycophancy (Crença #11)

| Prompt | Anti-Sycophancy | Contra-Argumentação | Benchmarks Setoriais |
|--------|----------------|---------------------|---------------------|
| P1 Talent Funnel | AUSENTE | AUSENTE | AUSENTE |
| P2 Job Table | AUSENTE | AUSENTE | AUSENTE |
| P3 Kanban (IN_JOB) | AUSENTE | AUSENTE | AUSENTE |
| P4 Float (Global) | AUSENTE | AUSENTE | AUSENTE |
| P5 Hiring Policy | PRESENTE | PRESENTE | PRESENTE |
| P6 Job Wizard | PRESENTE | PRESENTE | PRESENTE |

**ACHADO CRÍTICO:** Apenas 2 dos 6 prompts implementam anti-sycophancy. Os prompts P1, P2, P3 e P4 podem concordar silenciosamente com pedidos que comprometam qualidade de contratação (ex: "quero só candidatos de universidades top" — sem contra-argumentar sobre viés).

- **Evidência P5 (PRESENTE):** `policy_system_prompt.py` — seção "=== PREVENÇÃO DE SYCOPHANCY ==="
- **Evidência P1 (AUSENTE):** `talent_assistant_prompts.py` — grep por "sycophancy" retorna 0 resultados
- **Runbook:** RM-08 (Anti-Sycophancy Ausente no System Prompt)
```

**Repetir para cada dimensão (DP-09.2 a DP-09.10).**

### 3.2 ConfidencePolicyService (sub-seção de DP-09.2)

Incluir verificação dos thresholds de confiança:

| Threshold | Spec | Implementação | Status |
|-----------|------|--------------|--------|
| APPLY_SILENT | >= 0.85 | >= 0.85 | OK / FALHA |
| APPLY_NOTIFY | 0.70-0.84 | 0.70-0.84 | OK / FALHA |
| ASK_USER | < 0.70 | < 0.70 (floor 0.50) | OK / FALHA |

### 3.3 Matriz Consolidada (Tabela Final)

**Usar saída de DP-09.11.** Esta é a tabela mais importante do relatório:

| Dimensão | P1 Talent | P2 Jobs | P3 Kanban | P4 Float | P5 Policy | P6 Wizard |
|----------|----------|---------|-----------|----------|-----------|-----------|
| Anti-Sycophancy | OK/FALHA | OK/FALHA | OK/FALHA | OK/FALHA | OK/FALHA | OK/FALHA |
| FairnessGuard Input | | | | | | |
| FairnessGuard Tools | | | | | | |
| HITL Enforcement | | | | | | |
| Negation Detection | | | | | | |
| Confiança Real | | | | | | |
| Circuit Breaker Direto | | | | | | |
| Pre-call Budget Check | | | | | | |
| PII Masking | | | | | | |
| Consent Check | | | | | | |
| Multi-Tenant Isolation | | | | | | |
| Audit Trail | | | | | | |
| Observabilidade | | | | | | |
| Token Tracking | | | | | | |

**Regras de interpretação:**
- Linha toda OK → Dimensão saudável sistêmica
- Qualquer FALHA em Inegociável (FairnessGuard, HITL, Consent, PII) → **P0 CRÍTICO**
- Qualquer FALHA em Crença (Anti-Sycophancy) → **P0 CRÍTICO**
- Mais de 50% FALHA em uma dimensão → **Problema sistêmico** (a correção deve ser arquitetural, não por prompt)
- Prompt com mais de 3 FALHAs → **Prompt em risco** (priorizar na correção)
- Coluna toda OK → Prompt exemplar (usar como referência para os outros)

---

## SEÇÃO 4: ANÁLISE COMPARATIVA DE CAPACIDADES

**Procedimentos fonte:** DP-08 (Mapa), DP-10 (Padronização), DP-11 (Tools Preditivos), DP-12 (Assistente Completo)

**Passos para o auditor:**

1. Executar **DP-08** → Gerar mapa Capacidade × Prompt (usar as 7 categorias obrigatórias: Análise, Preditivo, Ações, Proativo, Relatórios, Chat/Conversa)
2. Executar **DP-10** → Definir 3 níveis de padronização
3. Executar **DP-11** → Mapear tools preditivos subutilizados
4. Executar **DP-12** → Verificar checklist de "assistente completo"

### 4.1 Mapa de Capacidades Atual

**Usar tabela de DP-08.** Valores: SIM, PARCIAL, DECLARADO, via routing, N/A, — (traço).

Incluir TODAS as 7 categorias com seus sub-itens (ver template completo em DP-08).

### 4.2 O que Deveria Ser Padrão

**Usar saída de DP-10.** Organizar em 3 níveis:

**NÍVEL 1 — Padrão para TODOS os prompts (sem exceção):**

| Capacidade | Justificativa | Hoje (X/N prompts) | Runbook |
|------------|--------------|--------------------|---------| 
| Anti-sycophancy | Crença #11 do Manifesto | (verificar) | RM-08 |
| FairnessGuard no input | Inegociável #3 | (verificar) | RM-02 |
| Negation detection | Qualidade de intent | (verificar) | RM-17 |
| Confiança real | Decisões baseadas em dados | (verificar) | RM-09 |

**NÍVEL 2 — Padrão para prompts operacionais (exceto Policy):**

| Capacidade | Justificativa | Hoje | Esforço |
|------------|--------------|------|---------|
| Gerar relatórios | Todos os contextos operacionais | (verificar) | Médio |
| Histórico de conversas | Retomar análises | (verificar) | Baixo (backend existe) |
| Novo/limpar chat | Separar contextos | (verificar) | Baixo (API existe) |
| Capacidade preditiva | Dropout, forecast | (verificar) | Médio |
| Smart alerts | SLA, at-risk | (verificar) | Médio |
| Pendências | Produtividade | (verificar) | Baixo |
| Sugestões proativas | Proatividade da LIA | (verificar) | Alto |

**NÍVEL 3 — Específico por tipo de prompt:**

| Tipo de Prompt | Requisitos Específicos | Justificativa |
|---------------|----------------------|---------------|
| Configuracional (Policy) | Setup guiado, validação ética, checklist | Natureza não-recorrente |
| Conversacional (Float) | Routing, cross-domain, briefing diário | Hub central |
| Workflow (Wizard) | Stages, validação, preview, compliance | Fluxo estruturado |
| Analítico (Talent, Jobs) | KPIs, tendências, export | Visão macro |
| Operacional (Kanban) | Pipeline, movimentação, triagem | Ação direta |

### 4.3 Tools Preditivos — Mapa de Subutilização

**Usar saída de DP-11.** Incluir:

| Tool | Existe em | Usado por | Deveria ser usado por | Gap |
|------|-----------|-----------|----------------------|-----|
| predict_dropout_risk | predictive_tools.py | P3 Kanban | P1, P2, P3, P6 | 3 prompts |
| get_pipeline_forecast | predictive_tools.py | P3 Kanban | P2, P3 | 1 prompt |
| get_ml_predictions | analytics_query_tools.py | Ninguém | P1, P4 | 2 prompts |
| get_conversion_patterns | analytics_query_tools.py | Ninguém | P1, P2, P3 | 3 prompts |
| get_smart_alerts | analytics_query_tools.py | P3 Kanban | P1, P2, P3, P4 | 3 prompts |
| get_at_risk_candidates | kanban_tool_registry.py | P3 Kanban | P1, P3 | 1 prompt |
| get_pending_actions | analytics_query_tools.py | P4 Float (parcial) | P1, P2, P3, P4 | 3 prompts |

Proposta de ativação por prompt (ver DP-11 para detalhes).

### 4.4 Cada Prompt como Assistente Completo

**Usar saída de DP-12.** Verificar capacidades padronizadas:

| Capacidade Padrão | P1 Talent | P2 Jobs | P3 Kanban | P4 Float | P6 Wizard |
|-------------------|----------|---------|-----------|----------|-----------|
| "O que preciso fazer?" | | | | | |
| "Me dê um resumo" | | | | | |
| "Gera um relatório" | | | | | |
| "O que está em risco?" | | | | | |
| "Sugira próximos passos" | | | | | |
| "Compare X com Y" | | | | | |
| Histórico de chats | | | | | |
| Anti-sycophancy | | | | | |
| Negation detection | | | | | |

---

## SEÇÃO 5: ANÁLISE DE FUNCIONALIDADES TRANSVERSAIS

**Procedimentos fonte:** DP-13 (Histórico de Chats), DP-14 (Geração de Relatórios)

### 5.1 Histórico de Chats

**Usar saída de DP-13.**

**Estado atual do backend (APIs existentes):**

| Endpoint | Método | Descrição | Status |
|----------|--------|-----------|--------|
| /api/v1/conversations | GET | Lista conversas paginadas | (verificar) |
| /api/v1/conversations | POST | Cria nova conversa | (verificar) |
| /api/v1/conversations/{id}/clear | POST | Limpa mensagens | (verificar) |
| /api/v1/conversations/{id}/archive | POST | Soft-delete | (verificar) |
| /api/v1/conversations/{id} | DELETE | Hard-delete | (verificar) |

**Estado por prompt:**

| Prompt | Backend | UI Histórico | UI Novo Chat | UI Limpar | Recomendação |
|--------|---------|-------------|-------------|-----------|-------------|
| P1 Talent | (verificar) | (verificar) | (verificar) | (verificar) | SIM/NÃO |
| P2 Jobs | | | | | |
| P3 Kanban | | | | | SIM (por vaga) |
| P4 Float | | | | | SIM (central) |
| P5 Policy | | | | | NÃO (setup linear) |
| P6 Wizard | | | | | POR VAGA |

**Ciclo de vida da conversa:**
- Chats ficam inativos após X horas sem interação
- Auto-archive após 48h sem atividade
- ConversationMemory faz summarization após 10 mensagens
- Recrutador pode: continuar, criar novo, arquivar, limpar

### 5.2 Geração de Relatórios

**Usar saída de DP-14.**

| Prompt | Tipo de Relatório | Formato | Status Atual | Tool Existente |
|--------|-------------------|---------|-------------|----------------|
| P1 Talent | Pool (distribuição, scores, diversidade) | Markdown + dados | (verificar) | (verificar) |
| P2 Jobs | Portfolio (KPIs, SLAs, tendências) | Markdown + tabelas | (verificar) | export_analytics |
| P3 Kanban | Vaga (funil, velocidade, gargalos) | Markdown + métricas | (verificar) | PARCIAL |
| P4 Float | Consolidado (briefing executivo) | Markdown + resumo | (verificar) | generate_report |
| P5 Policy | Compliance (políticas, gaps) | Markdown + checklist | (verificar) | NÃO |
| P6 Wizard | Pré-publicação (completude, riscos) | Markdown + score | (verificar) | check_job_draft_health |

---

## SEÇÃO 6: PRIORIDADES DE CORREÇÃO COM RUNBOOKS

**Procedimentos fonte:** DP-15 (Priorização), DP-16 (Arquivos-Chave)

**Passos para o auditor:**

1. Coletar TODOS os problemas de:
   - Seção 2 (DP-06 — problemas por prompt)
   - Seção 3 (DP-09 — problemas transversais)
   - Seção 4 (DP-10, DP-11 — gaps de padronização)
   - Seção 5 (DP-13, DP-14 — funcionalidades ausentes)
2. Classificar por prioridade usando os critérios de DP-15
3. Associar cada achado ao runbook correspondente (RM-01..RM-44)
4. Mapear arquivos-chave usando DP-16

### 6.1 Critérios de Classificação

| Prioridade | Critério | Exemplos Típicos | Prazo |
|-----------|---------|-----------------|-------|
| **P0 — Crítico** | Viola Inegociáveis WeDO ou pode causar decisões discriminatórias | FairnessGuard ausente como middleware, anti-sycophancy ausente em 4/6 prompts, tools declarados mas não implementados | ANTES do próximo deploy |
| **P1 — Alto** | Afeta qualidade, resiliência ou produz resultados incorretos | HITL incompleto, confiança artificial, consent soft enforcement, GUARDRAIL_TOOLS estreito | Próximo sprint |
| **P2 — Médio** | Degradação de performance, manutenibilidade ou arquitetura | Circuit breaker ausente em agentes, scope manual, duplicação de prompts, frontend monolítico | Sprint N+2/N+3 |
| **P3 — Baixo** | Melhoria desejável, feature futura | Upload JD, simulação de políticas, proatividade, templates por indústria | Backlog |

### 6.2 Template de Achado

Para cada achado, usar este formato:

```markdown
### [ACH-XXX] — [Título do Achado]
- **Prioridade:** P0 / P1 / P2 / P3
- **Dimensão:** [Dimensão 1-14 / DP-XX que identificou o problema]
- **Prompt(s) afetado(s):** [P1, P3, P4 — ou "Todos"]
- **Runbook:** [RM-XX] (PARTE VII/IX do playbook)
- **Arquivo(s) afetado(s):**
  - `[caminho/arquivo1.py]`
  - `[caminho/arquivo2.tsx]`
- **Descrição:** [O que está errado — com evidência técnica]
- **Evidência:** [comando grep/trecho de código que comprova]
- **Impacto se não corrigido:** [Consequência concreta para o produto/usuário/compliance]
- **Correção proposta:** [O QUE FAZER — não apenas "melhorar"]
- **Esforço estimado:** [horas] — Responsável: [Backend / Frontend / Infra / Full-stack]
- **Depende de:** [ACH-YYY, se houver dependência]
```

### 6.3 Exemplo de Achados Preenchidos

```markdown
### ACH-001 — FairnessGuard Não É Middleware Automático
- **Prioridade:** P0
- **Dimensão:** Dimensão 12 — Governança e Resiliência IA (DP-09.3)
- **Prompt(s) afetado(s):** Todos (P1..P6)
- **Runbook:** RM-02
- **Arquivo(s) afetado(s):**
  - `lia-agent-system/libs/agents-core/lia_agents_core/react_loop.py`
  - `lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py`
- **Descrição:** O FairnessGuard não é middleware obrigatório no ReActLoop ou EnhancedAgentMixin. Cada agente precisa chamar manualmente — e a maioria NÃO chama no input.
- **Evidência:** `grep -n "fairness" react_loop.py` retorna 0 resultados
- **Impacto se não corrigido:** Viola Inegociável #3. Inputs com viés discriminatório podem passar sem detecção em 4 dos 6 prompts.
- **Correção proposta:** Mover FairnessGuard.check() para dentro do ReActLoop.run() ou EnhancedAgentMixin._pre_process() como gatekeeper automático.
- **Esforço estimado:** 4h — Backend
- **Depende de:** Nenhum

### ACH-002 — Anti-Sycophancy Ausente em 4 dos 6 Prompts
- **Prioridade:** P0
- **Dimensão:** Dimensão 10 — Qualidade LLM (DP-09.1)
- **Prompt(s) afetado(s):** P1, P2, P3, P4
- **Runbook:** RM-08
- **Arquivo(s) afetado(s):**
  - `lia-agent-system/app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py`
  - `lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`
  - `lia-agent-system/app/domains/recruiter_assistant/prompts/jobs_management_prompts.py`
  - `lia-agent-system/app/orchestrator/orchestrator.py`
- **Descrição:** Apenas os prompts de Hiring Policy e Job Wizard implementam anti-sycophancy. Os 4 restantes podem concordar silenciosamente com pedidos discriminatórios ou contra-produtivos.
- **Evidência:** `grep -n "sycophancy" talent_assistant_prompts.py` retorna 0 resultados
- **Impacto se não corrigido:** Viola Crença #11. Recrutador pode pedir "só candidatos de universidades top" e a LIA aceitar sem questionar.
- **Correção proposta:** Adicionar seções "=== PREVENÇÃO DE SYCOPHANCY ===" e "=== CONTRA-ARGUMENTAÇÃO ===" nos 4 prompts, seguindo o modelo de policy_system_prompt.py.
- **Esforço estimado:** 8h — Backend
- **Depende de:** Nenhum
```

---

## SEÇÃO 7: RESUMO EXECUTIVO DE ESFORÇO

**Procedimentos fonte:** DP-15, DP-16

### 7.1 Tabela Consolidada para Sprint Planning

| Prioridade | Qtd. Achados | Esforço Total (h) | Responsável Principal | Sprint Alvo |
|:----------:|:------------:|:-----------------:|:---------------------:|:-----------:|
| P0 — Crítico | (contar) | (somar) | Backend | Imediato |
| P1 — Alto | (contar) | (somar) | Backend/Frontend | Sprint N+1 |
| P2 — Médio | (contar) | (somar) | Backend | Sprint N+2/N+3 |
| P3 — Baixo | (contar) | (somar) | Backend/Frontend | Backlog |
| **Total** | **(somar)** | **(somar)** | — | — |

### 7.2 Tabela Detalhada de Execução

| ACH-ID | Título | Prioridade | Runbook | Arquivo(s) Principal(is) | Esforço (h) | Responsável | Depende de |
|--------|--------|-----------|---------|-------------------------|------------|-------------|-----------|
| ACH-001 | (título) | P0 | RM-XX | (caminho) | Xh | Backend | — |
| ACH-002 | (título) | P0 | RM-XX | (caminho) | Xh | Backend | — |
| ... | | | | | | | |

### 7.3 Ordem de Execução Recomendada

Agrupar por dependências e sugerir ordem de execução:

```markdown
**Sprint 1 (Imediato — P0):**
1. ACH-001 → RM-02 (FairnessGuard middleware) — 4h Backend — SEM dependências
2. ACH-002 → RM-08 (Anti-sycophancy 4 prompts) — 8h Backend — SEM dependências
3. ACH-003 → RM-17 (Negation detection) — 6h Backend — SEM dependências
4. ACH-004 → RM-25 (Tools declarados vs implementados) — 4h Backend — SEM dependências
   → Total Sprint 1: ~22h

**Sprint 2 (P1):**
5. ACH-005 → RM-XX — Xh — Depende de ACH-001
6. ...
   → Total Sprint 2: ~XXh

**Backlog (P2/P3):**
7. ...
```

---

## ANEXO A DO RELATÓRIO: ARQUIVOS-CHAVE PARA CORREÇÕES

**Procedimento fonte:** DP-16

Índice completo de todos os arquivos relevantes, organizado por categoria:

```markdown
### Backend — Prompts
- lia-agent-system/app/domains/recruiter_assistant/prompts/talent_assistant_prompts.py
- lia-agent-system/app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py
- lia-agent-system/app/domains/recruiter_assistant/prompts/jobs_management_prompts.py
- lia-agent-system/app/domains/job_management/agents/wizard_system_prompt.py
- lia-agent-system/app/domains/hiring_policy/agents/policy_system_prompt.py
- lia-agent-system/app/prompts/shared/agent_prompts.yaml
- lia-agent-system/app/shared/prompts/job_wizard.py
- lia-agent-system/app/shared/prompts/prompt_registry.py
- lia-agent-system/app/shared/prompts/templates.py

### Backend — Agentes
- lia-agent-system/app/domains/recruiter_assistant/agents/talent_react_agent.py
- lia-agent-system/app/domains/recruiter_assistant/agents/kanban_react_agent.py
- lia-agent-system/app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py
- lia-agent-system/app/domains/job_management/agents/wizard_react_agent.py
- lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py
- lia-agent-system/app/domains/hiring_policy/agents/policy_react_agent.py
- lia-agent-system/app/domains/cv_screening/agents/pipeline_react_agent.py
- lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py
- lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py
- lia-agent-system/app/domains/analytics/agents/analytics_react_agent.py
- lia-agent-system/app/domains/communication/agents/communication_react_agent.py
- lia-agent-system/app/domains/ats_integration/agents/ats_integration_react_agent.py

### Backend — Orquestração
- lia-agent-system/app/orchestrator/orchestrator.py
- lia-agent-system/app/orchestrator/intent_router.py
- lia-agent-system/app/orchestrator/cascaded_router.py
- lia-agent-system/app/orchestrator/task_planner.py
- lia-agent-system/app/orchestrator/policy_engine.py
- lia-agent-system/app/orchestrator/state_manager.py
- lia-agent-system/app/orchestrator/semantic_cache.py
- lia-agent-system/app/orchestrator/vector_semantic_cache.py
- lia-agent-system/app/shared/execution/plan_detector.py
- lia-agent-system/app/shared/execution/plan_executor.py
- lia-agent-system/app/domains/registry.py
- lia-agent-system/app/domains/workflow.py

### Backend — Tools e Scope
- lia-agent-system/app/tools/scope_config.py
- lia-agent-system/app/tools/registry.py
- lia-agent-system/app/domains/job_management/tools/job_wizard_tools.py
- lia-agent-system/app/domains/job_management/agents/wizard_tool_registry.py
- lia-agent-system/app/domains/recruiter_assistant/agents/talent_tool_registry.py
- lia-agent-system/app/domains/recruiter_assistant/agents/kanban_tool_registry.py

### Backend — Serviços
- lia-agent-system/app/services/llm.py
- lia-agent-system/app/shared/providers/llm_factory.py
- lia-agent-system/app/shared/providers/llm_claude.py
- lia-agent-system/app/shared/providers/llm_gemini.py
- lia-agent-system/app/shared/providers/llm_openai.py
- lia-agent-system/app/services/conversation_memory.py
- lia-agent-system/app/services/market_benchmark_service.py
- lia-agent-system/app/services/skills_catalog_service.py
- lia-agent-system/app/services/config_completeness_service.py
- lia-agent-system/app/services/pearch_service.py
- lia-agent-system/app/domains/job_management/services/jd_enrichment_service.py
- lia-agent-system/app/domains/recruiter_assistant/services/kanban_assistant_service.py
- lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py

### Backend — Compliance e Governança
- lia-agent-system/app/shared/compliance/fairness_guard.py
- lia-agent-system/app/shared/compliance/audit_service.py
- lia-agent-system/app/shared/compliance/fact_checker.py
- lia-agent-system/app/shared/compliance/guardrail_repository.py

### Backend — Resiliência e Observabilidade
- lia-agent-system/libs/agents-core/lia_agents_core/react_loop.py
- lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py
- lia-agent-system/libs/agents-core/lia_agents_core/langgraph_react_base.py
- lia-agent-system/libs/audit/lia_audit/audit_callback.py
- lia-agent-system/libs/audit/lia_audit/audit_writer.py
- lia-agent-system/libs/agents-core/lia_agents_core/execution_log_store.py
- lia-agent-system/libs/agents-core/lia_agents_core/observability.py
- lia-agent-system/app/services/token_tracking_service.py
- lia-agent-system/app/services/confidence_policy_service.py
- lia-agent-system/app/services/consent_checker_service.py
- lia-agent-system/app/services/hitl_service.py
- lia-agent-system/app/shared/pii_masking.py
- lia-agent-system/app/shared/resilience/circuit_breaker.py
- lia-agent-system/app/shared/resilience/cache_manager_service.py
- lia-agent-system/app/api/v1/data_subject_requests.py

### Frontend — Componentes
- plataforma-lia/src/components/expandable-ai-prompt.tsx
- plataforma-lia/src/components/lia-expanded-prompt.tsx
- plataforma-lia/src/components/lia-float/LiaChatPanel.tsx
- plataforma-lia/src/components/lia-float/LiaSplitPanel.tsx
- plataforma-lia/src/components/lia-float/LiaChatButton.tsx
- plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx
- plataforma-lia/src/components/job-wizard/WizardContainer.tsx
- plataforma-lia/src/components/kanban/components/TransitionChatPanel.tsx
- plataforma-lia/src/components/triagem/ChatContainer.tsx
- plataforma-lia/src/components/settings/HiringPoliciesHub.tsx
- plataforma-lia/src/components/pages/candidates-page.tsx
- plataforma-lia/src/components/pages/jobs-page.tsx
- plataforma-lia/src/components/pages/job-kanban-page.tsx
- plataforma-lia/src/components/modals/job-insights-modal.tsx
- plataforma-lia/src/components/chat/message-bubble.tsx
- plataforma-lia/src/components/chat/chat-input-bar.tsx
- plataforma-lia/src/components/search/smart-search-input.tsx

### Frontend — Hooks e Context
- plataforma-lia/src/contexts/lia-float-context.tsx
- plataforma-lia/src/hooks/use-float-streaming.ts
- plataforma-lia/src/hooks/use-navigation-intent.ts
- plataforma-lia/src/hooks/use-action-intent.ts
- plataforma-lia/src/hooks/use-float-conversation.ts
- plataforma-lia/src/hooks/use-hiring-policies.ts
- plataforma-lia/src/hooks/useCreditEstimator.ts
- plataforma-lia/src/lib/api/kanban-assistant.ts
```

---

## ANEXO B DO RELATÓRIO: REFERÊNCIA CRUZADA ACHADO → RUNBOOK

**Procedimento fonte:** DP-20

Para cada achado do relatório, o time deve localizar o runbook correspondente no playbook:

| Tipo de Achado | Runbook(s) | Localização no Playbook |
|---------------|-----------|------------------------|
| PII não mascarada | RM-01 | PARTE VII |
| FairnessGuard ausente (middleware) | RM-02 | PARTE VII |
| HITL/Human review ausente | RM-03 | PARTE VII |
| Consent check ausente | RM-04 | PARTE VII |
| Audit trail incompleto | RM-05 | PARTE VII |
| Multi-tenant isolation | RM-06 | PARTE VII |
| Decisão automatizada sem opt-out | RM-07 | PARTE VII |
| Anti-sycophancy ausente | RM-08 | PARTE VII |
| Confiança artificial (fórmula fake) | RM-09 | PARTE VII |
| Circuit breaker ausente | RM-10 | PARTE VII |
| Token budget sem pre-call | RM-11 | PARTE VII |
| Observabilidade insuficiente | RM-12 | PARTE VII |
| Degradation path incompleto | RM-13 | PARTE VII |
| Few-shot examples inadequados | RM-14 | PARTE VII |
| FairnessGuard ausente na SAÍDA | RM-15 | PARTE VII |
| PII scrubbing na resposta | RM-16 | PARTE VII |
| Negation detection ausente | RM-17 | PARTE VII |
| Padrão 4-arquivos não seguido | RM-18 | PARTE VII |
| Stage context ausente | RM-19 | PARTE VII |
| Memória sem decay/limite | RM-20 | PARTE VII |
| Drift detection ausente | RM-21 | PARTE VII |
| Guardrails não configurados | RM-22 | PARTE VII |
| Testes de fairness fora do CI | RM-23 | PARTE VII |
| ConfidencePolicy limitada | RM-24 | PARTE VII |
| Wiring desconectado | RM-25 | PARTE VII |
| EU AI Act gaps | RM-26 | PARTE VII |
| WCAG 2.1 AA não atendido | RM-27 | PARTE VII |
| Outreach automatizado | RM-28 | PARTE VII |
| Profile enrichment | RM-29 | PARTE VII |
| WhatsApp ↔ WSI | RM-30 | PARTE VII |
| Blind review | RM-31 | PARTE VII |
| Calibração contínua de busca | RM-32 | PARTE VII |
| NPS / Sentiment | RM-33 | PARTE VII |
| Cascata de confiança T3 | RM-34 | PARTE VII |
| Discriminação em critérios | RM-35 | PARTE VII |
| Pipeline/stages não validado | RM-36 | PARTE VII |
| Video interview com IA | RM-37 | PARTE VII |
| Data flow quebrado | RM-38 | PARTE VII |
| Backend/API incorreto | RM-39 | PARTE VII |
| Types/contracts inconsistentes | RM-40 | PARTE VII |
| User flow quebrado | RM-41 | PARTE VII |
| Inconsistência entre componentes | RM-42 | PARTE VII |
| Documentação desatualizada | RM-43 | PARTE VII |
| Performance insuficiente | RM-44 | PARTE VII |

### Mapa Dimensão → Runbook(s) mais comuns

| Dimensão de Auditoria | Runbooks Típicos |
|----------------------|-----------------|
| Anti-Sycophancy | RM-08 |
| FairnessGuard | RM-02, RM-15, RM-35 |
| Intent Detection | RM-17, RM-09 |
| HITL | RM-03 |
| Circuit Breaker | RM-10, RM-13 |
| Token Budget | RM-11 |
| PII | RM-01, RM-16 |
| Consent | RM-04 |
| Multi-Tenant | RM-06 |
| Audit Trail | RM-05, RM-12 |
| Observabilidade | RM-12 |
| Tools/Wiring | RM-25, RM-39 |
| Prompts/Qualidade LLM | RM-08, RM-14, RM-17, RM-19, CI-01 |
| Arquitetura de Agentes | RM-18, CI-17 |

---

## CHECKLIST FINAL DO AUDITOR

Antes de entregar o relatório, verificar:

- [ ] **Seção 0 (Resumo Executivo)** escrita APÓS todas as outras seções
- [ ] **Seção 1** tem: componentes compartilhados + inventário de N prompts + N tabelas de stack (14 camadas cada) + N tabelas de tools
- [ ] **Seção 2** tem: 1 bloco completo por prompt (O que faz, O que NÃO faz, Problemas, Oportunidades) com evidências
- [ ] **Seção 3** tem: 10 matrizes individuais (DP-09.1..09.10) + 1 matriz consolidada (DP-09.11)
- [ ] **Seção 4** tem: mapa de capacidades (7 categorias) + 3 níveis de padronização + tools preditivos + assistente completo
- [ ] **Seção 5** tem: estado do histórico de chats + estado de geração de relatórios
- [ ] **Seção 6** tem: TODOS os achados classificados P0-P3 com template completo (ID, prioridade, runbook, arquivo, evidência, impacto, correção)
- [ ] **Seção 7** tem: tabela consolidada + tabela detalhada + ordem de execução recomendada
- [ ] **Anexo A** tem: índice completo de arquivos por categoria
- [ ] **Anexo B** tem: referência cruzada achado → runbook
- [ ] Cada achado tem: evidência real (arquivo + linha ou resultado de grep), não apenas afirmação
- [ ] Cada achado P0/P1 tem: correção proposta concreta (O QUE FAZER, não apenas "melhorar")
- [ ] Todos os prompts identificados em DP-01 foram cobertos em TODAS as seções
- [ ] Nenhuma FALHA em Inegociável foi classificada abaixo de P0
- [ ] O relatório é auto-contido: um engenheiro pode executar as correções sem perguntar ao auditor

---

# ANEXO A: GABARITO DE ARQUITETURA — PADRÕES CANÔNICOS DE AGENTES

> **Nota:** Os Anexos A–J complementam as Partes I–VIII com padrões de referência (gabaritos) extraídos do Guia de Arquitetura IA v1.0 e do Diagnóstico de Compliance. O auditor deve usar estes gabaritos como critério de verificação ao executar as dimensões de auditoria definidas nas partes anteriores.

Esta seção contém os padrões arquiteturais obrigatórios que servem como gabarito para verificação. O auditor deve comparar cada agente/componente contra estes padrões.

---

## GA-1. PADRÃO 4 ARQUIVOS — Template Canônico de Agente ReAct (ADR-002)

Todo domínio de agente ReAct DEVE seguir esta estrutura de 4 arquivos:

```
app/domains/[domain]/
├── agents/
│   ├── [domain]_react_agent.py     ← Agente principal (implementa BaseAgent)
│   ├── [domain]_tool_registry.py   ← Definição das ferramentas
│   ├── [domain]_system_prompt.py   ← Prompt do sistema (get_*_system_prompt)
│   └── [domain]_stage_context.py   ← Definição de stages e transições
└── services/                       ← Serviços de domínio
```

### GA-1.1 Checklist de Conformidade por Arquivo

**Arquivo 1 — `[domain]_react_agent.py`:**
- [ ] Herda `EnhancedAgentMixin` + `BaseAgent`
- [ ] Implementa `domain_name` (property)
- [ ] Implementa `available_tools` (property)
- [ ] Implementa `process(input: AgentInput) -> AgentOutput`
- [ ] Chama `self._setup_enhanced(domain="[domain]")` no `__init__`
- [ ] Cria `ReActObserver` com `company_id` e `user_id`
- [ ] Usa `conversation_history[-5:]` (não ilimitado)
- [ ] Trata exceções com fallback gracioso (nunca crash silencioso)
- [ ] Chama `self._post_loop_learning()` após o loop
- [ ] `ReActConfig.max_iterations` <= 10 (idealmente 5)
- [ ] `ReActConfig.temperature` <= 0.7 (idealmente 0.3)

**Arquivo 2 — `[domain]_tool_registry.py`:**
- [ ] Cada tool retorna `dict` com campo `"success": True/False`
- [ ] Todas as funções são `async`
- [ ] Tools acessam dados via services (nunca DB diretamente)
- [ ] `get_stage_tools(stage)` filtra tools por stage
- [ ] `get_[domain]_tools()` retorna lista completa

**Arquivo 3 — `[domain]_system_prompt.py`:**
- [ ] Função `get_[domain]_system_prompt(stage, context)` exportada
- [ ] Segue anatomia de 7 seções (ver GA-2)
- [ ] Tamanho: 800-1500 tokens (alerta se > 2000)
- [ ] Inclui princípios inegociáveis de compliance
- [ ] Inclui instruções de formato JSON ReAct

**Arquivo 4 — `[domain]_stage_context.py`:**
- [ ] `STAGE_DEFINITIONS` dict com todos os stages
- [ ] `get_stage_context(stage, collected_fields)` exportada
- [ ] Cada stage define: nome, descrição, campos obrigatórios, próximos stages

### GA-1.2 Schemas de I/O Padronizados

```python
class AgentInput(BaseModel):
    message: str
    session_id: str
    company_id: str          # Multi-tenant OBRIGATÓRIO
    user_id: str
    pipeline_stage: Optional[str]
    context: Optional[dict]

class AgentOutput(BaseModel):
    response: str
    actions: List[AgentAction]
    navigation: Optional[NavigationCommand]
    confidence: float
    metadata: dict
```

**Verificação:** Todo agente DEVE aceitar `AgentInput` e retornar `AgentOutput`. Se usar schemas próprios, é violação do padrão.

### GA-1.3 ADR-002 — Graph vs. ReAct (Decisão Arquitetural)

| Cenário | Padrão Correto | Razão |
|---------|----------------|-------|
| Fluxo com steps definidos (wizard, interview, onboarding) | **Graph** (LangGraph StateGraph) | Previsível, auditável, testável |
| Raciocínio livre (chat, análise, recomendação) | **ReAct** (ReActLoop custom) | Flexível, iterativo |
| Operações CRUD simples | **REST direto** | Sem overhead de LLM |

**Verificação:** Se um agente ReAct tem fluxo previsível de steps, deveria ser Graph. Se um Graph precisa de raciocínio livre, deveria ser ReAct.

---

## GA-2. ANATOMIA OBRIGATÓRIA DO SYSTEM PROMPT — 10 Seções

Todo system prompt de agente ReAct DEVE conter estas 10 seções na ordem:

```
[1]  IDENTIDADE E PAPEL           ← quem é o agente, qual seu papel específico
[2]  PRINCÍPIOS INEGOCIÁVEIS      ← o que nunca pode fazer (compliance)
[3]  CONTEXTO DO STAGE ATUAL      ← o que está acontecendo agora
[4]  MEMÓRIA RELEVANTE            ← o que o agente já sabe desta sessão
[5]  FERRAMENTAS DISPONÍVEIS      ← injetado automaticamente pelo ReActLoop
[6]  PROTOCOLO REACT              ← como responder (JSON format)
[7]  CONTRA-ARGUMENTAÇÃO          ← anti-sycophancy: quando e como contra-argumentar
[8]  CALIBRAÇÃO                   ← benchmarks setoriais para validar pedidos do usuário
[9]  CONFIRMAÇÕES                 ← protocolo de confirmação antes de ações destrutivas
[10] EXEMPLOS FEW-SHOT            ← 2-3 exemplos de reasoning correto (incl. 1 bloqueio ético)
```

**Tamanho ideal:** 800-1500 tokens. Acima de 2000 tokens = custo desnecessário. Seções 7-9 podem ser condensadas em 3-5 linhas cada para manter o budget de tokens.

### GA-2.1 Template de Identidade (Seção 1)

```
Você é a LIA (Learning Intelligence Assistant), assistente de IA especialista em
[função específica do agente] da plataforma WeDOTalent.

Seu papel: [descrever o que este agente faz em 1-2 frases]
Seu estilo: consultivo, direto, baseado em dados — nunca vago ou evasivo
```

### GA-2.2 Princípios Inegociáveis Obrigatórios (Seção 2)

```
PRINCÍPIOS INEGOCIÁVEIS:
- Nunca discriminar candidatos por gênero, raça, idade, religião, orientação sexual,
  estado civil ou deficiência
- Sempre citar a base legal quando bloquear solicitação discriminatória
- Nunca inventar dados ou confirmar informações que não foram fornecidas
- Identificar-se como IA quando perguntado diretamente
- Responder em português brasileiro
```

### GA-2.3 Protocolo ReAct JSON (Seção 6)

```
PROTOCOLO DE RACIOCÍNIO — IMPORTANTE:

Para cada mensagem, analise o contexto e responda com JSON:
{
  "thought": "raciocínio estratégico PROFUNDO...",
  "action": "call_tool" | "respond" | "ask_clarification",
  "tool_name": "nome da ferramenta (null se action != call_tool)",
  "tool_args": { ... parâmetros da ferramenta ... },
  "response": "sua resposta ao usuário (null se chamando ferramenta)"
}

Regras de decisão:
- call_tool   → quando precisa de dados externos para responder bem
- respond     → quando tem informação suficiente para uma resposta útil
- ask_clarification → quando a pergunta é ambígua e precisa de mais contexto

Responda SOMENTE com o JSON. Sem markdown, sem texto extra.
```

### GA-2.4 Anti-Sycophancy (Seção 7)

```
CONTRA-ARGUMENTAÇÃO:
- Se o recrutador pedir algo que comprometa qualidade (ex: reduzir requisitos por urgência),
  contra-argumente com dados e benchmarks setoriais ANTES de executar
- 8 benchmarks de referência: ABRH, GPTW, Gupy, Robert Half, LinkedIn Economic Graph,
  Glassdoor, IBGE/PNAD, MTE/CAGED
- Divergências registradas na trilha de auditoria
- Nunca concordar silenciosamente com pedidos problemáticos
```

### GA-2.5 Confirmações (Seção 9)

```
CONFIRMAÇÕES:
- Ações destrutivas (rejeitar candidato, mover etapa, enviar comunicação)
  requerem confirmação explícita do usuário
- Palavras de confirmação aceitas: "sim", "pode", "confirmo", "vamos", "ok",
  "beleza", "perfeito", "positivo"
- Após primeira confirmação por padrão de ação, salvar preferência
  (anti-chatbot: não perguntar repetidamente)
```

### GA-2.6 Checklist de Verificação de Prompt

- [ ] Contém identidade clara (nome LIA + papel específico) — Seção 1
- [ ] Contém princípios inegociáveis de compliance — Seção 2
- [ ] Contém instruções de formato JSON ReAct — Seção 6
- [ ] Contém instruções de contra-argumentação (anti-sycophancy) — Seção 7
- [ ] Contém protocolo de confirmação para ações destrutivas — Seção 9
- [ ] Tamanho total: 800-1500 tokens (máximo absoluto: 2000)
- [ ] Contexto dinâmico vai em `extra_context`, NÃO no system prompt
- [ ] Não tem instruções vagas ("seja bom", "tente ajudar")
- [ ] Few-shot com 2-3 exemplos concretos (incluindo 1 de bloqueio ético)

---

## GA-3. ESTRUTURA YAML DE DOMÍNIO — Padrão Canônico

Cada domínio tem um YAML em `app/prompts/domains/` com esta estrutura obrigatória:

```yaml
persona:
  name: "LIA"
  role: "..."
  tone: "..."

scope_in:
  - "O que o agente DEVE fazer"

scope_out:
  - "O que o agente NÃO DEVE fazer"

behavioral_rules:
  - "Regras comportamentais"

system_prompt: |
  Prompt completo do agente

intent_examples:
  - input: "exemplo de mensagem"
    intent: "nome_da_intenção"
    domain: "nome_do_domínio"
```

**Verificação:**
- [ ] YAML existe para cada domínio ativo
- [ ] `scope_out` define claramente o que o agente NÃO faz
- [ ] `behavioral_rules` inclui regras de compliance
- [ ] `intent_examples` tem pelo menos 5 exemplos por intenção
- [ ] Carregado via `PromptLoader.load("domains/[nome]")`

---

## GA-4. INFRAESTRUTURA COMPARTILHADA — EnhancedAgentMixin

### GA-4.1 Componentes do Mixin

Todo agente herda `EnhancedAgentMixin`, que fornece automaticamente:

| Componente | Arquivo | Propósito |
|-----------|---------|-----------|
| WorkingMemory | `shared/agents/working_memory.py` | Histórico da sessão atual |
| LongTermMemory | `shared/agents/long_term_memory.py` | Learnings persistidos entre sessões |
| MemoryIntegration | `shared/agents/memory_integration.py` | Combina working + long-term em contexto |
| AutonomyEngine | `shared/agents/autonomy_engine.py` | Decide nível de autonomia por ação |
| LearningExtractor | `shared/agents/learning_extractor.py` | Extrai aprendizados após cada execução |
| Insight tools | `shared/tools/insight_tools.py` | Ferramentas de análise |
| Proactive tools | `shared/tools/proactive_tools.py` | Ferramentas proativas |
| Predictive tools | `shared/tools/predictive_tools.py` | Ferramentas preditivas |

**Verificação:**
- [ ] Agente chama `self._setup_enhanced(domain="[domain]")` no `__init__`
- [ ] Agente usa `self._get_memory_context()` antes de montar o prompt
- [ ] Agente chama `self._post_loop_learning()` após o loop
- [ ] Agente usa `self._get_all_enhanced_tools()` para tools adicionais

### GA-4.2 BaseAgent Interface

```python
class BaseAgent(ABC):
    @property
    @abstractmethod
    def domain_name(self) -> str: ...

    @property
    @abstractmethod
    def available_tools(self) -> List[str]: ...

    @abstractmethod
    async def process(self, input: AgentInput, db: AsyncSession) -> AgentOutput: ...
```

**Verificação:** Todo agente DEVE implementar estas 3 propriedades/métodos.

### GA-4.3 Memória em 3 Níveis

```
Sessão atual        → Working Memory    (StateManager, minutos/horas)
Cross-sessão        → Conversation Memory (PostgreSQL + pgvector, dias/semanas)
Permanente          → Long-Term Memory  (agent_long_term_memory, meses/anos)
                                          ↓
                      MemoryIntegration.get_enriched_context()
                      → "=== Session Memory ===" + "=== Cross-Session Learnings ==="
                      → Injetado no prompt do agente como extra_context
```

| Nível | Tabela/Store | Escopo | Similaridade mínima |
|-------|-------------|--------|---------------------|
| Working Memory | StateManager (in-memory) | Sessão (minutos/horas) | N/A |
| Conversation Memory | `conversation_memories` (pgvector) | Cross-sessão (dias/semanas) | 0.7 |
| Long-Term Memory | `agent_long_term_memory` | Permanente (meses/anos) | N/A |

**Long-Term Memory ranking:** `score = relevance × (usage_count + 1)`, `decay_factor = 0.95`

**Verificação:**
- [ ] Agente usa os 3 níveis de memória
- [ ] `company_id` presente em todas as queries de memória (multi-tenant)
- [ ] Conversation memory usa `embedding Vector(768)`
- [ ] Long-term memory tem `relevance_score` com decay

### GA-4.4 RAG Service

```python
augment_with_context(query, session_id, company_id)
```

| Fonte | Limite | Similaridade mínima |
|-------|--------|---------------------|
| Conversation History | 10 | — |
| Similar Messages | 5 | 0.7 |
| Knowledge Base | 5 | 0.6 |

---

## GA-5. DETERMINÍSTICO VS NÃO-DETERMINÍSTICO — Fronteira Obrigatória

### GA-5.1 Regra Arquitetural

**Padrão:** A IA fica no meio. As extremidades (entrada e saída) são SEMPRE determinísticas — controláveis, testáveis, auditáveis.

```
Mensagem do Recrutador / Candidato
          |
          v
[Router de Intenção — DETERMINÍSTICO]
  keyword matching → WizardIntent enum
          |
          v
[FairnessGuard Camada 1 — DETERMINÍSTICO]
  regex + léxico implícito
  Se bloqueado → retorna mensagem educativa (sem LLM)
          |
          v
[Agente ReAct LangGraph — NÃO-DETERMINÍSTICO]
  LLM → raciocínio, tool calls, resposta
          |
          v
[Guardrails de Saída — DETERMINÍSTICO]
  Score threshold check (APPROVAL_THRESHOLD = 60.0)
  Drift detection (4 triggers com limites fixos)
          |
          v
[Persistência + Auditoria — DETERMINÍSTICO]
  decision_log, bias_audit_snapshot, audit_log
```

### GA-5.2 Tabela de Decisão — Classificação por Componente

| Componente | Tipo | Arquivo | Razão |
|-----------|------|---------|-------|
| Detecção de intenção do Wizard | Determinístico | `wizard_orchestrator_service.py` | Keyword matching com lista fixa |
| FairnessGuard Camada 1 (regex) | Determinístico | `fairness_guard.py` | Regex compiladas, resultado binário |
| FairnessGuard Camada 2 (léxico) | Determinístico | `fairness_guard.py` | Dicionário `IMPLICIT_BIAS_TERMS` — lookup exato |
| Cálculo Four-Fifths Rule | Determinístico | `bias_audit_service.py` | `menor_taxa / maior_taxa >= 0.80` |
| Detecção de drift (4 triggers) | Determinístico | `model_drift_service.py` | Comparação de médias com threshold fixo |
| Score threshold de aprovação | Determinístico | `bias_audit_service.py` | `APPROVAL_THRESHOLD = 60.0` |
| Cache de avaliação por hash | Determinístico | `rubric_evaluation_service.py` | Hash MD5 dos campos estáveis |
| Scoring de competências WSI | Determinístico | `wsi_deterministic_scorer.py` | Funções puras sem LLM |
| Avaliação WSI de candidato | Não-determinístico | `rubric_evaluation_service.py` | LLM analisa CV + rubrica |
| Geração de feedback ao candidato | Não-determinístico | `personalized_feedback_service.py` | LLM redige texto personalizado |
| Resposta da LIA em chat | Não-determinístico | Todos os agentes ReAct | Raciocínio livre do modelo |
| FairnessGuard Camada 3 (LLM) | Não-determinístico | `fairness_guard.py` | LLM detecta viés sutil — opt-in |

**Verificação:**
- [ ] Decisões de rejeição usam componente determinístico (threshold, não LLM puro)
- [ ] Routing de intenção é determinístico (keyword matching, não LLM)
- [ ] FairnessGuard Camadas 1 e 2 são determinísticas
- [ ] Componentes não-determinísticos têm guardrails de saída determinísticos

---

# ANEXO B: GABARITO DE ANTI-PADRÕES — O QUE NUNCA FAZER

O auditor deve verificar a AUSÊNCIA destes anti-padrões em todo o código auditado. Cada anti-padrão encontrado é classificação FALHA.

---

## AP-1. Anti-Padrões de Agentes IA

| # | Anti-Padrão | Razão | Severidade |
|---|-------------|-------|-----------|
| AP-1.1 | Sync functions em tools do agente | Tools devem ser `async`. O ReActLoop usa `await tool_def.function(**args)` | Alto |
| AP-1.2 | Retornar dados brutos sem campo `"success"` | Todo tool DEVE retornar `{"success": True/False}`. Erro: `{"success": False, "error": "msg"}` | Alto |
| AP-1.3 | Loop infinito — tool chamando o próprio agente | `REACT_DUPLICATE_THRESHOLD=3` protege, mas evitar tools que disparam outros agentes no mesmo loop | Crítico |
| AP-1.4 | Prompt sem instruções de formato de saída | Loop espera JSON com `thought/action/tool_name/tool_args/response`. Sem isso, `_parse_reasoning()` falha | Crítico |
| AP-1.5 | System prompt > 4000 tokens | Aumenta custo e latência. Usar `extra_context` para contexto dinâmico | Médio |
| AP-1.6 | Agente sem observer | Sem `ReActObserver`, não há telemetria, debugging ou rastreabilidade | Alto |
| AP-1.7 | `max_iterations > 10` | Custo explode. Se precisa > 5 iterações na média, reconsiderar arquitetura para Graph | Médio |

## AP-2. Anti-Padrões de Compliance

| # | Anti-Padrão | Razão | Severidade |
|---|-------------|-------|-----------|
| AP-2.1 | Logar texto original de queries de candidatos | LGPD: logar apenas hash SHA-256. Texto pode conter dados pessoais | Crítico |
| AP-2.2 | Retornar dados individuais em bias audit | Apenas estatísticas agregadas (LGPD Art. 12 — dados anonimizados) | Crítico |
| AP-2.3 | Permitir filtros discriminatórios sem FairnessGuard | Todo input que vai para busca/filtro de candidatos DEVE passar por `check()` | Crítico |
| AP-2.4 | Desativar guardrails em produção | Guardrails mandatórios para BCB 498, ISO 27001 | Crítico |
| AP-2.5 | Email de candidato sem `AI_GENERATED_FOOTER` | Requisito LGPD + EU AI Act. `ai_generated=True` aplica automaticamente | Alto |

## AP-3. Anti-Padrões de Multi-Tenancy

| # | Anti-Padrão | Razão | Severidade |
|---|-------------|-------|-----------|
| AP-3.1 | Query sem filtro `company_id` | Cross-tenant data leak. SEMPRE: `.where(Model.company_id == company_id)` | Crítico |
| AP-3.2 | `session_id` sem `company_id` no namespace | Sessões DEVEM incluir: `f"{company_id}:{session_id}"` | Alto |
| AP-3.3 | State compartilhado entre empresas | WorkingMemory, LongTermMemory, GuardrailRepository — TODOS scopeados por `company_id` | Crítico |
| AP-3.4 | Admin API sem verificação de super-admin role | Endpoints `/api/v1/admin/*` DEVEM verificar role | Alto |

## AP-4. Anti-Padrões de Código

| # | Anti-Padrão | Razão | Severidade |
|---|-------------|-------|-----------|
| AP-4.1 | Importar modelos SQLAlchemy fora de services/repositórios | Routers só falam com services. Services falam com DB | Médio |
| AP-4.2 | `await` no `__init__` | Python não suporta. Usar async classmethods ou factory pattern | Alto |
| AP-4.3 | Global state em services | FastAPI instancia services uma vez. State global = problemas em multiprocess | Alto |
| AP-4.4 | `except Exception: pass` (silently swallow) | Compliance e debugging dependem de logs. SEMPRE: `except Exception as e: logger.error(...)` | Alto |
| AP-4.5 | Hardcoded `company_id` em testes | Usar fixture com UUID: `company_id = str(uuid.uuid4())` | Médio |
| AP-4.6 | f-strings em queries SQL | SQL injection. Usar parâmetros SQLAlchemy: `.where(Model.name == name)` | Crítico |
| AP-4.7 | Commitar `.env` com secrets | `.env` no `.gitignore`. Usar `.env.example` com placeholders | Crítico |

## AP-5. Anti-Padrões de Arquitetura

| # | Anti-Padrão | Razão | Severidade |
|---|-------------|-------|-----------|
| AP-5.1 | ReAct para fluxos com steps definidos | Usar Graph (LangGraph StateGraph). ReAct é para raciocínio livre | Alto |
| AP-5.2 | LLM para operações CRUD simples | CRUD = REST direto. LLM só onde há raciocínio, classificação ou geração | Médio |
| AP-5.3 | Chamada LLM síncrona em endpoint REST | LLMs levam 2-10s. Usar Celery task + WebSocket para progresso | Alto |
| AP-5.4 | Memória de agente ilimitada | WorkingMemory tem limite. `conversation_history[-5:]` | Médio |
| AP-5.5 | Um agente faz tudo | Separação de domínios obrigatória. Agentes se comunicam via `AgentInput/AgentOutput` | Alto |

---

# ANEXO C: GABARITO DE OBSERVABILIDADE E MONITORAMENTO

---

## OBS-1. Schemas de Observabilidade

### OBS-1.1 AgentExecutionLog — Schema Obrigatório

```python
class AgentExecutionLog:
    session_id: str
    domain: str
    agent_class: str
    company_id: Optional[str]
    user_id: Optional[str]
    start_time: str
    end_time: Optional[str]
    total_duration_ms: float
    total_iterations: int
    tools_called: list
    tools_succeeded: int
    tools_failed: int
    final_confidence: float
    model_provider: str
    iterations: list[IterationLog]

class IterationLog:
    iteration: int
    timestamp: str
    phase: str           # "thinking" | "acting" | "observing"
    duration_ms: float
    tool_name: Optional[str]
    tool_args: Optional[dict]
    tool_success: Optional[bool]
    reasoning: Optional[str]
    observation: Optional[str]  # truncado em REACT_OBSERVATION_MAX_CHARS=5000
    decision: Optional[str]
    error: Optional[str]
```

**Verificação:**
- [ ] Todo agente gera `AgentExecutionLog` completo
- [ ] `company_id` e `user_id` presentes nos logs
- [ ] `iterations` lista cada passo do ReAct loop
- [ ] `reasoning` NÃO é truncado (ver gap `decision_final`)

### OBS-1.2 Métricas Prometheus

| Métrica | Tipo | Onde |
|---------|------|------|
| `agent_iterations_total` | Counter | `react_loop.py` — por domínio/status |
| `router_tier_hit_total` | Counter | CascadedRouter — hits por tier |
| `router_latency_ms` | Histogram | CascadedRouter — latência por tier |
| `router_confidence_histogram` | Histogram | Distribuição de confiança |
| `fairness_blocks_total` | Counter | Bloqueios por categoria |
| `circuit_breaker_state` | Gauge | Estado dos circuit breakers |

### OBS-1.3 Dashboard de Saúde de Agentes

```python
await get_domain_health(db, company_id)
```

| Status | Critério |
|--------|---------|
| `healthy` | confiança >= 0.8, erro < 5% |
| `warning` | confiança >= 0.6 ou erro < 15% |
| `degraded` | confiança < 0.6 ou erro >= 15% |
| `stale` | sem execuções nas últimas 24h |

**Endpoints:**
- `GET /api/v1/agent-monitoring/domains/health`
- `GET /api/v1/agent-monitoring/domains/{domain}/metrics`

**Verificação:**
- [ ] Dashboard acessível via Admin UI
- [ ] Status calculado corretamente por domínio
- [ ] Alerta automático em `degraded` ou `stale`

## OBS-2. Drift Detection — 4 Triggers

| Trigger | Descrição | Tipo |
|---------|----------|------|
| `score` | Score médio de candidatos cai abaixo do baseline | Threshold configurável |
| `aprovação` | Taxa de aprovação diverge do histórico | Threshold configurável |
| `custo` | Custo por request LLM aumenta acima do esperado | Threshold configurável |
| `latência` | P95 de latência ultrapassa limite | Threshold configurável |

**Alertas automáticos:**
- 1 trigger → WARNING → Bell in-app + Teams
- 2+ triggers → URGENT → Bell in-app + Teams

**Verificação:**
- [ ] `model_drift_service.py` monitora os 4 triggers
- [ ] Celery Beat roda `drift.run_batch` diariamente às 06h Brasília
- [ ] Alertas via `drift_alert_service.py` funcionam

## OBS-3. AgentQualityEvaluator — Avaliação Contínua

**5 métricas avaliadas via LLM-as-judge (Claude Haiku):**

| Métrica | O que mede |
|---------|-----------|
| `task_completion` | Task solicitada foi executada completamente? |
| `factual_accuracy` | Afirmações verificáveis? Sem alucinações? |
| `fairness` | Livre de viés discriminatório? |
| `coherence` | Coerente com contexto e histórico? |
| `actionability` | Oferece próximos passos acionáveis? |

**Configuração:** `QUALITY_EVAL_SAMPLING_RATE` (default 10%)

**Verificação:**
- [ ] Sampling ativo em produção
- [ ] Scores persistidos em `agent_quality_evaluations` (JSONB)
- [ ] LangSmith integrado para avaliação contínua em staging

## OBS-4. AgentHealthAlertService — Alertas de Falha

| Threshold | Ação |
|-----------|------|
| 3 falhas consecutivas | WARNING → Bell in-app + Teams |
| 5 falhas consecutivas | CRITICAL → Bell in-app + Teams |
| Qualquer sucesso | Contador resetado |

**Storage:** Redis sliding window TTL=30min (fallback: in-memory dict)
**Chave:** `agent_failures:{company_id}:{agent_id}`

**Verificação:**
- [ ] `record_failure()` e `record_success()` chamados em cada execução
- [ ] Alertas disparam corretamente nos thresholds
- [ ] Redis key tem TTL configurado

---

# ANEXO D: GABARITO DE GUARDRAILS EM BANCO DE DADOS

---

## GR-1. Modelo de Guardrail

```python
class Guardrail(Base):
    __tablename__ = "guardrails"
    id              = Column(UUID, primary_key=True)
    level           = Column(String(20))     # "primary" | "secondary"
    domain          = Column(String(50))     # NULL = todos os domínios
    node            = Column(String(50))     # NULL = todos os nós
    tool            = Column(String(50))     # NULL = todas as tools
    rule            = Column(Text)           # Regra em linguagem natural
    blocking_message = Column(Text)          # Mensagem se bloqueado
    is_active       = Column(Boolean)
    company_id      = Column(UUID)           # NULL = global
    updated_by      = Column(String)
    updated_at      = Column(TIMESTAMP)
```

## GR-2. Prioridade de Carregamento (3-tier)

```
1. Guardrails primários globais (domain=None, company_id=None)
2. Guardrails primários do tenant
3. Guardrails secundários globais do domínio
4. Guardrails secundários do tenant para o domínio
```

## GR-3. Seed Inicial — 13 Guardrails Obrigatórios

**6 guardrails primários (globais — LGPD/fairness):**
1. "Nunca revelar informações pessoais de candidatos não compartilhadas explicitamente"
2. "Nunca discriminar por gênero, raça, idade, religião ou estado civil"
3. "Sempre identificar comunicação gerada por IA quando solicitado"
4. "Nunca criar perguntas que impliquem questões familiares, filhos ou vida pessoal"
5. "Não tomar decisões finais de rejeição sem revisão humana habilitada"
6. "Registrar auditoria completa de todas as avaliações automatizadas"

**7 guardrails secundários (por domínio):**
1. `wsi_interviewer`: "Perguntas exclusivamente sobre competências profissionais"
2. `wsi_interviewer`: "Não interromper candidato durante resposta"
3. `communication`: "Todo email deve incluir identificação de IA no rodapé"
4. `sourcing`: "Não contatar candidatos já recusados nos últimos 6 meses"
5. `pipeline`: "Gate humano obrigatório antes de rejeição em massa"
6. `analytics`: "Nunca expor dados individuais em relatórios agregados"
7. `policy`: "Alterações em políticas requerem confirmação explícita do usuário"

**Verificação:**
- [ ] Todos os 13 guardrails existem no banco
- [ ] Guardrails primários aplicados a TODOS os domínios
- [ ] Guardrails secundários filtrados por domínio
- [ ] API CRUD funcional (`GET/POST/PUT/PATCH /api/v1/guardrails`)
- [ ] Admin UI permite edição sem deploy

---

# ANEXO E: GABARITO DE COMPLIANCE — TAXONOMIA DE GAPS

Esta seção consolida os gaps conhecidos do diagnóstico de compliance para referência do auditor.

---

## CG-1. Gap Crítico (P0)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-M1 | PII não mascarada nos prompts ao LLM | PII Masking | Dados de candidatos (nome, CPF, email) enviados ao provider. Violação LGPD Art. 6 |

## CG-2. Gaps Altos (P1)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-P1 | Ausência de instrução EU AI Act nos prompts | Prompts | Não-conformidade com EU AI Act para clientes europeus |
| G-F1 | Camada 3 semântica não integrada no workflow | FairnessGuard | Vieses reformulados/sutis podem passar |
| G-C1 | Sem escalação humana no fluxo principal | Confiança | EU AI Act Art. 14 requer human oversight |
| G-M2 | Sem blind review pré-LLM | PII/Fairness | Atributos protegidos no prompt — proteção depende do LLM |
| G-M3 | Sem módulo de remoção de atributos protegidos | PII/Fairness | Nenhuma função dedicada para anonymizar candidato |
| G-RL1 | ReAct loop não aplica FairnessGuard na saída | FairnessGuard | Respostas geradas pelo loop podem conter viés |

## CG-3. Gaps Médios (P2)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-R1 | Silent fallback para recruiter_assistant | Router | Roteamento potencialmente incorreto |
| G-P2 | Ausência de instrução de explicabilidade | Prompts | Decisões sem justificativa estruturada |
| G-F2 | `log_check()` não chamado automaticamente | FairnessGuard | Auditoria de fairness incompleta |
| G-C2 | Confidence scoring heurístico | Confiança | Scores não calibrados |
| G-C3 | ConfidencePolicyService limitado ao Wizard | Confiança | Decisões de triagem sem política de confiança |
| G-CB1 | Sem alerting quando circuit abre | Resiliência | Degradação sem notificação |
| G-RL2 | Resposta do ReAct sem PII scrubbing | PII | Dados de candidato na resposta |
| G-FC1 | FactChecker não consulta dados reais | FactChecker | Verificação contra ranges estáticos |

## CG-4. Gaps Baixos (P3)

| # | Gap | Componente | Impacto |
|---|-----|-----------|---------|
| G-R2 | Cache key MD5 | Router | Risco teórico de colisão |
| G-P3 | Persona do Orchestrator simplificada | Prompts | Fallback sem diretrizes éticas completas |
| G-F3 | Cobertura de idiomas limitada | FairnessGuard | Relevante para expansão internacional |
| G-CB2 | Duas implementações de circuit breaker | Resiliência | Complexidade de manutenção |
| G-FC2 | FactChecker ausente no ReAct loop direto | FactChecker | Respostas LangGraph nativo sem fact-check |
| G-RL3 | Sem rate limiting por sessão | ReAct Loop | Potencial abuso por sessão |

## CG-5. Bloqueadores de Produção Remanescentes

| Gap | Localização | Urgência |
|-----|------------|----------|
| `decision_final` truncada em 500 chars | `observability.py` | Crítico |
| Frontend: mock data residual em algumas páginas | FE | Média |
| Operações longas em lote sem queue dedicada | Celery/WS | Média |
| Few-shot T3 sem exemplos de RH sênior | `orchestrator/examples/` | Alta |
| `MAX_TOOL_CALLS_PER_REQUEST` hardcoded | `llm.py:26` | Alta |
| Cascata de confiança T3 não automática | `intent_router.py` | Alta |
| Auto-confirm por usuário (anti-chatbot) | `pending_action.py` | Alta |
| Sem testes de integração de agentes | `tests/agents/` | Alta |

## CG-6. Recomendações Priorizadas

### Prioridade 1 — Crítico (Implementar imediatamente)

| # | Recomendação |
|---|-------------|
| R1 | Implementar PII masking nos prompts enviados ao LLM (G-M1). Criar módulo `prompt_pii_filter` que remove/mascara CPF, email, telefone antes de montar o prompt |

### Prioridade 2 — Alto (Implementar em 30 dias)

| # | Recomendação |
|---|-------------|
| R2 | Implementar blind review: criar `candidate_anonymizer` que remove nome, idade, foto e gênero inferido antes de prompts de triagem/ranking (G-M2, G-M3) |
| R3 | Integrar `check_semantic()` no `DomainWorkflow._pre_check()` para queries com soft_warnings (G-F1) |
| R4 | Integrar `HumanReviewSamplingService.should_flag_for_review()` no `DomainWorkflow._execute()` (G-C1) |
| R5 | Adicionar FairnessGuard check na SAÍDA do ReAct loop (G-RL1). Aplicar `check_implicit_bias()` na resposta final |
| R6 | Adicionar instruções EU AI Act nos prompts éticos (G-P1). Referenciar Art. 14, 52, Anexo III |

### Prioridade 3 — Médio (Implementar em 60 dias)

| # | Recomendação |
|---|-------------|
| R7 | Automatizar `FairnessGuard.log_check()` dentro do `DomainWorkflow` (G-F2) |
| R8 | Expandir `ConfidencePolicyService` para decisões de triagem (G-C3) |
| R9 | Adicionar alerting via webhook/email quando circuit breaker abre (G-CB1) |
| R10 | Conectar FactChecker a dados reais do banco para validação de contagens (G-FC1) |
| R11 | Adicionar PII scrubbing na resposta do ReAct loop (G-RL2) |

---

# ANEXO F: GABARITO DE PIPELINE E COMPLIANCE DE PROCESSAMENTO

---

## PL-1. DomainWorkflow — Pipeline de Processamento (7 Etapas)

```
PRE_CHECK (FairnessGuard) →
  RESOLVE_REFERENCES (pronomes/contexto) →
    SMART_EXTRACT (regex params) →
      ANALYZE_INTENT (domínio classifica) →
        EXECUTE (ReAct agent ou heurística) →
          FORMAT (metadata + sugestões) →
            POST_CHECK (FactChecker)
```

**Verificação:**
- [ ] FairnessGuard aplicado na entrada (PRE_CHECK)
- [ ] FactChecker aplicado na saída (POST_CHECK)
- [ ] Learning loop (`record_interaction`) ativo
- [ ] Dual-path: ReAct agent OU heurística (decisão automática)
- [ ] Execution log completo em cada etapa

## PL-2. Human Review Sampling (5% LGPD)

```python
HUMAN_REVIEW_SAMPLING_RATE = 0.05  # 5% das avaliações
```

- Determinístico por MD5 hash — mesma decisão sempre cai na mesma categoria
- ALWAYS_REVIEW: `finalize_hiring`, `mass_rejection`, `fairness_flagged`
- Requisito: LGPD Art. 20 (direito à revisão humana em decisões automatizadas)

**Verificação:**
- [ ] Sampling ativo para avaliações automáticas
- [ ] `requires_human_review=True` flag aplicada
- [ ] Notificação ao recrutador para revisão manual
- [ ] Decisões `ALWAYS_REVIEW` NUNCA passam sem revisão humana

## PL-3. LGPD — Implementações Ativas

| Implementação | Arquivo | Status |
|--------------|---------|--------|
| Footer de IA em emails | `email_adapter.py` → `AI_GENERATED_FOOTER` | Automático quando `ai_generated=True` |
| Consentimento email providers | `communication_settings.py` → `DATA_SHARING_EMAIL_PROVIDERS` | Ativo |
| Consentimento SMS providers | `communication_settings.py` → `DATA_SHARING_SMS_PROVIDERS` | Ativo |
| Consentimento comunicações IA | `communication_settings.py` → `AI_GENERATED_COMMUNICATIONS` | Ativo |
| Data Retention cleanup | `data_retention_job.py` → Celery 05h | Ativo |
| DSR Notifications (SLA 15 dias) | `data_request_service.py` | Ativo |

## PL-4. Compliance Enterprise (BCB 498 / SOX / ISO 27001)

| Componente | Arquivo |
|-----------|---------|
| Controles SOX/ISO | `app/api/v1/compliance_controls.py` |
| Logs de auditoria | `app/api/v1/audit_logs.py` |
| Trust center portal | `app/api/v1/trust_center.py` |
| Snapshots auditáveis | `app/models/bias_audit_snapshot.py` |
| Serviço de auditoria | `app/shared/compliance/audit_service.py` |

---

# ANEXO G: GABARITO DE BENCHMARKING — ONDE ESTAMOS VS. ESTADO DA ARTE 2026

---

## BM-1. Comparativo com Estado da Arte

| Padrão | Onde LIA usa | Estado da Arte (referência) | Status |
|--------|-------------|----------------------------|--------|
| ReAct Loop | `shared/agents/react_loop.py` (custom) | LangGraph ReAct (built-in), OpenAI Assistants API | OK |
| LangGraph StateGraph | `job_wizard_graph.py`, `wsi_interview_graph.py`, `interview_graph.py` | Standard para fluxos previsíveis | OK |
| Multi-agent routing | `orchestrator.py` + domain registry | Anthropic Multi-Agent + OpenAI Swarm | OK |
| Memory (3 camadas) | Working + Conversation + Long-term | Mem0, LangMem | OK |
| Tool calling | Claude `tool_use` + função registrada | MCP (Model Context Protocol) — futuro | OK |
| Guardrails | DB-based (migration 020 + API + UI) | NeMo Guardrails (NVIDIA), Guardrails AI | OK |
| Observabilidade | LangSmith + Prometheus + AgentQualityEvaluator | LangSmith, Helicone, Braintrust | OK |
| Avaliação de agentes | `agent_quality_evaluator.py` (custom, LLM-as-judge) | Ragas, DeepEval, HELM | Custom |
| Cascata de confiança T3 | Manual (3 providers, sem threshold auto) | Threshold automático por confidence | Pendente |
| Monorepo | UV workspaces (`libs/` + `app/`) | Standard Python ML repos | OK |

## BM-2. Comparativo com Paradox (Olivia) — Referência WSI

| Feature | Paradox | LIA Status |
|---------|---------|-----------|
| Entrevista conversacional via WhatsApp | Implementado | `wsi_interview_graph.py` cobre; integração direta WA pendente |
| Score automático pós-entrevista | Implementado | `wsi_deterministic_scorer.py` — OK |
| Persistência entre sessões | Implementado | WorkingMemory existe; integração WA pendente |
| Identificação de IA na 1ª msg | Implementado | Implementado |
| Fallback humano | Implementado | `PendingActionState` existe; fluxo completo pendente |

---

# ANEXO H: CHECKLIST DE PRONTIDÃO PARA PRODUÇÃO (18 Critérios)

---

## PR-1. Checklist por Agente

- [ ] Segue padrão 4 arquivos (`react_agent` + `tool_registry` + `system_prompt` + `stage_context`)?
- [ ] `company_id` + `user_id` presentes em todos os traces?
- [ ] Decisão final **não truncada** (remover limite de 500 chars)?
- [ ] Guardrails primários aplicados (via banco de dados)?
- [ ] Guardrails secundários de domínio configurados?
- [ ] Fallback de LLM configurado (Claude → OpenAI/Gemini)?
- [ ] Fallback manual disponível (usuário pode fazer sem LIA)?
- [ ] Timeout por iteração/nó configurado?
- [ ] Persistência de estado para agentes de longa duração (LangGraph + checkpointer)?
- [ ] `AgentHealthAlertService.record_failure/success()` integrado?
- [ ] `AgentQualityEvaluator.evaluate_if_sampled()` integrado?

## PR-2. Checklist por Integração Externa

- [ ] Rate limiting respeitado?
- [ ] Retry com exponential backoff?
- [ ] Circuit breaker para serviços críticos?
- [ ] Custo monitorado (tokens, créditos Pearch, WhatsApp messages)?
- [ ] Identificação de IA em comunicações externas?

## PR-3. Checklist do Sistema Completo

| Critério | Status Esperado |
|---------|----------------|
| Guardrails no banco (API + migration 020) | Implementado |
| AgentHealthAlertService (Bell + Teams) | Implementado |
| AgentQualityEvaluator (10% sampling) | Implementado |
| WebSocket com streaming | Implementado |
| Drift detection (4 triggers, Celery beat diário) | Implementado |
| Load tests com cenários reais | Implementado |
| LangSmith ativo em staging | Implementado |
| Prompts consolidados em `app/shared/prompts/` | Implementado |
| `decision_final` sem truncamento | Pendente — Crítico |
| Few-shot T3 validado com profissional de RH | Pendente |
| Cascata de confiança T3 automática | Pendente |
| Frontend sem mock data residual | Pendente |
| Teste ponta a ponta completo | Pendente |
| Cláusula LGPD email nos Termos de Uso | Pendente |
| Red team formal FairnessGuard (< 1% jailbreak) | Pendente |

---

# ANEXO I: GABARITO DE TROUBLESHOOTING DE AGENTES

---

## TS-1. Problemas Mais Comuns e Soluções

### TS-1.1 Loop Infinito (agente não responde)

| Item | Detalhe |
|------|---------|
| Sintoma | Agente chama a mesma ferramenta repetidamente sem parar |
| Causa | Tool retorna `{"success": False}` repetidamente e agente não muda de estratégia |
| Proteção | `state.consecutive_duplicate_count` (limite: `REACT_DUPLICATE_THRESHOLD=3`) |
| Debug | 1. Verificar se tool retorna `"success"` corretamente. 2. Adicionar logging no tool |

### TS-1.2 Resposta Genérica / Sem Conteúdo

| Item | Detalhe |
|------|---------|
| Sintoma | Agente responde "Desculpe, não consegui processar..." em loop |
| Causa A | `_parse_reasoning()` falhou — LLM não retornou JSON válido |
| Causa B | `max_iterations` atingido sem resposta útil |
| Debug | 1. `LANGCHAIN_TRACING_V2=true` para trace. 2. `grep "Failed to parse reasoning"`. 3. Verificar temperatura (< 0.7) |

### TS-1.3 Tool Não Encontrada

| Item | Detalhe |
|------|---------|
| Sintoma | Log "Unknown tool requested: [nome]" |
| Causa | Nome no reasoning diferente do registrado em `ToolDefinition` |
| Debug | 1. Comparar `tool.name` no registry. 2. Verificar `get_stage_tools()` para o stage atual |

### TS-1.4 Guardrail Bloqueando Ação Legítima

| Item | Detalhe |
|------|---------|
| Sintoma | "Requires user confirmation before executing [tool]" |
| Causa | Tool listada em `config.guardrails` (requer confirmação) |
| Debug | 1. `GuardrailRepository.get_active()`. 2. Remover do guardrails se desnecessário |

### TS-1.5 Timeout LLM

| Item | Detalhe |
|------|---------|
| Sintoma | "LLM call timed out after 30s" |
| Causa A | Modelo sobrecarregado |
| Causa B | Prompt muito longo (> 8000 tokens) |
| Solução | 1. Reduzir `extra_context`. 2. `conversation_history[-5:]`. 3. `LLM_TIMEOUT_SECONDS=60` |

## TS-2. LangSmith para Debug Operacional

```
1. Configurar:
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=ls__...
   LANGCHAIN_PROJECT=lia-agent-system

2. Todos os ReAct loops decorados com @traceable via react_loop.py

3. No LangSmith:
   - Filtrar por session_id ou company_id
   - Ver trace completo: prompt → reasoning → tool calls → response
   - Identificar iterações desnecessárias (custo)
   - Comparar quality scores entre versões de prompt
```

## TS-3. Triagem Estruturada de Logs

```
1. Verificar health de agentes:
   GET /api/v1/agent-monitoring/domains/health
   → Identifica domínios degraded/stale

2. Verificar drift:
   GET /api/v1/drift/status
   → Identifica triggers ativos (score, aprovação, custo, latência)

3. Verificar circuit breakers:
   GET /api/v1/admin/circuit-breakers/status
   → Identifica serviços externos com falha

4. Grep nos logs:
   grep "Failed to parse reasoning" → problemas de formato
   grep "Unknown tool requested"   → tools mal registradas
   grep "LLM call timed out"       → timeouts
   grep "circuit_breaker_open"     → serviços indisponíveis
```

---

# ANEXO J: GABARITO DE MONOREPO E ESTRUTURA DE LIBS

---

## MR-1. Arquitetura de Libs (Monorepo UV)

As implementações reais residem em `libs/`. O diretório `app/shared/` contém shims (re-exports). Ao auditar, SEMPRE verificar a lib, não o shim.

```
libs/
├── agents-core/lia_agents_core/   ← IMPLEMENTAÇÕES REAIS
│   ├── langgraph_base.py           ← LangGraphBase._run_graph() com AuditCallback
│   ├── langgraph_react_base.py     ← LangGraphReActBase._process_langgraph()
│   ├── react_agent_registry.py     ← ReactAgentRegistry singleton
│   └── ...
├── audit/lia_audit/               ← AuditCallback, AuditWriter, AuditStorage
├── models/lia_models/             ← guardrail.py, e outros modelos compartilhados
├── messaging/lia_messaging/       ← NotificationService, EmailAdapter
└── config/                        ← Settings, database, Redis
```

### MR-1.1 Infraestruturas Compartilhadas

| Serviço | Arquivo | Propósito |
|---------|---------|-----------|
| PII Masking | `shared/pii_masking.py` | Remove PII de logs |
| Prompt Injection Guard | `shared/prompt_injection.py` | Detecta tentativas de injection |
| FactChecker | `shared/compliance/fact_checker.py` | Verifica fatos em avaliações |
| AuditService | `shared/compliance/audit_service.py` | Log de auditoria SOX |
| EmbeddingService | `shared/intelligence/embedding_service.py` | Embeddings via pgvector |
| SemanticSearch | `shared/intelligence/semantic_search_service.py` | Busca semântica |
| LearningLoop | `shared/learning/learning_loop_service.py` | Feedback implícito |
| ABTesting | `shared/learning/ab_testing_service.py` | Testes A/B de prompts |
| CircuitBreaker | `shared/resilience/circuit_breaker.py` | Protege chamadas externas |

### MR-1.2 Prompts — Hierarquia Canônica

```
app/shared/prompts/                  ← FONTE DE VERDADE
├── loader.py                        ← PromptLoader — carrega YAMLs
├── templates.py                     ← PromptTemplate, PromptLibrary
├── cot.py                           ← ChainOfThoughtBuilder, CoTStrategy
├── few_shot_examples.py             ← FewShotExamples + constantes
├── agent_prompts.py                 ← system prompts compartilhados
├── prompt_registry.py               ← registro central de templates
└── examples/                        ← exemplos por domínio

app/domains/*/agents/*_system_prompt.py  ← PADRÃO CANÔNICO por agente

app/prompts/                         ← SHIMS (não modificar)
└── domains/                         ← YAMLs de domínio
```

**Verificação:**
- [ ] Imports usam `app.shared.prompts` (não `app.prompts` legado)
- [ ] System prompts por agente em `app/domains/*/agents/*_system_prompt.py`
- [ ] YAMLs de domínio em `app/prompts/domains/`
- [ ] Shims intactos (não modificados)

---

# ANEXO K: MELHORES PRÁTICAS DE MERCADO — CRITÉRIOS DE AVALIAÇÃO

> O auditor deve usar esta seção para avaliar não apenas se o código segue os padrões internos, mas se está alinhado com as melhores práticas de mercado em IA para recrutamento.

---

## MP-1. Frameworks Regulatórios e Standards Aplicáveis

### MP-1.1 Frameworks Obrigatórios

| Framework | Aplicação | Critérios-chave para Auditoria |
|-----------|-----------|-------------------------------|
| **EU AI Act (2024)** | Sistemas de IA em recrutamento = Alto Risco (Anexo III) | Art. 14: human oversight obrigatório; Art. 52: transparência; Art. 9: risk management; Art. 10: data governance; FRIA obrigatória |
| **LGPD (Brasil)** | Todo processamento de dados de candidatos | Art. 6: finalidade/adequação/necessidade; Art. 12: dados anonimizados; Art. 18: direitos do titular; Art. 20: revisão humana em decisões automatizadas |
| **EEOC / Title VII (EUA)** | Clientes americanos | Four-fifths rule (Adverse Impact); disparate impact analysis; ADA compliance em assessments |
| **NIST AI RMF 1.0** | Voluntário, referência de mercado | Govern, Map, Measure, Manage — 4 funções; categorização de riscos; teste de viés contínuo |
| **ISO/IEC 42001:2023** | Certificação de gestão de IA | Sistema de gestão de IA; avaliação de riscos; monitoramento contínuo; documentação de decisões |
| **SOC 2 Type II** | Clientes enterprise | Segurança, disponibilidade, integridade de processamento, confidencialidade, privacidade |

### MP-1.2 Checklist de Compliance Regulatório

- [ ] FRIA (Fundamental Rights Impact Assessment) documentada para o WSI
- [ ] Candidate Anonymization antes de enviar dados ao LLM (blind review)
- [ ] Human-in-the-loop em todas as decisões de rejeição
- [ ] Opt-out disponível para avaliação por IA
- [ ] Explicabilidade: "Por que fui rejeitado?" respondível com trace auditável
- [ ] Data minimization nos prompts enviados ao LLM
- [ ] Consentimento granular para comunicações automatizadas
- [ ] Retenção de dados com prazos definidos e cleanup automático
- [ ] Right to erasure (LGPD Art. 18) implementado e testado
- [ ] AI disclosure em todas as comunicações geradas por IA

## MP-2. Melhores Práticas de Engenharia de Agentes IA

### MP-2.1 Arquitetura de Agentes (Estado da Arte 2026)

| Prática | Descrição | Status Esperado | Como Verificar |
|---------|-----------|----------------|----------------|
| Multi-agent orchestration | Agentes especializados por domínio com orquestrador central | Implementado | Verificar `orchestrator.py` + domain registry |
| Tool calling nativo | Usar APIs nativas do modelo (Claude tool_use, GPT function_calling) | Implementado | Verificar se tools usam formato nativo do provider |
| MCP (Model Context Protocol) | Protocolo padronizado de contexto — futuro próximo | Monitorar | Avaliar roadmap de migração |
| Structured output / JSON mode | Forçar formato JSON na saída do LLM | Implementado | Verificar `_parse_reasoning()` + fallback |
| Streaming responses | Respostas em tempo real via WebSocket/SSE | Implementado | Verificar `agent_chat_ws.py` |
| Guardrails-as-code em banco | Guardrails editáveis sem deploy | Implementado | Verificar migration 020 + Admin UI |
| LLM evaluation framework | Avaliação contínua via LLM-as-judge | Implementado (custom) | Verificar `AgentQualityEvaluator` — considerar migrar para Ragas/DeepEval |
| Observability integrada | Tracing + métricas + alertas automáticos | Implementado | Verificar LangSmith + Prometheus + health alerts |
| Memory management | Memória em camadas (sessão, cross-sessão, permanente) | Implementado | Verificar os 3 níveis e decay factor |
| Graceful degradation | Fallback chain de LLM + modo sem IA | Parcial | Verificar fallback Claude→OpenAI→Gemini + manual fallback |

### MP-2.2 Padrões de Prompt Engineering (Referência Mercado)

| Prática | Descrição | Como Verificar no Código |
|---------|-----------|--------------------------|
| Role-based prompting | System prompt com papel claro e limitado | Verificar seção [1] do prompt |
| Few-shot examples | 2-3 exemplos concretos incluindo edge cases | Verificar seção [10] + `few_shot_examples.py` |
| Chain-of-Thought (CoT) | Forçar raciocínio explícito antes da resposta | Verificar campo `"thought"` no JSON de saída |
| Output schema enforcement | Schema JSON definido e validado | Verificar `_parse_reasoning()` |
| Negative examples | Exemplos do que NÃO fazer (bloqueio ético) | Verificar se few-shot inclui exemplos de recusa |
| Dynamic context injection | Contexto variável separado do system prompt | Verificar `extra_context` vs system prompt fixo |
| Prompt versioning | Versionamento de prompts para auditoria | Verificar se prompts têm versão ou hash |
| Temperature control | Temperatura baixa para decisões, alta para criação | Verificar `temperature` por tipo de operação |
| Token budget awareness | Controle de custo por interação | Verificar `token_budget` no ReActConfig |
| Bias-aware prompting | Instruções explícitas anti-viés no prompt | Verificar seção [2] princípios inegociáveis |

### MP-2.3 Padrões de Fairness (Referência Eightfold/Greenhouse)

| Prática | Líder de Mercado | Como Verificar na LIA |
|---------|-----------------|----------------------|
| Attribute masking pré-LLM | Eightfold (remove nome, foto, gênero, idade) | Verificar `pii_masking.py` — gap G-M2: blind review ausente |
| Four-fifths rule automated | Greenhouse (monitoramento contínuo) | Verificar `bias_audit_service.py` + golden_dataset |
| Adverse impact analysis | Eightfold (por grupo protegido) | Verificar `AUDIT_DIMENSIONS` = 4 dimensões |
| Bias audit dashboard | Eightfold + Greenhouse | Verificar Admin UI `/admin/compliance/auditoria/bias` |
| Model card / transparency report | Eightfold (publicado) | Verificar se existe documentação pública de fairness |
| Regular fairness testing | Eightfold (contínuo) + EEOC | Verificar se testes de fairness estão em CI/CD |
| Red teaming | Paradox + Greenhouse | Verificar `< 1% jailbreak` target no FairnessGuard |
| Explainable rejections | Greenhouse | Verificar gate-differentiated feedback (4 templates) |

### MP-2.4 Padrões de Segurança e Privacidade (Referência SOC 2/ISO)

| Prática | Descrição | Como Verificar |
|---------|-----------|----------------|
| PII masking em logs | Nenhum dado pessoal em logs de produção | `grep -r "logger\." \| grep -v "pii_masking"` |
| Prompt injection protection | Detectar e bloquear tentativas de injection | Verificar `prompt_injection.py` em todos os endpoints |
| Data minimization em prompts | Enviar apenas dados necessários ao LLM | Verificar se prompts incluem CPF, email, telefone brutos |
| Encryption at rest e in transit | TLS 1.3+ para dados em trânsito, AES-256 at rest | Verificar configuração de banco e API |
| Secret management | Nenhum secret hardcoded, vault/env vars | `grep -r "sk-\|api_key=" --include="*.py" \| grep -v ".env"` |
| Rate limiting | Proteção contra abuso | Verificar middleware de rate limiting |
| Audit trail imutável | Log de auditoria que não pode ser alterado | Verificar `audit_service.py` + tabela `audit_log` |
| Data retention policy | Cleanup automático com prazos definidos | Verificar `data_retention_job.py` + Celery beat |

---

# ANEXO L: MAPA DE CAPACIDADES POR AGENTE — INVENTÁRIO COMPLETO

> O auditor deve preencher este mapa para cada agente, documentando capacidades implementadas, ausentes e oportunidades identificadas por comparação com concorrentes.

---

## MC-1. Inventário de Agentes LIA

### MC-1.1 Agentes ReAct (Raciocínio Livre)

| # | Agente | Domínio | Arquivo | Tools |
|---|--------|---------|---------|-------|
| A1 | SourcingReActAgent | sourcing | `sourcing/agents/sourcing_react_agent.py` | 10 |
| A2 | PipelineReActAgent | cv_screening | `cv_screening/agents/pipeline_react_agent.py` | 10 |
| A3 | CommunicationReActAgent | communication | `communication/agents/communication_react_agent.py` | 5 |
| A4 | AnalyticsReActAgent | analytics | `analytics/agents/analytics_react_agent.py` | 6 |
| A5 | ATSIntegrationReActAgent | ats_integration | `ats_integration/agents/ats_integration_react_agent.py` | 5 |
| A6 | AutomationReActAgent | automation | `automation/agents/automation_react_agent.py` | 6 |
| A7 | PolicyReActAgent | hiring_policy | `hiring_policy/agents/policy_react_agent.py` | 10 |
| A8 | WizardReActAgent | job_management | `job_management/agents/wizard_react_agent.py` | 10 |
| A9 | KanbanReActAgent | recruiter_assistant | `recruiter_assistant/agents/kanban_react_agent.py` | 10 |
| A10 | TalentReActAgent | recruiter_assistant | `recruiter_assistant/agents/talent_react_agent.py` | 10 |
| A11 | JobsMgmtReActAgent | recruiter_assistant | `recruiter_assistant/agents/jobs_mgmt_react_agent.py` | 10 |

### MC-1.2 Agentes Graph (Fluxo Estruturado)

| # | Agente | Domínio | Arquivo | Nós |
|---|--------|---------|---------|-----|
| G1 | JobWizardGraph | job_management | `job_management/agents/job_wizard_graph.py` | 6 |
| G2 | WSIInterviewGraph | cv_screening | `cv_screening/agents/wsi_interview_graph.py` | Entrevista WSI |
| G3 | InterviewGraph | interview_scheduling | `interview_scheduling/agents/interview_graph.py` | Agendamento |

---

## MC-2. Mapa Detalhado de Capacidades por Agente

### MC-2.1 Template de Avaliação (Usar para cada agente)

Para cada agente, o auditor deve preencher:

```
AGENTE: [nome]
DOMÍNIO: [domínio]

CAPACIDADES IMPLEMENTADAS:
- [ ] [capacidade 1]: [status OK/PARCIAL/FALHA] — evidência: [arquivo:linha]
- [ ] [capacidade 2]: ...

CAPACIDADES AUSENTES (vs. concorrentes):
- [ ] [capacidade X]: oferecida por [concorrente] — impacto: [alto/médio/baixo]

OPORTUNIDADES:
- [oportunidade 1]: [descrição + referência de mercado]

ANTI-PADRÕES ENCONTRADOS:
- [anti-padrão]: [referência AP-X.X]

CONFORMIDADE COM PADRÃO 4 ARQUIVOS:
- [ ] react_agent.py: [OK/FALHA]
- [ ] tool_registry.py: [OK/FALHA]
- [ ] system_prompt.py: [OK/FALHA]
- [ ] stage_context.py: [OK/FALHA]
```

### MC-2.2 Sourcing Agent (A1) — Capacidades vs. Concorrentes

| Capacidade | LIA | Tezi Max | Findem | Gem | Eightfold | Status LIA |
|-----------|-----|----------|--------|-----|-----------|-----------|
| Busca por skills/cargo/localização | `search_candidates` | 750M+ perfis | 3D data + atributos | AI sourcing | 1.6B perfis | Implementado |
| Outreach automatizado personalizado | Ausente | Email "on behalf of" | CRM sequences | Automated outreach | Campaigns | **Gap — Alta Prioridade** |
| Calibração contínua de busca | Ausente | Auto-calibrate after feedback | Talent analytics | Auto-calibration | Deep learning | **Gap — Média** |
| Shortlist inteligente | `add_to_shortlist` | Auto-shortlist | AI ranking | Gem Assist | AI match score | Implementado |
| Profile enrichment (multi-fonte) | Ausente | LinkedIn + GitHub + sites | 3D data fusion | Chrome extension | Data enrichment | **Gap — Alta** |
| Boolean search / natural language | `set_search_criteria` (NL) | NL + deep search | Attribute-based | NL search | NL + skills graph | Implementado |
| Análise comparativa de candidatos | `compare_candidates` | Ausente | Side-by-side | Compare view | AI comparison | Implementado |
| Scoring de fit com vaga | `score_candidate` (WSI) | Match scoring | Fit score | Gem Score | Talent Match | Implementado |
| Fairness check em critérios | `check_search_fairness` | Ausente | Ausente | Ausente | Bias detection | **Diferencial LIA** |

### MC-2.3 Pipeline/Screening Agent (A2) — Capacidades vs. Concorrentes

| Capacidade | LIA | Paradox | DigaAI | Beam AI | Eightfold | Status LIA |
|-----------|-----|---------|--------|---------|-----------|-----------|
| Visualizar perfil completo | `view_candidate_profile` | Ausente (chat-first) | Ausente | Dashboard | Full profile | Implementado |
| Movimentação de etapa | `move_candidate` + `batch_move` | Auto-move | Auto-stage | Auto-transition | Workflow | Implementado |
| Análise de CV por IA | `analyze_cv` | Screening questions | AI interview | Resume parsing | Deep learning CV | Implementado |
| Screening WSI (entrevista IA) | `run_wsi_screening` + Graph G2 | Conversational screening | Voice/video AI | Ausente | Assessment | **Diferencial LIA** |
| Scoring determinístico | `wsi_deterministic_scorer.py` | Ausente (chat-based) | Score automático | Ausente | AI scoring | **Diferencial LIA** |
| Agendamento de entrevista | `schedule_interview` | Auto-schedule | Ausente | Calendar AI | Smart scheduling | Implementado |
| Comunicação multicanal | `send_communication` | WhatsApp + SMS + web | WhatsApp + web | Email + SMS | Email + portal | Implementado |
| Batch operations | `batch_move` | Ausente | Ausente | Bulk actions | Bulk processing | Implementado |
| Human review sampling | 5% LGPD sampling | Ausente | Ausente | Ausente | Ausente | **Diferencial LIA** |
| Gate-differentiated feedback | 4 templates por gate | Generic rejection | Ausente | Ausente | Generic | **Diferencial LIA** |

### MC-2.4 Communication Agent (A3) — Capacidades vs. Concorrentes

| Capacidade | LIA | Paradox | Gem | Greenhouse | Status LIA |
|-----------|-----|---------|-----|------------|-----------|
| Email com IA | `send_email` | Ausente (chat-only) | AI email sequences | Email templates | Implementado |
| WhatsApp | `send_whatsapp` | WhatsApp nativo | Ausente | Ausente | Implementado |
| Histórico de comunicação | `get_communication_history` | Chat history | CRM timeline | Activity feed | Implementado |
| Agendamento de mensagens | `schedule_message` | Ausente | Scheduled sequences | Ausente | Implementado |
| Rate limiting | `check_rate_limit` | Ausente | Ausente | Ausente | Implementado |
| AI footer obrigatório | `AI_GENERATED_FOOTER` | Self-identify | Ausente | Ausente | **Diferencial LIA** |
| Email tracking (pixel+click) | `email_tracking_service.py` | Ausente | Open tracking | Basic tracking | Implementado |
| Templates por canal | Comunicação via CommunicationMatrix | Multi-channel | Sequences | Templates | Implementado |
| Personalização por IA | Geração via LLM | Conversational AI | AI personalization | AI suggestions | Implementado |
| NPS/sentiment em respostas | Ausente | Sentiment analysis | Ausente | Ausente | **Gap — Média** |

### MC-2.5 Job Wizard Agent (A8 + G1) — Capacidades vs. Concorrentes

| Capacidade | LIA | Gem | Greenhouse | Tezi | Status LIA |
|-----------|-----|-----|------------|------|-----------|
| Criação guiada de vaga | Graph G1 (6 nós) | AI job creation | AI job posts | Job intake form | Implementado |
| Validação anti-viés | `validate_job_requirements` (FairnessGuard) | Ausente | Bias scanner | Ausente | **Diferencial LIA** |
| Benchmark salarial | `get_salary_benchmarks` (SQL + mercado) | Salary insights | Compensation data | Ausente | Implementado |
| Geração de JD enriquecida | `generate_enriched_jd` | AI JD generation | AI job posts | Ausente | Implementado |
| Health check pré-publicação | `check_job_draft_health` | Ausente | Ausente | Ausente | **Diferencial LIA** |
| Sugestões de skills/benefícios | `get_job_suggestions` | AI suggestions | Ausente | Ausente | Implementado |
| Compliance check em perguntas | FairnessGuard em screening questions | Ausente | EEOC guidance | Ausente | **Diferencial LIA** |

### MC-2.6 Analytics Agent (A4) — Capacidades vs. Concorrentes

| Capacidade | LIA | Gem | Eightfold | Greenhouse | Findem | Status LIA |
|-----------|-----|-----|-----------|------------|--------|-----------|
| Insights por vaga | `get_job_insights` | Pipeline analytics | Talent analytics | Pipeline reports | People analytics | Implementado |
| Previsão de métricas | `predict_hiring_metrics` | Predictive analytics | Workforce planning | Ausente | Talent forecasting | Implementado |
| Relatórios de candidatos | `generate_candidate_report` | Candidate reports | Talent profiles | Candidate reports | Candidate insights | Implementado |
| Performance de agentes IA | `get_agent_performance` | Ausente | Ausente | Ausente | Ausente | **Diferencial LIA** |
| Search analytics | `get_search_analytics` | Sourcing analytics | Sourcing metrics | Source tracking | Search analytics | Implementado |
| Bias audit dashboard | Sim (Admin UI) | Ausente | Bias detection | EEOC reports | Ausente | **Diferencial LIA** |
| Drift detection | 4 triggers automatizados | Ausente | Model monitoring | Ausente | Ausente | **Diferencial LIA** |

### MC-2.7 Hiring Policy Agent (A7) — Capacidades vs. Concorrentes

| Capacidade | LIA | Greenhouse | Eightfold | Status LIA |
|-----------|-----|------------|-----------|-----------|
| Configuração guiada de políticas | `get_current_policy` + `save_policy_field` | Settings panel | Configuration | Implementado |
| Validação de compliance | `validate_policy_compliance` (FairnessGuard) | EEOC check | Bias check | **Diferencial LIA** |
| Benchmarks por setor | `get_industry_benchmarks` + `get_platform_benchmarks` | Industry data | Ausente | Implementado |
| Detecção de anomalias | `detect_policy_impact_anomalies` | Ausente | Ausente | **Diferencial LIA** |
| Impacto de configurações | `explain_policy_impact` | Ausente | Ausente | **Diferencial LIA** |
| Setup progress tracking | `get_setup_progress` | Onboarding wizard | Setup guide | Implementado |

### MC-2.8 Recruiter Assistant — Kanban (A9) + Talent (A10) + Jobs (A11)

| Capacidade | LIA | Gem | Greenhouse | Tezi | Status LIA |
|-----------|-----|-----|------------|------|-----------|
| Pipeline summary | `get_pipeline_summary` | Pipeline view | Pipeline dashboard | Ausente | Implementado |
| Bottleneck detection | `identify_bottlenecks` | Ausente | Ausente | Ausente | **Diferencial LIA** |
| Candidate aging report | `get_candidate_aging` | Stale candidate alerts | Ausente | Ausente | **Diferencial LIA** |
| Stage comparison | `compare_stages` | Ausente | Stage analytics | Ausente | Implementado |
| Movement suggestions | `suggest_movements` | Ausente | Ausente | Ausente | **Diferencial LIA** |
| Pipeline benchmarks (SQL) | `get_pipeline_benchmarks` (SQL real) | Pipeline metrics | Benchmark reports | Ausente | Implementado |
| Ranking de candidatos | `rank_candidates` | Gem Score | Scorecard | Match score | Implementado |
| Comparação lado a lado | `compare_candidates` | Compare view | Compare | Ausente | Implementado |
| Shortlist creation | `create_shortlist` | Shortlist | Shortlist | Auto-shortlist | Implementado |
| SLA monitoring | `check_sla` | Ausente | Ausente | Ausente | **Diferencial LIA** |
| Busca com fairness check | `check_search_fairness` | Ausente | Ausente | Ausente | **Diferencial LIA** |

---

## MC-3. Gaps Competitivos Consolidados — Oportunidades por Prioridade

### MC-3.1 Alta Prioridade (Concorrentes já oferecem, impacto direto em vendas)

| # | Capacidade Ausente | Oferecida por | Agente Afetado | Esforço |
|---|-------------------|---------------|----------------|---------|
| CG-1 | Outreach automatizado personalizado (email sequences) | Tezi, Gem, Findem, Eightfold | Sourcing (A1) | Alto |
| CG-2 | Profile enrichment multi-fonte (LinkedIn + GitHub + social) | Tezi, Findem, Gem (extensão Chrome) | Sourcing (A1) | Alto |
| CG-3 | Integração direta WhatsApp ↔ WSI (entrevista pelo WhatsApp) | Paradox (nativo), DigaAI | WSI Graph (G2) | Médio |
| CG-4 | Blind review / candidate anonymizer pré-LLM | Eightfold (masking automático) | Pipeline (A2) | Médio |
| CG-5 | Cascata de confiança T3 automática | Estado da arte LLM routing | Orchestrator | Médio |

### MC-3.2 Média Prioridade (Diferenciação competitiva)

| # | Capacidade Ausente | Oferecida por | Agente Afetado | Esforço |
|---|-------------------|---------------|----------------|---------|
| CG-6 | Calibração contínua de busca (auto-adjust com feedback) | Tezi, Findem | Sourcing (A1) | Alto |
| CG-7 | NPS/sentiment analysis em respostas de candidatos | Paradox | Communication (A3) | Médio |
| CG-8 | AI video interview (vídeo assíncrono) | DigaAI, Paradox | WSI (G2) — novo canal | Alto |
| CG-9 | Avaliação com Ragas/DeepEval (benchmark padronizado) | Estado da arte ML | Quality Evaluator | Médio |
| CG-10 | Career page AI chatbot (widget público) | Paradox Olivia, Gem | Novo agente | Alto |
| CG-11 | Workforce planning / talent mapping | Eightfold, Findem | Analytics (A4) — expansão | Alto |

### MC-3.3 Diferencial LIA (Capacidades que concorrentes NÃO têm)

O auditor deve verificar que estes diferenciais estão REALMENTE implementados e funcionais:

| # | Diferencial | Implementação | Verificação |
|---|------------|---------------|-------------|
| D-1 | FairnessGuard 3 camadas (regex + léxico + LLM) | `fairness_guard.py` | Testar com 6 cenários de red teaming |
| D-2 | Scoring determinístico WSI (sem LLM) | `wsi_deterministic_scorer.py` | Verificar que score é reproduzível |
| D-3 | Human Review Sampling 5% (LGPD Art. 20) | `human_review_sampling_service.py` | Verificar MD5 sampling determinístico |
| D-4 | Gate-differentiated feedback (4 templates) | `candidate_feedback_service.py` | Testar os 4 templates |
| D-5 | Policy impact detection (anomalias) | `policy_react_agent.py` | Verificar `detect_policy_impact_anomalies` |
| D-6 | Anti-sycophancy com benchmarks setoriais | System prompts | Verificar seção [7] do prompt |
| D-7 | Guardrails editáveis sem deploy (banco) | `guardrails` table + Admin UI | Testar CRUD via API |
| D-8 | Bottleneck detection + movement suggestions | `kanban_react_agent.py` | Verificar tools `identify_bottlenecks` + `suggest_movements` |
| D-9 | Pipeline benchmarks via SQL real | `jobs_mgmt_react_agent.py` | Verificar que usa dados reais, não mock |
| D-10 | Drift detection (4 triggers + alertas automáticos) | `model_drift_service.py` | Verificar Celery beat + alertas |
| D-11 | AI footer em emails (EU AI Act compliance) | `email_adapter.py` | Verificar `AI_GENERATED_FOOTER` ativo |
| D-12 | Agent performance monitoring (auto-observabilidade) | `analytics_react_agent.py` | Verificar `get_agent_performance` tool |

---

## MC-4. Benchmark Competitivo Consolidado

### MC-4.1 Tabela de Cobertura Funcional vs. Concorrentes

| Capacidade | LIA | Tezi | Paradox | DigaAI | Findem | Eightfold | Gem | Greenhouse | Beam AI |
|-----------|:---:|:----:|:-------:|:------:|:------:|:---------:|:---:|:----------:|:-------:|
| AI Sourcing | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| AI Screening/Triagem | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| AI Interview (WSI) | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Scoring Determinístico | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Job Wizard (criação guiada) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Pipeline Management | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Communication (email+WA) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Outreach Automatizado | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| FairnessGuard (3 camadas) | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Bias Audit Dashboard | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| ATS Integration | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | N/A | ✅ |
| Analytics/Reporting | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Hiring Policy Config | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Drift Detection | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Human Review Sampling | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multi-tenant | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| WhatsApp Nativo | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Video Interview AI | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Career Page Chatbot | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| LGPD Compliance Nativo | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Contagem de capacidades:**
- LIA: 16/20 (80%)
- Eightfold: 12/20 (60%) — líder em AI/ML mas sem comunicação multicanal
- Gem: 9/20 (45%) — forte em CRM/sourcing
- Greenhouse: 8/20 (40%) — forte em ATS/compliance
- Tezi: 7/20 (35%) — forte em sourcing autônomo
- Paradox: 7/20 (35%) — forte em conversacional/WhatsApp

---

## MC-5. Procedimento de Mapeamento de Capacidades (Para o Auditor)

### Passo 1: Inventário de Tools por Agente

Para cada agente, executar:

```bash
grep -E "name=|description=" app/domains/[domain]/agents/[domain]_tool_registry.py
```

### Passo 2: Verificar Wiring (Tool existe vs. está conectado)

Para cada tool listada no registry:
1. Verificar se a função implementada faz algo real (não é stub)
2. Verificar se o service que a tool chama acessa dados reais (não mock)
3. Verificar se há testes para a tool
4. Classificar: REAL / STUB / MOCK / PARCIAL

### Passo 3: Comparar com Matriz de Concorrentes

Para cada capacidade ausente (❌) na tabela MC-4.1:
1. Avaliar impacto no negócio (alto/médio/baixo)
2. Avaliar esforço de implementação
3. Priorizar: CG-1 a CG-N

### Passo 4: Validar Diferenciais

Para cada diferencial listado em MC-3.3:
1. Executar cenário de teste manual
2. Verificar que funciona end-to-end (não apenas existe no código)
3. Classificar: FUNCIONAL / PARCIAL / APENAS CÓDIGO

### Passo 5: Gerar Relatório

Incluir no relatório final:
- Tabela de capacidades por agente (preenchida)
- Gaps competitivos priorizados
- Diferenciais validados vs. apenas implementados
- Recomendações de roadmap baseadas em gaps

---

# ANEXO M: MANUAL DE REMEDIAÇÃO — RUNBOOKS ACIONÁVEIS POR PRIORIDADE

> **Para o Time:** Este anexo contém instruções passo-a-passo para resolver cada tipo de problema que a auditoria pode encontrar. Cada runbook inclui: o que está errado, por que importa, como resolver (passo-a-passo), arquivos a modificar, padrão de código a seguir, esforço estimado, critério de aceitação e responsável. Use o ID do runbook (RM-XX) para vincular achados do relatório às instruções de correção.

---

## ÍNDICE DE RUNBOOKS POR PRIORIDADE

### Mapa Rápido de Navegação

| ID | Título | Prioridade | Esforço | Responsável | Depende de |
|:---|:-------|:----------:|:-------:|:-----------:|:----------:|
| RM-01 | PII não mascarada nos prompts ao LLM | P0 | 8h | Backend | — |
| RM-02 | FairnessGuard ausente como middleware automático | P0 | 12h | Backend | — |
| RM-03 | Human Review gate ausente em rejeições | P0 | 8h | Backend | — |
| RM-04 | Consent check ausente antes de processar candidato | P0 | 6h | Backend | — |
| RM-05 | Audit trail incompleto ou mutável | P0 | 8h | Backend | — |
| RM-06 | Multi-tenant isolation falha (query sem company_id) | P0 | 4h | Backend | — |
| RM-07 | Decisão automatizada sem opt-out para candidato | P0 | 6h | Backend+FE | — |
| RM-35 | Discriminação em critérios de vaga / triagem | P0 | 6h | Backend | — |
| RM-08 | Anti-sycophancy ausente no system prompt | P1 | 4h | Backend | — |
| RM-09 | Confiança artificial (fórmula fake) | P1 | 6h | Backend | — |
| RM-10 | Circuit breaker ausente em integração externa | P1 | 4h | Backend | — |
| RM-11 | Token budget sem pre-call check | P1 | 4h | Backend | — |
| RM-12 | Observabilidade insuficiente (sem observer/métricas) | P1 | 6h | Backend | — |
| RM-13 | Degradation path incompleto (sem fallback chain) | P1 | 8h | Backend | RM-10 |
| RM-14 | Few-shot examples inadequados ou ausentes | P1 | 3h | Backend | — |
| RM-15 | FairnessGuard ausente na SAÍDA do ReAct loop | P1 | 4h | Backend | RM-02 |
| RM-16 | PII scrubbing ausente na resposta do agente | P1 | 4h | Backend | RM-01 |
| RM-17 | Negation detection ausente | P1 | 3h | Backend | — |
| RM-18 | Padrão 4 arquivos não seguido pelo agente | P2 | 6h | Backend | — |
| RM-19 | Stage context ausente ou incompleto | P2 | 4h | Backend | RM-18 |
| RM-20 | Memória sem decay factor / sem limite | P2 | 4h | Backend | — |
| RM-21 | Drift detection desligado ou não configurado | P2 | 4h | Backend+Infra | — |
| RM-22 | Guardrails não configurados no banco | P2 | 3h | Backend | — |
| RM-23 | Testes de fairness fora do CI/CD | P2 | 6h | Backend+Infra | — |
| RM-24 | ConfidencePolicy limitada a um agente | P2 | 6h | Backend | — |
| RM-25 | Wiring desconectado (componente existe mas não é chamado) | P2 | Variável | Backend/FE | — |
| RM-26 | EU AI Act compliance gaps nos prompts | P2 | 3h | Backend | — |
| RM-27 | WCAG 2.1 AA não atendido | P2 | 8h | Frontend | — |
| RM-38 | Data flow quebrado ou incompleto (Dimensão 2) | P2 | 2-4h/item | Backend+FE | — |
| RM-39 | Backend/API incorreto ou incompleto (Dimensão 6) | P2 | 2-4h/item | Backend | — |
| RM-40 | Types/Contracts inconsistentes (Dimensão 7) | P2 | 4h | Backend+FE | — |
| RM-41 | User flow quebrado ou incompleto (Dimensão 8) | P2 | 2-4h/item | Frontend | — |
| RM-42 | Inconsistência entre componentes (Dimensão 9) | P2 | 4-8h | Frontend | — |
| RM-43 | Documentação desatualizada ou ausente (Dimensão 11) | P2 | 4h | Backend+FE | — |
| RM-44 | Performance / escalabilidade insuficiente (Dimensão 14) | P2 | 8h | Backend | — |
| RM-36 | Pipeline não validado / stages sem verificação | P2 | 6h | Backend+FE | — |
| RM-28 | Outreach automatizado (gap competitivo CG-1) | P3 | 40h | Backend+FE | — |
| RM-29 | Profile enrichment multi-fonte (CG-2) | P3 | 40h | Backend | — |
| RM-30 | WhatsApp ↔ WSI direto (CG-3) | P3 | 24h | Backend | — |
| RM-31 | Blind review / candidate anonymizer (CG-4) | P3 | 16h | Backend | RM-01 |
| RM-32 | Calibração contínua de busca (CG-6) | P3 | 32h | Backend | — |
| RM-33 | NPS / Sentiment analysis (CG-7) | P3 | 16h | Backend | — |
| RM-34 | Cascata de confiança T3 automática (CG-5) | P3 | 16h | Backend | RM-09 |
| RM-37 | Video interview com análise por IA (CG-8) | P3 | 40h | Backend+FE | — |

---

## P0 — CRÍTICO: VIOLAÇÕES DE INEGOCIÁVEIS

> Cada item P0 é um **bloqueador de deploy**. O time NÃO deve fazer deploy com qualquer P0 aberto.

---

### RM-01: PII Não Mascarada nos Prompts ao LLM

**O que está errado:** Dados pessoais de candidatos (nome, CPF, email, telefone) são enviados diretamente nos prompts ao LLM sem mascaramento. O provider (OpenAI, Anthropic, Google) recebe dados que não deveria ter.

**Por que importa:** Violação direta da LGPD Art. 6 (minimização de dados) e do Inegociável #4 (PII masking em todos os logs). Dados pessoais ficam nos logs do provider fora do controle da empresa.

**Referência:** Gap G-M1 (Anexo E), Dimensão 13.1

**Passo-a-passo para resolver:**

1. Criar módulo `app/shared/prompt_pii_filter.py`:
```python
import re
from app.shared.pii_masking import PIIMaskingFilter

class PromptPIIFilter:
    PATTERNS = {
        'cpf': (r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', '***CPF***'),
        'email': (r'[\w.-]+@[\w.-]+\.\w+', '***EMAIL***'),
        'phone': (r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}', '***PHONE***'),
        'name_field': (r'"(?:nome|name|candidato)":\s*"[^"]*"', '"nome": "***NAME***"'),
    }

    @classmethod
    def sanitize_prompt(cls, text: str) -> str:
        result = text
        for pattern, replacement in cls.PATTERNS.values():
            result = re.sub(pattern, replacement, result)
        return result
```

2. Integrar no `DomainWorkflow._prepare()` ou no `react_loop.py` antes de montar o prompt:
```python
from app.shared.prompt_pii_filter import PromptPIIFilter
extra_context = PromptPIIFilter.sanitize_prompt(raw_extra_context)
```

3. Verificar que TODOS os `extra_context` passados aos agentes passam pelo filtro.

4. Adicionar teste:
```python
def test_pii_filter_removes_cpf():
    text = "Candidato João, CPF 123.456.789-00, email joao@email.com"
    result = PromptPIIFilter.sanitize_prompt(text)
    assert "123.456.789-00" not in result
    assert "joao@email.com" not in result
```

**Padrão de código a seguir:** Usar `PIIMaskingFilter` existente em `app/shared/pii_masking.py` como referência. O novo `PromptPIIFilter` deve seguir o mesmo padrão de regex + replacement. Referência: Anexo A (PL-1 — `_prepare()` é o ponto de injeção canônico).

**Arquivos a modificar:**
- Criar: `app/shared/prompt_pii_filter.py`
- Modificar: `app/shared/agents/react_loop.py` (ou equivalente)
- Modificar: cada `_prepare()` de DomainWorkflow que monta `extra_context`
- Criar: `tests/unit/test_prompt_pii_filter.py`

**Esforço estimado:** 8h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Nenhum CPF, email ou telefone aparece nos prompts enviados ao LLM (verificar via LangSmith traces)
- [ ] Teste unitário passa com 100% dos patterns cobertos
- [ ] `grep -rn "extra_context" app/domains/` mostra que todos passam pelo filtro

---

### RM-02: FairnessGuard Ausente como Middleware Automático

**O que está errado:** FairnessGuard depende de cada agente/endpoint chamar `check()` manualmente. Se um novo agente for criado sem chamar, vieses passam sem detecção.

**Por que importa:** Violação do Inegociável #3 (FairnessGuard ativo em 100%). Se depende de "lembrar", haverá falhas — é questão de tempo.

**Referência:** Gap G-RL1 (Anexo E), Dimensão 12.1, AP-2.3

**Passo-a-passo para resolver:**

1. Criar middleware no `DomainWorkflow` que intercepta ANTES de processar:
```python
async def _pre_check(self, input_data: AgentInput) -> AgentInput:
    guard = FairnessGuard()
    result = guard.check(input_data.message)
    if result.blocked:
        raise FairnessViolationError(result.warning_message)
    if result.warnings:
        input_data.metadata["fairness_warnings"] = result.warnings
    await guard.log_check(
        company_id=input_data.company_id,
        agent_type=self.agent_type,
        input_text=input_data.message,
        result=result
    )
    return input_data
```

2. Garantir que `_pre_check` é chamado em `DomainWorkflow.execute()` ANTES de qualquer processamento:
```python
async def execute(self, input_data: AgentInput) -> AgentOutput:
    input_data = await self._pre_check(input_data)  # OBRIGATÓRIO
    # ... resto do fluxo
```

3. Adicionar FairnessGuard check na SAÍDA (ver RM-15).

4. Verificar que NENHUM domínio faz override de `execute()` pulando `_pre_check()`.

**Padrão de código a seguir:** Seguir o padrão de `FairnessGuard.check()` existente em `app/shared/compliance/fairness_guard.py`. A integração deve usar o padrão DomainWorkflow com hook `_pre_check()` no base class. Referência: Anexo A (pipeline canônico: classify → route → **pre_check** → execute → validate → format → respond). Tabela de anti-padrões: AP-2.3 (Anexo B).

**Arquivos a modificar:**
- `app/shared/agents/domain_workflow.py` (ou equivalente de base workflow)
- Verificar: cada `app/domains/*/workflow.py` que faz override

**Esforço estimado:** 12h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `grep -rn "FairnessGuard" app/shared/agents/` confirma integração no workflow base
- [ ] Teste: enviar "apenas homens" → recebe BLOCK_AND_WARN (não processa)
- [ ] Teste: enviar "boa aparência" → recebe soft_warning (processa com alerta)
- [ ] Nenhum domínio faz bypass do `_pre_check`

---

### RM-03: Human Review Gate Ausente em Rejeições

**O que está errado:** Decisões de rejeição de candidatos podem ser executadas automaticamente sem passar por aprovação humana.

**Por que importa:** Violação do Inegociável #2 (nenhuma rejeição automática sem review gate), EU AI Act Art. 14 (human oversight obrigatório) e LGPD Art. 20 (revisão humana em decisões automatizadas).

**Referência:** Gap G-C1 (Anexo E), Dimensão 12.2

**Passo-a-passo para resolver:**

1. Verificar que `HumanReviewSamplingService` está integrado no fluxo de rejeição:
```python
from app.services.human_review_sampling_service import HumanReviewSamplingService

async def reject_candidate(candidate_id, reason, company_id):
    service = HumanReviewSamplingService()
    if service.should_flag_for_review(candidate_id, company_id):
        await create_pending_review(candidate_id, reason, "rejection")
        return {"status": "pending_human_review"}
    # ... processa rejeição
```

2. Para TODA movimentação para etapa de rejeição, verificar que o tool `move_candidate` no pipeline agent impõe o gate:
   - Score < 4.0 → rejeição exige review
   - Score 4.0-6.9 → review obrigatório (faixa "Em análise")
   - Qualquer rejeição manual → registrar motivo obrigatório

3. Integrar no `DomainWorkflow._execute()`:
```python
if self._is_destructive_action(action):
    await self._require_human_approval(action, context)
```

4. Verificar lista explícita de ações HITL em cada `tool_registry.py`:
```python
HITL_ACTIONS = ["reject_candidate", "move_to_rejected", "batch_reject"]
```

**Padrão de código a seguir:** Seguir o padrão de `HumanReviewSamplingService` em `app/services/human_review_sampling_service.py`. A lista `HITL_ACTIONS` deve ser explícita em cada `tool_registry.py`. Referência: Anexo A (tools com `requires_confirmation=True`), Crença 01, Inegociável #2.

**Arquivos a modificar:**
- `app/domains/cv_screening/agents/pipeline_tool_registry.py`
- `app/services/human_review_sampling_service.py` (verificar integração)
- Cada tool de movimentação que permite rejeição

**Esforço estimado:** 8h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Nenhum candidato é rejeitado sem registro de `reviewed_by` (humano ou sampling)
- [ ] 5% das decisões são flagged para human review (LGPD Art. 20)
- [ ] Motivo de rejeição é obrigatório e registrado na audit trail
- [ ] `grep -rn "HITL_ACTIONS\|hitl\|human_review" app/domains/` mostra cobertura em todos os domínios

---

### RM-04: Consent Check Ausente Antes de Processar Candidato

**O que está errado:** Dados de candidatos são processados (enviados ao LLM, armazenados, analisados) sem verificar se o candidato deu consentimento prévio.

**Por que importa:** Violação do Inegociável #5 (consent antes de qualquer processamento) e LGPD Art. 7 (bases legais para tratamento).

**Referência:** Dimensão 13.2, Crença 04

**Passo-a-passo para resolver:**

1. Adicionar check no início de cada workflow que processa dados de candidato:
```python
async def _check_consent(self, candidate_id: str, company_id: str, purpose: str):
    consent = await consent_service.get_consent(candidate_id, company_id, purpose)
    if not consent or consent.revoked:
        raise ConsentRequiredError(
            f"Consent '{purpose}' required for candidate {candidate_id}"
        )
```

2. Mapear purposes obrigatórios por domínio:
   - `cv_screening` → `personal_data` + `sensitive_data`
   - `communication` → `personal_data` + `marketing` (se marketing)
   - `sourcing` → `personal_data`
   - `analytics` → `analytics` (dados agregados não precisam de consent individual)

3. Implementar HTTP 451 quando consent obrigatório ausente:
```python
from fastapi import HTTPException
raise HTTPException(status_code=451, detail="Consent required: personal_data")
```

4. Verificar que consentimento revogado bloqueia IMEDIATAMENTE todo processamento:
```python
@router.post("/consent/revoke")
async def revoke_consent(candidate_id: str, consent_type: str):
    await consent_service.revoke(candidate_id, consent_type)
    await stop_all_processing(candidate_id)  # Hard stop
```

**Padrão de código a seguir:** Seguir o padrão de consent management com SHA256 hash. HTTP 451 para consent ausente. 7 tipos granulares. Referência: PARTE IV (6 Pilares LGPD), Tabela de Retenção. Padrão: `consent_service.check()` como guard no início do workflow.

**Arquivos a modificar:**
- `app/shared/agents/domain_workflow.py` (adicionar `_check_consent` no base)
- `app/services/consent_service.py` (verificar existência e completude)
- Cada domain workflow que processa dados de candidato

**Esforço estimado:** 6h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Processar candidato sem consent → HTTP 451
- [ ] Revogar consent → para processamento imediatamente
- [ ] 7 tipos de consent suportados com prova SHA256
- [ ] `grep -rn "consent" app/domains/` mostra check em todos os domínios com dados de candidato

---

### RM-05: Audit Trail Incompleto ou Mutável

**O que está errado:** Nem todas as ações relevantes são registradas na trilha de auditoria, ou a trilha permite alteração/deleção de registros.

**Por que importa:** Violação do Inegociável #8 (Crença 08 — observável e rastreável), SOC 2 (audit trail imutável), e impede rastreabilidade de decisões para candidatos.

**Referência:** Dimensão 13, Crença 08, Production Readiness #11

**Passo-a-passo para resolver:**

1. Verificar que a tabela `audit_log` é append-only (sem UPDATE/DELETE):
```sql
-- Verificar se existe trigger ou policy que impede UPDATE/DELETE
-- Se não existir, criar:
CREATE POLICY audit_append_only ON audit_log
    FOR ALL USING (false) WITH CHECK (true);
-- Ou usar trigger:
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_immutable
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
```

2. Verificar que TODOS os eventos obrigatórios são logados:
   - Toda movimentação de candidato no pipeline
   - Toda decisão do agente IA (com reasoning)
   - Toda intervenção do FairnessGuard
   - Todo login / ação administrativa
   - Toda comunicação enviada
   - Toda alteração de política/configuração

3. Adicionar audit logging no DomainWorkflow base:
```python
async def _audit_log(self, action: str, details: dict, company_id: str):
    await audit_service.log(
        action=action,
        agent_type=self.agent_type,
        company_id=company_id,
        details=details,
        timestamp=datetime.utcnow(),
        immutable=True
    )
```

**Padrão de código a seguir:** Tabela `audit_log` deve ser append-only com trigger PostgreSQL. Usar `audit_service.log()` com formato estruturado. Referência: Crença 08, Anexo C (schemas de observabilidade), SOC 2 Type II requirements.

**Arquivos a modificar:**
- `app/services/audit_service.py`
- Migration para trigger de imutabilidade
- `app/shared/agents/domain_workflow.py`

**Esforço estimado:** 8h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `UPDATE audit_log SET ...` → erro (trigger bloqueia)
- [ ] `DELETE FROM audit_log` → erro (trigger bloqueia)
- [ ] Toda ação de agente gera registro na tabela
- [ ] Registro inclui: timestamp, company_id, agent_type, action, details, user_id

---

### RM-06: Multi-Tenant Isolation Falha

**O que está errado:** Existem queries SQL que não filtram por `company_id`, permitindo potencial vazamento de dados entre tenants.

**Por que importa:** Violação crítica de segurança. Empresa A pode ver dados da Empresa B. Impacto legal, comercial e reputacional catastrófico.

**Referência:** AP-3.1 (Anexo B), Dimensão 13.4

**Passo-a-passo para resolver:**

1. Auditar TODAS as queries:
```bash
grep -rn "select\|query\|filter\|where" app/domains/ --include="*.py" | grep -v "company_id" | grep -v "test_\|#\|def \|import"
```

2. Para cada query encontrada sem `company_id`, adicionar:
```python
# ANTES (ERRADO):
results = session.query(Candidate).all()

# DEPOIS (CORRETO):
results = session.query(Candidate).filter(
    Candidate.company_id == company_id
).all()
```

3. Adicionar middleware de validação que verifica `company_id` em todas as rotas:
```python
@app.middleware("http")
async def tenant_isolation_check(request, call_next):
    company_id = get_company_id_from_token(request)
    if not company_id:
        raise HTTPException(401, "company_id required")
    request.state.company_id = company_id
    return await call_next(request)
```

4. Adicionar teste de cross-tenant:
```python
async def test_no_cross_tenant_leak():
    # Criar dados com company_A
    # Consultar com company_B
    # Verificar que retorna vazio
```

**Padrão de código a seguir:** TODA query SQL deve incluir `.filter(Model.company_id == company_id)`. Session IDs devem usar namespace `f"{company_id}:{session_id}"`. Referência: AP-3.1 a AP-3.4 (Anexo B), Dimensão 13.4.

**Arquivos a modificar:**
- Todos os repositories/services que fazem queries
- Middleware de autenticação

**Esforço estimado:** 4h (por domínio onde falha) | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `grep -rn "\.all()" app/domains/ | grep -v company_id` → 0 resultados
- [ ] Teste cross-tenant passa (company_B não vê dados de company_A)
- [ ] Todas as queries em todos os domínios filtram por company_id

---

### RM-07: Decisão Automatizada sem Opt-Out para Candidato

**O que está errado:** Candidatos não têm opção de recusar avaliação por IA ou solicitar avaliação humana alternativa.

**Por que importa:** Violação da LGPD Art. 20 (direito a revisão humana) e EU AI Act Art. 14 (human oversight). Candidato tem direito de saber que IA está envolvida e de optar por não ser avaliado por IA.

**Referência:** Crença 03 (Transparente e Explicável), Dimensão 13.6

**Passo-a-passo para resolver:**

1. Backend: adicionar flag `ai_opt_out` no modelo de candidato:
```python
class CandidatePreferences(Base):
    candidate_id = Column(UUID, ForeignKey("candidates.id"))
    ai_evaluation_opt_out = Column(Boolean, default=False)
    opt_out_date = Column(DateTime, nullable=True)
```

2. Backend: verificar opt-out antes de processar com IA:
```python
async def _check_ai_opt_out(self, candidate_id: str):
    prefs = await get_candidate_preferences(candidate_id)
    if prefs and prefs.ai_evaluation_opt_out:
        return AgentOutput(
            response="Candidato optou por não ser avaliado por IA. Encaminhar para avaliação humana.",
            requires_human_action=True
        )
```

3. Frontend: adicionar opção de opt-out na interface do candidato (portal do candidato ou email de consentimento).

4. Adicionar AI disclosure em todas as comunicações:
```python
AI_DISCLOSURE = "Esta comunicação foi gerada com auxílio de Inteligência Artificial."
```

**Padrão de código a seguir:** Flag `ai_evaluation_opt_out` no modelo de candidato. AI disclosure footer obrigatório (`AI_GENERATED_FOOTER`). Referência: LGPD Art. 20, EU AI Act Art. 14/52, Crença 03.

**Arquivos a modificar:**
- Migration para `candidate_preferences`
- `app/shared/agents/domain_workflow.py`
- Frontend: portal do candidato / tela de consentimento

**Esforço estimado:** 6h | **Responsável:** Backend + Frontend

**Critério de aceitação:**
- [ ] Candidato com opt-out → IA não processa, encaminha para humano
- [ ] AI disclosure em todas as comunicações geradas por IA
- [ ] Opt-out é registrado com timestamp na tabela

---

### RM-35: Discriminação em Critérios de Vaga / Triagem

**O que está errado:** Critérios discriminatórios (gênero, idade, raça, estado civil, aparência) podem ser configurados em vagas ou usados pelo agente sem bloqueio automático.

**Por que importa:** Violação da Constituição Federal Art. 7 (XXX/XXXI), CLT Art. 373-A, e Lei 9.029/95. Discriminação direta em critérios é a forma mais grave de viés — precisa ser bloqueada ANTES de chegar ao LLM. FairnessGuard Camada 1 (Lexical) deveria capturar isso.

**Referência:** Crença 02, Inegociável #2, FairnessGuard Camada 1 (PARTE II), Dimensão 4

**Passo-a-passo para resolver:**

1. Expandir a lista de termos discriminatórios no FairnessGuard Camada 1:
```python
DISCRIMINATORY_CRITERIA = {
    "gender": ["sexo masculino", "sexo feminino", "apenas homens", "apenas mulheres",
               "preferência por homens", "preferência por mulheres"],
    "age": ["idade máxima", "até 30 anos", "até 35 anos", "jovem",
            "recém-formado obrigatório", "máximo 40 anos"],
    "appearance": ["boa aparência", "boa apresentação", "bonita", "atraente"],
    "marital": ["solteiro", "solteira", "sem filhos", "casado", "casada"],
    "race": ["branco", "negro", "pardo", "cor da pele"],
    "origin": ["nascido em", "natural de", "morador de"],
    "religion": ["cristão", "evangélico", "católico"],
}

def check_discriminatory_criteria(job_description: str) -> FairnessResult:
    for category, terms in DISCRIMINATORY_CRITERIA.items():
        for term in terms:
            if term.lower() in job_description.lower():
                return FairnessResult(
                    action="BLOCK_AND_WARN",
                    reason=f"Critério discriminatório detectado ({category}): '{term}'",
                    category=category
                )
    return FairnessResult(action="PASS")
```

2. Integrar no fluxo de criação de vaga (Job Wizard) e no pipeline de triagem:
```python
async def _validate_job_criteria(self, job_data, company_id):
    result = check_discriminatory_criteria(job_data.get("description", ""))
    if result.action == "BLOCK_AND_WARN":
        await audit_service.log(company_id, "DISCRIMINATION_BLOCKED", result.to_dict())
        raise DiscriminatoryCriteriaError(result.reason)
```

3. Aplicar verificação também nos critérios de triagem automática e ranking.

**Padrão de código a seguir:** Expandir `FairnessGuard.check()` Camada 1 (lexical) com dicionário de termos por categoria. BLOCK_AND_WARN é a ação para discriminação direta. Registrar na audit trail. Referência: Crença 02, Lei 9.029/95, PARTE II (FairnessGuard 3 camadas).

**Arquivos a modificar:**
- Modificar: `app/shared/compliance/fairness_guard.py` (expandir Camada 1)
- Modificar: `app/domains/job_wizard/` (validar critérios na criação de vaga)
- Modificar: `app/domains/cv_screening/` (validar antes de triagem)
- Criar: `tests/unit/test_discriminatory_criteria.py`

**Esforço estimado:** 6h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Vaga com "apenas homens" → BLOCK_AND_WARN, vaga não é criada
- [ ] Vaga com "boa aparência" → BLOCK_AND_WARN
- [ ] Vaga com "até 30 anos" → BLOCK_AND_WARN
- [ ] Cada bloqueio registrado na audit trail com categoria e termo detectado
- [ ] Teste unitário cobre todos os termos do dicionário

---

## P1 — ALTO: QUALIDADE E RESILIÊNCIA

> Itens P1 devem ser resolvidos no **próximo sprint**. Não bloqueiam deploy mas impactam qualidade.

---

### RM-08: Anti-Sycophancy Ausente no System Prompt

**O que está errado:** O system prompt do agente não contém instruções para contra-argumentar quando o recrutador faz pedidos problemáticos.

**Por que importa:** Sem anti-sycophancy, o agente concorda com tudo — inclusive pedidos que comprometem a qualidade da contratação (ex: "contrate o mais barato", "ignore a experiência").

**Referência:** Crença 11 (obrigatório em TODOS os prompts), Dimensão 10.1

**Passo-a-passo para resolver:**

1. Adicionar seção [7] no system prompt do agente:
```python
ANTI_SYCOPHANCY_SECTION = """
## [7] CONTRA-ARGUMENTAÇÃO E ANTI-BAJULAÇÃO

Você NÃO é um assistente que concorda com tudo. Quando o recrutador fizer
pedidos que comprometam a qualidade da contratação, você DEVE:

1. ALERTAR com dados concretos do mercado
2. CITAR benchmarks setoriais (ABRH, GPTW, Gupy, Robert Half, LinkedIn Economic Graph, Glassdoor, IBGE/PNAD, MTE/CAGED)
3. PROPOR alternativa fundamentada
4. REGISTRAR a divergência na trilha de auditoria

Exemplos de quando contra-argumentar:
- "Quero fechar em 3 dias" → Mostrar time-to-fill médio do setor
- "Salário de R$3.000 para sênior" → Mostrar benchmark salarial
- "Contrate sem entrevista" → Alertar sobre risco de turnover
- "Ignore a formação" → Diferenciar entre formação como filtro (proibido) e certificação legal obrigatória (permitido)

NUNCA concorde silenciosamente. Sempre documente.
"""
```

2. Adicionar seção [8] de calibração:
```python
CALIBRATION_SECTION = """
## [8] CALIBRAÇÃO COM DADOS REAIS

Toda recomendação quantitativa deve ser embasada em:
- Dados internos da empresa (SQL) quando disponíveis
- Benchmarks de mercado com fonte citável
- Nunca usar "em geral" ou "normalmente" sem número

Se não há dados disponíveis, diga explicitamente: "Não tenho dados para embasar esta recomendação."
"""
```

3. Verificar que TODOS os system prompts dos 14 agentes contêm estas seções:
```bash
grep -rn "CONTRA-ARGUMENTAÇÃO\|anti.sycophancy\|ANTI_SYCOPHANCY" app/domains/*/agents/*system_prompt*
```

**Padrão de código a seguir:** System prompt deve ter 10 seções obrigatórias. Seção [7] = contra-argumentação com 8 benchmarks setoriais (ABRH, GPTW, Gupy, Robert Half, LinkedIn, Glassdoor, IBGE/PNAD, MTE/CAGED). Referência: Anexo A (anatomia de prompt 10 seções), Crença 11.

**Arquivos a modificar:**
- `app/domains/[cada_dominio]/agents/[agente]_system_prompt.py` (todos os 14 agentes)

**Esforço estimado:** 4h (copiar padrão para todos os prompts) | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `grep -rn "CONTRA-ARGUMENTAÇÃO" app/domains/` → match em TODOS os 14 agentes
- [ ] Teste: "contrate sem entrevista" → agente contra-argumenta com dados
- [ ] Cada contra-argumentação cita pelo menos 1 benchmark setorial

---

### RM-09: Confiança Artificial (Fórmula Fake)

**O que está errado:** O sistema usa fórmulas heurísticas para calcular confiança (ex: `max(0.6, min(best_score * 3, 0.95))`) que mascaram a incerteza real.

**Por que importa:** Scores artificialmente altos levam a decisões automáticas (APPLY_SILENT >= 0.85) que na verdade deveriam pedir confirmação humana (ASK_USER < 0.70).

**Referência:** Dimensão 10.2, Crença 10

**Passo-a-passo para resolver:**

1. Identificar todas as fórmulas de confiança:
```bash
grep -rn "confidence\|score.*max\|score.*min\|best_score" app/ --include="*.py"
```

2. Substituir por confiança real baseada em dados:
```python
# ANTES (ERRADO):
confidence = max(0.6, min(best_score * 3, 0.95))

# DEPOIS (CORRETO):
confidence = calculate_real_confidence(
    keyword_matches=keyword_result.matches,
    llm_classification=llm_result.intent if llm_result else None,
    historical_accuracy=get_historical_accuracy(intent, company_id)
)

def calculate_real_confidence(keyword_matches, llm_classification, historical_accuracy):
    if not keyword_matches and not llm_classification:
        return 0.0  # Sem dados = sem confiança
    base = len(keyword_matches) / max_possible_matches
    if llm_classification:
        base = (base + llm_classification.confidence) / 2
    if historical_accuracy:
        base *= historical_accuracy  # Calibrar com histórico
    return min(base, 0.99)  # Nunca 1.0
```

3. Garantir que ConfidencePolicy usa os thresholds corretos:
   - >= 0.85 → APPLY_SILENT
   - 0.70-0.84 → APPLY_NOTIFY
   - < 0.70 → ASK_USER

**Padrão de código a seguir:** Confiança deve ser calculada com dados reais: keyword_matches + llm_confidence + historical_accuracy. Nunca `max(X, min(Y, Z))`. Referência: Crença 10, ConfidencePolicy 3 níveis (Anexo E, G-C2).

**Arquivos a modificar:**
- `app/shared/agents/intent_router.py` (ou equivalente)
- `app/services/confidence_policy_service.py`
- Qualquer arquivo com fórmula de confiança

**Esforço estimado:** 6h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Nenhuma fórmula `max(X, min(Y, Z))` para confiança no código
- [ ] `grep -rn "max.*min.*score\|min.*max.*score" app/` → 0 resultados
- [ ] Confiança 0.0 quando não há dados
- [ ] Integração com ConfidencePolicy funcionando com 3 níveis

---

### RM-10: Circuit Breaker Ausente em Integração Externa

**O que está errado:** Chamadas a serviços externos (LLM providers, APIs de email, WhatsApp) não têm circuit breaker configurado.

**Por que importa:** Sem circuit breaker, uma falha externa causa cascade failure — o sistema inteiro fica lento ou cai. Violação da Crença 07 (Resiliente por Design) e Production Readiness #1.

**Referência:** Dimensão 12.3, AP-5.3

**Passo-a-passo para resolver:**

1. Usar o circuit breaker já existente ou criar:
```python
from app.shared.circuit_breaker import CircuitBreaker

llm_breaker = CircuitBreaker(
    name="llm_provider",
    failure_threshold=5,
    recovery_timeout=30,  # segundos
    half_open_max_calls=2
)

async def call_llm(prompt):
    async with llm_breaker:
        return await llm_client.complete(prompt)
```

2. Verificar que TODA integração externa tem circuit breaker:
   - LLM providers (OpenAI, Anthropic, Google)
   - Email (SendGrid, SES)
   - WhatsApp (API)
   - ATS integrations
   - Calendar APIs

3. Adicionar alerting quando circuit abre:
```python
@llm_breaker.on_open
async def alert_circuit_open(breaker_name):
    await alert_service.send(
        level="P1",
        message=f"Circuit breaker {breaker_name} OPEN — fallback ativo",
        channel="ops-alerts"
    )
```

**Padrão de código a seguir:** Usar padrão `CircuitBreaker` com 3 estados (CLOSED → OPEN → HALF_OPEN). `failure_threshold=5`, `recovery_timeout=30s`. Referência: Crença 07, Production Readiness #1/#2, AP-5.3 (Anexo B).

**Arquivos a modificar:**
- `app/shared/circuit_breaker.py` (verificar/criar)
- Cada service que faz chamada externa
- `app/shared/agents/llm_client.py` (ou equivalente)

**Esforço estimado:** 4h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `grep -rn "CircuitBreaker\|circuit_breaker" app/` → match em todos os services externos
- [ ] Circuit breaker abre após 5 falhas consecutivas
- [ ] Recovery automático em HALF_OPEN após 30s
- [ ] Alerta enviado quando circuit abre

---

### RM-11: Token Budget sem Pre-Call Check

**O que está errado:** O sistema não verifica o orçamento de tokens ANTES de chamar o LLM — só conta depois. Se o budget estourou, a chamada já foi feita (e cobrada).

**Por que importa:** Violação da Crença 09 (Consciente de Custos). Empresa pode ter custos inesperados. Sem pre-call check, não há como impor limites reais.

**Referência:** Dimensão 12.4, Production Readiness #6

**Passo-a-passo para resolver:**

1. Adicionar pre-call check no client LLM:
```python
async def _pre_call_budget_check(self, company_id: str, estimated_tokens: int):
    budget = await token_budget_service.get_remaining(company_id)
    if budget.remaining < estimated_tokens:
        if budget.remaining <= 0:
            raise BudgetExhaustedError(f"Token budget exausto para company {company_id}")
        logger.warning(f"Budget baixo: {budget.remaining} tokens restantes")

    if budget.usage_percent >= 80:
        await alert_service.send_budget_warning(company_id, budget.usage_percent)
```

2. Integrar ANTES de cada chamada LLM:
```python
async def complete(self, prompt, company_id, **kwargs):
    estimated = self._estimate_tokens(prompt)
    await self._pre_call_budget_check(company_id, estimated)
    result = await self._llm_call(prompt, **kwargs)
    await token_budget_service.record_usage(company_id, result.usage)
    return result
```

3. Configurar alertas em 80% e 100% do budget.

**Padrão de código a seguir:** Pre-call check ANTES de `llm_client.complete()`. `BudgetExhaustedError` quando budget=0. Alertas em 80% e 100%. Referência: Crença 09, Production Readiness #6, Dimensão 12.4.

**Arquivos a modificar:**
- `app/shared/agents/llm_client.py` (ou equivalente)
- `app/services/token_budget_service.py`

**Esforço estimado:** 4h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Budget exausto → erro 429 (não faz chamada ao LLM)
- [ ] Alerta em 80% do budget
- [ ] Alerta em 100% do budget
- [ ] `grep -rn "pre_call_budget\|budget_check" app/` → match no client LLM

---

### RM-12: Observabilidade Insuficiente

**O que está errado:** Agente não tem `ReActObserver` configurado, ou métricas/traces não estão sendo coletados.

**Por que importa:** Sem observabilidade, não há como debugar problemas, medir performance ou rastrear decisões. Violação da Crença 08.

**Referência:** Dimensão 12, Anexo C, AP-1.6

**Passo-a-passo para resolver:**

1. Verificar que todo agente registra observer:
```python
class MyReActAgent(BaseAgent):
    def __init__(self, ...):
        self.observer = ReActObserver(
            agent_type=self.agent_type,
            company_id=company_id
        )
```

2. Verificar que observer coleta:
   - `iteration_count` por execução
   - `tool_calls` com duração
   - `token_usage` por chamada
   - `error_rate` por agente
   - `latency_p95` por agente
   - `decision_trace` (reasoning completo)

3. Adicionar health alerts:
```python
HEALTH_ALERT_RULES = {
    "error_rate > 5%": "P1 - Investigar agente",
    "latency_p95 > 10s": "P2 - Otimizar",
    "token_usage > budget * 0.8": "P1 - Budget warning",
}
```

**Padrão de código a seguir:** Todo agente deve instanciar `ReActObserver` no `__init__`. Observer coleta: iteration_count, tool_calls, token_usage, error_rate, latency_p95. Referência: AP-1.6 (Anexo B), Anexo C (schemas de observabilidade).

**Arquivos a modificar:**
- `app/shared/agents/react_observer.py`
- Cada agente que não tem observer configurado

**Esforço estimado:** 6h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `grep -rn "ReActObserver\|observer" app/domains/*/agents/*react_agent*` → match em todos
- [ ] LangSmith mostra traces completos de cada execução
- [ ] Métricas Prometheus exportadas por agente

---

### RM-13: Degradation Path Incompleto

**O que está errado:** Quando o LLM provider principal falha, o sistema não tenta automaticamente o próximo provider na cadeia de fallback.

**Por que importa:** Crença 07 (Resiliente por Design). Se Claude cai, o sistema deve tentar OpenAI, depois Gemini, e só então retornar erro 503 com mensagem clara.

**Referência:** Production Readiness #2, Dimensão 12.3

**Depende de:** RM-10 (Circuit Breaker)

**Passo-a-passo para resolver:**

1. Implementar fallback chain:
```python
LLM_FALLBACK_CHAIN = [
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
    {"provider": "openai", "model": "gpt-4o"},
    {"provider": "google", "model": "gemini-2.0-flash"},
]

async def complete_with_fallback(prompt, company_id, **kwargs):
    for provider_config in LLM_FALLBACK_CHAIN:
        try:
            async with circuit_breaker[provider_config["provider"]]:
                return await call_provider(provider_config, prompt, **kwargs)
        except (ProviderError, CircuitBreakerOpen) as e:
            logger.warning(f"Fallback: {provider_config['provider']} falhou: {e}")
            continue
    raise ServiceUnavailableError("Todos os LLM providers indisponíveis")
```

2. Testar a cadeia completa end-to-end:
   - Mock: Claude offline → deve usar OpenAI
   - Mock: Claude + OpenAI offline → deve usar Gemini
   - Mock: Todos offline → deve retornar 503 com mensagem clara

**Padrão de código a seguir:** Fallback chain: `LLM_FALLBACK_CHAIN = [anthropic, openai, google]`. Tentar próximo provider quando `CircuitBreakerOpen` ou `ProviderError`. 503 só quando todos falham. Referência: Production Readiness #2, Crença 07.

**Arquivos a modificar:**
- `app/shared/agents/llm_client.py`
- `app/config/llm_config.py`

**Esforço estimado:** 8h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Teste: mock Claude offline → resposta vem do OpenAI
- [ ] Teste: mock todos offline → 503 com mensagem "serviço temporariamente indisponível"
- [ ] Log registra qual provider respondeu
- [ ] Fallback chain testada em CI

---

### RM-14: Few-Shot Examples Inadequados ou Ausentes

**O que está errado:** O system prompt não contém exemplos concretos (few-shot) ou os exemplos existentes não cobrem edge cases relevantes.

**Por que importa:** Sem few-shot, o LLM produz respostas inconsistentes. Exemplos negativos (de recusa ética) são especialmente importantes para evitar que o agente execute pedidos discriminatórios.

**Referência:** Dimensão 10, Anexo A (seção [10] do prompt)

**Passo-a-passo para resolver:**

1. Cada agente deve ter pelo menos 3 few-shot examples:
   - 1 caminho feliz (ação normal)
   - 1 edge case (dado incompleto ou ambíguo)
   - 1 recusa ética (pedido discriminatório)

2. Formato padrão:
```python
FEW_SHOT_EXAMPLES = [
    {
        "user": "Busque candidatos sênior em Python para São Paulo",
        "assistant": '{"thought": "Busca válida com critérios objetivos", "action": "tool_call", "tool_name": "search_candidates", "tool_args": {"skills": ["Python"], "seniority": "senior", "location": "São Paulo"}}'
    },
    {
        "user": "Me mostre o pipeline",
        "assistant": '{"thought": "Pergunta ambígua, preciso perguntar qual vaga", "action": "respond", "response": "Para qual vaga você gostaria de ver o pipeline? Posso listar as vagas ativas."}'
    },
    {
        "user": "Busque apenas candidatos homens jovens",
        "assistant": '{"thought": "Pedido discriminatório por gênero e idade - violar LGPD e CLT", "action": "respond", "response": "Não posso filtrar por gênero ou idade — isso viola a legislação trabalhista (CLT Art. 5°) e a LGPD. Posso buscar por competências técnicas, experiência e localização. Quais critérios profissionais são relevantes para esta vaga?"}'
    }
]
```

3. Verificar cobertura:
```bash
grep -rn "FEW_SHOT\|few_shot\|examples" app/domains/*/agents/*system_prompt*
```

**Padrão de código a seguir:** Mínimo 3 few-shot examples por agente: 1 caminho feliz, 1 edge case, 1 recusa ética. Formato JSON com `thought/action/tool_name/tool_args/response`. Referência: Anexo A (seção [10] do prompt), MP-2.2 (Anexo K).

**Arquivos a modificar:**
- `app/domains/[cada_dominio]/agents/[agente]_system_prompt.py`

**Esforço estimado:** 3h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Todo agente tem >= 3 few-shot examples
- [ ] Pelo menos 1 exemplo de recusa ética por agente
- [ ] Examples incluem formato JSON esperado

---

### RM-15: FairnessGuard Ausente na SAÍDA do ReAct Loop

**O que está errado:** FairnessGuard verifica o INPUT do usuário, mas a RESPOSTA gerada pelo LLM não é verificada.

**Por que importa:** O LLM pode gerar conteúdo com viés mesmo com input limpo. Gap G-RL1.

**Depende de:** RM-02

**Passo-a-passo para resolver:**

1. Adicionar check na saída do loop:
```python
async def _post_check(self, output: AgentOutput) -> AgentOutput:
    guard = FairnessGuard()
    implicit_warnings = guard.check_implicit_bias(output.response)
    if implicit_warnings:
        output.response = self._sanitize_response(output.response, implicit_warnings)
        output.metadata["fairness_output_warnings"] = implicit_warnings
    return output
```

2. Integrar no fluxo de saída:
```python
async def execute(self, input_data):
    input_data = await self._pre_check(input_data)
    result = await self._process(input_data)
    result = await self._post_check(result)  # NOVO
    return result
```

**Padrão de código a seguir:** Usar `FairnessGuard.check_implicit_bias()` na resposta do agente. Soft warning (não bloqueia), registra e sanitiza. Hook: `_post_check()` no DomainWorkflow base. Referência: Gap G-RL1 (Anexo E), Parte II (FairnessGuard Camada 2).

**Arquivos a modificar:**
- `app/shared/agents/domain_workflow.py`
- `app/shared/agents/react_loop.py`

**Esforço estimado:** 4h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Resposta do agente com "boa aparência" → warning gerado e registrado
- [ ] Check na saída não bloqueia (soft warning), apenas registra e sanitiza

---

### RM-16: PII Scrubbing Ausente na Resposta do Agente

**O que está errado:** A resposta do agente pode conter dados pessoais de candidatos (nome, email, CPF) que foram incluídos pelo LLM.

**Por que importa:** Gap G-RL2. Dados pessoais na resposta podem ser logados, armazenados em cache ou exibidos em contextos não autorizados.

**Depende de:** RM-01

**Passo-a-passo para resolver:**

1. Aplicar PII filter na saída:
```python
async def _post_check(self, output: AgentOutput) -> AgentOutput:
    output.response = PromptPIIFilter.sanitize_prompt(output.response)
    return output
```

2. Exceção: quando o agente está MOSTRANDO dados do candidato ao recrutador (ex: `view_candidate_profile`), PII é permitida na resposta mas deve ser marcada:
```python
if output.metadata.get("contains_candidate_data"):
    output.metadata["pii_present"] = True  # Flag para frontend
else:
    output.response = PromptPIIFilter.sanitize_prompt(output.response)
```

**Padrão de código a seguir:** Aplicar `PromptPIIFilter.sanitize_prompt()` na saída. Exceção: quando `contains_candidate_data=True`, marcar `pii_present=True` sem mascarar. Referência: Gap G-RL2 (Anexo E), RM-01 (mesma classe).

**Arquivos a modificar:**
- `app/shared/agents/domain_workflow.py` (post-check)

**Esforço estimado:** 4h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Resposta genérica do agente não contém PII
- [ ] Resposta com dados de candidato tem flag `pii_present=True`

---

### RM-17: Negation Detection Ausente

**O que está errado:** O intent router não detecta negação em inputs ("NÃO quero ranking" é interpretado como "quero ranking").

**Por que importa:** Dimensão 10.2. Ações incorretas executadas por má interpretação do intent.

**Passo-a-passo para resolver:**

1. Adicionar detecção de negação no router:
```python
NEGATION_PATTERNS = [
    r'\b(não|nao|nunca|jamais|sem|nenhum|nenhuma|pare|cancele|desista)\b',
    r'\b(don\'t|do not|never|stop|cancel|no)\b',
]

def detect_negation(text: str) -> bool:
    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def classify_intent(text: str):
    has_negation = detect_negation(text)
    raw_intent = keyword_match(text)
    if has_negation and raw_intent:
        return Intent(
            action=f"negate_{raw_intent.action}",
            confidence=raw_intent.confidence * 0.5  # Reduzir confiança
        )
```

**Padrão de código a seguir:** Padrão `NEGATION_PATTERNS` com regex para pt-BR e en-US. Quando negação detectada, prefixar intent com `negate_` e reduzir confiança × 0.5. Referência: Dimensão 10.2, Crença 10.

**Arquivos a modificar:**
- `app/shared/agents/intent_router.py`

**Esforço estimado:** 3h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] "não quero ranking" → não executa ranking
- [ ] "pare de enviar emails" → não envia email
- [ ] Confiança reduzida quando há negação detectada

---

## P2 — MÉDIO: MELHORIAS DE ARQUITETURA

> Itens P2 devem ser planejados para **sprints futuros (30-60 dias)**. Melhoram a manutenibilidade e robustez.

---

### RM-18: Padrão 4 Arquivos Não Seguido pelo Agente

**O que está errado:** Agente não segue o padrão canônico de 4 arquivos: `react_agent.py`, `tool_registry.py`, `system_prompt.py`, `stage_context.py`.

**Por que importa:** Inconsistência arquitetural dificulta manutenção e auditoria. Difícil auditar um agente que está estruturado diferente de todos os outros.

**Referência:** Anexo A

**Passo-a-passo para resolver:**

1. Verificar cada domínio:
```bash
for domain in $(ls app/domains/); do
  echo "=== $domain ==="
  ls app/domains/$domain/agents/ 2>/dev/null
done
```

2. Para domínios faltando arquivos, criar seguindo o gabarito do Anexo A:
   - `react_agent.py` — classe do agente herdando de `BaseAgent`
   - `tool_registry.py` — lista de `ToolDefinition` com name, description, function, schema
   - `system_prompt.py` — prompt com 10 seções obrigatórias
   - `stage_context.py` — contexto dinâmico por estágio/situação

3. Migrar lógica dispersa para os arquivos canônicos.

**Padrão de código a seguir:** 4 arquivos canônicos por domínio: `react_agent.py` (herda BaseAgent), `tool_registry.py` (lista ToolDefinition), `system_prompt.py` (10 seções), `stage_context.py` (contexto dinâmico). Referência: Anexo A completo.

**Arquivos a modificar:**
- Cada `app/domains/*/agents/` que não segue o padrão de 4 arquivos
- Referência de gabarito: Anexo A (arquivos 1-4 com boilerplate completo)

**Esforço estimado:** 6h (por agente fora do padrão) | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Todo domínio em `app/domains/*/agents/` tem os 4 arquivos
- [ ] `system_prompt.py` tem as 10 seções obrigatórias

---

### RM-19: Stage Context Ausente ou Incompleto

**O que está errado:** Agente não recebe contexto específico do estágio em que o candidato/vaga está.

**Por que importa:** Sem contexto de estágio, o agente dá respostas genéricas. Candidato em fase de oferta recebe instruções de sourcing — experiência confusa e decisões incorretas.

**Depende de:** RM-18

**Passo-a-passo para resolver:**

1. Criar `stage_context.py` para o domínio:
```python
STAGE_CONTEXTS = {
    "sourcing": "Você está no estágio de sourcing. O candidato ainda não foi contatado.",
    "screening": "Candidato em triagem. Verifique WSI score e fit com a vaga.",
    "interview": "Candidato em fase de entrevista. Foque em agendamento e feedback.",
    "offer": "Candidato recebeu proposta. Foque em negociação e onboarding.",
}

def get_stage_context(stage: str) -> str:
    return STAGE_CONTEXTS.get(stage, "Estágio desconhecido — peça clarificação.")
```

2. Injetar via `extra_context` no agente.

**Padrão de código a seguir:** Dicionário `STAGE_CONTEXTS` com contexto por estágio do pipeline. Injetar via `extra_context` no agente. Referência: Anexo A (arquivo 4 do padrão canônico).

**Arquivos a modificar:**
- Criar: `app/domains/<domínio>/agents/stage_context.py` (para cada domínio sem)
- Modificar: `app/shared/agents/react_loop.py` (injetar `extra_context` com stage)

**Esforço estimado:** 4h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Todo domínio tem `stage_context.py` com dicionário `STAGE_CONTEXTS`
- [ ] Agente recebe contexto correto para cada estágio (verificar via logs)
- [ ] Estágio desconhecido → fallback explícito ("Estágio desconhecido — peça clarificação")

---

### RM-20: Memória sem Decay Factor / sem Limite

**O que está errado:** Memória do agente cresce indefinidamente ou não aplica decay factor para informações antigas.

**Por que importa:** Memória ilimitada causa context overflow (tokens), alucinações por contexto antigo irrelevante, e custo crescente de tokens. Decay factor garante que informações recentes tenham prioridade.

**Referência:** AP-5.4 (Anexo B)

**Passo-a-passo para resolver:**

1. Limitar working memory:
```python
conversation_history = conversation_history[-5:]  # Últimas 5 interações
```

2. Aplicar decay factor em memória de longo prazo:
```python
DECAY_FACTOR = 0.95
relevance = base_relevance * (DECAY_FACTOR ** days_since_interaction)
if relevance < 0.1:
    archive_or_delete(memory_entry)
```

**Padrão de código a seguir:** Working memory: `conversation_history[-5:]`. Long-term memory: `DECAY_FACTOR=0.95`, arquivar quando `relevance < 0.1`. Referência: AP-5.4 (Anexo B), Anexo A (memória 3 níveis).

**Arquivos a modificar:**
- Modificar: `app/shared/agents/react_loop.py` (limitar working memory)
- Criar/Modificar: `app/services/memory_service.py` (decay factor)

**Esforço estimado:** 4h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `conversation_history` nunca excede 5 entradas no working memory
- [ ] Memória com `relevance < 0.1` é arquivada automaticamente
- [ ] Decay aplicado em cada consulta de longo prazo

---

### RM-21: Drift Detection Desligado ou Não Configurado

**O que está errado:** Os 4 triggers de drift detection não estão ativos ou não geram alertas.

**Por que importa:** Sem drift detection, degradações graduais (score inflation, latência crescente, custo disparando) passam despercebidas até causar impacto visível ao cliente. Production Readiness exige monitoramento contínuo.

**Referência:** Screening Compliance, Anexo C

**Passo-a-passo para resolver:**

1. Verificar que Celery beat tem os 4 jobs configurados:
```python
CELERY_BEAT_SCHEDULE = {
    "check-score-drift": {"task": "check_wsi_score_drift", "schedule": crontab(hour=6)},
    "check-approval-drift": {"task": "check_approval_rate_drift", "schedule": crontab(hour=6)},
    "check-cost-drift": {"task": "check_ai_cost_drift", "schedule": crontab(hour=6)},
    "check-latency-drift": {"task": "check_latency_drift", "schedule": crontab(hour=6)},
}
```

2. Configurar thresholds:
   - Score WSI varia > 0.5 em 30 dias → alerta P1
   - Taxa de aprovação varia > 10% → alerta P1
   - Custo de IA aumenta > 20% → alerta P2
   - Latência P95 aumenta > 50% → alerta P2

**Padrão de código a seguir:** 4 jobs Celery beat: score drift (>0.5/30d), approval drift (>10%), cost drift (>20%), latency drift (P95 >50%). Referência: Screening Compliance (Model Drift Detection), Anexo C.

**Arquivos a modificar:**
- Modificar: `app/celery_config.py` ou equivalente (adicionar 4 jobs)
- Criar: `app/tasks/drift_detection.py`
- Criar: `app/services/drift_alert_service.py`

**Esforço estimado:** 4h | **Responsável:** Backend + Infra

**Critério de aceitação:**
- [ ] 4 jobs Celery beat configurados e rodando (verificar via `celery inspect scheduled`)
- [ ] Score drift > 0.5 em 30 dias → alerta P1 gerado
- [ ] Métricas de drift visíveis no dashboard

---

### RM-22: Guardrails Não Configurados no Banco

**O que está errado:** A tabela `guardrails` existe (migration 020) mas não tem seed data ou não está sendo consultada pelo workflow.

**Por que importa:** Guardrails no banco permitem configuração por empresa (multi-tenant) e ativação/desativação sem deploy. Sem seed data, workflows rodam sem proteções — equivale a não ter guardrails.

**Referência:** Anexo D

**Passo-a-passo para resolver:**

1. Verificar seed data:
```sql
SELECT COUNT(*) FROM guardrails WHERE is_active = true;
-- Deve retornar >= 13 (ver lista canônica no Anexo D)
```

2. Se vazio, inserir os 13 guardrails canônicos via migration ou seed script.

3. Verificar que `DomainWorkflow` consulta guardrails ativos:
```python
async def _load_guardrails(self, company_id):
    return await guardrail_repo.get_active(company_id=company_id)
```

**Padrão de código a seguir:** 13 guardrails canônicos devem existir na tabela com `is_active=true`. Usar seed migration. `DomainWorkflow._load_guardrails()` consulta por `company_id`. Referência: Anexo D (lista completa dos 13 guardrails).

**Arquivos a modificar:**
- Criar: migration seed para inserir 13 guardrails canônicos
- Modificar: `app/shared/agents/domain_workflow.py` (adicionar `_load_guardrails()`)

**Esforço estimado:** 3h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] `SELECT COUNT(*) FROM guardrails WHERE is_active = true` retorna >= 13
- [ ] `DomainWorkflow._load_guardrails(company_id)` retorna lista filtrada por empresa
- [ ] Guardrail desativado → workflow não o aplica

---

### RM-23: Testes de Fairness Fora do CI/CD

**O que está errado:** Testes de fairness (golden dataset, four-fifths rule) existem mas não rodam automaticamente no CI.

**Por que importa:** Testes de fairness que não rodam no CI ficam desatualizados e são ignorados. Four-fifths rule como gate de deploy é exigência EEOC/OFCCP e melhor prática para recrutamento IA.

**Referência:** Screening Compliance, Nível 1 (Pre-Deployment)

**Passo-a-passo para resolver:**

1. Criar golden dataset com 100 candidatos:
   - 25 por quartil de score
   - Mix de: universidade, bootcamp, autodidata, transição de carreira
   - Mix de gênero, idade, região

2. Adicionar no CI/CD:
```yaml
fairness-test:
  script:
    - python -m pytest tests/fairness/ -v
    - python scripts/run_four_fifths_check.py
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

3. Four-fifths rule como gate de deploy:
```python
def check_four_fifths(results_by_group):
    reference_rate = max(results_by_group.values())
    for group, rate in results_by_group.items():
        ratio = rate / reference_rate
        if ratio < 0.80:
            raise FairnessGateFailure(f"Grupo {group}: ratio {ratio:.2f} < 0.80")
```

**Padrão de código a seguir:** Golden dataset: 100 candidatos (25/quartil, mix trajetórias). Four-fifths rule como gate: `ratio < 0.80` bloqueia deploy. CI/CD: `pytest tests/fairness/ -v`. Referência: Parte V (Framework de Teste de Viés), PARTE III (Bias Audit Dashboard).

**Arquivos a modificar:**
- Criar: `tests/fairness/test_four_fifths.py`
- Criar: `tests/fairness/golden_dataset.json` (100 candidatos)
- Criar: `scripts/run_four_fifths_check.py`
- Modificar: `.gitlab-ci.yml` ou equivalente CI (adicionar stage fairness)

**Esforço estimado:** 6h | **Responsável:** Backend + Infra

**Critério de aceitação:**
- [ ] Golden dataset com 100 candidatos (25 por quartil)
- [ ] `pytest tests/fairness/` passa no CI
- [ ] Four-fifths ratio < 0.80 → pipeline falha (gate)
- [ ] Resultados por grupo demográfico visíveis no relatório

---

### RM-24: ConfidencePolicy Limitada a Um Agente

**O que está errado:** `ConfidencePolicyService` só é usado no Job Wizard (gap G-C3). Decisões de triagem, sourcing e pipeline não usam.

**Por que importa:** Se apenas o Wizard usa ConfidencePolicy, triagem e sourcing tomam decisões com alta incerteza sem pedir confirmação humana. Viola Crença 10 (determinismo) e EU AI Act Art. 14 (human oversight).

**Referência:** Dimensão 10.4, Gap G-C3

**Passo-a-passo para resolver:**

1. Integrar no `DomainWorkflow` base:
```python
async def _apply_confidence_policy(self, action, confidence, company_id):
    policy = ConfidencePolicyService()
    decision = policy.evaluate(confidence)
    if decision == "APPLY_SILENT":
        return await self._execute_action(action)
    elif decision == "APPLY_NOTIFY":
        await self._notify_user(action, confidence)
        return await self._execute_action(action)
    else:  # ASK_USER
        return await self._request_confirmation(action, confidence)
```

2. Aplicar em TODOS os domínios que tomam decisões sobre candidatos.

**Padrão de código a seguir:** Integrar `ConfidencePolicyService.evaluate()` no DomainWorkflow base, não apenas no Wizard. 3 níveis: APPLY_SILENT (>=0.85), APPLY_NOTIFY (0.70-0.84), ASK_USER (<0.70). Referência: Crença 10, Parte IV (EU AI Act), Gap G-C3 (Anexo E).

**Arquivos a modificar:**
- Modificar: `app/shared/agents/domain_workflow.py` (integrar `_apply_confidence_policy`)
- Modificar: `app/services/confidence_policy_service.py` (generalizar para todos domínios)
- Modificar: cada `app/domains/*/workflow.py` que toma decisões sobre candidatos

**Esforço estimado:** 6h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Confiança >= 0.85 → ação executada silenciosamente
- [ ] Confiança 0.70-0.84 → ação executada + notificação ao recrutador
- [ ] Confiança < 0.70 → recrutador confirma antes de executar
- [ ] Todos os domínios usam ConfidencePolicy (não apenas Wizard)

---

### RM-25: Wiring Desconectado

**O que está errado:** Componente/endpoint/hook/tool existe no código mas não está conectado ao fluxo real. "Existe" mas não "funciona".

**Por que importa:** Código desconectado cria ilusão de funcionalidade. Recrutador vê botão que não funciona, endpoint existe mas nunca é chamado. A Dimensão 1 (Wiring) é o achado mais frequente nas auditorias.

**Referência:** Dimensão 1 (Integração/Wiring) — o achado mais comum nas auditorias

**Passo-a-passo para resolver:**

1. Para cada item identificado como "desconectado":
   - Frontend: verificar se hook é importado E chamado por componente
   - Backend: verificar se endpoint tem rota registrada E proxy frontend
   - Tool: verificar se está no registry E o agente a usa

2. Procedimento de verificação:
```bash
# Frontend: hook não usado
grep -rn "useMyHook" src/ | head -5

# Backend: endpoint sem proxy
grep -rn "/api/v1/my-endpoint" plataforma-lia/vite.config.ts

# Tool: não no registry
grep -rn "my_tool" app/domains/*/agents/*tool_registry*
```

3. Para cada desconexão, escolher: CONECTAR ou REMOVER (código morto).

**Padrão de código a seguir:** Para frontend: hook importado + chamado. Para backend: rota registrada + proxy. Para tool: no registry + agente usa. Código morto deve ser removido. Referência: Dimensão 1 (Wiring), PARTE XI nota 6.

**Arquivos a modificar:**
- Variável por item (cada achado de wiring desconectado terá arquivos diferentes)
- Referência: usar comandos `grep` listados acima para identificar os arquivos

**Esforço estimado:** Variável (1-4h por item) | **Responsável:** Backend ou Frontend

**Critério de aceitação:**
- [ ] Todo hook importado é efetivamente chamado por pelo menos um componente
- [ ] Todo endpoint tem rota registrada E proxy configurado
- [ ] Toda tool está no registry E é referenciada pelo system prompt do agente
- [ ] Código morto removido (nenhum import sem uso)

---

### RM-26: EU AI Act Compliance Gaps nos Prompts

**O que está errado:** System prompts não referenciam obrigações do EU AI Act (Art. 14, 52, Anexo III).

**Por que importa:** EU AI Act entra em vigor com penalidades de até 35M EUR ou 7% do faturamento global. Sistemas de IA em recrutamento são classificados como alto risco (Anexo III). Compliance nos prompts é obrigatório.

**Referência:** Gap G-P1, Dimensão 13.6

**Passo-a-passo para resolver:**

1. Adicionar instrução nos prompts:
```python
EU_AI_ACT_SECTION = """
## CONFORMIDADE EU AI ACT
- Este sistema é classificado como ALTO RISCO (Anexo III — sistemas de IA em recrutamento)
- Art. 14: human oversight obrigatório — NUNCA tome decisões finais sem aprovação humana
- Art. 52: transparência — SEMPRE informe que IA está envolvida
- FRIA (Fundamental Rights Impact Assessment) deve estar documentada
- Toda decisão deve ser explicável e rastreável
"""
```

**Padrão de código a seguir:** Adicionar bloco `EU_AI_ACT_SECTION` referenciando Art. 14, 52, Anexo III nos system prompts. Classificação: alto risco. Referência: PARTE IV (EU AI Act), Gap G-P1 (Anexo E), MP-1.1 (Anexo K).

**Arquivos a modificar:**
- Modificar: cada `app/domains/*/agents/system_prompt.py` (adicionar seção EU AI Act)
- Criar: `app/shared/compliance/eu_ai_act_section.py` (bloco reutilizável)

**Esforço estimado:** 3h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Todos os system prompts incluem seção EU AI Act
- [ ] Art. 14, 52 e Anexo III referenciados explicitamente
- [ ] Classificação "alto risco" presente

---

### RM-27: WCAG 2.1 AA Não Atendido

**O que está errado:** Componentes frontend não atendem WCAG 2.1 AA (faltam aria-labels, contraste insuficiente, navegação por teclado ausente).

**Por que importa:** Acessibilidade é Inegociável #8 da plataforma e requisito legal em muitos mercados. Candidatos com deficiência visual ou motora não conseguem usar a plataforma sem WCAG 2.1 AA.

**Referência:** Inegociável #8, Crença 13, Dimensão 3

**Passo-a-passo para resolver:**

1. Audit com axe-core:
```bash
npx axe-cli http://localhost:3000 --rules wcag2aa
```

2. Checklist por componente:
   - [ ] `aria-label` em todos os botões sem texto visível
   - [ ] `role` em componentes interativos custom
   - [ ] Contraste >= 4.5:1 (texto normal), >= 3:1 (texto grande)
   - [ ] `focus-visible` com ring visível
   - [ ] `sr-only` para textos de screen reader
   - [ ] Tab order lógico
   - [ ] `prefers-reduced-motion` respeitado

3. Para cada violação encontrada pelo axe-core, corrigir o componente.

**Padrão de código a seguir:** Usar axe-core para audit. Checklist: `aria-label`, `role`, contraste >=4.5:1, `focus-visible`, `sr-only`, tab order, `prefers-reduced-motion`. Referência: Crença 13, Inegociável #8, Dimensão 3.

**Arquivos a modificar:**
- Todos os componentes em `plataforma-lia/src/components/`
- Todos os componentes de página em `plataforma-lia/src/app/(protected)/`
- Criar: `tests/a11y/axe_audit.test.ts`

**Esforço estimado:** 8h | **Responsável:** Frontend

**Critério de aceitação:**
- [ ] `npx axe-cli` retorna 0 violações WCAG 2.1 AA
- [ ] Todo botão sem texto visível tem `aria-label`
- [ ] Contraste >= 4.5:1 em todo texto normal
- [ ] Tab order lógico em todos os formulários
- [ ] `prefers-reduced-motion` respeitado em animações

---

### RM-38: Data Flow Quebrado ou Incompleto (Dimensão 2)

**O que está errado:** Dados não fluem corretamente entre componentes. Exemplos: frontend envia payload mas backend ignora campos, API retorna dados que frontend não renderiza, transformações perdem campos no caminho.

**Por que importa:** Data flow quebrado causa dados fantasma (existem no banco mas não aparecem na UI), campos que o usuário preenche mas são descartados silenciosamente, e inconsistência entre o que o backend sabe e o que o frontend mostra.

**Referência:** Dimensão 2 (Data Flow), AP-4.2 (Anexo B)

**Passo-a-passo para resolver:**

1. Mapear o fluxo de dados completo para a feature auditada:
```bash
grep -rn "fieldName" plataforma-lia/src/ --include="*.ts" --include="*.tsx"
grep -rn "field_name" lia-agent-system/app/ --include="*.py"
```

2. Verificar cada ponto de transformação:
   - Frontend form → API request: campo está no payload?
   - API request → backend handler: campo é lido do request?
   - Backend handler → banco: campo é persistido?
   - Banco → API response: campo é retornado?
   - API response → frontend: campo é renderizado?

3. Para cada campo fantasma, decidir: CONECTAR (se deveria funcionar) ou REMOVER (se foi abandonado).

**Padrão de código a seguir:** Todo campo deve ter caminho completo: form → payload → handler → DB → response → render. Se qualquer ponto está ausente, o campo é "fantasma". Usar TypeScript types compartilhados para garantir consistência frontend↔backend. Referência: Dimensão 2, AP-4.2.

**Arquivos a modificar:**
- Variável por feature (depende de qual data flow está quebrado)
- Verificar: schemas de API, handlers, componentes de formulário

**Esforço estimado:** 2-4h por data flow quebrado | **Responsável:** Backend + Frontend

**Critério de aceitação:**
- [ ] Campo preenchido no formulário → persiste no banco → aparece na UI
- [ ] Nenhum campo enviado pelo frontend é silenciosamente ignorado pelo backend
- [ ] API response inclui todos os campos que o frontend renderiza

---

### RM-39: Backend/API Incorreto ou Incompleto (Dimensão 6)

**O que está errado:** Endpoints de API existem mas retornam dados incorretos, não tratam erros adequadamente, ou têm lógica de negócio com bugs.

**Por que importa:** API incorreta causa comportamento errado em toda a plataforma. Se um endpoint de movimentação de candidato não valida transições, candidatos podem ser movidos para stages inválidos.

**Referência:** Dimensão 6 (Backend/API), Dimensão 1 (Wiring)

**Passo-a-passo para resolver:**

1. Verificar endpoints críticos:
```bash
grep -rn "@router\.\|@app\." lia-agent-system/app/ --include="*.py" | grep -E "post|put|patch|delete"
```

2. Para cada endpoint, verificar:
   - Input validation: payload é validado com Pydantic/schema?
   - Error handling: exceções retornam status code correto?
   - Business logic: regras de negócio estão corretas?
   - Response: retorna dados completos e consistentes?

3. Corrigir:
```python
@router.post("/candidates/{id}/move")
async def move_candidate(id: str, body: MoveCandidateRequest, company_id: str = Depends(get_company)):
    if not body.to_stage:
        raise HTTPException(400, "to_stage é obrigatório")
    candidate = await get_candidate(id, company_id)
    if not candidate:
        raise HTTPException(404, "Candidato não encontrado")
    result = await pipeline_service.move(candidate, body.to_stage, company_id)
    return {"status": "success", "data": result}
```

**Padrão de código a seguir:** Todo endpoint: Pydantic validation, `company_id` via Depends, HTTPException com status correto, response padronizada `{"status": ..., "data": ...}`. Referência: Dimensão 6, padrão FastAPI.

**Arquivos a modificar:**
- Variável por endpoint (verificar cada rota em `app/api/`)
- Referência: padrão de rotas existentes em `app/api/v1/`

**Esforço estimado:** 2-4h por endpoint com problema | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Todo endpoint valida input com Pydantic
- [ ] Erros retornam status code HTTP correto (400, 404, 500)
- [ ] company_id é verificado em toda query (multi-tenant)
- [ ] Response tem formato consistente

---

### RM-40: Types/Contracts Inconsistentes (Dimensão 7)

**O que está errado:** Tipos TypeScript no frontend não correspondem aos schemas Pydantic no backend. Contratos de API não documentados ou desatualizados.

**Por que importa:** Tipos inconsistentes causam erros em runtime que TypeScript deveria prevenir em compile time. Frontend espera `candidateId` mas backend envia `candidate_id`. Sem contrato claro, cada mudança no backend pode quebrar o frontend silenciosamente.

**Referência:** Dimensão 7 (Types/Contracts)

**Passo-a-passo para resolver:**

1. Verificar consistência de naming:
```bash
grep -rn "interface.*Candidate\|type.*Candidate" plataforma-lia/src/ --include="*.ts"
grep -rn "class.*Candidate.*Model\|class.*Candidate.*Schema" lia-agent-system/app/ --include="*.py"
```

2. Para cada API endpoint, verificar que o tipo TypeScript corresponde ao schema Pydantic:
   - camelCase (frontend) ↔ snake_case (backend) mapeado corretamente
   - Campos opcionais marcados como `?` no TypeScript e `Optional` no Pydantic
   - Enums têm mesmos valores nos dois lados

3. Criar tipos compartilhados ou schema de contrato:
```typescript
export interface CandidateResponse {
  id: string;
  name: string;
  email: string;
  stage: 'sourcing' | 'screening' | 'interview' | 'offer' | 'standby';
  wsiScore?: number;
}
```

**Padrão de código a seguir:** Tipos TypeScript devem espelhar schemas Pydantic. camelCase no frontend, snake_case no backend, com conversão no proxy/API layer. Usar `zod` para validação runtime no frontend. Referência: Dimensão 7.

**Arquivos a modificar:**
- `plataforma-lia/src/types/` (criar ou atualizar tipos compartilhados)
- `lia-agent-system/app/schemas/` (schemas Pydantic)

**Esforço estimado:** 4h | **Responsável:** Frontend + Backend

**Critério de aceitação:**
- [ ] Todo tipo TypeScript tem correspondente Pydantic
- [ ] Naming convention consistente (camelCase ↔ snake_case mapeado)
- [ ] Campos opcionais marcados corretamente em ambos os lados

---

### RM-41: User Flow Quebrado ou Incompleto (Dimensão 8)

**O que está errado:** Fluxo do usuário tem caminhos mortos (botão leva a lugar nenhum), estados não tratados (loading infinito, erro sem mensagem), ou passos faltando (ação concluída mas UI não atualiza).

**Por que importa:** Fluxo quebrado frustra o recrutador e pode levar a perda de dados. Candidato movido no kanban mas UI não reflete a mudança. Formulário submetido mas sem feedback de sucesso/erro.

**Referência:** Dimensão 8 (User Flow)

**Passo-a-passo para resolver:**

1. Mapear cada fluxo crítico:
   - Criar vaga → configurar pipeline → publicar
   - Receber candidato → triar → agendar entrevista → fazer oferta
   - Chat com LIA → ação executada → feedback visual

2. Para cada fluxo, verificar:
   - [ ] Estado de loading visível enquanto processa
   - [ ] Erro exibe mensagem clara (não tela branca)
   - [ ] Sucesso atualiza a UI imediatamente (optimistic update ou refetch)
   - [ ] Navegação pós-ação é correta (volta para lista, vai para detalhe, etc.)

3. Corrigir usando padrão de mutation:
```typescript
const mutation = useMutation({
  mutationFn: moveCandidate,
  onSuccess: () => {
    queryClient.invalidateQueries(['candidates', jobId]);
    toast.success('Candidato movido com sucesso');
  },
  onError: (error) => {
    toast.error(`Erro ao mover candidato: ${error.message}`);
  },
});
```

**Padrão de código a seguir:** Todo fluxo: loading state → sucesso com feedback + invalidação de cache → erro com mensagem clara. Usar `react-query` mutations com `onSuccess`/`onError`. Referência: Dimensão 8, Design System v4.2.1.

**Arquivos a modificar:**
- Variável por fluxo (componentes de página e hooks)
- Verificar: `plataforma-lia/src/app/(protected)/` (pages com forms/actions)

**Esforço estimado:** 2-4h por fluxo quebrado | **Responsável:** Frontend

**Critério de aceitação:**
- [ ] Nenhum botão leva a tela branca ou erro silencioso
- [ ] Todo formulário mostra loading durante submit e feedback ao concluir
- [ ] Navegação pós-ação é intuitiva (não fica em página vazia)

---

### RM-42: Inconsistência entre Componentes (Dimensão 9)

**O que está errado:** Componentes similares usam padrões diferentes (ex: dois modais com APIs diferentes, tabelas com props inconsistentes, nomenclatura variável para mesmos conceitos).

**Por que importa:** Inconsistência dificulta manutenção, confunde desenvolvedores, e cria UX fragmentada para o recrutador. O mesmo conceito ("score") aparece como porcentagem em uma tela e como decimal em outra.

**Referência:** Dimensão 9 (Consistência), Design System v4.2.1

**Passo-a-passo para resolver:**

1. Inventariar componentes duplicados:
```bash
grep -rn "Modal\|Dialog" plataforma-lia/src/components/ --include="*.tsx" -l
grep -rn "Table\|DataGrid" plataforma-lia/src/components/ --include="*.tsx" -l
```

2. Para cada par de componentes similares:
   - Unificar API (mesmas props para mesma funcionalidade)
   - Usar Design System tokens (cores, tipografia, espaçamento)
   - Padronizar nomenclatura (score sempre 0-100, datas sempre ISO)

3. Criar componentes base reutilizáveis quando há duplicação.

**Padrão de código a seguir:** Usar componentes do Design System v4.2.1. Regra 90/10 (90% componentes padronizados). Tokens canônicos para cores/tipografia. Referência: Dimensão 9, skill `design-standardize`.

**Arquivos a modificar:**
- `plataforma-lia/src/components/ui/` (componentes base)
- Componentes duplicados identificados no inventário

**Esforço estimado:** 4-8h (depende da quantidade de inconsistências) | **Responsável:** Frontend

**Critério de aceitação:**
- [ ] Score exibido no mesmo formato em todas as telas (0-100 ou 0-1, não ambos)
- [ ] Modais usam mesma API de componente base
- [ ] Cores e tipografia seguem tokens do Design System

---

### RM-43: Documentação Desatualizada ou Ausente (Dimensão 11)

**O que está errado:** Documentação técnica (READMEs, comentários de API, guias de setup) está desatualizada, incompleta, ou ausente para módulos críticos.

**Por que importa:** Documentação ausente faz novos desenvolvedores perderem tempo entendendo código. Documentação desatualizada é pior que ausente — causa decisões baseadas em informação errada.

**Referência:** Dimensão 11 (Documentação), Production Readiness

**Passo-a-passo para resolver:**

1. Verificar documentação mínima para cada módulo:
   - README com setup e arquitetura
   - Docstrings em funções públicas
   - Schemas de API documentados (FastAPI auto-gera via Pydantic)

2. Priorizar documentação de:
   - Módulos com mais contribuidores
   - APIs consumidas por múltiplos clientes
   - Lógica de negócio complexa (scoring, fairness, routing)

3. Para cada módulo sem documentação:
```python
class FairnessGuard:
    """Guardrail de fairness com 3 camadas de verificação.

    Camada 1 (Lexical): Detecta termos discriminatórios via regex.
    Camada 2 (Semântica): Analisa viés implícito via LLM.
    Camada 3 (Estatística): Verifica four-fifths rule nos resultados.

    Usage:
        guard = FairnessGuard()
        result = guard.check(input_text, company_id)
        if result.action == "BLOCK_AND_WARN":
            raise FairnessViolation(result.reason)
    """
```

**Padrão de código a seguir:** Docstrings obrigatórias em classes e funções públicas. README por módulo com setup + arquitetura. FastAPI schemas auto-documentados. Referência: Dimensão 11, Production Readiness #11.

**Arquivos a modificar:**
- Módulos sem docstrings em `lia-agent-system/app/`
- READMEs em `lia-agent-system/` e `plataforma-lia/`

**Esforço estimado:** 4h | **Responsável:** Backend + Frontend

**Critério de aceitação:**
- [ ] Todo módulo público tem docstring explicando propósito e uso
- [ ] APIs FastAPI auto-documentadas via `/docs`
- [ ] README de setup funciona para dev novo

---

### RM-44: Performance / Escalabilidade Insuficiente (Dimensão 14)

**O que está errado:** Queries N+1, falta de caching, endpoints lentos (>2s P95), falta de paginação, ou operações síncronas que deveriam ser assíncronas.

**Por que importa:** Performance ruim degrada experiência do recrutador e aumenta custos de infra. Query N+1 num kanban com 500 candidatos pode levar >10s. Sem paginação, listar candidatos de empresa grande trava o browser.

**Referência:** Dimensão 14 (Performance), Production Readiness #3/#4

**Passo-a-passo para resolver:**

1. Identificar queries N+1:
```python
# ANTES (N+1):
candidates = await db.query(Candidate).filter_by(job_id=job_id).all()
for c in candidates:
    c.stage = await db.query(Stage).get(c.stage_id)  # N queries extras

# DEPOIS (joinedload):
candidates = await db.query(Candidate).options(
    joinedload(Candidate.stage)
).filter_by(job_id=job_id).all()
```

2. Adicionar paginação em listagens:
```python
@router.get("/candidates")
async def list_candidates(page: int = 1, per_page: int = 50, company_id = Depends(get_company)):
    offset = (page - 1) * per_page
    total = await db.query(func.count(Candidate.id)).filter_by(company_id=company_id).scalar()
    items = await db.query(Candidate).filter_by(company_id=company_id).offset(offset).limit(per_page).all()
    return {"items": items, "total": total, "page": page, "per_page": per_page}
```

3. Adicionar caching para dados que mudam pouco (configurações, guardrails):
```python
from functools import lru_cache
@lru_cache(maxsize=128, ttl=300)
async def get_company_config(company_id):
    return await db.query(CompanyConfig).filter_by(company_id=company_id).first()
```

4. Operações longas devem ser assíncronas (Celery tasks):
   - Enriquecimento de perfil
   - Geração de relatórios
   - Envio de outreach em massa

**Padrão de código a seguir:** `joinedload` para evitar N+1. Paginação obrigatória em listagens (`page`/`per_page`). Cache com TTL para configs. Celery para operações >5s. Referência: Dimensão 14, Production Readiness #3/#4, AP-5.5 (Anexo B).

**Arquivos a modificar:**
- Endpoints de listagem em `app/api/v1/` (adicionar paginação)
- Queries com N+1 (adicionar `joinedload`/`selectinload`)
- Operações longas (mover para Celery tasks)

**Esforço estimado:** 8h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Nenhuma query N+1 nos endpoints principais (verificar via SQLAlchemy echo)
- [ ] Toda listagem paginada (`page`/`per_page` obrigatórios)
- [ ] P95 latency < 2s nos endpoints principais
- [ ] Operações >5s executam via Celery (não bloqueiam request)

---

### RM-36: Pipeline Não Validado / Stages Sem Verificação

**O que está errado:** Pipeline de recrutamento pode ter stages mal configurados, sem validação de transições (candidato pula etapa, stage sem critérios de saída, stage "standby" filtrado incorretamente no frontend).

**Por que importa:** Pipeline mal validado causa candidatos perdidos (stuck em stages), transições inválidas que corrompem dados, e UX quebrada no kanban. O bug de `mapInterviewStagesToKanban` filtrando `stageType === 'standby'` é um exemplo concreto.

**Referência:** Dimensão 1 (Wiring), Dimensão 5 (Pipeline), AP-4.1 (Anexo B)

**Passo-a-passo para resolver:**

1. Criar validador de pipeline:
```python
class PipelineValidator:
    REQUIRED_STAGES = ["sourcing", "screening", "interview", "offer"]
    VALID_TRANSITIONS = {
        "sourcing": ["screening", "rejected"],
        "screening": ["interview", "rejected", "standby"],
        "interview": ["offer", "rejected", "standby"],
        "offer": ["hired", "rejected"],
        "standby": ["screening", "interview", "rejected"],
    }

    def validate(self, pipeline_config: dict) -> list[str]:
        errors = []
        stages = [s["type"] for s in pipeline_config.get("stages", [])]
        for required in self.REQUIRED_STAGES:
            if required not in stages:
                errors.append(f"Stage obrigatório ausente: {required}")
        for stage in pipeline_config.get("stages", []):
            if not stage.get("exit_criteria"):
                errors.append(f"Stage '{stage['name']}' sem critérios de saída")
        return errors
```

2. Corrigir filtro de stages no frontend:
```typescript
// ANTES (bug): filtrava standby
const stages = allStages.filter(s => s.stageType !== 'standby');
// DEPOIS: incluir standby como stage visível
const stages = allStages; // ou lógica correta de visibilidade
```

3. Adicionar validação de transições no backend:
```python
async def move_candidate(self, candidate_id, from_stage, to_stage, company_id):
    if to_stage not in self.VALID_TRANSITIONS.get(from_stage, []):
        raise InvalidTransitionError(f"Transição inválida: {from_stage} → {to_stage}")
```

**Padrão de código a seguir:** Validação no backend com `PipelineValidator`. Transições explícitas em `VALID_TRANSITIONS`. Frontend não filtra stages — backend controla visibilidade. Referência: `stage-utils.ts` (frontend), pipeline config no backend.

**Arquivos a modificar:**
- Criar: `app/services/pipeline_validator.py`
- Modificar: `plataforma-lia/src/lib/stage-utils.ts` (corrigir filtro standby)
- Modificar: `plataforma-lia/src/app/(protected)/jobs/[id]/kanban/job-kanban-page.tsx`
- Modificar: backend endpoint de movimentação de candidato

**Esforço estimado:** 6h | **Responsável:** Backend + Frontend

**Critério de aceitação:**
- [ ] Pipeline sem stage obrigatório → erro de validação
- [ ] Transição inválida → `InvalidTransitionError`
- [ ] Stages standby visíveis no kanban (bug corrigido)
- [ ] Todo stage tem critérios de saída documentados

---

## P3 — BAIXO: GAPS COMPETITIVOS E ROADMAP

> Itens P3 são oportunidades de diferenciação. Devem ser planejados no **backlog** com análise de ROI.

---

### RM-28: Outreach Automatizado (Gap CG-1)

**O que está errado:** LIA não tem capacidade de enviar sequences automatizadas de outreach para candidatos passivos. Concorrentes (Tezi, Gem, Findem, Eightfold) oferecem nativamente.

**Por que importa:** Gap competitivo de alta prioridade. Clientes que usam sourcing ativo esperam poder enviar sequences personalizadas sem sair da plataforma.

**Referência:** Anexo L, MC-3.1 CG-1

**Passo-a-passo para resolver:**

1. Criar modelos de dados:
```python
class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"
    id = Column(UUID, primary_key=True)
    company_id = Column(UUID, ForeignKey("companies.id"))
    name = Column(String)
    steps = relationship("OutreachStep")
    status = Column(Enum("draft", "active", "paused", "completed"))

class OutreachStep(Base):
    __tablename__ = "outreach_steps"
    id = Column(UUID, primary_key=True)
    sequence_id = Column(UUID, ForeignKey("outreach_sequences.id"))
    step_order = Column(Integer)
    channel = Column(Enum("email", "whatsapp", "linkedin"))
    template = Column(Text)
    delay_hours = Column(Integer)

class OutreachExecution(Base):
    __tablename__ = "outreach_executions"
    id = Column(UUID, primary_key=True)
    sequence_id = Column(UUID, ForeignKey("outreach_sequences.id"))
    candidate_id = Column(UUID, ForeignKey("candidates.id"))
    current_step = Column(Integer)
    status = Column(Enum("in_progress", "replied", "completed", "opted_out"))
```

2. Criar domínio `outreach` com padrão 4 arquivos (RM-18):
   - `outreach_react_agent.py` — agente com tools: create_sequence, start_sequence, pause_sequence, get_metrics, add_candidates, view_execution_status
   - `outreach_tool_registry.py` — 6 tools com schema tipado
   - `outreach_system_prompt.py` — com anti-sycophancy e FairnessGuard
   - `outreach_stage_context.py` — contexto por status da sequence

3. Integrar com Communication Agent para envio real via email/WhatsApp.

4. Frontend: criar UI para visualizar/criar sequences com drag-and-drop de steps.

**Padrão de código a seguir:** Seguir padrão canônico de 4 arquivos (Anexo A). Communication via `CommunicationMatrix` existente. Rate limiting via `check_rate_limit` tool existente. FairnessGuard obrigatório em templates de outreach. Referência: MC-2.4 (Communication Agent patterns), Crença 02 (fairness em comunicações).

**Arquivos a modificar:**
- Criar: `app/domains/outreach/` (domínio completo com 4 arquivos)
- Criar: migration para tabelas `outreach_sequences`, `outreach_steps`, `outreach_executions`
- Modificar: `app/domains/communication/` (integrar envio)
- Criar: `plataforma-lia/src/app/(protected)/outreach/` (UI)

**Esforço estimado:** 40h | **Responsável:** Backend + Frontend

**Critério de aceitação:**
- [ ] Sequence criada com 3 steps (email dia 1, email dia 3, WhatsApp dia 5)
- [ ] Candidato adicionado → recebe primeiro email automaticamente
- [ ] Candidato responde → sequence pausa automaticamente
- [ ] Opt-out → nunca mais recebe outreach dessa sequence
- [ ] Métricas visíveis: taxa de resposta, opt-out, step reached

---

### RM-29: Profile Enrichment Multi-Fonte (Gap CG-2)

**O que está errado:** LIA só busca candidatos no banco interno. Não enriquece perfis com dados de LinkedIn, GitHub, portfólios.

**Por que importa:** Concorrentes (Tezi: 750M+ perfis, Findem: 3D data fusion, Eightfold: 1.6B perfis) oferecem enriquecimento automático que dá ao recrutador dados mais completos para tomar decisões.

**Referência:** Anexo L, MC-3.1 CG-2

**Passo-a-passo para resolver:**

1. Criar service de enriquecimento:
```python
class ProfileEnrichmentService:
    PROVIDERS = {
        "proxycurl": ProxycurlAdapter,
        "people_data_labs": PDLAdapter,
        "github": GitHubAdapter,
    }

    async def enrich(self, candidate_id: str, company_id: str) -> EnrichedProfile:
        candidate = await get_candidate(candidate_id, company_id)
        enriched_data = {}
        for provider_name, adapter in self.PROVIDERS.items():
            try:
                data = await adapter.fetch(candidate.email, candidate.linkedin_url)
                enriched_data[provider_name] = data
            except Exception as e:
                logger.warning(f"Enrichment failed for {provider_name}: {e}")
        return self._merge_data(candidate, enriched_data)

    def _merge_data(self, candidate, enriched_data: dict) -> EnrichedProfile:
        merged = candidate.to_dict()
        for source, data in enriched_data.items():
            for field, value in data.items():
                if field not in merged or merged[field] is None:
                    merged[field] = value
                    merged[f"{field}_source"] = source
        return EnrichedProfile(**merged)
```

2. Adicionar tool `enrich_profile` ao Sourcing Agent (A1).

3. Garantir LGPD compliance: consent para enriquecimento com fontes externas, registrar fonte de cada dado.

4. Frontend: indicar visualmente quais dados vieram de enriquecimento vs. candidato.

**Padrão de código a seguir:** Padrão adapter por provider com interface comum. Circuit breaker por provider externo (RM-10). PII dos dados enriquecidos passa pelo filtro (RM-01). Consent check obrigatório antes de enriquecer (RM-04). Referência: AP-5.3 (chamada externa assíncrona), Crença 04 (privacidade).

**Arquivos a modificar:**
- Criar: `app/services/profile_enrichment_service.py`
- Criar: `app/adapters/proxycurl.py`, `app/adapters/pdl.py`, `app/adapters/github_profile.py`
- Modificar: `app/domains/sourcing/agents/sourcing_tool_registry.py` (adicionar tool)
- Criar: migration para campo `enrichment_sources` no candidato

**Esforço estimado:** 40h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Candidato com LinkedIn URL → perfil enriquecido com dados adicionais
- [ ] Fonte de cada dado rastreada (`field_source`)
- [ ] Consent check antes de enriquecer
- [ ] Circuit breaker em cada provider externo
- [ ] Fallback gracioso quando provider offline

---

### RM-30: WhatsApp ↔ WSI Direto (Gap CG-3)

**O que está errado:** WSI Interview (Graph G2) funciona apenas via web. Candidatos não podem fazer a entrevista WSI pelo WhatsApp.

**Por que importa:** Paradox e DigaAI oferecem entrevistas conversacionais via WhatsApp nativamente. Em mercados mobile-first (ex: Brasil), WhatsApp tem penetração muito superior à web.

**Referência:** Anexo L, MC-3.1 CG-3

**Passo-a-passo para resolver:**

1. Criar adapter WhatsApp para o WSI Graph:
```python
class WhatsAppWSIAdapter:
    async def start_interview(self, candidate_id: str, job_id: str):
        session = await WSISession.create(candidate_id, job_id, channel="whatsapp")
        first_question = await wsi_graph.get_first_question(session)
        await whatsapp_service.send(candidate_id, first_question.text)
        return session

    async def handle_response(self, candidate_id: str, message: str):
        session = await WSISession.get_active(candidate_id)
        if not session:
            return
        result = await wsi_graph.process_answer(session, message)
        if result.has_next_question:
            await whatsapp_service.send(candidate_id, result.next_question.text)
        else:
            await whatsapp_service.send(candidate_id, result.completion_message)
            await session.complete()
```

2. Gerenciar estado da sessão WSI para conversação assíncrona (candidato pode responder horas depois).

3. Suportar respostas em texto e áudio (transcrever áudio antes de processar).

4. Rate limiting: máximo 1 pergunta WSI por mensagem, intervalo mínimo entre mensagens.

**Padrão de código a seguir:** Usar `CommunicationMatrix` existente para templates WhatsApp. Session state persistido em banco (não in-memory). `WSIInterviewGraph` recebe channel como parâmetro. Referência: MC-2.3 (Pipeline Agent patterns), `send_whatsapp` tool existente no Communication Agent.

**Arquivos a modificar:**
- Criar: `app/adapters/whatsapp_wsi_adapter.py`
- Modificar: `app/domains/cv_screening/agents/wsi_interview_graph.py` (aceitar channel)
- Criar: migration para campo `channel` em `wsi_sessions`
- Modificar: webhook WhatsApp para rotear para WSI adapter

**Esforço estimado:** 24h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Candidato inicia entrevista WSI pelo WhatsApp
- [ ] Cada pergunta enviada como mensagem separada
- [ ] Candidato responde em texto → processado normalmente
- [ ] Candidato não responde em 24h → lembrete automático
- [ ] Score WSI final idêntico ao canal web

---

### RM-31: Blind Review / Candidate Anonymizer (Gap CG-4)

**O que está errado:** Atributos protegidos (nome, idade, gênero, foto) não são removidos antes de enviar dados de candidato ao LLM para triagem/ranking.

**Por que importa:** Eightfold faz blind review automático. Sem anonymization, o LLM pode ser influenciado por atributos protegidos mesmo com instruções anti-viés no prompt. Referência: Gap G-M2/G-M3.

**Depende de:** RM-01 (PII filter)

**Referência:** Anexo L, MC-3.1 CG-4, Gap G-M2/G-M3 (Anexo E)

**Passo-a-passo para resolver:**

1. Criar módulo `candidate_anonymizer.py`:
```python
class CandidateAnonymizer:
    PROTECTED_FIELDS = ['name', 'age', 'gender', 'photo', 'ethnicity',
                        'marital_status', 'nationality', 'religion',
                        'date_of_birth', 'photo_url']

    def anonymize(self, candidate_data: dict) -> dict:
        anonymized = candidate_data.copy()
        for field in self.PROTECTED_FIELDS:
            if field in anonymized:
                anonymized[field] = f"[REDACTED_{field.upper()}]"
        anonymized['_anonymized'] = True
        anonymized['_anonymized_fields'] = [f for f in self.PROTECTED_FIELDS if f in candidate_data]
        return anonymized

    def is_anonymized(self, candidate_data: dict) -> bool:
        return candidate_data.get('_anonymized', False)
```

2. Integrar no pipeline de screening ANTES de enviar ao LLM:
```python
async def _prepare_candidate_for_llm(self, candidate_data, company_id):
    anonymizer = CandidateAnonymizer()
    config = await get_company_config(company_id)
    if config.blind_review_enabled:
        return anonymizer.anonymize(candidate_data)
    return candidate_data
```

3. Frontend: toggle blind review na configuração da empresa (Hiring Policy).

4. Verificar que dados originais são preservados em banco — apenas o prompt é anonymizado.

**Padrão de código a seguir:** `CandidateAnonymizer` complementa `PromptPIIFilter` (RM-01). PII filter mascara formatos (CPF, email), anonymizer remove atributos protegidos semânticos (nome, gênero). Usar juntos. Referência: MP-2.3 (Padrões de Fairness, Eightfold attribute masking), Crença 02, Parte II (FairnessGuard Camada 1).

**Arquivos a modificar:**
- Criar: `app/shared/candidate_anonymizer.py`
- Modificar: `app/domains/cv_screening/agents/pipeline_react_agent.py` (integrar antes de LLM)
- Modificar: `app/domains/hiring_policy/` (adicionar config blind_review)
- Criar: `tests/unit/test_candidate_anonymizer.py`

**Esforço estimado:** 16h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Com blind review ON: prompt ao LLM contém `[REDACTED_NAME]` ao invés do nome
- [ ] Score WSI com blind review ON vs OFF: variância < 0.5 (prova que não dependia do nome)
- [ ] Dados originais intactos no banco
- [ ] Config por empresa via Hiring Policy

---

### RM-32: Calibração Contínua de Busca (Gap CG-6)

**O que está errado:** Sourcing Agent não aprende com o feedback do recrutador (accept/reject candidatos) para melhorar buscas futuras.

**Por que importa:** Tezi e Findem auto-calibram baseado em feedback. Sem isso, o recrutador precisa refinar critérios manualmente a cada busca.

**Referência:** Anexo L, MC-3.2 CG-6

**Passo-a-passo para resolver:**

1. Criar modelo de feedback:
```python
class SearchFeedback(Base):
    __tablename__ = "search_feedback"
    id = Column(UUID, primary_key=True)
    company_id = Column(UUID, ForeignKey("companies.id"))
    search_criteria_id = Column(UUID)
    candidate_id = Column(UUID, ForeignKey("candidates.id"))
    action = Column(Enum("accepted", "rejected", "shortlisted", "ignored"))
    timestamp = Column(DateTime)
```

2. Criar service de calibração:
```python
class SearchCalibrationService:
    async def learn_from_feedback(self, search_id: str, company_id: str):
        feedback = await get_feedback(search_id, company_id)
        accepted = [f for f in feedback if f.action in ("accepted", "shortlisted")]
        rejected = [f for f in feedback if f.action == "rejected"]
        adjustments = self._compute_adjustments(accepted, rejected)
        return adjustments

    def _compute_adjustments(self, accepted, rejected):
        accepted_skills = self._extract_common_skills(accepted)
        rejected_skills = self._extract_common_skills(rejected)
        return {
            "boost_skills": accepted_skills - rejected_skills,
            "reduce_skills": rejected_skills - accepted_skills,
            "adjust_seniority": self._compute_seniority_adjustment(accepted),
        }
```

3. Integrar sugestão de refinamento no Sourcing Agent:
   - Após N rejeições, sugerir proativamente ajustes nos critérios
   - Após aceitar candidatos com skills extras, sugerir adicionar essas skills

4. Adicionar tool `get_search_calibration` ao Sourcing Agent.

**Padrão de código a seguir:** Feedback loop como service separado, não embutido no agente. Padrão observer para capturar feedback. Sugestões proativas seguem padrão anti-sycophancy (RM-08) — calibrar com dados, não opinião. Referência: MP-2.1 (Anexo K — calibração contínua como estado da arte).

**Arquivos a modificar:**
- Criar: `app/services/search_calibration_service.py`
- Criar: migration para `search_feedback`
- Modificar: `app/domains/sourcing/agents/sourcing_tool_registry.py` (adicionar tool)
- Modificar: `app/domains/sourcing/agents/sourcing_system_prompt.py` (instruções de calibração)

**Esforço estimado:** 32h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Após 5 rejects consecutivos → sugestão proativa de ajuste
- [ ] Skills comuns nos aceitos são boosted na próxima busca
- [ ] Métricas de calibração: taxa de accept antes vs. depois

---

### RM-33: NPS / Sentiment Analysis (Gap CG-7)

**O que está errado:** Respostas de candidatos (email, WhatsApp) não são analisadas para sentiment. Não há NPS tracking por etapa do pipeline.

**Por que importa:** Paradox oferece sentiment analysis nativamente. Sentiment negativo em comunicações pode indicar problemas no processo que o recrutador não percebe.

**Referência:** Anexo L, MC-3.2 CG-7

**Passo-a-passo para resolver:**

1. Criar sentiment analyzer:
```python
class CandidateSentimentAnalyzer:
    SENTIMENT_LABELS = ["positive", "neutral", "negative"]

    async def analyze(self, message: str, company_id: str) -> SentimentResult:
        result = await llm_client.classify(
            prompt=f"Classifique o sentiment desta resposta de candidato: '{message}'",
            labels=self.SENTIMENT_LABELS,
            company_id=company_id
        )
        return SentimentResult(
            sentiment=result.label,
            confidence=result.confidence,
            keywords=result.keywords
        )
```

2. Integrar no webhook de respostas (email e WhatsApp):
```python
async def on_candidate_reply(candidate_id, message, channel, company_id):
    sentiment = await sentiment_analyzer.analyze(message, company_id)
    await save_sentiment(candidate_id, sentiment, channel)
    if sentiment.sentiment == "negative" and sentiment.confidence > 0.8:
        await alert_recruiter(candidate_id, sentiment)
```

3. NPS tracking por etapa:
```python
async def calculate_stage_nps(job_id, stage, company_id):
    sentiments = await get_sentiments_by_stage(job_id, stage, company_id)
    promoters = sum(1 for s in sentiments if s.sentiment == "positive")
    detractors = sum(1 for s in sentiments if s.sentiment == "negative")
    total = len(sentiments)
    return ((promoters - detractors) / total) * 100 if total > 0 else None
```

4. Dashboard: mostrar NPS por etapa no pipeline view.

**Padrão de código a seguir:** LLM classification com budget check (RM-11). Sentiment salvo na tabela existente de communication history. Alertas via canais existentes. Referência: Crença 06 (melhoria contínua com métricas), `get_communication_history` tool existente.

**Arquivos a modificar:**
- Criar: `app/services/candidate_sentiment_service.py`
- Modificar: webhook de email/WhatsApp para chamar sentiment analyzer
- Modificar: `app/domains/analytics/agents/analytics_tool_registry.py` (tool `get_sentiment_metrics`)
- Criar: migration para campo `sentiment` em `communication_history`

**Esforço estimado:** 16h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Resposta negativa de candidato → alerta ao recrutador
- [ ] NPS por etapa visível no pipeline
- [ ] Sentiment classificado com confiança > 0.7

---

### RM-34: Cascata de Confiança T3 Automática (Gap CG-5)

**O que está errado:** Quando o intent router (T1 cache + T2 keywords) não atinge confiança suficiente, deveria escalar automaticamente para LLM classification (T3), mas a cascata não é automática.

**Por que importa:** Sem cascata automática, queries ambíguas caem em fallback genérico ao invés de serem classificadas corretamente pelo LLM. Isso degrada a experiência do recrutador.

**Depende de:** RM-09 (Confiança real)

**Referência:** Anexo L, MC-3.1 CG-5, Gap CG-5 (Anexo E)

**Passo-a-passo para resolver:**

1. Automatizar cascata no router:
```python
async def route(self, message: str, company_id: str) -> RouteResult:
    t1_result = await self._try_cache(message)
    if t1_result and t1_result.confidence >= 0.85:
        self._metrics.record("t1_cache_hit")
        return t1_result

    t2_result = self._keyword_match(message)
    if t2_result.confidence >= 0.70:
        self._metrics.record("t2_keyword_hit")
        await self._cache_result(message, t2_result)
        return t2_result

    t3_result = await self._llm_classify(message, company_id)
    self._metrics.record("t3_llm_classify")
    await self._cache_result(message, t3_result)
    return t3_result
```

2. Rate limiting para T3:
```python
T3_RATE_LIMIT = 100  # max LLM classifications per company per hour

async def _llm_classify(self, message, company_id):
    if await self._t3_rate_exceeded(company_id):
        return RouteResult(intent="general", confidence=0.5, tier="t3_limited")
    # ... LLM call
```

3. Métricas de cascata:
```python
async def get_cascade_metrics(self, company_id: str, period: str):
    return {
        "t1_hit_rate": await self._get_tier_rate("t1", company_id, period),
        "t2_hit_rate": await self._get_tier_rate("t2", company_id, period),
        "t3_hit_rate": await self._get_tier_rate("t3", company_id, period),
        "avg_confidence_by_tier": await self._get_confidence_by_tier(company_id, period),
    }
```

4. Verificar que cache key é segura (não MD5 — ver Gap G-R2):
```python
import hashlib
cache_key = hashlib.sha256(f"{company_id}:{message}".encode()).hexdigest()
```

**Padrão de código a seguir:** Router em cascata T1→T2→T3 com métricas por tier. Rate limiting T3 por company. Cache key SHA-256 (não MD5). ConfidencePolicy integrada (RM-24). Referência: Crença 09 (custos), Crença 10 (determinismo vs IA), Gap G-R2 (Anexo E).

**Arquivos a modificar:**
- Modificar: `app/shared/agents/intent_router.py`
- Criar: `app/services/cascade_metrics_service.py`
- Modificar: `app/domains/analytics/agents/analytics_tool_registry.py` (tool `get_cascade_metrics`)

**Esforço estimado:** 16h | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Query clara ("mostre o pipeline") → resolve em T2 sem LLM call
- [ ] Query ambígua ("e aí, como tá?") → escala para T3 automaticamente
- [ ] T3 rate limiting ativo (100/hora/company)
- [ ] Métricas de cascata visíveis: % T1, % T2, % T3

---

### RM-37: Video Interview com Análise por IA (Gap CG-8)

**O que está errado:** LIA não oferece entrevista por vídeo com análise automatizada. Candidatos fazem entrevista WSI apenas por texto/áudio, sem opção de vídeo assíncrono.

**Por que importa:** Paradox (Olivia), HireVue e MyInterview oferecem video interview com análise de conteúdo por IA. É uma expectativa crescente do mercado B2B de recrutamento, especialmente para posições executivas e customer-facing.

**Referência:** Anexo L, MC-3.2 (gaps competitivos)

**Passo-a-passo para resolver:**

1. Criar modelo de video interview:
```python
class VideoInterview(Base):
    __tablename__ = "video_interviews"
    id = Column(UUID, primary_key=True)
    company_id = Column(UUID, ForeignKey("companies.id"))
    candidate_id = Column(UUID, ForeignKey("candidates.id"))
    job_id = Column(UUID, ForeignKey("jobs.id"))
    questions = Column(JSONB)  # Lista de perguntas com tempo limite
    status = Column(Enum("pending", "in_progress", "completed", "expired"))
    deadline = Column(DateTime)

class VideoResponse(Base):
    __tablename__ = "video_responses"
    id = Column(UUID, primary_key=True)
    interview_id = Column(UUID, ForeignKey("video_interviews.id"))
    question_index = Column(Integer)
    video_url = Column(String)  # S3/storage URL
    transcript = Column(Text)
    duration_seconds = Column(Integer)
    ai_analysis = Column(JSONB)  # Análise de conteúdo (NÃO facial/emocional)
```

2. Criar domínio `video_interview` com padrão 4 arquivos:
   - Transcrição do vídeo via speech-to-text
   - Análise de CONTEÚDO apenas (NÃO análise facial/emocional — viés comprovado, ver HireVue settlement)
   - Scoring baseado em conteúdo das respostas vs. critérios da vaga

3. Frontend: portal do candidato para gravar vídeo assíncrono com countdown por pergunta.

4. Compliance obrigatória:
```python
VIDEO_INTERVIEW_COMPLIANCE = {
    "facial_analysis": False,  # PROIBIDO — viés comprovado
    "emotion_detection": False,  # PROIBIDO — pseudociência em contexto de recrutamento
    "content_only": True,  # Apenas transcrição + análise textual
    "ai_disclosure": True,  # Candidato sabe que IA analisa
    "opt_out_available": True,  # Candidato pode recusar e fazer entrevista ao vivo
}
```

**Padrão de código a seguir:** Análise apenas de CONTEÚDO transcrito — NUNCA facial/emocional (viés comprovado, FTC settlement HireVue). Seguir padrão 4 arquivos (RM-18). FairnessGuard obrigatório no scoring. Opt-out para entrevista humana (RM-07). Referência: Crença 02, Crença 03 (transparência), Inegociável #2.

**Arquivos a modificar:**
- Criar: `app/domains/video_interview/` (domínio completo com 4 arquivos)
- Criar: migrations para `video_interviews`, `video_responses`
- Criar: `plataforma-lia/src/app/(protected)/video-interview/` (portal candidato)
- Integrar: speech-to-text API (Google/Whisper)

**Esforço estimado:** 40h | **Responsável:** Backend + Frontend

**Critério de aceitação:**
- [ ] Candidato recebe link, grava vídeo assíncrono por pergunta
- [ ] Vídeo transcrito automaticamente
- [ ] Scoring baseado APENAS em conteúdo (zero análise facial/emocional)
- [ ] AI disclosure visível antes de gravar
- [ ] Opt-out disponível → agenda entrevista ao vivo com humano
- [ ] FairnessGuard aplicado no scoring das respostas

---

## TABELA DE DEPENDÊNCIAS ENTRE RUNBOOKS

```
RM-01 (PII prompts) ──┬──→ RM-16 (PII resposta)
                       └──→ RM-31 (Blind review)

RM-02 (FairnessGuard middleware) ──→ RM-15 (FairnessGuard saída)

RM-09 (Confiança real) ──→ RM-34 (Cascata T3)

RM-10 (Circuit breaker) ──→ RM-13 (Fallback chain)

RM-18 (Padrão 4 arquivos) ──→ RM-19 (Stage context)
```

**Regra:** Resolver dependências ANTES do dependente. Ex: RM-01 antes de RM-16 e RM-31.

---

## ESTIMATIVA TOTAL DE ESFORÇO POR PRIORIDADE

| Prioridade | Qtd. | Esforço Total | Sprint Alvo | Responsável Principal |
|:----------:|:----:|:-------------:|:-----------:|:---------------------:|
| P0 | 8 | 58h (~8 dias) | Imediato (bloqueador) | Backend |
| P1 | 10 | 46h (~6 dias) | Sprint N+1 | Backend |
| P2 | 18 | ~100h (~13 dias) | Sprint N+2 a N+4 | Backend + Frontend |
| P3 | 8 | 224h (~28 dias) | Backlog (roadmap) | Backend + Frontend |
| **Total** | **44** | **~428h (~54 dias)** | — | — |

**Nota:** Nem todos os runbooks serão aplicáveis a cada auditoria. O auditor deve identificar quais se aplicam e gerar o resumo executivo com os itens relevantes.

---

# PARTE X: AUDITORIA DA CAMADA DE INTELIGÊNCIA

> **Origem:** Seções derivadas da análise cruzada de `docs/mapa_inteligencia_lia_completo.md`, `lia-agent-system/docs/MAPA_CAMADA_INTELIGENCIA.md` e `lia-agent-system/docs/ai-architecture-audit.md`. Cada checklist verifica se as capacidades DESCRITAS nesses documentos existem DE FATO no código e funcionam conforme o padrão esperado.
>
> **Regra geral:** Para cada item, o auditor deve: (1) verificar se o arquivo existe, (2) verificar se contém a implementação descrita (não é stub), (3) verificar se está conectado ao fluxo real (importado e invocado). Classificação: **OK** = existe e funciona, **PARCIAL** = existe mas incompleto/desconectado, **FALHA** = existe mas quebrado/stub, **AUSENTE** = não encontrado no codebase.

---

## CI-1. Orquestrador e Roteamento

O orquestrador é o ponto de entrada central que recebe mensagens, classifica intenção e roteia para o agente/fluxo correto. Descrito como CascadedRouter com 3 tiers (cache → regex → LLM), mais 3 mecanismos de execução distintos.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| Orchestrator principal | `app/orchestrator/orchestrator.py` | Ponto de entrada — recebe requisição, coordena, retorna |
| MainOrchestrator | `app/orchestrator/main_orchestrator.py` | Ciclo de vida completo de alto nível |
| CascadedRouter | `app/orchestrator/cascaded_router.py` | Router em 3 tiers: semantic cache → fast_router → intent_router |
| FastRouter | `app/orchestrator/fast_router.py` | Tier 2: regex/keywords sem LLM |
| IntentRouter | `app/orchestrator/intent_router.py` | Tier 3: classificação via LLM |
| SemanticCache | `app/orchestrator/semantic_cache.py` | Tier 1: cache semântico (alias) |
| VectorSemanticCache | `app/orchestrator/vector_semantic_cache.py` | Cache semântico via pgvector cosine similarity |
| TenantBudget | `app/orchestrator/tenant_budget.py` | Controle de budget de tokens por tenant |
| NavigationIntent | `app/orchestrator/navigation_intent.py` | Grupos de intent de navegação |
| LLMCascade | `app/orchestrator/llm_cascade.py` | Cascata LLM (Haiku→Sonnet→Opus) |
| ActionExecutor | `app/orchestrator/action_executor.py` | Execução de ações com confirmação |
| PendingAction | `app/orchestrator/pending_action.py` | Estado de ações pendentes (multi-turn) |
| StateManager | `app/orchestrator/state_manager.py` | Persistência de estado de sessão |
| PolicyEngine | `app/orchestrator/policy_engine.py` | Políticas de negócio e guardrails |
| TaskPlanner | `app/orchestrator/task_planner.py` | Decomposição de tarefas complexas |
| ContextAdapter | `app/orchestrator/context_adapter.py` | Adaptação de contexto entre componentes |
| MemoryResolver | `app/orchestrator/memory_resolver.py` | Resolução de memória para o agente |

### Checklist de Auditoria

- [ ] **CI-1.1** CascadedRouter implementa 3 tiers na ordem correta: (1) semantic cache, (2) fast_router (regex), (3) intent_router (LLM)
- [ ] **CI-1.2** SemanticCache/VectorSemanticCache usa pgvector com cosine similarity para lookup de intents já classificados
- [ ] **CI-1.3** FastRouter classifica por regex/keywords sem invocação de LLM — verificar que não há chamada a LLM neste tier
- [ ] **CI-1.4** IntentRouter invoca LLM apenas quando tiers anteriores falham — verificar condicionalidade
- [ ] **CI-1.5** TenantBudget implementa pre-call budget check ANTES de cada invocação LLM (Crença 09)
- [ ] **CI-1.6** TenantBudget possui limites configuráveis por tenant (não hardcoded)
- [ ] **CI-1.7** LLMCascade implementa cascata de modelo barato→caro (ex: Haiku→Sonnet→Opus) com fallback automático
- [ ] **CI-1.8** NavigationIntent agrupa intents de navegação: Configurações, Indicadores, WSI
- [ ] **CI-1.9** ActionExecutor implementa confirmação humana antes de ações de alto impacto (HITL)
- [ ] **CI-1.10** PendingAction gerencia estado multi-turno de ações que aguardam confirmação
- [ ] **CI-1.11** PolicyEngine aplica políticas de negócio como guardrails antes/depois da execução
- [ ] **CI-1.12** TaskPlanner decompõe tarefas complexas em subtarefas sequenciais
- [ ] **CI-1.13** Orchestrator roteia para os 3 mecanismos de execução: ConversationGraph, JobWizardGraph, ReActLoop
- [ ] **CI-1.14** StateManager persiste estado entre turnos de conversa com isolamento por tenant
- [ ] **CI-1.15** MemoryResolver carrega contexto relevante (working + long-term memory) antes de invocar agente

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Arquivos existem | 17/17 (100%) |
| Tiers do CascadedRouter implementados | 3/3 |
| Pre-call budget check presente | Obrigatório (Crença 09) |
| Fallback chain testável | LLM cascade com ≥ 2 providers |
| Isolamento multi-tenant | Presente em cache, budget e state |

---

## CI-2. Grafos LangGraph e State Machines

Fluxos multi-etapa complexos implementados com LangGraph StateGraph. A documentação descreve ConversationGraph (47 nós, 4 subgrafos), JobWizardGraph (6 nós), WSIInterviewGraph e InterviewGraph.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| ConversationGraph | `app/shared/agents/conversation.py` (**documentado mas pode não existir — verificar**) | Grafo principal (47 nós, 4 subgrafos) — ponto de entrada do chat |
| JobWizardGraph | `app/domains/job_management/agents/job_wizard_graph.py` | Grafo do wizard de vagas (6 nós) |
| JobVacancyNodes | `app/domains/job_management/agents/job_vacancy_nodes.py` | Nós do grafo de vagas |
| WSIInterviewGraph | `app/domains/cv_screening/agents/wsi_interview_graph.py` | Grafo da entrevista WSI |
| InterviewGraph | `app/domains/interview_scheduling/agents/interview_graph.py` | Grafo de agendamento de entrevistas |
| InterviewNodes | `app/domains/interview_scheduling/agents/interview_scheduling_nodes.py` | Nós do grafo de agendamento |
| LangGraphBase | `app/shared/agents/langgraph_base.py` | Base genérica para grafos LangGraph stateful |
| LangGraphReActBase | `app/shared/agents/langgraph_react_base.py` | Base para agentes ReAct com LangGraph prebuilt |
| BaseStateMachine | `app/shared/agents/base_state_machine.py` | State machine base para agentes |
| StateMachine | `app/shared/agents/state_machine.py` | State machine implementada |
| Checkpointer | `app/shared/agents/checkpointer.py` | PostgresSaver wrapper com isolamento por tenant |
| SharedNodes | `app/shared/agents/nodes.py` | Nós compartilhados reutilizáveis |
| TimedToolNode | `app/shared/agents/timed_tool_node.py` | Nó de tool com timeout configurável |

### Checklist de Auditoria

- [ ] **CI-2.1** ConversationGraph existe e implementa StateGraph com ≥ 40 nós
- [ ] **CI-2.2** ConversationGraph contém 4 subgrafos: core, job wizard, interview, sourcing
- [ ] **CI-2.3** ConversationGraph define ConversationState como TypedDict com campos obrigatórios (messages, intent, entities, tenant_id)
- [ ] **CI-2.4** JobWizardGraph implementa 6 nós: intent_classifier → field_extractor → tool_router → tool_executor → response_generator → stage_transition
- [ ] **CI-2.5** JobWizardGraph usa conditional edges para roteamento entre nós
- [ ] **CI-2.6** JobWizardGraph define JobWizardState como TypedDict
- [ ] **CI-2.7** WSIInterviewGraph implementa grafo para conduzir entrevista WSI em tempo real
- [ ] **CI-2.8** InterviewGraph implementa grafo para agendamento de entrevistas (≥ 6 nós)
- [ ] **CI-2.9** Todos os grafos possuem proteção contra loops infinitos (max_iterations ou recursion_limit)
- [ ] **CI-2.10** Todos os grafos usam interrupt_before para pontos de decisão que requerem HITL
- [ ] **CI-2.11** Checkpointer implementa PostgresSaver com isolamento por tenant (thread_id inclui tenant_id)
- [ ] **CI-2.12** TimedToolNode implementa timeout configurável (evita hanging de tools)
- [ ] **CI-2.13** BaseStateMachine define estados e transições válidas com proteção contra transições ilegais
- [ ] **CI-2.14** SharedNodes são efetivamente reutilizados em múltiplos grafos (não são dead code)
- [ ] **CI-2.15** LangGraphBase e LangGraphReActBase são usados como base classes pelos grafos de domínio

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Grafos existem | 4/4 (ConversationGraph, JobWizardGraph, WSIInterview, Interview) |
| Proteção contra loops | Presente em 100% dos grafos |
| interrupt_before HITL | Presente em grafos com ações de alto impacto |
| Checkpointer multi-tenant | Isolamento verificado |
| State schemas tipados | TypedDict em todos os grafos |

---

## CI-3. Memória em 3 Níveis

O sistema de memória opera em 3 níveis: Working Memory (sessão), Conversation Memory (cross-sessão via pgvector), Long-Term Memory (permanente com decay). MemoryIntegration unifica os 3 níveis.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| WorkingMemory | `app/shared/agents/working_memory.py` | Memória de trabalho durante uma execução (sessão) |
| LongTermMemory | `app/shared/agents/long_term_memory.py` | Memória permanente com decay — insights cross-sessão |
| MemoryIntegration | `app/shared/agents/memory_integration.py` | Integração: `get_enriched_context()` unifica 3 níveis |
| ConversationState | `app/shared/memory/conversation_state.py` | Estado de conversação |
| ConversationMemory | `app/services/conversation_memory.py` | Memória conversacional cross-sessão (pgvector) |
| ConversationManager | `app/services/conversation_manager.py` | Gerenciamento de conversas |
| MemoryService | `app/services/memory_service.py` | Serviço de memória centralizado |
| CandidateListStore | `app/shared/memory/candidate_list_store.py` | Store de listas de candidatos em memória |
| ReferenceResolver | `app/shared/memory/reference_resolver.py` | Resolução de referências em memória |
| EnhancedAgentMixin | `app/shared/agents/enhanced_agent_mixin.py` | Mixin que adiciona working + LTM a qualquer agente |
| LearningExtractor | `app/shared/agents/learning_extractor.py` | Extrai aprendizados da interação para LTM |

### Checklist de Auditoria

- [ ] **CI-3.1** WorkingMemory mantém contexto apenas durante uma execução/sessão (não persiste entre sessões)
- [ ] **CI-3.2** WorkingMemory armazena: mensagens recentes, entidades extraídas, ferramentas usadas, estado do agente
- [ ] **CI-3.3** ConversationMemory usa pgvector para busca semântica cross-sessão
- [ ] **CI-3.4** ConversationMemory armazena embeddings das interações anteriores com TTL configurável
- [ ] **CI-3.5** LongTermMemory implementa memória permanente com decay factor (insights perdem relevância ao longo do tempo)
- [ ] **CI-3.6** LongTermMemory armazena aprendizados por recrutador (personalização individual)
- [ ] **CI-3.7** MemoryIntegration.get_enriched_context() unifica os 3 níveis: working + conversation + long-term
- [ ] **CI-3.8** MemoryIntegration é efetivamente chamado pelo orquestrador antes de invocar agentes
- [ ] **CI-3.9** EnhancedAgentMixin injeta working + LTM automaticamente em todos os agentes que herdam dele
- [ ] **CI-3.10** LearningExtractor extrai insights ao final de cada interação e persiste no LTM
- [ ] **CI-3.11** Isolamento multi-tenant: cada tenant acessa apenas sua própria memória em TODOS os 3 níveis
- [ ] **CI-3.12** Working Memory tem limite de tamanho (max tokens/mensagens) para evitar context overflow
- [ ] **CI-3.13** Conversation Memory tem retenção configurável (TTL) e limpeza automática
- [ ] **CI-3.14** Long-Term Memory tem mecanismo de decay (insights antigos perdem peso)
- [ ] **CI-3.15** CandidateListStore e ReferenceResolver resolvem referências anafóricas ("ele", "o primeiro") na conversa

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| 3 níveis implementados | Working + Conversation + Long-Term |
| get_enriched_context() funcional | Unifica 3 níveis efetivamente |
| Isolamento multi-tenant | Presente em todos os 3 níveis |
| Decay factor no LTM | Implementado (não peso fixo) |
| Limite de tamanho | Presente no Working Memory |

---

## CI-4. Comunicação Multi-Canal

Sistema com 5 adapters (email, WhatsApp, SMS, Teams, in-app), múltiplos providers (Twilio, Resend, SendGrid, Meta), dispatcher inteligente, webhook handling, e controles de opt-out/quarantine.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| MultiChannelService | `app/shared/channels/multi_channel_service.py` | Serviço multi-canal centralizado |
| ChannelAdapter | `app/shared/channels/channel_adapter.py` | Interface base de adapter de canal |
| ChannelRouter | `app/shared/channels/channel_router.py` | Roteamento entre canais |
| EmailAdapter | `app/shared/channels/adapters/email_adapter.py` | Adapter de email |
| WhatsAppAdapter | `app/shared/channels/adapters/whatsapp_adapter.py` | Adapter de WhatsApp |
| SMSAdapter | `app/shared/channels/adapters/sms_adapter.py` | Adapter de SMS |
| TeamsAdapter | `app/shared/channels/adapters/teams_adapter.py` | Adapter de Teams |
| InAppAdapter | `app/shared/channels/adapters/in_app_adapter.py` | Adapter in-app |
| CommunicationDispatcher | `app/services/communication_dispatcher.py` | Dispatcher — decide canal e executa envio |
| CommunicationService | `app/services/communication_service.py` | Serviço principal de comunicação |
| EmailService | `app/services/email_service.py` | Envio de email |
| ResendProvider | `app/domains/communication/services/email_providers/resend_provider.py` | Provider Resend |
| SendGridProvider | `app/domains/communication/services/email_providers/sendgrid_provider.py` | Provider SendGrid |
| WhatsAppService | `app/services/whatsapp_service.py` | WhatsApp (modo simulado) |
| WhatsAppMetaService | `app/services/whatsapp_meta_service.py` | WhatsApp via Meta/Graph API |
| WhatsAppTwilioService | `app/services/whatsapp_twilio_service.py` | WhatsApp via Twilio |
| WhatsAppFactory | `app/services/whatsapp_factory.py` | Factory de provedores WhatsApp |
| TeamsService | `app/services/teams_service.py` | Integração com Microsoft Teams |
| TeamsBot | `app/services/teams_bot.py` | Bot framework para Teams |
| WebhookService | `app/services/webhook_service.py` | Webhook handling |
| CommunicationHistoryService | `app/services/communication_history_service.py` | Histórico por candidato |
| TransitionDispatchService | `app/domains/communication/services/transition_dispatch_service.py` | Dispatch automático em transições |
| InferBehaviorService | `app/domains/communication/services/infer_behavior_service.py` | Inferência de comportamento |
| InterpretContextLLM | `app/domains/communication/services/interpret_context_llm_service.py` | Interpretação de contexto via LLM |
| EmailTemplatesData | `app/domains/communication/services/email_templates_data.py` | Templates de email |

### Checklist de Auditoria

- [ ] **CI-4.1** MultiChannelService suporta 5 canais: email, WhatsApp, SMS, Teams, in-app
- [ ] **CI-4.2** Cada adapter implementa a interface ChannelAdapter com métodos send() e check_status()
- [ ] **CI-4.3** ChannelRouter implementa lógica de seleção de canal (preferência do candidato, disponibilidade, fallback)
- [ ] **CI-4.4** CommunicationDispatcher seleciona canal e despacha mensagem com retry automático
- [ ] **CI-4.5** EmailService suporta 2+ providers (Resend, SendGrid) com fallback entre eles
- [ ] **CI-4.6** WhatsAppFactory implementa factory pattern para alternar entre providers (Twilio, Meta)
- [ ] **CI-4.7** TeamsService e TeamsBot integram com Microsoft Graph API para comunicação com recrutadores
- [ ] **CI-4.8** WebhookService recebe e processa callbacks de providers (delivery receipts, respostas)
- [ ] **CI-4.9** Opt-out de comunicação é respeitado por TODOS os canais antes do envio
- [ ] **CI-4.10** Rate limiting existe por canal (ex: max WhatsApp/hora por tenant) para evitar spam
- [ ] **CI-4.11** AI_GENERATED_FOOTER é adicionado automaticamente a toda mensagem gerada por IA (Crença 03 — Transparência)
- [ ] **CI-4.12** Quarantine/blocklist existe para destinatários que reportaram spam ou bounced
- [ ] **CI-4.13** CommunicationHistoryService registra todo envio com canal, status, timestamp e tenant
- [ ] **CI-4.14** TransitionDispatchService dispara comunicação automaticamente em transições de pipeline
- [ ] **CI-4.15** InferBehaviorService ajusta tom e conteúdo com base no comportamento do candidato
- [ ] **CI-4.16** InterpretContextLLM entende contexto da situação para gerar mensagem adequada
- [ ] **CI-4.17** Todos os canais possuem PII masking em logs de envio (Crença 04)

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Adapters implementados | 5/5 (email, WhatsApp, SMS, Teams, in-app) |
| Providers com fallback | ≥ 2 providers por canal principal |
| Opt-out respeitado | 100% dos canais |
| AI_GENERATED_FOOTER | Presente em toda mensagem gerada por IA |
| Rate limiting | Configurado por canal e tenant |

---

## CI-5. Processamento Assíncrono

RabbitMQ como message broker, Celery para workers/tasks, DomainTaskManager com controles de concorrência, Dead Letter Queue para mensagens falhadas, e Celery Beat para agendamento.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| CeleryApp | `app/core/celery_app.py` | Configuração do Celery app |
| CeleryConfig | `app/shared/messaging/celery_config.py` | Configuração de filas e exchanges |
| CeleryTasks | `app/jobs/celery_tasks.py` | Definição das tasks Celery |
| EnhancedTaskManager | `app/shared/async_processing/enhanced_task_manager.py` | Task manager com max_concurrent e queue_size |
| TaskManager | `app/shared/async_processing/task_manager.py` | Task manager base |
| TaskScheduler | `app/shared/async_processing/task_scheduler.py` | Agendamento de tasks |
| TaskPersistence | `app/shared/async_processing/task_persistence.py` | Persistência de tasks e DLQ |
| TaskQueue | `app/shared/async_processing/task_queue.py` | Fila de tasks |
| AutomationScheduler | `app/services/automation_scheduler.py` | Agendamento de automações |
| PlannedTaskService | `app/services/planned_task_service.py` | Serviço de tasks planejadas |
| TaskMonitoringAPI | `app/api/v1/task_monitoring.py` | API de monitoramento de tasks |

### Checklist de Auditoria

- [ ] **CI-5.1** CeleryApp está configurado e conecta ao RabbitMQ como broker
- [ ] **CI-5.2** CeleryConfig define exchanges e queues por domínio (routing keys separadas)
- [ ] **CI-5.3** CeleryTasks define tasks para operações pesadas: screening batch, embedding, comunicação em massa
- [ ] **CI-5.4** EnhancedTaskManager implementa `max_concurrent` (limite de tasks simultâneas por domínio)
- [ ] **CI-5.5** EnhancedTaskManager implementa `queue_size` (limite de fila para backpressure)
- [ ] **CI-5.6** Dead Letter Queue (DLQ) está configurada em TaskPersistence para mensagens que falharam após retries
- [ ] **CI-5.7** DLQ possui mecanismo de replay (reprocessamento manual de mensagens falhadas)
- [ ] **CI-5.8** TaskScheduler/AutomationScheduler implementa agendamento periódico (Celery Beat ou APScheduler)
- [ ] **CI-5.9** ASYNC_ELIGIBLE_ACTIONS por domínio — existe lista explícita de quais ações podem ser executadas async
- [ ] **CI-5.10** Tasks possuem timeout configurável (não executam indefinidamente)
- [ ] **CI-5.11** Tasks possuem retry policy: max_retries, exponential backoff, e condições de retry
- [ ] **CI-5.12** TaskMonitoringAPI expõe status de tasks em execução, falhadas e em DLQ
- [ ] **CI-5.13** Isolamento multi-tenant: tasks de um tenant não afetam outro (filas ou prioridades separadas)
- [ ] **CI-5.14** Observabilidade: logs estruturados de task start/complete/fail com duração e tenant_id

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Celery + RabbitMQ configurados | Ambos funcionais |
| DLQ ativa | Com replay mechanism |
| max_concurrent implementado | Por domínio |
| Retry policy | Presente em todas as tasks |
| Monitoramento | API de monitoring funcional |

---

## CI-6. Cache em 3 Camadas

3 camadas de cache: Session Cache (in-memory), Redis Cache (8 namespaces com TTLs), Database Cache. CacheManagerService gerencia com graceful degradation e scoping multi-tenant.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| CacheManagerService | `app/shared/resilience/cache_manager_service.py` | Gerenciador central de cache multi-camada |
| CacheStrategy | `app/shared/cache_strategy.py` | Estratégias de cache (TTL, eviction) |
| AICacheService | `app/services/ai_cache_service.py` | Cache específico para respostas de IA |
| ResponseCacheService | `app/services/response_cache_service.py` | Cache de respostas HTTP |
| EmbeddingCacheService | `app/services/embedding_cache_service.py` | Cache de embeddings |
| JDTemplateCacheService | `app/services/jd_template_cache_service.py` | Cache de templates de JD |
| SemanticCache | `app/orchestrator/semantic_cache.py` | Cache semântico de intents |
| VectorSemanticCache | `app/orchestrator/vector_semantic_cache.py` | Cache semântico via pgvector |
| CircuitBreaker | `app/shared/resilience/circuit_breaker.py` | Circuit breaker (relacionado) |
| StatsManager | `app/shared/resilience/stats_manager.py` | Estatísticas de cache hits/misses |

### Checklist de Auditoria

- [ ] **CI-6.1** CacheManagerService implementa 3 camadas: in-memory (L1), Redis (L2), database (L3)
- [ ] **CI-6.2** Redis Cache define namespaces distintos com TTLs específicos (≥ 8 namespaces documentados)
- [ ] **CI-6.3** Cada namespace Redis tem TTL configurado e documentado (ex: session=1h, intent=24h, embedding=7d)
- [ ] **CI-6.4** Session Cache (in-memory) tem eviction policy (LRU ou size-based) para evitar memory leak
- [ ] **CI-6.5** Database Cache é usado como L3 para dados que sobrevivem a restart do Redis
- [ ] **CI-6.6** Graceful degradation: falha do Redis não derruba a aplicação — fallback para DB ou bypass
- [ ] **CI-6.7** CacheManagerService implementa cache invalidation (manual e TTL-based)
- [ ] **CI-6.8** Multi-tenant scoping: chaves de cache incluem tenant_id para isolamento
- [ ] **CI-6.9** StatsManager registra hit/miss rates por namespace para otimização
- [ ] **CI-6.10** SemanticCache/VectorSemanticCache é efetivamente consultado antes de chamadas LLM (Crença 09)
- [ ] **CI-6.11** EmbeddingCacheService evita recomputação de embeddings já calculados
- [ ] **CI-6.12** CircuitBreaker protege chamadas ao Redis — timeout + fallback configurados

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| 3 camadas implementadas | L1 (memory) + L2 (Redis) + L3 (DB) |
| Graceful degradation | Redis down não derruba app |
| Multi-tenant scoping | tenant_id nas chaves de cache |
| TTLs configurados | Por namespace |
| Cache hit rates monitorados | StatsManager funcional |

---

## CI-7. Sourcing e Busca Inteligente

Dual search (Elasticsearch BM25 + PGVector semântico), WRF (Weighted Ranking Function), pre_wrf_filter, integrações externas (Pearch AI, Apify), e analytics de busca.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| SourcingPipeline | `app/domains/sourcing/services/sourcing_pipeline.py` | Pipeline principal de sourcing |
| WRFService | `app/domains/sourcing/services/wrf_service.py` | Weighted Ranking Function |
| PreWRFFilter | `app/domains/sourcing/services/pre_wrf_filter.py` | Filtro pré-WRF (eligibilidade) |
| ESAnalyzer | `app/domains/sourcing/services/es_analyzer.py` | Busca via Elasticsearch BM25 |
| PGVAnalyzer | `app/domains/sourcing/services/pgv_analyzer.py` | Busca via pgvector (semântica) |
| SearchAnalytics | `app/domains/sourcing/services/search_analytics.py` | Analytics de buscas |
| QueryBuilders | `app/domains/sourcing/services/query_builders.py` | Construtores de queries |
| VacancySearch | `app/domains/sourcing/services/vacancy_search.py` | Busca por vagas |
| CandidateSearchRouteService | `app/domains/sourcing/services/candidate_search_route_service.py` | Roteamento de busca |
| EvaluationCriteria | `app/domains/sourcing/services/evaluation_criteria.py` | Critérios de avaliação |
| PearchService | `app/domains/sourcing/services/pearch_service.py` | Integração Pearch AI |
| ApifyService | `app/domains/sourcing/services/apify_service.py` | Integração Apify (web scraping) |
| ApifyMCPClient | `app/domains/sourcing/services/apify_mcp_client.py` | Cliente MCP para Apify |
| WRFDynamicK | `app/services/wrf_dynamic_k_service.py` | WRF com K dinâmico |
| HybridSearchService | `app/services/hybrid_search_service.py` | Busca híbrida (ES + PGV) |
| SemanticSearchService | `app/shared/intelligence/semantic_search_service.py` | Busca semântica compartilhada |
| EmbeddingService | `app/shared/intelligence/embedding_service.py` | Serviço de embeddings |

### Checklist de Auditoria

- [ ] **CI-7.1** Dual search implementado: Elasticsearch BM25 (keyword) + PGVector (semântico) rodando em paralelo
- [ ] **CI-7.2** WRFService combina scores de ambas as buscas com pesos configuráveis por tipo de vaga
- [ ] **CI-7.3** WRFDynamicK ajusta dinamicamente o K (número de resultados) com base na qualidade dos matches
- [ ] **CI-7.4** PreWRFFilter aplica filtros de eligibilidade ANTES do ranking WRF (eficiência)
- [ ] **CI-7.5** ESAnalyzer usa BM25 com boosting por campos relevantes (título, skills, experiência)
- [ ] **CI-7.6** PGVAnalyzer usa cosine similarity com embeddings pré-computados
- [ ] **CI-7.7** EmbeddingService gera e armazena embeddings de candidatos e vagas
- [ ] **CI-7.8** SearchAnalytics registra métricas de busca: queries, resultados, cliques, conversão
- [ ] **CI-7.9** PearchService e ApifyService integram fontes externas de candidatos
- [ ] **CI-7.10** CandidateSearchRouteService roteia entre busca interna e externa com base em critérios
- [ ] **CI-7.11** QueryBuilders geram queries otimizadas para cada backend (ES, pgvector)
- [ ] **CI-7.12** HybridSearchService unifica resultados de ES + PGV com deduplicação
- [ ] **CI-7.13** FairnessGuard é aplicado nos resultados de busca ANTES de apresentar ao recrutador (Crença 02)
- [ ] **CI-7.14** Isolamento multi-tenant: busca retorna apenas candidatos do tenant correto

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Dual search funcional | ES BM25 + PGVector ambos operacionais |
| WRF com pesos configuráveis | Por tipo de vaga/tenant |
| Pre-WRF filter ativo | Filtra antes de ranquear |
| Analytics de busca | Métricas registradas |
| FairnessGuard pós-busca | Aplicado antes de exibir resultados |

---

## CI-8. Machine Learning e Predição

Serviços de ML: OutcomePredictor, FeatureEngineering, ModelRegistry, PredictiveAnalytics, JobPattern, LearningHub. Verificar se são implementações reais ou stubs.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| OutcomePredictor | `app/services/ml/outcome_predictor.py` | Predição de sucesso de contratação |
| FeatureEngineering | `app/services/ml/feature_engineering.py` | Engenharia de features para ML |
| ModelRegistry | `app/services/ml/model_registry.py` | Registry de modelos ML (versionamento) |
| PredictiveAnalytics | `app/services/predictive_analytics_service.py` | 7 tipos de predição |
| JobPattern | `app/services/job_pattern_service.py` | Padrões históricos de vagas |
| LearningHub | `app/services/learning_hub_service.py` | Hub de aprendizado da plataforma |
| OutcomeCorrelator | `app/services/outcome_correlator_service.py` | Correlação de outcomes |
| PatternDetector | `app/services/pattern_detector_service.py` | Detecção de padrões |
| PipelinePrediction | `app/services/pipeline_prediction_service.py` | Predição de pipeline |
| PipelineVelocity | `app/services/pipeline_velocity_service.py` | Velocidade do pipeline |
| LearningLoop | `app/services/learning_loop_service.py` | Loop de aprendizado |
| FeedbackLearning | `app/services/feedback_learning_service.py` | Aprendizado por feedback |
| LearningAnalytics | `app/services/learning_analytics_service.py` | Analytics de aprendizado |

### Checklist de Auditoria

- [ ] **CI-8.1** OutcomePredictor é implementação REAL com modelo treinado (não heurística hardcoded)
- [ ] **CI-8.2** OutcomePredictor usa features de FeatureEngineering (não features ad hoc)
- [ ] **CI-8.3** FeatureEngineering extrai features estruturadas de candidatos e vagas para alimentar modelos
- [ ] **CI-8.4** ModelRegistry implementa versionamento de modelos com rollback capability
- [ ] **CI-8.5** PredictiveAnalytics implementa ≥ 5 tipos de predição (tempo de contratação, fit, churn, etc.)
- [ ] **CI-8.6** PredictiveAnalytics usa modelos treinados ou LLM-based (não fórmulas artificiais tipo `max(0.6, min(x*3, 0.95))`)
- [ ] **CI-8.7** JobPattern detecta padrões históricos em vagas similares para calibrar avaliações
- [ ] **CI-8.8** LearningHub agrega aprendizados de múltiplas fontes (feedback, outcomes, interações)
- [ ] **CI-8.9** OutcomeCorrelator correlaciona predições com outcomes reais para feedback loop
- [ ] **CI-8.10** PatternDetector identifica anomalias e tendências em dados de recrutamento
- [ ] **CI-8.11** LearningLoop implementa ciclo completo: predição → outcome → feedback → retrain/adjust
- [ ] **CI-8.12** Nenhum serviço de ML retorna confidence score sem base em dados reais (Nota Final #8)
- [ ] **CI-8.13** ModelDrift é monitorado: alertas quando predições divergem de outcomes reais

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Serviços existem | ≥ 10/13 |
| Implementações reais (não stubs) | 100% dos que existem |
| Feedback loop implementado | Predição → Outcome → Adjust |
| Confidence baseada em dados reais | Zero fórmulas artificiais |
| Model drift monitorado | Alertas configurados |

---

## CI-9. Intelligence Layer Services

Serviços de inteligência: SmartExtractor, RAG, embedding_service, semantic_search_service, MarketBenchmark, InferBehavior, InterpretContextLLM.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| SmartExtractor | `app/shared/intelligence/smart_extractor.py` | Extração inteligente de dados de documentos |
| EmbeddingService | `app/shared/intelligence/embedding_service.py` | Geração de embeddings vetoriais |
| SemanticSearchService | `app/shared/intelligence/semantic_search_service.py` | Busca semântica via similaridade vetorial |
| RAGService | `app/services/rag_service.py` | Retrieval-Augmented Generation |
| RAGPipelineService | `app/services/rag_pipeline_service.py` | Pipeline RAG completo |
| MarketBenchmark | `app/services/market_benchmark_service.py` | Benchmarks de mercado (salários, competências) |
| InferBehavior | `app/domains/communication/services/infer_behavior_service.py` | Inferência de comportamento do candidato |
| InterpretContextLLM | `app/domains/communication/services/interpret_context_llm_service.py` | Interpretação de contexto via LLM |
| IntelligenceLayerService | `app/services/intelligence_layer_service.py` | Orquestração da camada de inteligência |
| SuggestionInteraction | `app/services/suggestion_interaction_service.py` | Interações de sugestão inteligente |
| ManagerInference | `app/services/manager_inference_service.py` | Inferência sobre gestores |
| KnowledgeBaseService | `app/services/knowledge_base_service.py` | Base de conhecimento |
| ParamPatterns | `app/shared/intelligence/param_patterns.py` | Patterns de parâmetros para extração |

### Checklist de Auditoria

- [ ] **CI-9.1** SmartExtractor extrai dados estruturados de CVs, JDs e documentos não estruturados via LLM
- [ ] **CI-9.2** SmartExtractor produz output tipado (Pydantic model) — não apenas texto livre
- [ ] **CI-9.3** RAGService implementa augment_with_context(): busca documentos relevantes e injeta como contexto ao LLM
- [ ] **CI-9.4** RAGPipelineService orquestra: embedding → retrieval → ranking → augmentation → generation
- [ ] **CI-9.5** EmbeddingService gera embeddings e os persiste para reuso (não recomputa a cada chamada)
- [ ] **CI-9.6** SemanticSearchService usa pgvector para busca por similaridade em embeddings armazenados
- [ ] **CI-9.7** MarketBenchmark fornece dados de benchmark setorial: salários, competências, tempo de contratação
- [ ] **CI-9.8** MarketBenchmark usa dados dos 8 benchmarks de referência (ABRH, GPTW, Gupy, Robert Half, etc.)
- [ ] **CI-9.9** InferBehavior infere comportamento do candidato a partir de histórico de interações
- [ ] **CI-9.10** InterpretContextLLM interpreta contexto da situação (estágio, canal, histórico) para gerar comunicação adequada
- [ ] **CI-9.11** IntelligenceLayerService orquestra os serviços de inteligência como fachada unificada
- [ ] **CI-9.12** SuggestionInteraction gera sugestões proativas contextualizadas para o recrutador
- [ ] **CI-9.13** KnowledgeBaseService fornece base de conhecimento consultável via RAG

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Serviços existem | ≥ 10/13 |
| RAG funcional | Retrieval + Augmentation + Generation |
| SmartExtractor com output tipado | Pydantic models na saída |
| Embeddings persistidos | Cache efetivo |
| MarketBenchmark com dados reais | ≥ 3 fontes de benchmark |

---

## CI-10. Automação Inteligente

StageAutomationEngine, AutomationScheduler, 16 tipos de triggers, 18 alertas proativos, AutonomyEngine (níveis de autonomia), ProactiveWorker, prediction_action_bridge.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| StageAutomationEngine | `app/services/stage_automation_engine.py` | Engine de automação por estágio |
| AutomationScheduler | `app/services/automation_scheduler.py` | Agendamento de automações |
| AutomationService | `app/services/automation_service.py` | Serviço principal de automação |
| AutomationTriggerService | `app/services/automation_trigger_service.py` | 16 tipos de triggers |
| AutomationHandlers | `app/services/automation_handlers.py` | Handlers de automação |
| ProactiveAlertService | `app/services/proactive_alert_service.py` | 18 alertas proativos |
| ProactiveService | `app/services/proactive_service.py` | Serviço proativo geral |
| AutonomyEngine | `app/shared/agents/autonomy_engine.py` | Engine de autonomia (níveis configuráveis) |
| AutonomousAgentService | `app/services/autonomous_agent_service.py` | Serviço de agente autônomo |
| ProactiveWorker | `app/shared/agents/proactive_worker.py` | Worker proativo |
| PredictionActionBridge | `app/domains/automation/services/prediction_action_bridge.py` | Ponte predição → ação |
| StageTransitionAutomation | `app/services/stage_transition_automation.py` | Automação de transições |
| EventActionConnector | `app/domains/automation/services/event_action_connector.py` | Conector evento → ação |
| LearningAutomation | `app/domains/automation/services/learning_automation.py` | Automação de aprendizado |
| PatternApplier | `app/domains/automation/services/pattern_applier.py` | Aplicação de padrões |
| PipelineMonitor | `app/domains/automation/services/pipeline_monitor.py` | Monitor de pipeline |
| PlannedTaskService | `app/domains/automation/services/planned_task_service.py` | Serviço de tasks planejadas |
| ConfidencePolicyService | `app/services/confidence_policy_service.py` | Política de confiança (3 níveis) |

### Checklist de Auditoria

- [ ] **CI-10.1** StageAutomationEngine implementa automações por estágio do pipeline (não genérica)
- [ ] **CI-10.2** AutomationTriggerService define ≥ 16 tipos de triggers (candidato aplicou, tempo expirou, score calculado, etc.)
- [ ] **CI-10.3** ProactiveAlertService implementa ≥ 18 tipos de alertas proativos para o recrutador
- [ ] **CI-10.4** AutonomyEngine implementa níveis de autonomia configuráveis por empresa (Crença 12)
- [ ] **CI-10.5** AutonomyEngine começa com autonomia mínima e escala com confiança demonstrada
- [ ] **CI-10.6** AutonomyEngine define pelo menos 3 níveis: ASSISTANT (sugere), SEMI-AUTO (sugere + executa com aprovação), AUTO (executa)
- [ ] **CI-10.7** ConfidencePolicyService implementa 3 níveis: APPLY_SILENT (>= 0.85), APPLY_NOTIFY (0.70-0.84), ASK_USER (< 0.70)
- [ ] **CI-10.8** PredictionActionBridge conecta predições de ML a ações automáticas (ex: predição de churn → alerta proativo)
- [ ] **CI-10.9** ProactiveWorker executa verificações periódicas e gera sugestões sem esperar input do recrutador
- [ ] **CI-10.10** EventActionConnector mapeia eventos de negócio a ações automáticas
- [ ] **CI-10.11** AutomationScheduler agenda execuções periódicas (diárias, semanais)
- [ ] **CI-10.12** Todas as automações de alto impacto passam por HITL (Crença 01)
- [ ] **CI-10.13** Isolamento multi-tenant: automações de um tenant não afetam outro
- [ ] **CI-10.14** PipelineMonitor detecta anomalias no pipeline e dispara alertas

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Triggers implementados | ≥ 16 tipos |
| Alertas proativos | ≥ 18 tipos |
| Níveis de autonomia | ≥ 3 com escalação progressiva |
| ConfidencePolicy | 3 níveis com thresholds corretos |
| HITL em ações de alto impacto | Obrigatório |

---

## CI-11. Integração ATS

ats_sync_service, 4 clientes (Gupy, Pandapé, Merge, StackOne), criptografia de credenciais, idempotency, retry automático.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| ATSSyncService | `app/services/ats_sync_service.py` | Serviço principal de sincronização ATS |
| ATSBase | `app/services/ats_clients/base.py` | Interface base para clientes ATS |
| GupyClient | `app/services/ats_clients/gupy.py` | Cliente ATS Gupy |
| PandapeClient | `app/services/ats_clients/pandape.py` | Cliente ATS Pandapé |
| MergeClient | `app/services/ats_clients/merge.py` | Cliente Merge (unificado) |
| StackOneClient | `app/services/ats_clients/stackone.py` | Cliente StackOne |
| ATSFactory | `app/shared/providers/ats_factory.py` | Factory de provedores ATS |
| Encryption | `app/shared/encryption.py` | Criptografia de credenciais |
| ATSJobHistory | `app/services/ats_job_history_service.py` | Histórico de jobs ATS |
| ATSIntegrationAgent | `app/domains/ats_integration/agents/ats_integration_react_agent.py` | Agente ReAct de integração |
| GupyService | `app/services/gupy_service.py` | Serviço Gupy (legacy) |
| PandapeService | `app/services/pandape_service.py` | Serviço Pandapé (legacy) |
| MergeATSService | `app/services/merge_ats_service.py` | Serviço Merge (legacy) |

### Checklist de Auditoria

- [ ] **CI-11.1** ATSSyncService implementa sincronização bidirecional (import + export) de candidatos e vagas
- [ ] **CI-11.2** ATSBase define interface com métodos obrigatórios: sync_candidates, sync_jobs, get_status
- [ ] **CI-11.3** 4 clientes ATS implementados: Gupy, Pandapé, Merge, StackOne — todos herdam de ATSBase
- [ ] **CI-11.4** ATSFactory implementa factory pattern para instanciar o cliente correto por configuração do tenant
- [ ] **CI-11.5** Credenciais de ATS são criptografadas em repouso (Fernet ou similar) via `app/shared/encryption.py`
- [ ] **CI-11.6** Credenciais NUNCA aparecem em logs (PII masking intercepta antes de logar)
- [ ] **CI-11.7** Sincronização é idempotente (re-executar não duplica registros) — verificar uso de IDs externos
- [ ] **CI-11.8** Retry automático com exponential backoff em chamadas a APIs de ATS
- [ ] **CI-11.9** Circuit breaker protege chamadas a cada provedor ATS (Crença 07)
- [ ] **CI-11.10** ATSJobHistory registra histórico de sincronizações para auditoria
- [ ] **CI-11.11** Isolamento multi-tenant: cada tenant conecta a seu próprio ATS com credenciais isoladas
- [ ] **CI-11.12** ATSIntegrationAgent (ReAct) pode executar sincronização sob demanda via chat

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Clientes ATS | 4/4 (Gupy, Pandapé, Merge, StackOne) |
| Criptografia de credenciais | Fernet at-rest |
| Idempotência | Presente em sync operations |
| Circuit breaker | Por provedor ATS |
| Retry automático | Exponential backoff |

---

## CI-12. HITL Persistence

HITLService com Redis fast-path + PostgreSQL, modelos HITLPendingAction/HITLAuditTrail, interrupt_before nos grafos, aprovação via WebSocket.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| HITLService | `app/services/hitl_service.py` | Serviço principal HITL (Redis + PostgreSQL) |
| HITLModels | `app/models/hitl.py` | Modelos: HITLPendingAction, HITLAuditTrail |
| PendingAction | `app/orchestrator/pending_action.py` | Ações pendentes no orquestrador |
| ActionExecutor | `app/orchestrator/action_executor.py` | Executor com confirmação humana |
| Checkpointer | `app/shared/agents/checkpointer.py` | Checkpointing para interrupt_before |
| HumanReviewSampling | `app/services/human_review_sampling_service.py` | Amostragem para revisão humana |
| ConfidencePolicyService | `app/services/confidence_policy_service.py` | Política de confiança |
| ApprovalModel | `app/models/approval.py` | Modelo de aprovação |
| WebSocketModule | `app/shared/websocket/` | Módulo WebSocket |

### Checklist de Auditoria

- [ ] **CI-12.1** HITLService implementa dual storage: Redis (fast-path para ações pendentes) + PostgreSQL (persistência definitiva)
- [ ] **CI-12.2** HITLPendingAction modelo define: action_type, payload, requester_id, tenant_id, status, created_at, expires_at
- [ ] **CI-12.3** HITLAuditTrail modelo registra: quem aprovou/rejeitou, quando, motivo, e a ação original
- [ ] **CI-12.4** HITLAuditTrail é append-only (imutável) para compliance (Crença 08)
- [ ] **CI-12.5** interrupt_before é usado em grafos LangGraph para pausar execução em pontos de decisão humana
- [ ] **CI-12.6** interrupt_before está presente em todos os grafos que executam ações de alto impacto (rejeição, movimentação, comunicação)
- [ ] **CI-12.7** Aprovação via WebSocket: frontend recebe notificação real-time de ações pendentes
- [ ] **CI-12.8** Ações pendentes têm timeout (expires_at) — se não aprovadas, expiram automaticamente
- [ ] **CI-12.9** HumanReviewSampling implementa amostragem estatística de decisões automáticas para revisão
- [ ] **CI-12.10** ConfidencePolicyService roteia para HITL quando confiança < 0.70 (ASK_USER)
- [ ] **CI-12.11** Frontend exibe card de confirmação (HITLConfirmCard) com contexto suficiente para decisão
- [ ] **CI-12.12** Isolamento multi-tenant: ações pendentes visíveis apenas para o tenant correto

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Dual storage (Redis + PG) | Ambos funcionais |
| Audit trail append-only | Imutável |
| interrupt_before nos grafos | Em todos os pontos de alto impacto |
| Timeout de ações pendentes | Configurado |
| WebSocket para aprovação | Real-time |

---

## CI-13. Fluxos End-to-End do Produto

Verificação de que os 10 fluxos descritos no ai-architecture-audit (seção 2) existem no código como implementações funcionais, não apenas documentação.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| WizardAgent / JobWizardGraph | `app/domains/job_management/agents/wizard_react_agent.py`, `job_wizard_graph.py` | F1: Wizard de criação de vaga |
| PipelineAgent | `app/domains/cv_screening/agents/pipeline_react_agent.py` | F2, F6, F10: Triagem e jornada candidato |
| WSIScreeningPipeline | `app/services/wsi_screening_pipeline.py` | F6: Pipeline WSI completo |
| WSIQuestionGenerator | `app/services/wsi_question_generator.py` | F7: Geração de perguntas |
| WhatsAppService | `app/services/whatsapp_service.py` | F3, F8: Comunicação e inscrição WhatsApp |
| WhatsAppMetaService | `app/services/whatsapp_meta_service.py` | F3: WhatsApp via Meta API |
| TeamsBot | `app/services/teams_bot.py` | F4: Comunicação Teams |
| EmailService | `app/services/email_service.py` | F5: Comunicação Email |
| CommunicationDispatcher | `app/services/communication_dispatcher.py` | F3-F5: Dispatcher multi-canal |
| TalentAgent | `app/domains/recruiter_assistant/agents/talent_react_agent.py` | F9: Ajuda ao recrutador |
| CVScoringService | `app/services/cv_scoring_service.py` | F10: Scoring de CV |
| ConsentCheckerService | `app/services/consent_checker_service.py` | F8: Consentimento do candidato |
| WebhookService | `app/services/webhook_service.py` | F3, F8: Webhooks de entrada |
| OrchestratorRoutes | `app/api/orchestrator_routes.py` | Rota principal do chat (todos os fluxos) |

### Fluxos a verificar

| # | Fluxo | Seção de Referência | Domínios Envolvidos |
|---|-------|---------------------|---------------------|
| F1 | Wizard de Criação de Vaga | §2.1 | job_management |
| F2 | Jornada Completa do Candidato | §2.2 | cv_screening, sourcing, communication |
| F3 | Comunicação WhatsApp com Candidatos | §2.3 | communication |
| F4 | Comunicação Teams com Recrutadores | §2.4 | communication |
| F5 | Comunicação Email | §2.5 | communication |
| F6 | Triagem e Scoring WSI Detalhado | §2.6 | cv_screening |
| F7 | Criação de Perguntas de Triagem via Edição de Vaga | §2.7 | cv_screening, job_management |
| F8 | Inscrição de Candidato via WhatsApp | §2.8 | communication, cv_screening |
| F9 | Pedido de Ajuda do Recrutador Quando IA Falha | §2.9 | recruiter_assistant |
| F10 | Comportamento Completo da IA na Triagem | §2.10 | cv_screening |

### Checklist de Auditoria

- [ ] **CI-13.1** **F1 — Wizard**: JobWizardGraph/WizardAgent implementa coleta passo-a-passo de dados da vaga, validação e criação
- [ ] **CI-13.2** **F1 — Wizard**: JD é gerada via LLM com sugestões de skills, requisitos e descrição
- [ ] **CI-13.3** **F2 — Jornada Candidato**: Pipeline completo existe: aplicação → triagem → avaliação → entrevista → proposta
- [ ] **CI-13.4** **F2 — Jornada Candidato**: Transições de estágio são rastreadas com audit trail
- [ ] **CI-13.5** **F3 — WhatsApp**: WhatsApp é canal funcional para comunicação com candidatos (não apenas simulado)
- [ ] **CI-13.6** **F3 — WhatsApp**: Webhook recebe respostas do candidato e as processa no pipeline
- [ ] **CI-13.7** **F4 — Teams**: Integração Teams permite interação do recrutador com LIA via bot
- [ ] **CI-13.8** **F4 — Teams**: TeamsBot implementa BotBuilder com autenticação Azure AD
- [ ] **CI-13.9** **F5 — Email**: Envio de email funcional com providers reais (Resend, SendGrid)
- [ ] **CI-13.10** **F5 — Email**: Templates de email são personalizáveis e suportam variáveis dinâmicas
- [ ] **CI-13.11** **F6 — WSI**: Pipeline WSI implementa 7 blocos de avaliação com scoring determinístico + IA
- [ ] **CI-13.12** **F6 — WSI**: WSI scoring usa calibração por senioridade (Dreyfus × Bloom)
- [ ] **CI-13.13** **F7 — Perguntas Triagem**: Perguntas são geradas por IA com calibração por taxonomia de Bloom
- [ ] **CI-13.14** **F7 — Perguntas Triagem**: Perguntas são ajustáveis dinamicamente durante a entrevista
- [ ] **CI-13.15** **F8 — Inscrição WhatsApp**: Candidato pode se inscrever em vaga via WhatsApp (fluxo completo)
- [ ] **CI-13.16** **F8 — Inscrição WhatsApp**: Consentimento é coletado ANTES de processar dados do candidato
- [ ] **CI-13.17** **F9 — Ajuda Recrutador**: Existe fallback quando IA não consegue resolver — escalação para modo manual
- [ ] **CI-13.18** **F9 — Ajuda Recrutador**: Recrutador pode sobrescrever qualquer decisão da IA (Crença 01)
- [ ] **CI-13.19** **F10 — Comportamento IA Triagem**: IA nunca rejeita automaticamente sem gate de revisão (Inegociável #2)
- [ ] **CI-13.20** **F10 — Comportamento IA Triagem**: FairnessGuard ativo em 100% das decisões de screening

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Fluxos com implementação real | ≥ 8/10 |
| Fluxos com wiring completo (front→back→agente→serviço) | ≥ 6/10 |
| Consentimento antes de processamento | 100% dos fluxos com candidatos |
| FairnessGuard em fluxos de avaliação | 100% |
| Escalação humana disponível | 100% dos fluxos |

---

## CI-14. Telas do Produto e Pontos de IA

Verificação de que as 7 telas com touchpoints de IA descritas no ai-architecture-audit (seção 2.0) existem no frontend com os componentes de IA conectados ao backend.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| OrchestratorRoutes | `app/api/orchestrator_routes.py` | Backend: rota principal do chat |
| KanbanAssistantAPI | `app/api/v1/kanban_assistant.py` | Backend: API do Kanban assistant |
| KanbanAssistantService | `app/services/kanban_assistant_service.py` | Backend: serviço do Kanban |
| JDEnrichmentService | `app/services/jd_enrichment_service.py` | Backend: enriquecimento de JD |
| CVScoringService | `app/services/cv_scoring_service.py` | Backend: scoring de candidatos |
| CompanyConfigurationService | `app/services/company_configuration_service.py` | Backend: configuração de empresa |
| ConfidencePolicyService | `app/services/confidence_policy_service.py` | Backend: política de confiança |
| LiaScoreService | `app/services/lia_score_service.py` | Backend: score LIA |
| LiaFieldConfigService | `app/services/lia_field_config_service.py` | Backend: configuração de campos LIA |

> **Nota:** Os componentes frontend (`jobs-page.tsx`, `ExpandedChatModal`, Kanban, etc.) devem ser localizados na árvore do frontend. Se o frontend não está no mesmo repositório, o auditor deve verificar no repositório correspondente. Os paths de backend acima são os endpoints e serviços que esses componentes consomem.

### Telas a verificar

| # | Tela | Componente Frontend Esperado | Pontos de IA |
|---|------|------------------------------|--------------|
| T1 | Gestão de Vagas — Tabela | `jobs-page.tsx` | Busca inteligente, LIA chat, insights, sugestões, pipeline score |
| T2 | Gestão de Vagas — Painel LIA Expandido | `jobs-page.tsx` (estado expandido) | Suggestion cards, queries guide, áudio |
| T3 | Wizard de Criação / Super Chat | `ExpandedChatModal` | Chat conversacional, JD generation, skills suggestion |
| T4 | Super Chat Fullscreen | `ExpandedChatModal` (fullscreen) | Wizard completo, painéis contextuais |
| T5 | Kanban Pipeline | Componente Kanban | LIA contextual, drag-and-drop, sugestões por coluna |
| T6 | Painel do Candidato | Perfil do candidato | WSI score, histórico, comunicação, avaliação |
| T7 | Dashboard Admin/Configurações | Configurações | Políticas de contratação, níveis de autonomia |

### Checklist de Auditoria

- [ ] **CI-14.1** **T1**: Componente de tabela de vagas existe com integração de busca inteligente (AISearchToggle)
- [ ] **CI-14.2** **T1**: Pipeline LIA (barras visuais) exibe score por estágio calculado pelo backend
- [ ] **CI-14.3** **T1**: Badge de sugestões proativas (💡) conectado a `useLiaSuggestions` hook
- [ ] **CI-14.4** **T2**: Painel LIA expandido renderiza à esquerda da tabela com suggestion cards
- [ ] **CI-14.5** **T2**: Suggestion cards são geradas pelo backend (não hardcoded no frontend)
- [ ] **CI-14.6** **T3**: ExpandedChatModal implementa chat à esquerda + side panel contextual à direita
- [ ] **CI-14.7** **T3**: Progress tracker no wizard mostra campos preenchidos vs. pendentes
- [ ] **CI-14.8** **T4**: Modo fullscreen ocupa 100% com todos os painéis contextuais (JD preview, skills, critérios)
- [ ] **CI-14.9** **T5**: Kanban com drag-and-drop que dispara transição de estágio com confirmação
- [ ] **CI-14.10** **T5**: LIA contextual no Kanban gera sugestões por coluna/estágio
- [ ] **CI-14.11** **T6**: Painel do candidato exibe WSI score com breakdown por dimensão
- [ ] **CI-14.12** **T6**: Histórico de comunicação (email, WhatsApp) visível no painel
- [ ] **CI-14.13** **T7**: Configurações permitem ajustar nível de autonomia da IA por empresa
- [ ] **CI-14.14** **T7**: Configurações de políticas de contratação (CompanyHiringPolicy) editáveis
- [ ] **CI-14.15** Todas as telas seguem o design system: LIA à esquerda, conteúdo ao centro, preview à direita
- [ ] **CI-14.16** Todas as telas são acessíveis: aria-labels, keyboard navigation, WCAG 2.1 AA (Crença 13)

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Telas existem no frontend | ≥ 5/7 |
| Pontos de IA conectados ao backend | ≥ 70% dos pontos descritos |
| Design system consistente | Layout LIA-esquerda em todas as telas |
| Acessibilidade | WCAG 2.1 AA em todas as telas |

---

## CI-15. Token Tracking e Controle de Custos

token_tracking_service, tenant_budget, pre-call budget check, cascata de modelo (barato→caro), LLM fallback chain, cost alerting.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| TokenTrackingService | `app/services/token_tracking_service.py` | Registro de consumo de tokens por chamada |
| TokenBudgetService | `app/services/token_budget_service.py` | Orçamento de tokens por tenant |
| TenantBudget | `app/orchestrator/tenant_budget.py` | Budget check no orquestrador |
| LLMCascade | `app/orchestrator/llm_cascade.py` | Cascata de modelos (barato→caro) |
| LLMFactory | `app/shared/providers/llm_factory.py` | Factory com fallback chain |
| LLMClaude | `app/shared/providers/llm_claude.py` | Provider Claude |
| LLMGemini | `app/shared/providers/llm_gemini.py` | Provider Gemini |
| LLMOpenAI | `app/shared/providers/llm_openai.py` | Provider OpenAI |
| LLMClient | `app/shared/providers/llm_client.py` | Cliente LLM base |
| LLMProvider | `app/shared/providers/llm_provider.py` | Interface de provider |
| BillingService | `app/services/billing_service.py` | Serviço de billing |
| PlanLimitsService | `app/services/plan_limits_service.py` | Limites por plano |
| AIConsumption | `app/models/ai_consumption.py` | Modelo de consumo de IA |
| DriftAlertService | `app/services/drift_alert_service.py` | Alertas de drift de custos |

### Checklist de Auditoria

- [ ] **CI-15.1** TokenTrackingService registra tokens consumidos por chamada: input_tokens, output_tokens, modelo, tenant_id, custo_estimado
- [ ] **CI-15.2** TokenBudgetService define orçamento por tenant com limites diários/mensais
- [ ] **CI-15.3** TenantBudget implementa pre-call budget check ANTES de invocar LLM (Crença 09)
- [ ] **CI-15.4** Pre-call check bloqueia chamada quando budget excedido (não apenas loga)
- [ ] **CI-15.5** LLMCascade implementa cascata: modelo barato primeiro (Haiku/Flash), escala para caro (Sonnet/Opus) apenas quando necessário
- [ ] **CI-15.6** LLMFactory implementa fallback chain: Provider1 → Provider2 → Provider3 → Erro 503
- [ ] **CI-15.7** Fallback chain é testável end-to-end (Production Readiness Gate #2)
- [ ] **CI-15.8** 3 providers LLM implementados: Claude (Anthropic), Gemini (Google), OpenAI
- [ ] **CI-15.9** Cada provider implementa a interface LLMProvider com métodos consistentes
- [ ] **CI-15.10** Circuit breaker protege cada provider individualmente (Crença 07)
- [ ] **CI-15.11** Cost alerting: alertas disparam quando custo diário/mensal excede threshold
- [ ] **CI-15.12** DriftAlertService detecta aumento anômalo de custos (> 20% em relação à média)
- [ ] **CI-15.13** AIConsumption modelo persiste dados de consumo para dashboards e relatórios
- [ ] **CI-15.14** PlanLimitsService aplica limites de consumo por plano de assinatura

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Pre-call budget check | Obrigatório (Crença 09) |
| Cascata de modelo | ≥ 2 tiers (barato → caro) |
| Fallback chain | ≥ 3 providers com fallback |
| Token tracking | Por chamada, com custo estimado |
| Cost alerting | Alertas configurados |

---

## CI-16. Explainability e User Preferences

explainability_service, ExecutionLogStore, API de explicabilidade, UserAgentPreferenceService (auto-confirm), agent_quality_evaluator.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| ExplainabilityService | `app/services/explainability_service.py` | Explicabilidade das decisões da IA |
| ExecutionLogStore | `app/shared/agents/execution_log_store.py` | Store de logs de execução |
| UserAgentPreferenceService | `app/services/user_agent_preference_service.py` | Preferências do recrutador (auto-confirm) |
| AgentQualityEvaluator | `app/services/agent_quality_evaluator.py` | Avaliação de qualidade do agente |
| AgentQualityEvaluation | `app/models/agent_quality_evaluation.py` | Modelo de avaliação |
| Observability | `app/shared/agents/observability.py` | Observabilidade dos agentes |
| Confidence | `app/shared/agents/confidence.py` | Estimativa de confiança |
| RecruiterPersonalization | `app/services/recruiter_personalization_service.py` | Personalização por recrutador |
| LearningConfirmation | `app/services/learning_confirmation_service.py` | Confirmação de aprendizado |
| LearningOutcome | `app/services/learning_outcome_service.py` | Outcomes de aprendizado |

### Checklist de Auditoria

- [ ] **CI-16.1** ExplainabilityService gera explicações legíveis para cada decisão da IA (Crença 03)
- [ ] **CI-16.2** ExplainabilityService fornece API consultável: `/api/v1/explainability/{decision_id}`
- [ ] **CI-16.3** Explicações incluem: input, raciocínio, ferramentas usadas, output, confiança
- [ ] **CI-16.4** "Por que fui rejeitado?" é respondível com raciocínio rastreável (Crença 03)
- [ ] **CI-16.5** ExecutionLogStore registra cada etapa do agente: thought, action, observation, final_answer
- [ ] **CI-16.6** ExecutionLogStore é consultável para debugging e auditoria post-mortem
- [ ] **CI-16.7** UserAgentPreferenceService permite recrutador configurar auto-confirm para ações de baixo risco
- [ ] **CI-16.8** Auto-confirm respeita limites: NUNCA auto-confirma rejeições ou comunicações de alto impacto
- [ ] **CI-16.9** AgentQualityEvaluator avalia qualidade das respostas do agente (relevância, completude, tom)
- [ ] **CI-16.10** AgentQualityEvaluation modelo persiste avaliações para análise longitudinal
- [ ] **CI-16.11** RecruiterPersonalization adapta comportamento da LIA por recrutador (threshold: 10+ vagas)
- [ ] **CI-16.12** Confidence implementa estimativa de confiança baseada em dados reais (não fórmula artificial)
- [ ] **CI-16.13** Observability registra métricas: latência, tokens, confiança, erros — por agente e execução
- [ ] **CI-16.14** LearningConfirmation e LearningOutcome fecham o loop: decisão → resultado → ajuste

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| API de explicabilidade | Funcional e consultável |
| ExecutionLogStore | Registra todas as etapas |
| User preferences | Configuráveis por recrutador |
| Auto-confirm nunca em alto impacto | Verificado |
| Confidence baseada em dados reais | Zero fórmulas artificiais |

---

## CI-17. Agentes ReAct — Completude e Padrão 4-File

Verificação de que TODOS os agentes ReAct seguem o padrão 4-file (agent, system_prompt, tool_registry, stage_context) e estão registrados no ReactAgentRegistry.

### Arquivos a inspecionar

| Agente | Base Path | Domínio |
|--------|-----------|---------|
| WizardAgent | `app/domains/job_management/agents/wizard_*` | job_management |
| PipelineAgent | `app/domains/cv_screening/agents/pipeline_*` | cv_screening |
| SourcingAgent | `app/domains/sourcing/agents/sourcing_*` | sourcing |
| AutomationAgent | `app/domains/automation/agents/automation_*` | automation |
| TalentAgent | `app/domains/recruiter_assistant/agents/talent_*` | recruiter_assistant |
| KanbanAgent | `app/domains/recruiter_assistant/agents/kanban_*` | recruiter_assistant |
| JobsMgmtAgent | `app/domains/recruiter_assistant/agents/jobs_mgmt_*` | recruiter_assistant |
| PolicyAgent | `app/domains/policy/agents/` | policy |
| PipelineTransitionAgent | `app/domains/pipeline/agents/pipeline_transition_*` | pipeline |
| AnalyticsAgent | `app/domains/analytics/agents/analytics_*` | analytics |
| CommunicationAgent | `app/domains/communication/agents/communication_*` | communication |
| ATSIntegrationAgent | `app/domains/ats_integration/agents/ats_integration_*` | ats_integration |
| Registry | `app/shared/agents/react_agent_registry.py` | shared |
| ReActLoop | `app/shared/agents/react_loop.py` | shared |

### Checklist de Auditoria

- [ ] **CI-17.1** Cada agente ReAct possui 4 arquivos: `*_react_agent.py`, `*_system_prompt.py`, `*_tool_registry.py`, `*_stage_context.py`
- [ ] **CI-17.2** ReactAgentRegistry registra todos os agentes com nome, domínio e classe
- [ ] **CI-17.3** ReactAgentRegistry é usado pelo orquestrador para instanciar agentes (não import direto)
- [ ] **CI-17.4** ReActLoop implementa ciclo: REASON → ACT → OBSERVE → DECIDE com max_iterations
- [ ] **CI-17.5** Cada system_prompt contém seções obrigatórias: persona, capabilities, constraints, anti-sycophancy
- [ ] **CI-17.6** Cada system_prompt inclui few-shot examples relevantes ao domínio
- [ ] **CI-17.7** Cada tool_registry define lista explícita de ferramentas com type hints e docstrings
- [ ] **CI-17.8** Cada stage_context define comportamento por estágio do pipeline
- [ ] **CI-17.9** Todos os agentes herdam de base adequada (AgentInterface, EnhancedAgentMixin ou LangGraphReActBase)
- [ ] **CI-17.10** Todos os system_prompts incluem seção de anti-sycophancy (Crença 11 — sem exceção)
- [ ] **CI-17.11** Todos os agentes aplicam FairnessGuard na entrada e saída (Crença 02)
- [ ] **CI-17.12** Todos os agentes incluem calibração por contexto de empresa (STARTUP/PME/CORPORAÇÃO)
- [ ] **CI-17.13** Agentes que avaliam candidatos possuem PII masking antes de enviar ao LLM (Crença 04)

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| Padrão 4-file seguido | 100% dos agentes ReAct |
| Registrados no registry | 100% |
| Anti-sycophancy em prompts | 100% |
| FairnessGuard ativo | 100% dos agentes que avaliam candidatos |
| Few-shot examples | Presentes em 100% dos prompts |

---

## CI-18. Compliance e Governança Compartilhada

Verificação dos componentes compartilhados de compliance, governança, e resiliência que suportam toda a plataforma.

### Arquivos a inspecionar

| Componente | Path esperado | Papel |
|------------|---------------|-------|
| FairnessGuard | `app/shared/compliance/fairness_guard.py` | Guard anti-discriminação 3 camadas |
| AuditService | `app/shared/compliance/audit_service.py` | Serviço de trilha de auditoria |
| AuditModels | `app/shared/compliance/audit_models.py` | Modelos de auditoria |
| AuditWriter | `app/shared/compliance/audit_writer.py` | Writer de registros de auditoria |
| AuditCallback | `app/shared/compliance/audit_callback.py` | Callback de auditoria |
| AuditStorage | `app/shared/compliance/audit_storage.py` | Storage de auditoria |
| FactChecker | `app/shared/compliance/fact_checker.py` | Verificação de fatos |
| GuardrailRepository | `app/shared/compliance/guardrail_repository.py` | Repository de guardrails |
| PIIMasking | `app/shared/pii_masking.py` | PII masking global |
| PromptInjection | `app/shared/prompt_injection.py` | Proteção contra prompt injection |
| CircuitBreaker | `app/shared/resilience/circuit_breaker.py` | Circuit breaker |
| FeatureFlagService | `app/shared/governance/feature_flag_service.py` | Feature flags |
| AgentMonitoring | `app/shared/governance/agent_monitoring_service.py` | Monitoramento de agentes |
| ABTesting | `app/shared/ab_testing.py` | A/B testing |
| StructuredLogging | `app/shared/structured_logging.py` | Logging estruturado |
| Tracing | `app/shared/tracing.py` | Distributed tracing |
| PolicyMiddleware | `app/shared/policy_middleware.py` | Middleware de políticas |
| DelegationFallback | `app/shared/delegation_fallback.py` | Fallback de delegação |

### Checklist de Auditoria

- [ ] **CI-18.1** FairnessGuard implementa 3 camadas: regex (40+ patterns), léxico implícito (15+ termos), LLM semântico
- [ ] **CI-18.2** FairnessGuard é middleware automático (não depende de chamada manual por cada agente)
- [ ] **CI-18.3** AuditService gera trilha de auditoria append-only e imutável
- [ ] **CI-18.4** AuditTrail inclui: quem, o quê, quando, resultado, tenant_id
- [ ] **CI-18.5** PIIMasking está ativo no root logger (não apenas por app) — CPF, email, telefone, nomes mascarados
- [ ] **CI-18.6** PIIMasking intercepta ANTES de persistir logs (não após)
- [ ] **CI-18.7** PromptInjection detecta e bloqueia tentativas de injection nos inputs
- [ ] **CI-18.8** CircuitBreaker implementa 3 estados: CLOSED → OPEN → HALF-OPEN com thresholds configuráveis
- [ ] **CI-18.9** CircuitBreaker protege TODAS as integrações externas (LLM providers, ATS, communication)
- [ ] **CI-18.10** FeatureFlagService permite habilitar/desabilitar features por tenant
- [ ] **CI-18.11** AgentMonitoring registra métricas de saúde dos agentes (uptime, latência, erros)
- [ ] **CI-18.12** StructuredLogging usa formato JSON com campos obrigatórios: timestamp, level, tenant_id, request_id
- [ ] **CI-18.13** Tracing implementa distributed tracing com propagação de correlation_id
- [ ] **CI-18.14** PolicyMiddleware aplica políticas de empresa automaticamente em todas as rotas
- [ ] **CI-18.15** ABTesting suporta testes A/B para prompts e modelos com registro de outcomes
- [ ] **CI-18.16** FactChecker verifica afirmações factuais do LLM contra dados do banco

### Critérios de Aprovação

| Critério | Threshold |
|----------|-----------|
| FairnessGuard 3 camadas | Todas implementadas |
| FairnessGuard como middleware | Automático (não manual) |
| Audit trail imutável | Append-only verificado |
| PIIMasking no root logger | Global |
| CircuitBreaker em integrações | 100% das externas |

---

# PARTE XI: DIAGNÓSTICO POR PROMPT/ASSISTENTE — PROCEDIMENTO COMPLETO

> **Objetivo:** Gerar diagnóstico detalhado e comparativo de cada prompt/assistente da plataforma LIA, no mesmo nível de profundidade de um relatório executivo de arquitetura. Este procedimento produz: mapeamento de stack completo por prompt, inventário de tools, análise de capacidades vs gaps, problemas identificados, oportunidades, matrizes transversais multi-dimensionais e mapa comparativo de capacidades.

---

## DP-01: INVENTÁRIO DE PROMPTS/ASSISTENTES

**Objetivo:** Identificar todos os prompts/assistentes ativos na plataforma e seu escopo.

**Procedimento:**

1. Listar todos os scopes em `lia-agent-system/app/tools/scope_config.py`:
   ```bash
   grep -n "class PromptScope" lia-agent-system/app/tools/scope_config.py
   grep -n "TALENT_FUNNEL\|JOB_TABLE\|IN_JOB\|GLOBAL\|HIRING_POLICY\|JOB_WIZARD" lia-agent-system/app/tools/scope_config.py
   ```

2. Para cada scope, identificar o arquivo de prompt principal:
   ```bash
   grep -rn "PromptScope\." lia-agent-system/app/domains/ --include="*.py" | grep -i "prompt\|system"
   ```

3. Registrar na tabela de inventário:

| # | Nome do Prompt | Scope | Arquivo Principal | Linhas | Agente Vinculado |
|---|---------------|-------|-------------------|--------|-----------------|
| P1 | (preencher) | (scope) | (caminho) | (N) | (agente) |

**Critério de completude:** Todos os scopes definidos em `scope_config.py` devem ter entrada correspondente.

**Referência cruzada:** RM-36 (Inventário de Agentes), CI-01 (System Prompts)

---

## DP-02: MAPEAMENTO DE STACK COMPLETO POR PROMPT

**Objetivo:** Para cada prompt identificado em DP-01, mapear TODAS as camadas do stack — do system prompt até o componente frontend, passando por agentes, serviços, tools, compliance, APIs e WebSocket.

**Procedimento por prompt:**

1. **Identificar o agente vinculado:**
   ```bash
   grep -rn "class.*Agent\|class.*Graph" lia-agent-system/app/domains/<dominio>/agents/ --include="*.py"
   ```

2. **Identificar o domínio:**
   ```bash
   grep -rn "class.*Domain" lia-agent-system/app/domains/<dominio>/ --include="*.py" | head -5
   ```

3. **Identificar system prompt e reasoning prompt:**
   ```bash
   grep -rn "SYSTEM_PROMPT\|REASONING_PROMPT" lia-agent-system/app/domains/<dominio>/ --include="*.py"
   ```

4. **Identificar tool registry e tools implementados:**
   ```bash
   grep -rn "ToolRegistry\|tool_registry\|register_tool" lia-agent-system/app/domains/<dominio>/ --include="*.py"
   ls lia-agent-system/app/domains/<dominio>/tools/
   ```

5. **Identificar serviços vinculados:**
   ```bash
   grep -rn "Service\|service" lia-agent-system/app/domains/<dominio>/services/ --include="*.py" | grep "class "
   ```

6. **Identificar compliance integrado:**
   ```bash
   grep -rn "fairness_guard\|FairnessGuard\|guardrail\|validate.*compliance" lia-agent-system/app/domains/<dominio>/ --include="*.py"
   ```

7. **Identificar frontend — páginas:**
   ```bash
   grep -rn "<dominio>\|<scope>" plataforma-lia/src/components/pages/ --include="*.tsx" -l
   ```

8. **Identificar frontend — hooks e context:**
   ```bash
   grep -rn "use.*<dominio>\|use.*<scope>" plataforma-lia/src/hooks/ --include="*.ts" -l
   grep -rn "<dominio>\|<scope>" plataforma-lia/src/contexts/ --include="*.tsx" -l
   ```

9. **Identificar frontend — componentes de chat/interação:**
   ```bash
   grep -rn "ChatPanel\|ChatContainer\|TransitionChat\|MessageBubble\|ChatInputBar" plataforma-lia/src/components/ --include="*.tsx" -l
   ```

10. **Identificar API proxies:**
    ```bash
    grep -rn "backend-proxy.*<dominio>\|backend-proxy.*<scope>" plataforma-lia/src/ --include="*.ts" --include="*.tsx"
    ```

11. **Identificar WebSocket:**
    ```bash
    grep -rn "ws://\|WebSocket\|ws.*chat\|ws.*session" lia-agent-system/app/ plataforma-lia/src/ --include="*.py" --include="*.ts" --include="*.tsx" | head -20
    ```

**Template de saída obrigatório por prompt:**

```markdown
### Stack Completo — [Nome do Prompt] (P[N])

| Camada | Componente | Arquivo |
|--------|-----------|---------|
| Agente | (classe) | (caminho) |
| Domínio | (classe) | (caminho) |
| System Prompt | (constante) | (caminho) |
| Reasoning Prompt | (constante ou N/A) | (caminho) |
| Tool Registry | (classe) | (caminho) |
| Tools | (N tools) | (caminho) |
| Serviço(s) | (classes) | (caminho) |
| Compliance | (tipo) | (caminho) |
| Frontend — Página | (componente) | (caminho) |
| Frontend — Chat | (componente) | (caminho) |
| Frontend — Hooks | (hooks) | (caminho) |
| Frontend — Context | (provider) | (caminho) |
| API Proxy | (rota) | (endpoint backend) |
| WebSocket | (URL pattern) | (descrição) |
```

**Critério de completude:** Cada prompt DEVE ter TODAS as 14 camadas preenchidas. Se uma camada não existe, registrar "AUSENTE" — isso é um achado.

**Referência cruzada:** CI-03 (Tool Registry), CI-06 (Serviços de Domínio)

---

## DP-03: INVENTÁRIO DE TOOLS POR SCOPE

**Objetivo:** Para cada prompt/scope, listar TODOS os tools disponíveis, classificados como Query ou Action, e verificar se estão realmente implementados.

**Procedimento:**

1. **Extrair tools do scope_config:**
   ```bash
   grep -A 100 "PromptScope\.<SCOPE>" lia-agent-system/app/tools/scope_config.py | head -120
   ```

2. **Classificar cada tool:**
   - **Query:** Tools que apenas lêem dados (get_*, search_*, list_*, compare_*)
   - **Action:** Tools que modificam estado (create_*, update_*, delete_*, send_*, move_*, reject_*, pause_*, publish_*, export_*)

3. **Verificar implementação real:**
   ```bash
   # Para cada tool listado no scope:
   grep -rn "def <nome_do_tool>" lia-agent-system/app/ --include="*.py"
   # Se não encontrar: é um stub/declaração sem implementação → ACHADO CRÍTICO
   ```

4. **Registrar na tabela:**

```markdown
### Tools no scope [SCOPE] ([N] query + [M] action = [T] tools)

**Query ([N]):** tool1, tool2, ...

**Action ([M]):** tool1, tool2, ...

| Tool | Tipo | Implementado? | Arquivo | Observações |
|------|------|--------------|---------|-------------|
| (nome) | Query/Action | SIM/NÃO/STUB | (caminho) | (notas) |
```

**Critérios de alerta:**
- Tool declarado no scope mas sem implementação → **PROBLEMA CRÍTICO**
- Tool com `pass` ou `return {}` no corpo → **STUB** (registrar)
- Tool referenciado no reasoning prompt mas não no scope do prompt → **INCONSISTÊNCIA**

**Referência cruzada:** RM-39 (Scope × Tool), CI-03 (Tool Registry)

---

## DP-04: ANÁLISE "O QUE FAZ" POR PROMPT

**Objetivo:** Documentar todas as capacidades realmente implementadas de cada prompt/assistente.

**Procedimento:**

1. **Ler o system prompt completo** e extrair todas as capacidades declaradas:
   ```bash
   cat lia-agent-system/app/domains/<dominio>/prompts/<arquivo>.py | head -200
   ```

2. **Para cada capacidade declarada, verificar se está implementada:**
   - Existe tool correspondente? (verificar no scope)
   - O tool tem implementação real? (não é stub)
   - O frontend suporta a saída do tool? (UI components existem)

3. **Categorizar capacidades encontradas:**
   - Tipos de análise suportados (ranking, comparação, gargalos, etc.)
   - Método de detecção de intent (keywords, LLM, cascade)
   - Construção de contexto (como monta o prompt dinâmico)
   - Resolução de ações UI (como mapeia intents para ações no frontend)
   - Tools ativos por tipo (query vs action)
   - Mecanismos especiais (HITL, anti-sycophancy, memória, etc.)

**Template de saída:**

```markdown
### O que faz — [Nome do Prompt] (P[N])

[Descrição em 1-2 linhas do papel do assistente]

**Capacidades implementadas:**
- [N] tipos de [análise/comando]: (listar)
- Detecção de intent: [método] (keywords + LLM fallback / ReAct LLM direto / CascadedRouter N-tier)
- Construção de contexto: [como monta] (dados injetados, variáveis, etc.)
- Resolução de ações UI: [método] (resolve_ui_action / resolve_jobs_ui_action / etc.)
- [N] tools de query: (listar)
- [N] tools de action: (listar)
- [Mecanismos especiais]: HITL, anti-sycophancy, memória, confirmação dupla, etc.
```

**Referência cruzada:** CI-01 (System Prompts), CI-02 (Intent Detection)

---

## DP-05: ANÁLISE "O QUE NÃO FAZ" POR PROMPT

**Objetivo:** Identificar gaps — capacidades que o recrutador esperaria mas que NÃO estão implementadas.

**Procedimento:**

1. **Comparar com expectativas do domínio:**
   - Para prompt de Talent: espera-se ranking, comparação, diversidade, alertas, histórico
   - Para prompt de Jobs: espera-se KPIs, SLAs, tendências, alertas proativos, drill-down
   - Para prompt de Kanban: espera-se pipeline, movimentação, triagem, entrevistas, previsão
   - Para prompt Float: espera-se routing, cross-domain, proatividade, briefing
   - Para prompt Policy: espera-se configuração guiada, validação, versionamento, preview
   - Para prompt Wizard: espera-se criação guiada, importação, clone, preview, compliance

2. **Verificar capacidades ausentes comuns:**
   - Sem dados reais de tempo / séries temporais
   - Sem alertas proativos (push notifications)
   - Sem drill-down entre contextos
   - Sem previsão / forecasting
   - Sem importação de documentos (upload)
   - Sem clone / duplicação
   - Sem colaboração multi-usuário
   - Sem preview visual
   - Sem versionamento / histórico de mudanças
   - Sem exportação em formato compartilhável

3. **Verificar tools declarados mas não usados:**
   ```bash
   # Comparar tools no reasoning prompt vs tools no scope
   grep -n "tool\|function\|action" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py | grep -v "^#"
   ```

**Template de saída:**

```markdown
### O que NÃO faz — [Nome do Prompt] (P[N])

- Sem [capacidade ausente]: [descrição do impacto]
- ...
```

**Referência cruzada:** DP-04 (O que faz), DP-08 (Mapa Comparativo)

---

## DP-06: PROBLEMAS IDENTIFICADOS POR PROMPT

**Objetivo:** Documentar bugs, inconsistências, riscos e problemas técnicos específicos de cada prompt.

**Procedimento:**

1. **Verificar detecção de intent:**
   ```bash
   grep -n "def.*detect\|def.*classify\|def.*match\|substring\|\.lower()\|\.find(" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
   ```
   - Usa substring match sem negação? → PROBLEMA
   - Confiança artificial (fórmula `max(0.6, min(...)`)? → PROBLEMA
   - Sem fallback se nenhum intent é detectado? → PROBLEMA

2. **Verificar name matching:**
   ```bash
   grep -n "target_name\|candidate_name\|name.*in\|fuzzy\|match" lia-agent-system/app/domains/<dominio>/ --include="*.py" -r
   ```
   - Match por substring simples (`name in other_name`)? → PROBLEMA (false positives)

3. **Verificar duplicação de instruções:**
   ```bash
   grep -c "CONFIRMAÇÕES\|TRANSIÇÕES\|FILOSOFIA\|TRATAMENTO DE ERRO" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
   ```
   - Seções duplicadas dentro do mesmo prompt? → PROBLEMA

4. **Verificar tamanho do prompt:**
   ```bash
   wc -l lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
   # Se > 500 linhas: prompt potencialmente muito grande → registrar tamanho em tokens estimados (chars/4)
   ```

5. **Verificar tools referenciados mas não disponíveis:**
   ```bash
   # Extrair tools mencionados no prompt
   grep -oP "(?:get_|search_|create_|update_|delete_|send_|validate_|check_|predict_|export_|generate_)\w+" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py | sort -u
   # Comparar com tools realmente no scope
   ```

6. **Verificar validação de transições/stages:**
   ```bash
   grep -n "stage\|transition\|advance\|next_step" lia-agent-system/app/domains/<dominio>/ --include="*.py" -r | head -20
   ```

**Template de saída:**

```markdown
### Problemas identificados — [Nome do Prompt] (P[N])

1. **[Título do problema]:** [Descrição] — arquivo: `path/file.py`
2. ...
```

**Severidade de problemas:**
- **CRÍTICO:** Viola Inegociáveis WeDO ou pode causar decisões discriminatórias
- **ALTO:** Afeta qualidade da experiência ou produz resultados incorretos
- **MÉDIO:** Degradação de performance ou manutenibilidade
- **BAIXO:** Melhoria desejável mas não urgente

**Referência cruzada:** RM-08 (Anti-sycophancy), RM-17 (Negation Detection), CI-02 (Intent Detection)

---

## DP-07: OPORTUNIDADES DE MELHORIA POR PROMPT

**Objetivo:** Identificar melhorias concretas e viáveis para cada prompt/assistente.

**Procedimento:**

1. **Para cada gap identificado em DP-05**, avaliar viabilidade:
   - Existe infraestrutura de suporte? (backend existe, falta frontend?)
   - Existe tool implementado mas não conectado ao scope?
   - Qual o esforço estimado? (Baixo / Médio / Alto)

2. **Verificar tools existentes mas não utilizados pelo prompt:**
   ```bash
   # Tools que existem em outros scopes mas não neste:
   grep -rn "def " lia-agent-system/app/tools/ --include="*.py" | grep -v "__" | grep -v "test"
   # Comparar com o scope do prompt atual
   ```

3. **Verificar capacidades em outros prompts que poderiam ser replicadas:**
   - Smart alerts existe no Kanban mas não no Talent/Jobs? → Oportunidade
   - Anti-sycophancy existe no Policy/Wizard mas não nos outros? → Oportunidade
   - Memória de sessão existe no Float mas não nos outros? → Oportunidade

**Template de saída:**

```markdown
### Oportunidades — [Nome do Prompt] (P[N])

- [Oportunidade]: [Descrição do benefício]
- ...
```

**Referência cruzada:** DP-05 (O que NÃO faz), DP-08 (Mapa Comparativo)

---

## DP-08: MAPA COMPARATIVO DE CAPACIDADES

**Objetivo:** Gerar tabela cruzada Capacidade × Prompt mostrando o que cada prompt pode fazer hoje, identificando assimetrias e padronizações necessárias.

**Procedimento:**

1. Consolidar resultados de DP-04 e DP-05 para todos os prompts.

2. Preencher a matriz usando os valores:
   - **SIM** — Capacidade implementada e funcional
   - **PARCIAL** — Existe mas incompleta ou com limitações
   - **DECLARADO** — Mencionado no prompt/reasoning mas não implementado de fato
   - **via routing** — Disponível apenas via roteamento do Float/Orchestrator
   - **N/A** — Não se aplica ao domínio do prompt
   - **—** (traço) — Ausente

3. **Categorias obrigatórias da matriz:**

```markdown
### Mapa de Capacidades Atual

| Capacidade | P1 Talent | P2 Jobs | P3 Kanban | P4 Float | P5 Policy | P6 Wizard |
|------------|----------|---------|-----------|----------|-----------|-----------|
| **ANÁLISE** | | | | | | |
| Ranking/scoring de candidatos | | | | | | |
| Comparação lado-a-lado | | | | | | |
| Análise de perfil/resumo | | | | | | |
| KPIs e métricas | | | | | | |
| Skills gap analysis | | | | | | |
| Análise de diversidade | | | | | | |
| Market insights (salário, mercado) | | | | | | |
| Gargalos e bottlenecks | | | | | | |
| SLA monitoring | | | | | | |
| Performance por departamento | | | | | | |
| **PREDITIVO** | | | | | | |
| Predict dropout risk | | | | | | |
| Pipeline forecast | | | | | | |
| ML predictions | | | | | | |
| Conversion patterns | | | | | | |
| Smart alerts | | | | | | |
| At-risk candidates (EWS) | | | | | | |
| **AÇÕES** | | | | | | |
| Mover candidato | | | | | | |
| Batch move | | | | | | |
| Rejeitar candidato | | | | | | |
| Shortlist | | | | | | |
| Enviar email | | | | | | |
| Enviar WhatsApp | | | | | | |
| Disparar triagem WSI | | | | | | |
| Agendar entrevista | | | | | | |
| Criar/editar vaga | | | | | | |
| Pausar/fechar vaga | | | | | | |
| Salvar política | | | | | | |
| Salvar draft de vaga | | | | | | |
| **PROATIVO** | | | | | | |
| Daily briefing | | | | | | |
| Pending actions/backlog | | | | | | |
| Sugestões proativas | | | | | | |
| Alertas de SLA | | | | | | |
| **RELATÓRIOS** | | | | | | |
| Gerar relatório | | | | | | |
| Exportar dados | | | | | | |
| **CHAT/CONVERSA** | | | | | | |
| Histórico de conversas | | | | | | |
| Novo chat | | | | | | |
| Limpar chat | | | | | | |
| Memória entre turnos | | | | | | |
| Anti-sycophancy | | | | | | |
| Negation detection | | | | | | |
```

4. **Análise da matriz — perguntas a responder:**
   - Quais capacidades deveriam ser padrão em TODOS os prompts mas não são?
   - Quais capacidades são DECLARADAS mas não IMPLEMENTADAS?
   - Qual prompt tem mais gaps em relação aos outros?
   - Há assimetria injustificada? (ex: smart alerts só no Kanban quando seria útil em todos)

**Referência cruzada:** DP-04 (O que faz), DP-05 (O que NÃO faz), DP-10 (Padronização)

---

## DP-09: MATRIZES TRANSVERSAIS MULTI-DIMENSIONAIS

**Objetivo:** Gerar tabelas cruzadas que avaliam cada prompt em dimensões de governança, compliance, resiliência e qualidade LLM — permitindo identificar problemas sistêmicos.

### DP-09.1: Matriz Anti-Sycophancy × Prompt

```bash
# Para cada prompt, verificar:
grep -n "sycophancy\|contra.argum\|pushback\|empurrar.*de volta\|não concorde" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
grep -n "benchmark\|dados.*reais\|evidência\|sustent" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
```

| Prompt | Anti-Sycophancy | Contra-Argumentação | Benchmarks Setoriais |
|--------|----------------|---------------------|---------------------|
| P1 | PRESENTE/AUSENTE | PRESENTE/AUSENTE | PRESENTE/AUSENTE |
| ... | | | |

**Critério:** Crença #11 do Manifesto WeDO — anti-sycophancy deve ser PRESENTE em 100% dos prompts.

### DP-09.2: Matriz Detecção de Intent × Prompt

```bash
# Para cada prompt, verificar método:
grep -n "keyword\|detect_intent\|classify\|substring\|\.find(\|best_score\|confidence" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
# Verificar negation:
grep -n "negat\|não.*quero\|don't\|negate" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
# Verificar confiança artificial:
grep -n "max(0\.6\|min(.*0\.95\|artificial\|floor\|cap" lia-agent-system/app/domains/<dominio>/prompts/<prompt>.py
```

| Prompt | Método | Negation Detection | Confiança Real |
|--------|--------|-------------------|----------------|
| P1 | Keywords+LLM / ReAct / Cascade | PRESENTE/AUSENTE/N/A | OK/ARTIFICIAL |
| ... | | | |

**Critério:** Nenhum prompt deve usar fórmula de confiança artificial. Todos que usam keywords devem implementar negation detection.

### DP-09.3: Matriz FairnessGuard × Prompt

```bash
# Para cada agente do prompt:
grep -n "fairness_guard\|FairnessGuard\|check_bias\|validate.*fairness" lia-agent-system/app/domains/<dominio>/agents/<agente>.py
grep -n "fairness\|guardrail\|bias" lia-agent-system/app/domains/<dominio>/tools/ --include="*.py" -r
```

| Prompt/Agente | FairnessGuard no Input | FairnessGuard nas Tools | Status |
|---------------|----------------------|------------------------|--------|
| (agente) | SIM/NÃO | SIM/NÃO/PARCIAL | OK/FALHA/PARCIAL |
| ... | | | |

**Critério:** Inegociável #3 — FairnessGuard deve estar ativo em 100% das decisões. Verificar se é middleware automático ou chamada manual.

**Verificação adicional:**
```bash
# FairnessGuard como middleware (ideal):
grep -n "fairness\|FairnessGuard" lia-agent-system/libs/agents-core/lia_agents_core/react_loop.py
grep -n "fairness\|FairnessGuard" lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py
# Se NÃO estiver nesses arquivos → cada agente precisa chamar manualmente → RISCO
```

### DP-09.4: Matriz HITL × Prompt

```bash
# Para cada agente:
grep -n "HITL\|human.in.the.loop\|approval\|confirm\|guardrail_tools\|GUARDRAIL_TOOLS" lia-agent-system/app/domains/<dominio>/agents/<agente>.py
```

| Prompt/Agente | HITL Enforced | Ações Cobertas | Status |
|---------------|--------------|----------------|--------|
| (agente) | SIM/NÃO/PARCIAL/N/A | (lista de ações) | OK/ATENÇÃO/N/A |
| ... | | | |

**Critério:** Inegociável #7 — Human override sempre disponível. Todas as ações destrutivas devem exigir HITL.

### DP-09.5: Matriz Circuit Breaker × Componente

```bash
grep -rn "circuit_breaker\|CircuitBreaker\|breaker" lia-agent-system/app/ --include="*.py" | grep -v test | grep -v __pycache__
```

| Componente | Circuit Breaker | Fallback | Status |
|-----------|----------------|----------|--------|
| LLM Calls (agentes) | SIM/NÃO | (tipo) | OK/ATENÇÃO |
| LLM Factory | SIM/NÃO | Claude→Gemini→OpenAI | OK |
| Pearch AI | SIM/NÃO | (tipo) | OK |
| WorkOS | SIM/NÃO | (tipo) | OK |
| Tool Calls (LangGraph) | SIM/NÃO | (tipo) | OK |
| ... | | | |

### DP-09.6: Matriz Token Budget

```bash
grep -rn "token.*track\|TokenTracking\|check_limits\|record_usage\|budget\|AiCreditsBalance" lia-agent-system/app/ --include="*.py" | head -30
```

| Verificação | Status | Detalhes |
|------------|--------|---------|
| TokenTrackingService existe | OK/FALHA | |
| Pre-call budget check | OK/FALHA | check_limits() chamado ANTES de cada LLM call? |
| In-loop heuristic | OK/FALHA | chars/4 estimate com cap |
| Post-call recording | OK/FALHA | record_usage() chamado ao final |
| Budget por empresa | OK/FALHA | AiCreditsBalance wallet |

### DP-09.7: Matriz PII Masking

```bash
grep -rn "pii_masking\|PIIMasking\|install_global_pii\|strip_pii\|masked_logger" lia-agent-system/app/ --include="*.py" | head -20
```

| Verificação | Status | Detalhes |
|------------|--------|---------|
| install_global_pii_masking() ativo | OK/FALHA | Em main.py e apps |
| PIIMaskingFilter no root logger | OK/FALHA | Mascara CPF, email, telefone |
| get_masked_logger disponível | OK/FALHA | Camada extra |
| strip_pii_for_llm_prompt | OK/FALHA | Sanitiza antes de enviar ao LLM |
| Secrets fora do código | OK/FALHA | Via environment variables |

### DP-09.8: Matriz Consent Management

```bash
grep -rn "consent\|ConsentChecker\|consent_checker" lia-agent-system/app/ --include="*.py" | head -20
```

| Verificação | Status | Detalhes |
|------------|--------|---------|
| ConsentCheckerService existe | OK/FALHA | |
| Consent check no WSI screening | OK/FALHA | Gate em wsi_interview_graph |
| Consent check em rubric evaluation | OK/FALHA | |
| Consent check em candidates API | OK/FALHA | |
| Soft vs Hard enforcement | ATENÇÃO/OK | Soft = loga warning mas continua |
| Hard block se revogado | OK/FALHA | Bloqueia processamento |

### DP-09.9: Matriz Multi-Tenant

```bash
grep -rn "company_id\|tenant\|cross_tenant\|ToolExecutionContext" lia-agent-system/app/ --include="*.py" | head -20
```

| Verificação | Status | Detalhes |
|------------|--------|---------|
| company_id em todas as queries | OK/FALHA | WHERE company_id = ? |
| Cross-tenant prevention | OK/FALHA | cross_tenant_access_denied |
| Scope-based tool access | OK/FALHA | PromptScope limita tools |
| Tenant isolation em tool calls | OK/FALHA | ToolExecutionContext |

### DP-09.10: Matriz Audit Trail

```bash
grep -rn "AuditCallback\|audit_service\|audit_writer\|ExecutionLogStore\|agent_execution_records" lia-agent-system/app/ lia-agent-system/libs/ --include="*.py" | head -20
```

| Verificação | Status | Detalhes |
|------------|--------|---------|
| AuditCallback (LangChain/LangGraph) | OK/FALHA | Captura LLM calls, tool calls |
| Dual-Persistence (PostgreSQL + S3) | OK/FALHA | Metadata + payload |
| ReActObserver | OK/FALHA | Structured logging |
| ExecutionLogStore | OK/FALHA | agent_execution_records |
| TokenTrackingService | OK/FALHA | ai_consumption table |
| LangSmith tracing | OK/FALHA | @traceable |
| Structured logging (sem print) | OK/FALHA | Logger com PIIMasking |

### DP-09.11: Matriz Consolidada (Checklist Multi-Dimensional × Prompt)

Após preencher DP-09.1 a DP-09.10, consolidar em uma única tabela:

| Dimensão | P1 Talent | P2 Jobs | P3 Kanban | P4 Float | P5 Policy | P6 Wizard |
|----------|----------|---------|-----------|----------|-----------|-----------|
| Anti-Sycophancy | | | | | | |
| FairnessGuard Input | | | | | | |
| FairnessGuard Tools | | | | | | |
| HITL Enforcement | | | | | | |
| Negation Detection | | | | | | |
| Confiança Real | | | | | | |
| Circuit Breaker Direto | | | | | | |
| Pre-call Budget Check | | | | | | |
| PII Masking | | | | | | |
| Consent Check | | | | | | |
| Multi-Tenant Isolation | | | | | | |
| Audit Trail | | | | | | |
| Observabilidade | | | | | | |
| Token Tracking | | | | | | |

**Valores possíveis:** OK, FALHA, PARCIAL, ATENÇÃO, N/A

**Critério de avaliação:**
- Linha toda OK → Dimensão saudável
- Qualquer FALHA em Inegociável → **P0 CRÍTICO**
- Mais de 50% FALHA em uma dimensão → **Problema sistêmico**
- Prompt com mais de 3 FALHA → **Prompt em risco**

**Referência cruzada:** RM-02 (FairnessGuard), RM-03 (HITL), RM-08 (Anti-sycophancy), RM-09 (Score Normalization), RM-10 (Circuit Breaker), RM-17 (Negation Detection)

---

## DP-10: DIAGNÓSTICO DE PADRONIZAÇÃO — O QUE DEVERIA SER PADRÃO

**Objetivo:** Com base nas matrizes DP-08 e DP-09, definir 3 níveis de padronização que todo prompt deveria atingir.

**Procedimento:**

1. **Analisar a matriz DP-09.11** — identificar dimensões que são OK em alguns prompts mas FALHA em outros.

2. **Definir Nível 1 — Padrão para TODOS os prompts (sem exceção):**

| Capacidade | Justificativa | Status Atual (quantos dos N prompts) |
|------------|--------------|-------------------------------------|
| Anti-sycophancy | Crença #11 do Manifesto | X/N |
| FairnessGuard no input | Inegociável #3 | X/N como middleware |
| Negation detection | Qualidade básica de intent | X/N que usam keywords |
| Confiança real | Decisões baseadas em dados reais | X/N usam fórmula artificial |

3. **Definir Nível 2 — Padrão para prompts operacionais (exceto Policy):**

| Capacidade | Justificativa | Status Atual |
|------------|--------------|-------------|
| Gerar relatórios | Todos os contextos operacionais | Apenas N/M prompts |
| Histórico de conversas | Retomar análises anteriores | Backend existe, UI incompleta |
| Novo chat / Limpar chat | Separar contextos | API existe, UI não expõe |
| Capacidade preditiva | Dropout, forecast, patterns | Apenas N prompts usam ativamente |
| Smart alerts | Alertas de SLA, at-risk | Apenas N prompts |
| Pendências ("O que preciso fazer?") | Produtividade do recrutador | Apenas Float parcial |
| Sugestões proativas | Proatividade da LIA | Apenas Float e Wizard |

4. **Definir Nível 3 — Específico por tipo de prompt:**
   - Prompts configuracionais (Policy): O que faz sentido e o que não faz
   - Prompts conversacionais (Float): Requisitos específicos de routing
   - Prompts de workflow (Wizard): Requisitos específicos de stages

**Template de saída:**

```markdown
### Diagnóstico de Padronização

**NÍVEL 1 — Padrão para TODOS os N prompts:**
| Capacidade | Justificativa | Hoje | Meta |
|...

**NÍVEL 2 — Padrão para prompts operacionais:**
| Capacidade | Justificativa | Hoje | Meta |
|...

**NÍVEL 3 — Específico:**
| Prompt | Requisito Específico | Justificativa |
|...
```

**Referência cruzada:** DP-08 (Mapa Comparativo), DP-09.11 (Matriz Consolidada)

---

## DP-11: ANÁLISE DE TOOLS PREDITIVOS — SUBUTILIZAÇÃO

**Objetivo:** Identificar tools preditivos que EXISTEM na codebase mas são SUBUTILIZADOS pelos prompts.

**Procedimento:**

1. **Inventariar tools preditivos existentes:**
   ```bash
   grep -rn "def predict_\|def get_.*forecast\|def get_ml_\|def get_conversion_\|def get_smart_alert\|def get_at_risk\|def get_pending_action" lia-agent-system/app/ --include="*.py"
   ```

2. **Para cada tool preditivo, verificar em quais scopes está ativo:**
   ```bash
   grep -n "<nome_do_tool>" lia-agent-system/app/tools/scope_config.py
   ```

3. **Preencher a tabela de subutilização:**

| Tool | Existe em | Usado ativamente por | Deveria ser usado por |
|------|-----------|---------------------|----------------------|
| predict_dropout_risk | (arquivo) | (prompts) | (prompts ideais) |
| get_pipeline_forecast | (arquivo) | (prompts) | (prompts ideais) |
| get_ml_predictions | (arquivo) | (prompts) | (prompts ideais) |
| get_conversion_patterns | (arquivo) | (prompts) | (prompts ideais) |
| get_smart_alerts | (arquivo) | (prompts) | (prompts ideais) |
| get_at_risk_candidates | (arquivo) | (prompts) | (prompts ideais) |
| get_pending_actions | (arquivo) | (prompts) | (prompts ideais) |

4. **Proposta de ativação por prompt:**

| Prompt | Tools Preditivos a Ativar | Impacto Esperado |
|--------|--------------------------|-----------------|
| P1 Talent | (lista) | (benefício) |
| P2 Jobs | (lista) | (benefício) |
| ... | | |

**Referência cruzada:** DP-03 (Inventário de Tools), DP-08 (Mapa Comparativo), CI-03 (Tool Registry)

---

## DP-12: CADA PROMPT COMO "ASSISTENTE COMPLETO" — CHECKLIST

**Objetivo:** Verificar se cada prompt operacional (exceto Policy) funciona como assistente completo, com capacidades padronizadas que o recrutador espera.

**Capacidades obrigatórias para assistente completo:**

| Capacidade Padrão | Descrição | Implementação Esperada |
|-------------------|-----------|----------------------|
| "O que preciso fazer?" | Lista pendências e ações prioritárias | get_pending_actions + priorização |
| "Me dê um resumo" | Briefing do estado atual | Template de resumo por prompt |
| "Gera um relatório" | Relatório completo do domínio | Tool generate_report + formatação |
| "O que está em risco?" | Alertas preditivos | get_smart_alerts + predict_dropout_risk |
| "Sugira próximos passos" | Recomendações proativas | Proactive suggestions engine |
| "Compare X com Y" | Comparação lado-a-lado | Templates de comparação |
| Histórico de chats | Listar, retomar, criar novo, limpar | ConversationMemory + UI |
| Anti-sycophancy | Contra-argumentar com dados | Seção padrão no prompt |
| Negation detection | "NÃO quero ranking" = não executar | Implementar em todos |

**Procedimento:**

Para cada prompt operacional, verificar se CADA capacidade acima está implementada:

```bash
# Para cada capacidade:
grep -rn "<capacidade_keyword>" lia-agent-system/app/domains/<dominio>/ --include="*.py"
grep -rn "<capacidade_keyword>" plataforma-lia/src/components/ --include="*.tsx"
```

**Template de saída por prompt:**

| Capacidade Padrão | P1 Talent | P2 Jobs | P3 Kanban | P4 Float | P6 Wizard |
|-------------------|----------|---------|-----------|----------|-----------|
| "O que preciso fazer?" | SIM/NÃO | | | | |
| "Me dê um resumo" | SIM/NÃO | | | | |
| "Gera um relatório" | SIM/NÃO | | | | |
| ... | | | | | |

**Referência cruzada:** DP-08 (Mapa Comparativo), DP-10 (Padronização)

---

## DP-13: HISTÓRICO DE CHATS — AUDITORIA DE IMPLEMENTAÇÃO

**Objetivo:** Verificar o estado de implementação de histórico de conversas no backend e frontend, e mapear onde faz sentido ativar.

**Procedimento:**

1. **Verificar backend de conversas:**
   ```bash
   grep -rn "conversations\|ConversationMemory\|conversation_memory" lia-agent-system/app/ --include="*.py" | head -20
   # Verificar endpoints:
   grep -rn "GET.*conversations\|POST.*conversations\|DELETE.*conversations\|clear\|archive" lia-agent-system/app/api/ --include="*.py"
   ```

2. **Verificar frontend de histórico:**
   ```bash
   grep -rn "conversation\|historico\|history\|chat.*list\|sidebar" plataforma-lia/src/components/ --include="*.tsx" | head -20
   grep -rn "novo.*chat\|new.*chat\|clear.*chat\|limpar" plataforma-lia/src/components/ --include="*.tsx" | head -20
   ```

3. **Preencher tabela de estado:**

| Prompt | Histórico Backend | Histórico UI | Novo Chat | Limpar Chat | Status |
|--------|------------------|-------------|-----------|-------------|--------|
| P1 Talent | SIM/NÃO | SIM/NÃO | SIM/NÃO | SIM/NÃO | |
| P2 Jobs | | | | | |
| P3 Kanban | | | | | |
| P4 Float | | | | | |
| P5 Policy | | | | | |
| P6 Wizard | | | | | |

4. **Recomendação por prompt:**

| Prompt | Histórico | Novo Chat | Limpar | Justificativa |
|--------|-----------|-----------|--------|---------------|
| P1 Talent | SIM | SIM | SIM | Análises em dias diferentes |
| P2 Jobs | SIM | SIM | SIM | Análises macro recorrentes |
| P3 Kanban | SIM (por vaga) | SIM | SIM | Interações por vaga |
| P4 Float | SIM | SIM | SIM | Central — já tem backend |
| P5 Policy | NÃO | NÃO | NÃO | Setup linear |
| P6 Wizard | POR VAGA | NÃO | NÃO | Vinculado à vaga |

**Referência cruzada:** DP-12 (Assistente Completo), CI-09 (Conversation Memory)

---

## DP-14: GERAÇÃO DE RELATÓRIOS — AUDITORIA DE PADRONIZAÇÃO

**Objetivo:** Mapear capacidade de geração de relatórios por prompt e propor padronização.

**Procedimento:**

1. **Verificar tools de relatório existentes:**
   ```bash
   grep -rn "generate_report\|export.*analytics\|export.*candidates\|report" lia-agent-system/app/tools/ --include="*.py" | head -20
   ```

2. **Verificar quais prompts têm capacidade de relatório:**
   ```bash
   grep -rn "relatório\|report\|gerar.*relat\|generate.*report" lia-agent-system/app/domains/*/prompts/ --include="*.py"
   ```

3. **Preencher tabela de relatórios por prompt:**

| Prompt | Tipo de Relatório Esperado | Formato | Status Atual |
|--------|---------------------------|---------|-------------|
| P1 Talent | Pool (distribuição, scores, gaps, diversidade) | Markdown + dados | SIM/NÃO |
| P2 Jobs | Portfolio (KPIs, SLAs, performance, tendências) | Markdown + tabelas | SIM/NÃO |
| P3 Kanban | Vaga (funil, velocidade, gargalos, previsão) | Markdown + métricas | SIM/NÃO |
| P4 Float | Consolidado (briefing executivo, cross-domain) | Markdown + resumo | SIM/NÃO |
| P5 Policy | Compliance (políticas, gaps, status) | Markdown + checklist | SIM/NÃO |
| P6 Wizard | Pré-publicação (completude, riscos, market fit) | Markdown + score | SIM/NÃO |

**Referência cruzada:** DP-12 (Assistente Completo)

---

## DP-15: PRIORIZAÇÃO DE CORREÇÕES (P0-P3)

**Objetivo:** Consolidar todos os problemas identificados em DP-06, DP-09 e DP-10 e priorizá-los por impacto.

**Procedimento:**

1. **Coletar todos os problemas de DP-06 (por prompt) e DP-09 (transversais).**

2. **Classificar por prioridade:**

| Prioridade | Critério | Exemplos |
|-----------|---------|---------|
| **P0 — Crítico** | Viola Inegociáveis WeDO ou pode causar decisões discriminatórias | FairnessGuard ausente, anti-sycophancy ausente |
| **P1 — Alto** | Afeta qualidade, resiliência ou pode produzir resultados incorretos | HITL incompleto, confiança artificial, consent soft |
| **P2 — Médio** | Degradação de performance, manutenibilidade ou arquitetura | Circuit breaker, scope manual, duplicação |
| **P3 — Baixo** | Melhoria desejável, feature futura | Upload JD, simulação, templates |

3. **Template de saída:**

```markdown
### Prioridades de Correção

**P0 — Crítico (Violação de Inegociáveis):**
1. [Descrição] — Arquivo(s): `path/file.py`
2. ...

**P1 — Alto (Qualidade e Resiliência):**
1. [Descrição] — Arquivo(s): `path/file.py`
2. ...

**P2 — Médio (Melhorias de Arquitetura):**
1. [Descrição] — Arquivo(s): `path/file.py`
2. ...

**P3 — Baixo (Futuro):**
1. [Descrição]
2. ...
```

**Referência cruzada:** RM-01 a RM-44 (todos os runbooks de auditoria)

---

## DP-16: ARQUIVOS-CHAVE PARA CORREÇÕES

**Objetivo:** Para cada problema priorizado em DP-15, mapear exatamente quais arquivos precisam ser modificados.

**Template obrigatório:**

```markdown
### Arquivos-Chave para Correções

| Correção | Arquivo Principal |
|----------|------------------|
| (descrição da correção) | (caminho completo do arquivo) |
| ... | ... |

### Índice de Arquivos Relevantes

**Backend — Prompts:**
- (listar todos os arquivos de prompt)

**Backend — Agentes:**
- (listar todos os arquivos de agente)

**Backend — Orquestração:**
- (listar todos os arquivos de orquestração)

**Backend — Tools e Scope:**
- (listar arquivos de tools e scope_config)

**Backend — Serviços:**
- (listar serviços relevantes)

**Backend — Compliance:**
- (listar arquivos de compliance)

**Frontend — Componentes:**
- (listar componentes relevantes)

**Frontend — Hooks e Context:**
- (listar hooks e contexts)

**Backend — Resiliência e Governança:**
- (listar arquivos de resiliência, audit, observability)
```

**Referência cruzada:** DP-15 (Priorização), PARTE VI (Arquitetura Técnica)

---

## DP-17: TEMPLATE COMPLETO DE DIAGNÓSTICO POR PROMPT

**Objetivo:** Fornecer o template final que o auditor deve preencher para CADA prompt, consolidando DP-02 a DP-07.

**Template — copiar e preencher para cada prompt:**

```markdown
## [N]. PROMPT [NOME] ([Scope])

**Arquivo principal:** `lia-agent-system/app/domains/<dominio>/prompts/<arquivo>.py` ([N] linhas)
**Scope:** PromptScope.[SCOPE]

### Stack completo vinculado

| Camada | Componente | Arquivo |
|--------|-----------|---------|
| Agente | | |
| Domínio | | |
| System Prompt | | |
| Reasoning Prompt | | |
| Tool Registry | | |
| Tools | | |
| Serviço(s) | | |
| Compliance | | |
| Frontend — Página | | |
| Frontend — Chat | | |
| Frontend — Hooks | | |
| Frontend — Context | | |
| API Proxy | | |
| WebSocket | | |

### Tools no scope [SCOPE] ([N] query + [M] action = [T] tools)

**Query ([N]):** (listar)

**Action ([M]):** (listar)

### O que faz

[Descrição em 1-2 linhas]

**Capacidades implementadas:**
- (listar com bullets)

### O que NÃO faz

- (listar gaps com impacto)

### Problemas identificados

1. **[Título]:** [Descrição] — `arquivo:linha`
2. ...

### Oportunidades

- (listar com benefício esperado)
```

**Referência cruzada:** DP-02 a DP-07

---

## DP-18: TEMPLATE COMPLETO DE ANÁLISE TRANSVERSAL

**Objetivo:** Fornecer o template final para a análise transversal, consolidando DP-08 a DP-16.

**Template — preencher após todos os diagnósticos individuais:**

```markdown
## ANÁLISE TRANSVERSAL DA ARQUITETURA

### Pontos Fortes da Arquitetura
- (listar com evidências)

### Problemas Sistêmicos
- (listar problemas que afetam múltiplos prompts)

### Checklist Multi-Dimensional (DP-09.11)
(inserir tabela consolidada)

### Mapa Comparativo de Capacidades (DP-08)
(inserir tabela completa)

### Diagnóstico de Padronização (DP-10)
**NÍVEL 1:** (o que deve ser padrão em TODOS)
**NÍVEL 2:** (o que deve ser padrão nos operacionais)
**NÍVEL 3:** (específico por tipo)

### Tools Preditivos — Subutilização (DP-11)
(inserir tabela)

### Cada Prompt como Assistente Completo (DP-12)
(inserir tabela)

### Prioridades de Correção (DP-15)
**P0:** (listar)
**P1:** (listar)
**P2:** (listar)
**P3:** (listar)

### Arquivos-Chave (DP-16)
(inserir tabela + índice)
```

---

## DP-19: FLUXO DE EXECUÇÃO COMPLETO

**Objetivo:** Definir a ordem de execução dos procedimentos DP-01 a DP-18 para gerar o diagnóstico completo.

### Fase 1 — Inventário (DP-01 a DP-03)
1. **DP-01:** Inventário de prompts/assistentes
2. **DP-02:** Stack completo por prompt (para cada prompt de DP-01)
3. **DP-03:** Inventário de tools por scope (para cada scope de DP-01)

### Fase 2 — Análise Individual (DP-04 a DP-07)
Para CADA prompt identificado em DP-01:
4. **DP-04:** O que faz
5. **DP-05:** O que NÃO faz
6. **DP-06:** Problemas identificados
7. **DP-07:** Oportunidades

### Fase 3 — Análise Transversal (DP-08 a DP-11)
8. **DP-08:** Mapa comparativo de capacidades
9. **DP-09:** Matrizes transversais (09.1 a 09.11)
10. **DP-10:** Diagnóstico de padronização
11. **DP-11:** Tools preditivos — subutilização

### Fase 4 — Propostas e Priorização (DP-12 a DP-16)
12. **DP-12:** Cada prompt como assistente completo
13. **DP-13:** Histórico de chats
14. **DP-14:** Geração de relatórios
15. **DP-15:** Priorização P0-P3
16. **DP-16:** Arquivos-chave para correções

### Fase 5 — Consolidação (DP-17 e DP-18)
17. **DP-17:** Preencher template de diagnóstico individual para cada prompt
18. **DP-18:** Preencher template de análise transversal

### Estimativa de esforço:
- **Fase 1:** ~2h por prompt (inventário + stack + tools)
- **Fase 2:** ~1.5h por prompt (análise individual)
- **Fase 3:** ~3h total (consolidação transversal)
- **Fase 4:** ~2h total (propostas)
- **Fase 5:** ~1h total (templates finais)
- **Total estimado para 6 prompts:** ~20-25h de auditoria profunda

---

## DP-20: RUNBOOKS DE REFERÊNCIA CRUZADA

Os procedimentos DP-01 a DP-19 se apoiam nos seguintes runbooks existentes:

| Procedimento DP | Runbooks Relacionados | Relação |
|-----------------|----------------------|---------|
| DP-02 (Stack) | RM-36, RM-37, CI-01, CI-03, CI-06 | Mapeamento de agentes, prompts, tools, serviços |
| DP-03 (Tools) | RM-39, CI-03, CI-04 | Scope × Tool, Tool Registry |
| DP-04 (O que faz) | CI-01, CI-02 | System Prompts, Intent Detection |
| DP-06 (Problemas) | RM-08, RM-17, RM-09, RM-10 | Anti-sycophancy, Negation, Score, Circuit Breaker |
| DP-09.1 (Anti-Sycophancy) | RM-08 | Anti-sycophancy por prompt |
| DP-09.2 (Intent) | RM-17, CI-02 | Negation Detection, Intent |
| DP-09.3 (FairnessGuard) | RM-02 | FairnessGuard 3 camadas |
| DP-09.4 (HITL) | RM-03 | Human-in-the-Loop |
| DP-09.5 (Circuit Breaker) | RM-10 | Circuit Breaker |
| DP-09.6 (Token Budget) | RM-11 | Token Tracking |
| DP-09.7 (PII) | RM-06 | PII Masking |
| DP-09.8 (Consent) | RM-04 | Consent Management |
| DP-09.9 (Multi-Tenant) | RM-13 | Tenant Isolation |
| DP-09.10 (Audit) | RM-14, RM-15 | Audit Trail, Observability |
| DP-13 (Histórico) | CI-09 | Conversation Memory |
| DP-14 (Relatórios) | CI-15 | Geração de Relatórios |

---

# PARTE XII: NOTAS FINAIS

1. **Não assuma — investigue.** Sempre leia o código real antes de classificar um item. "Existe" e "funciona" são coisas diferentes.
2. **Priorize por impacto.** Violações de Inegociáveis são P0 — não importa quão pequenas pareçam.
3. **Documente evidências.** Cada achado deve ter: arquivo, linha (quando possível), e descrição do problema.
4. **Proponha correções concretas.** Não apenas "precisa melhorar" — diga O QUE FAZER.
5. **O relatório é o produto.** Siga o formato definido — consistência permite comparação entre auditorias.
6. **"Existir não é o mesmo que estar conectado. Compilar não é o mesmo que funcionar."** — a falha mais comum NÃO é código quebrado, é código que existe mas não foi conectado ao fluxo real.
7. **Regra dos 4/5 para fairness** — se qualquer grupo protegido tem taxa de seleção menor que 80% do grupo de referência, é uma falha que deve ser investigada.
8. **Toda fórmula de confiança deve usar dados reais** — fórmulas artificiais como `max(0.6, min(best_score * 3, 0.95))` mascaram a incerteza real e devem ser substituídas.
9. **Anti-sycophancy não é opcional** — um assistente de recrutamento que concorda com tudo que o recrutador pede pode produzir contratações ruins. A IA deve empurrar de volta quando necessário, com dados.
10. **FairnessGuard como middleware, não como chamada manual** — se depende de cada agente "lembrar" de chamar, haverá falhas. Deve ser automático e interceptar ANTES do processamento.