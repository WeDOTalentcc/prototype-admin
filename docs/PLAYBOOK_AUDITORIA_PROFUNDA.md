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

## SEÇÃO 5: PRIORIDADES DE CORREÇÃO COM RUNBOOKS

Classificar TODOS os achados em:

**P0 — Crítico (Violação de Inegociáveis):** Deve ser corrigido ANTES de qualquer deploy.
**P1 — Alto (Qualidade e Resiliência):** Deve ser corrigido no próximo sprint.
**P2 — Médio (Melhorias de Arquitetura):** Planejado para sprints futuros.
**P3 — Baixo (Futuro):** Backlog de melhorias.

Para cada item, usar este template:

```
### [ID] — [Título do Achado]
- **Prioridade:** P0/P1/P2/P3
- **Dimensão:** [Dimensão 1-14 que identificou o problema]
- **Runbook:** [RM-XX] (ver Anexo M)
- **Arquivo(s) afetado(s):** [caminhos]
- **Descrição:** [o que está errado]
- **Impacto se não corrigido:** [consequência]
- **Esforço estimado:** [horas] — [Responsável: Backend/Frontend/Infra]
- **Depende de:** [outro achado, se houver]
```

O campo **Runbook** deve apontar para o item correspondente no Anexo M, onde o time encontrará instruções passo-a-passo para resolver o problema.

## SEÇÃO 6: RESUMO EXECUTIVO DE ESFORÇO

Tabela consolidada para planejamento de sprint:

| Prioridade | Qtd. Achados | Esforço Total (h) | Responsável Principal | Sprint Alvo |
|:----------:|:------------:|:-----------------:|:---------------------:|:-----------:|
| P0 | X | Xh | Backend | Imediato |
| P1 | X | Xh | Backend/Frontend | Sprint N+1 |
| P2 | X | Xh | Backend | Sprint N+2/N+3 |
| P3 | X | Xh | Backend/Frontend | Backlog |
| **Total** | **X** | **Xh** | — | — |

Depois, tabela detalhada: Runbook → Arquivo(s) principal(is) → Esforço (h) → Responsável → Depende de

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
| RM-28 | Outreach automatizado (gap competitivo CG-1) | P3 | 40h | Backend+FE | — |
| RM-29 | Profile enrichment multi-fonte (CG-2) | P3 | 40h | Backend | — |
| RM-30 | WhatsApp ↔ WSI direto (CG-3) | P3 | 24h | Backend | — |
| RM-31 | Blind review / candidate anonymizer (CG-4) | P3 | 16h | Backend | RM-01 |
| RM-32 | Calibração contínua de busca (CG-6) | P3 | 32h | Backend | — |
| RM-33 | NPS / Sentiment analysis (CG-7) | P3 | 16h | Backend | — |
| RM-34 | Cascata de confiança T3 automática (CG-5) | P3 | 16h | Backend | RM-09 |

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

**Esforço estimado:** 6h (por agente fora do padrão) | **Responsável:** Backend

**Critério de aceitação:**
- [ ] Todo domínio em `app/domains/*/agents/` tem os 4 arquivos
- [ ] `system_prompt.py` tem as 10 seções obrigatórias

---

### RM-19: Stage Context Ausente ou Incompleto

**O que está errado:** Agente não recebe contexto específico do estágio em que o candidato/vaga está.

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

**Esforço estimado:** 4h | **Responsável:** Backend

---

### RM-20: Memória sem Decay Factor / sem Limite

**O que está errado:** Memória do agente cresce indefinidamente ou não aplica decay factor para informações antigas.

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

**Esforço estimado:** 4h | **Responsável:** Backend

---

### RM-21: Drift Detection Desligado ou Não Configurado

**O que está errado:** Os 4 triggers de drift detection não estão ativos ou não geram alertas.

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

**Esforço estimado:** 4h | **Responsável:** Backend + Infra

---

### RM-22: Guardrails Não Configurados no Banco

**O que está errado:** A tabela `guardrails` existe (migration 020) mas não tem seed data ou não está sendo consultada pelo workflow.

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

**Esforço estimado:** 3h | **Responsável:** Backend

---

### RM-23: Testes de Fairness Fora do CI/CD

**O que está errado:** Testes de fairness (golden dataset, four-fifths rule) existem mas não rodam automaticamente no CI.

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

**Esforço estimado:** 6h | **Responsável:** Backend + Infra

---

### RM-24: ConfidencePolicy Limitada a Um Agente

**O que está errado:** `ConfidencePolicyService` só é usado no Job Wizard (gap G-C3). Decisões de triagem, sourcing e pipeline não usam.

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

**Esforço estimado:** 6h | **Responsável:** Backend

---

### RM-25: Wiring Desconectado

**O que está errado:** Componente/endpoint/hook/tool existe no código mas não está conectado ao fluxo real. "Existe" mas não "funciona".

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

**Esforço estimado:** Variável (1-4h por item) | **Responsável:** Backend ou Frontend

---

### RM-26: EU AI Act Compliance Gaps nos Prompts

**O que está errado:** System prompts não referenciam obrigações do EU AI Act (Art. 14, 52, Anexo III).

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

**Esforço estimado:** 3h | **Responsável:** Backend

---

### RM-27: WCAG 2.1 AA Não Atendido

**O que está errado:** Componentes frontend não atendem WCAG 2.1 AA (faltam aria-labels, contraste insuficiente, navegação por teclado ausente).

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

**Esforço estimado:** 8h | **Responsável:** Frontend

---

## P3 — BAIXO: GAPS COMPETITIVOS E ROADMAP

> Itens P3 são oportunidades de diferenciação. Devem ser planejados no **backlog** com análise de ROI.

---

### RM-28: Outreach Automatizado (Gap CG-1)

**O que está errado:** LIA não tem capacidade de enviar sequences automatizadas de outreach para candidatos passivos.

**Referência:** Anexo L, MC-3.1 CG-1

**Roadmap de implementação:**

1. **Modelagem** (8h): Criar modelos `OutreachSequence`, `OutreachStep`, `OutreachExecution`
2. **Backend** (16h): Criar domínio `outreach` com agent + tools (create_sequence, start_sequence, pause_sequence, get_metrics)
3. **Integração** (8h): Conectar com Communication Agent para envio via email/WhatsApp
4. **Frontend** (8h): UI para criar/gerenciar sequences

**Esforço total:** 40h | **Responsável:** Backend + Frontend

---

### RM-29: Profile Enrichment Multi-Fonte (Gap CG-2)

**O que está errado:** LIA só busca candidatos no banco interno. Não enriquece perfis com dados de LinkedIn, GitHub, etc.

**Referência:** Anexo L, MC-3.1 CG-2

**Roadmap:**

1. **API integrations** (16h): Integrar com APIs de enriquecimento (Proxycurl, People Data Labs)
2. **Data merging** (12h): Lógica de merge de dados de múltiplas fontes sem duplicar
3. **Privacy compliance** (8h): Garantir LGPD compliance no enriquecimento
4. **Frontend** (4h): Mostrar fontes de dados no perfil do candidato

**Esforço total:** 40h | **Responsável:** Backend

---

### RM-30: WhatsApp ↔ WSI Direto (Gap CG-3)

**O que está errado:** WSI Interview (Graph G2) não funciona via WhatsApp — apenas via web.

**Referência:** Anexo L, MC-3.1 CG-3

**Roadmap:**

1. **WhatsApp adapter** (12h): Adaptar WSI Graph para receber/enviar via WhatsApp API
2. **Session management** (8h): Gerenciar estado da entrevista WSI via conversação assíncrona
3. **Media handling** (4h): Suportar respostas em áudio/texto pelo WhatsApp

**Esforço total:** 24h | **Responsável:** Backend

---

### RM-31: Blind Review / Candidate Anonymizer (Gap CG-4)

**O que está errado:** Atributos protegidos (nome, idade, gênero, foto) não são removidos antes de enviar ao LLM para triagem/ranking.

**Depende de:** RM-01 (PII filter)

**Referência:** Anexo L, MC-3.1 CG-4, Gap G-M2/G-M3

**Roadmap:**

1. **Criar `candidate_anonymizer.py`** (8h):
```python
class CandidateAnonymizer:
    PROTECTED_FIELDS = ['name', 'age', 'gender', 'photo', 'ethnicity',
                        'marital_status', 'nationality', 'religion']

    def anonymize(self, candidate_data: dict) -> dict:
        anonymized = candidate_data.copy()
        for field in self.PROTECTED_FIELDS:
            if field in anonymized:
                anonymized[field] = f"[REDACTED_{field.upper()}]"
        return anonymized
```

2. **Integrar no pipeline de screening** (4h): Antes de enviar ao LLM, anonymizer processa
3. **Frontend: toggle blind review** (4h): Recrutador pode ativar/desativar blind review

**Esforço total:** 16h | **Responsável:** Backend

---

### RM-32: Calibração Contínua de Busca (Gap CG-6)

**O que está errado:** Sourcing Agent não aprende com feedback do recrutador para melhorar buscas futuras.

**Referência:** Anexo L, MC-3.2 CG-6

**Roadmap:**

1. **Feedback loop** (12h): Capturar accept/reject do recrutador em cada candidato
2. **Re-ranking model** (12h): Usar feedback para ajustar pesos de busca
3. **Auto-suggest refinements** (8h): Sugerir mudanças nos critérios baseado em padrão de accepts

**Esforço total:** 32h | **Responsável:** Backend

---

### RM-33: NPS / Sentiment Analysis (Gap CG-7)

**O que está errado:** Respostas de candidatos (email, WhatsApp) não são analisadas para sentiment.

**Referência:** Anexo L, MC-3.2 CG-7

**Roadmap:**

1. **Sentiment analyzer** (8h): Classificar respostas em positivo/neutro/negativo
2. **NPS tracking** (4h): Calcular NPS por etapa do pipeline
3. **Alertas** (4h): Alertar quando sentiment negativo > threshold

**Esforço total:** 16h | **Responsável:** Backend

---

### RM-34: Cascata de Confiança T3 Automática (Gap CG-5)

**O que está errado:** Quando o router não tem confiança suficiente, deveria escalar automaticamente para LLM classification (T3), mas a cascata não é automática.

**Depende de:** RM-09 (Confiança real)

**Referência:** Anexo L, MC-3.1 CG-5, Gap CG-5 (Anexo E)

**Roadmap:**

1. **Automatizar cascata** (8h):
```python
async def route(self, message, company_id):
    # T1: Cache
    cached = await cache.get(message_hash)
    if cached and cached.confidence >= 0.85:
        return cached.result

    # T2: Keywords
    keyword_result = self.keyword_match(message)
    if keyword_result.confidence >= 0.70:
        return keyword_result

    # T3: LLM (automático se T1+T2 insuficientes)
    llm_result = await self.llm_classify(message, company_id)
    await cache.set(message_hash, llm_result)
    return llm_result
```

2. **Rate limiting T3** (4h): Limitar chamadas LLM para classificação
3. **Métricas de cascata** (4h): Medir % de queries resolvidas em T1, T2, T3

**Esforço total:** 16h | **Responsável:** Backend

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
| P0 | 7 | 52h (~7 dias) | Imediato (bloqueador) | Backend |
| P1 | 10 | 46h (~6 dias) | Sprint N+1 | Backend |
| P2 | 10 | 50h (~7 dias) | Sprint N+2 a N+4 | Backend + Frontend |
| P3 | 7 | 184h (~23 dias) | Backlog (roadmap) | Backend + Frontend |
| **Total** | **34** | **332h (~42 dias)** | — | — |

**Nota:** Nem todos os runbooks serão aplicáveis a cada auditoria. O auditor deve identificar quais se aplicam e gerar o resumo executivo com os itens relevantes.

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