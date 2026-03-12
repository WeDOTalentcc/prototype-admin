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

# PARTE VIII: FORMATO DO RELATÓRIO

O relatório final deve seguir EXATAMENTE esta estrutura:

## SEÇÃO 1: MAPEAMENTO DA ARQUITETURA
- Tabela de componentes compartilhados
- Stack completo por prompt (uma tabela por prompt)
- Mapa de tools por scope

## SEÇÃO 2: ANÁLISE DETALHADA POR PROMPT
Para cada prompt:
- O que faz (capacidades implementadas)
- O que NÃO faz (gaps)
- Problemas identificados (com evidências: arquivo + linha)
- Oportunidades de melhoria

## SEÇÃO 3: AUDITORIA MULTI-DIMENSIONAL

Tabela resumo com todas as dimensões críticas:

| Verificação | Prompt 1 | Prompt 2 | ... | Prompt N |
|:---|:---:|:---:|:---:|:---:|
| Anti-Sycophancy | OK/FALHA | OK/FALHA | ... | OK/FALHA |
| FairnessGuard Middleware | OK/FALHA | ... | ... | ... |
| Negation Detection | OK/FALHA/N/A | ... | ... | ... |
| Confiança Real | OK/FALHA | ... | ... | ... |
| Circuit Breaker Direto | OK/FALHA | ... | ... | ... |
| Pre-call Budget Check | OK/FALHA | ... | ... | ... |
| PII Masking | OK/FALHA | ... | ... | ... |
| Consent Check | OK/FALHA/N/A | ... | ... | ... |
| Multi-Tenant Isolation | OK/FALHA | ... | ... | ... |
| Audit Trail | OK/FALHA | ... | ... | ... |
| Observabilidade | OK/FALHA | ... | ... | ... |
| Token Tracking | OK/FALHA | ... | ... | ... |
| HITL Enforcement | OK/FALHA/N/A | ... | ... | ... |

Depois, detalhamento por dimensão com evidências.

## SEÇÃO 4: ANÁLISE COMPARATIVA DE CAPACIDADES
- Mapa grande de capacidades (tabela Prompt x Capacidade)
- O que deveria ser padrão (3 níveis)
- Tools declarados vs usados vs oportunidades
- Propostas de histórico de chats, relatórios, capacidades preditivas

## SEÇÃO 5: PRIORIDADES DE CORREÇÃO

Classificar TODOS os achados em:

**P0 — Crítico (Violação de Inegociáveis):** Deve ser corrigido ANTES de qualquer deploy.
**P1 — Alto (Qualidade e Resiliência):** Deve ser corrigido no próximo sprint.
**P2 — Médio (Melhorias de Arquitetura):** Planejado para sprints futuros.
**P3 — Baixo (Futuro):** Backlog de melhorias.

Para cada item:
- Descrição do problema
- Arquivo(s) afetado(s)
- Correção proposta (concreta, não "precisa melhorar")
- Impacto se não corrigido

## SEÇÃO 6: ARQUIVOS-CHAVE PARA CORREÇÕES

Tabela com: Correção → Arquivo(s) principal(is) → Complexidade estimada

---

# PARTE IX: NOTAS FINAIS

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