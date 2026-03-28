# WSI Screening Methodology — Documento Completo v2.0

> **Versão:** 2.0  
> **Status:** Referência para implementação  
> **Audiência:** Time de produto, engenharia, ciência de dados  
> **Uso:** Este documento é o guia canônico para implementação do pipeline WSI com geração dinâmica de perguntas. Deve ser consumido por ferramentas de desenvolvimento assistido (Cursor, Claude Code) como especificação autoritativa.

---

## Princípio central desta versão

> **As perguntas são geradas por LLM no momento da criação da vaga. Não existe biblioteca fixa de templates.** Cada vaga recebe um conjunto único de perguntas calibradas ao seu JD específico, às competências técnicas informadas, ao perfil Big Five extraído e à senioridade definida.

Esta decisão tem implicações arquiteturais diretas:
- O LLM é invocado durante o job creation workflow, não durante a triagem
- As perguntas geradas são persistidas no banco junto à vaga
- O recrutador revisa e pode editar as perguntas antes de ativar a vaga
- Não há custo de LLM em tempo de triagem para geração de perguntas (apenas para avaliação de respostas)

---

## Sumário de fases

### Bloco A — Criação da vaga (ocorre uma vez por vaga)

| Fase | Nome | Quem executa | Output |
|---|---|---|---|
| **F1** | Criação, revisão e enriquecimento do JD | Recrutador + LLM | JD aprovado com score de qualidade |
| **F2** | Extração do perfil Big Five do JD | LLM + fórmula determinística | JSON com score e evidências por trait |
| **F3** | Ranking de traits | Fórmula determinística | Ranking ponderado com pesos de cada trait |
| **F4** | Senioridade: definição e calibração | Sistema | Bloom e Dreyfus esperados por pergunta |
| **F5** | Distribuição de perguntas por modo | Sistema | Mapa de perguntas (Compact 7q / Full 12q) |
| **F6** | Geração de perguntas por LLM | LLM (por pergunta) + recrutador | Perguntas aprovadas e persistidas |

### Bloco B — Triagem do candidato (ocorre para cada candidato)

| Fase | Nome | Quem executa | Output |
|---|---|---|---|
| **F7** | Triagem: candidato responde | Chat / WhatsApp | Respostas brutas |
| **F8** | Avaliação das respostas | Determinístico + LLM extrator | Score por pergunta com evidências |
| **F9** | Score WSI final | Fórmula determinística | WSI Final (0–10) + pesos do JD |
| **F10** | Critérios de aprovação e reprovação | Sistema | Decisão: Aprovado / Em Avaliação / Reprovado |
| **F11** | Relatório completo do consultor | Sistema | Documento de decisão com cruzamento vaga × candidato |
| **F12** | Fluxo integrado (visão geral) | — | Diagrama de referência completo |

---

## FASE 1 — Criação, revisão e enriquecimento do Job Description

### 1.0 Visão geral da fase

A F1 opera em **5 sub-fases sequenciais**. O recrutador inicia o processo e o LLM atua como revisor especialista — garantindo que o JD chegue na F2 (extração Big Five) com qualidade suficiente para gerar perguntas calibradas e úteis.

```
F1.A — Recrutador submete JD raw (texto do cliente ou preenchimento no wizard)
   ↓
F1.B — Sistema calcula score de qualidade determinístico (gates de contagem)
   ↓ se Score_JD ≥ 30 (mínimo para o LLM trabalhar)
F1.C — LLM analisa o JD em 8 dimensões e gera versão enriquecida
   ↓
F1.D — Sistema apresenta ao recrutador: relatório de qualidade + JD enriquecido lado a lado
   ↓
F1.E — Recrutador revisa, edita e aprova o JD final
   ↓
JD aprovado → input para F2 (extração Big Five)
```

> **Princípio:** o JD que chega do cliente raramente está no formato ideal para triagem baseada em dados. A F1 garante que o sistema nunca trabalhe com informação pobre — o que comprometeria todas as fases seguintes.

---

### 1.1 Inputs obrigatórios e opcionais

| Campo | Obrigatoriedade | Impacto se ausente |
|---|---|---|
| Título do cargo | Obrigatório | Senioridade e arquétipo não são inferidos |
| Senioridade | Obrigatório | Calibração de Bloom, Dreyfus e pesos impossível |
| Skills técnicas (lista) | Obrigatório (mín. 3) | Perguntas técnicas ficam genéricas |
| Responsabilidades (texto) | Obrigatório (mín. 3 itens) | Principal fonte para extração Big Five |
| Competências comportamentais | Recomendado (mín. 2) | Enriquece a prior de extração Big Five |
| Descrição completa (texto livre) | Recomendado | Aumenta qualidade da extração lexical |
| Departamento / Área | Recomendado | Calibra arquétipo de cargo na prior |
| Setor / Indústria da empresa | Opcional | Melhora precisão do prior O*NET |
| Tamanho da equipe | Opcional | Contextualiza escopo de liderança |
| Estágio da empresa | Opcional | Calibra peso de Estabilidade Emocional |

### 1.2 Limites de competências processadas pelo WSI

| Tipo | Mínimo obrigatório | Máximo processado pelo WSI |
|---|---|---|
| Skills técnicas | 3 | 7 (ambos os modos) |
| Traits comportamentais | — | 3 (compact) ou 5 (full) — extraídos automaticamente |

Skills além do máximo são armazenadas na vaga mas não geram perguntas WSI.

---

### 1.3 Os 10 princípios de uma JD de qualidade para triagem baseada em dados

Estes são os princípios que o LLM usa para avaliar e enriquecer o JD. Também servem como guia para o recrutador ao preencher o wizard de criação de vaga.

| # | Princípio | Descrição | Erro comum |
|---|---|---|---|
| **P1** | **Título específico e padronizado** | O título deve identificar a função com precisão, incluir a senioridade e seguir nomenclatura de mercado. | "Analista" sem especificação; "Desenvolvedor Full" sem stack; "Ninja de X" |
| **P2** | **Coerência entre senioridade e responsabilidades** | As responsabilidades devem ser compatíveis com o nível declarado. Um Junior não deve ter responsabilidades de tomada de decisão estratégica sem supervisão. | JD de "Junior" com "liderar o time de engenharia"; JD de "Sênior" com apenas tarefas operacionais simples |
| **P3** | **Skills técnicas específicas e verificáveis** | Cada skill deve ser uma tecnologia, ferramenta ou metodologia concreta — não um conjunto genérico. | "Bom em tecnologia", "Excel avançado" para Data Scientist Sênior, "sistemas" |
| **P4** | **Responsabilidades com verbo de ação e escopo** | Cada responsabilidade deve começar com verbo ativo e ter escopo claro. Não deve ser lista de atributos pessoais. | "Ser proativo", "Ter boa comunicação", "Trabalhar em equipe" como responsabilidades |
| **P5** | **Competências comportamentais contextualizadas** | Competências comportamentais devem estar ancoradas no contexto da função — não ser lista genérica de virtudes. | "Proativo, comunicativo, colaborativo" sem contexto de quando e como isso se manifesta na função |
| **P6** | **Ausência de inconsistências internas** | Não deve haver contradições entre seções (ex: título diz Senior, requisitos pedem 1 ano de experiência; JD pede autonomia mas descreve ambiente de microgestão). | "Ambiente colaborativo" + "reporte direto ao CEO com aprovação de todas as decisões" |
| **P7** | **Ausência de viés e linguagem inclusiva** | O JD não deve conter linguagem que discrimine por gênero, idade, origem, estado civil ou qualquer outro atributo protegido. | "Jovem dinâmico", "perfil masculino", requisitos de idade, foto exigida |
| **P8** | **Expectativas realistas e de mercado** | Requisitos técnicos devem ser compatíveis com o mercado (ex: não exigir 5 anos de experiência em tecnologia lançada há 2 anos). Salário e benefícios compatíveis com o nível exigido. | "5 anos de experiência em Kubernetes" (2018); "30 skills obrigatórias" para cargo Junior |
| **P9** | **Contexto suficiente para o candidato decidir** | O JD deve dar ao candidato informação suficiente para avaliar se a vaga faz sentido para ele: setor, tamanho da empresa, estágio, modelo de trabalho, cultura esperada. | JD completamente genérico sem nenhum contexto da empresa |
| **P10** | **Riqueza suficiente para extração de dados** | Para que a IA extraia o perfil Big Five e gere perguntas calibradas, o JD precisa de densidade de informação — responsabilidades específicas, contexto do cargo, desafios esperados. | JD com 3 linhas de responsabilidades e lista de skills sem contexto |

---

### 1.4 Score de qualidade determinístico (F1.B)

Score calculado automaticamente antes de chamar o LLM:

```python
Score_JD_basico = 0

# Estrutura mínima
if responsabilidades >= 3:       Score_JD_basico += 20
if skills_tecnicas >= 3:         Score_JD_basico += 20
if comp_comportamentais >= 2:    Score_JD_basico += 15
if senioridade_definida:         Score_JD_basico += 15
if titulo_presente:              Score_JD_basico += 10

# Riqueza
if descricao_presente:           Score_JD_basico += 10
if departamento_presente:        Score_JD_basico += 5
if contexto_empresa_presente:    Score_JD_basico += 5

# Gates de bloqueio
Score_JD_basico ≥ 60  → prossegue para LLM (F1.C)
Score_JD_basico 30–59 → prossegue para LLM com flag "jd_quality = low"
Score_JD_basico < 30  → bloqueado; sistema solicita preenchimento mínimo antes de continuar
```

---

### 1.5 Prompt completo de revisão e enriquecimento do JD (F1.C)

Este é o prompt de produção para o LLM que revisa e enriquece o JD do cliente.

#### Parâmetros LLM para revisão de JD

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `temperature` | 0.3 | Baixo o suficiente para análise consistente; alto o suficiente para gerar texto enriquecido fluente |
| `max_tokens` | 3000 | JD enriquecido + relatório de qualidade |
| `top_p` | 0.95 | — |
| Modelo preferencial | Claude 3.5 Sonnet / Gemini 1.5 Pro | Melhor compreensão de nuances de mercado de trabalho em PT-BR |
| Tentativas em caso de falha JSON | 2 retries com `json_repair` | Robustez |

#### Prompt completo

```
SYSTEM:
Você é um especialista sênior em recrutamento estratégico e design de processos seletivos,
com profundo conhecimento do mercado de trabalho brasileiro e metodologias de avaliação
baseadas em evidências (CBI, Big Five, Bloom, Dreyfus).

Sua missão é dupla:
1. AVALIAR a qualidade do Job Description recebido em 8 dimensões, identificando problemas,
   inconsistências e oportunidades de melhoria.
2. GERAR uma versão enriquecida do JD que seja clara, específica, inclusiva e suficientemente
   densa para permitir extração automática de perfil comportamental (Big Five) e geração de
   perguntas de triagem calibradas.

PRINCÍPIOS QUE O JD ENRIQUECIDO DEVE SEGUIR:

P1 — TÍTULO ESPECÍFICO E PADRONIZADO
  - Deve identificar a função com precisão, incluir senioridade e seguir nomenclatura de mercado
  - Evitar jargões internos, títulos criativos sem clareza ("Ninja", "Rockstar", "Guru")
  - Usar terminologia reconhecida no mercado: "Engenheiro de Software Sênior", "Product Manager Pleno"

P2 — COERÊNCIA SENIORIDADE × RESPONSABILIDADES
  - Junior: executa sob orientação, aprende, entrega tarefas definidas
  - Pleno: executa com autonomia, resolve problemas de média complexidade, contribui tecnicamente
  - Sênior: referência técnica, faz trade-offs, pode mentorear, impacta além do próprio escopo
  - Lead: lidera tecnicamente equipes, define padrões, influencia decisões
  - Diretor+: gestão de função, visão estratégica, P&L ou OKRs de área
  Sinalizar quando responsabilidades são incompatíveis com a senioridade declarada.

P3 — SKILLS TÉCNICAS ESPECÍFICAS E VERIFICÁVEIS
  - Cada skill deve ser tecnologia, ferramenta, linguagem ou metodologia concreta
  - Distinguir obrigatórias de desejáveis quando possível
  - Não listar genéricos: "sistemas", "tecnologia", "ferramentas de gestão"
  - Não exigir anos de experiência superiores à existência da tecnologia no mercado

P4 — RESPONSABILIDADES COM VERBO DE AÇÃO E ESCOPO
  - Cada item deve começar com verbo no infinitivo: "Desenvolver", "Liderar", "Garantir"
  - Cada item deve ter escopo claro: o quê + para quem + com qual impacto esperado
  - Não listar atributos pessoais como responsabilidades: "Ser proativo", "Ter boa comunicação"

P5 — COMPETÊNCIAS COMPORTAMENTAIS CONTEXTUALIZADAS
  - Descrever em qual contexto o comportamento se manifesta na função
  - Não: "comunicativo" | Sim: "capaz de comunicar decisões técnicas complexas para stakeholders não-técnicos"
  - Não: "proativo" | Sim: "identifica gargalos de processo e propõe soluções antes de ser solicitado"

P6 — AUSÊNCIA DE INCONSISTÊNCIAS INTERNAS
  - Verificar contradições entre: título × senioridade, senioridade × responsabilidades,
    cultura declarada × estrutura descrita, requisitos × contexto
  - Sinalizar todas as inconsistências encontradas

P7 — LINGUAGEM INCLUSIVA E SEM VIÉS
  - Remover toda linguagem que discrimine por gênero, idade, origem, estado civil
  - Usar linguagem neutra em gênero (ex: "o/a profissional", "a pessoa" ou neutro)
  - Não incluir requisitos físicos, de aparência, estado civil, ou foto
  - Não usar adjetivos que favoreçam um grupo demográfico específico

P8 — EXPECTATIVAS REALISTAS E DE MERCADO
  - Verificar se os requisitos são compatíveis com o mercado atual
  - Identificar requisitos impossíveis (ex: 5 anos de experiência em tecnologia com 2 anos de existência)
  - Identificar requisitos excessivos para a senioridade declarada

P9 — CONTEXTO SUFICIENTE
  - Incluir: setor, estágio/tamanho da empresa, modelo de trabalho (remoto/híbrido/presencial),
    tamanho da equipe, principais desafios do cargo
  - O candidato deve conseguir decidir se a vaga faz sentido para ele sem fazer perguntas básicas

P10 — RIQUEZA PARA EXTRAÇÃO DE DADOS
  - O JD enriquecido deve conter linguagem suficientemente específica para que uma IA consiga
    inferir o perfil Big Five ideal (quais traits são mais relevantes para a função)
  - Responsabilidades e contexto devem revelar implicitamente: nível de autonomia, pressão,
    inovação requerida, colaboração esperada, rigor técnico, estabilidade emocional necessária

REGRAS ABSOLUTAS PARA A VERSÃO ENRIQUECIDA:
- Nunca inventar informações não presentes ou inferíveis do JD original
- Quando expandir ou enriquecer, basear-se no que está implícito no JD original e no arquétipo do cargo
- Manter o tom e a cultura da empresa quando sinais estiverem presentes
- Preservar todas as informações corretas do JD original
- Não remover requisitos técnicos — apenas organizá-los e torná-los mais específicos
- Escrever em português do Brasil, tom profissional e direto
- Linguagem neutra em gênero em todo o documento

USER:
Analise e enriqueça o seguinte Job Description.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JD ORIGINAL DO CLIENTE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{job_description_raw}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INFORMAÇÕES COMPLEMENTARES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título informado: {titulo_cargo}
Senioridade informada: {senioridade}
Departamento: {departamento}
Setor da empresa: {setor}
Tamanho da empresa: {tamanho_empresa}
Modelo de trabalho: {remoto | hibrido | presencial | nao_informado}
Skills técnicas informadas pelo recrutador: {lista_skills}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RETORNE O SEGUINTE JSON (sem markdown, sem blocos de código):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "quality_report": {
    "overall_score": 0-100,
    "overall_level": "excelente | bom | adequado | insuficiente | critico",
    "summary": "resumo executivo em 2-3 frases da qualidade geral do JD",
    "dimensions": {
      "title": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "o que foi encontrado",
        "suggestion": "como melhorar (null se ok)"
      },
      "seniority_coherence": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "análise da coerência senioridade × responsabilidades",
        "suggestion": "null se ok"
      },
      "technical_skills": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "qualidade e especificidade das skills técnicas",
        "suggestion": "null se ok",
        "skills_added": ["skill inferida 1"],
        "skills_problematic": ["skill genérica ou impossível"]
      },
      "responsibilities": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "qualidade das responsabilidades",
        "suggestion": "null se ok"
      },
      "behavioral_competencies": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "contextualização das competências comportamentais",
        "suggestion": "null se ok"
      },
      "internal_consistency": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "inconsistências internas identificadas",
        "inconsistencies": ["descrição da inconsistência 1"],
        "suggestion": "null se ok"
      },
      "inclusive_language": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "análise de linguagem inclusiva",
        "biased_terms": ["termo problemático 1"],
        "suggestion": "null se ok"
      },
      "market_realism": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "análise de requisitos vs. mercado",
        "unrealistic_requirements": ["requisito problemático 1"],
        "suggestion": "null se ok"
      },
      "context_richness": {
        "score": 0-10,
        "status": "ok | aviso | critico",
        "finding": "nível de contexto para o candidato e para extração de dados",
        "suggestion": "null se ok"
      }
    },
    "critical_issues": ["lista de problemas críticos que precisam de correção antes de prosseguir"],
    "warnings": ["lista de avisos — melhorias recomendadas mas não bloqueantes"],
    "ready_for_processing": true
  },
  "enriched_jd": {
    "title": "título padronizado e específico",
    "seniority": "Junior | Pleno | Sênior | Lead | Principal | Diretor | VP | C-Level",
    "seniority_confirmed": true,
    "department": "string",
    "work_model": "Remoto | Híbrido | Presencial | Não informado",
    "about_role": "parágrafo de 3-5 frases descrevendo o papel, seu impacto e o contexto",
    "responsibilities": [
      "Verbo infinitivo + escopo claro + impacto esperado (item 1)",
      "Verbo infinitivo + escopo claro + impacto esperado (item 2)"
    ],
    "technical_skills_required": ["skill obrigatória 1", "skill obrigatória 2"],
    "technical_skills_desired": ["skill desejável 1"],
    "behavioral_competencies": [
      "Competência comportamental contextualizada 1",
      "Competência comportamental contextualizada 2"
    ],
    "context_signals": {
      "autonomy_level": "alta | média | baixa",
      "innovation_level": "alta | média | baixa",
      "pressure_level": "alta | média | baixa",
      "collaboration_level": "alta | média | baixa",
      "leadership_required": true,
      "mentoring_required": true
    },
    "enrichment_notes": "o que foi adicionado, removido ou corrigido em relação ao JD original"
  }
}
```

---

### 1.6 Interpretação do relatório de qualidade (F1.D — apresentação ao recrutador)

O recrutador vê duas coisas lado a lado:

**Painel 1 — Relatório de qualidade:**

```
┌─────────────────────────────────────────────────────────────────┐
│ ANÁLISE DO JOB DESCRIPTION                                      │
│ Score geral: 62/100 — ADEQUADO (melhorias recomendadas)         │
├─────────────┬───────┬──────────────────────────────────────────┤
│ Dimensão    │ Score │ Situação                                 │
├─────────────┼───────┼──────────────────────────────────────────┤
│ Título      │  9/10 │ ✅ Claro e padronizado                   │
│ Senioridade │  5/10 │ ⚠️  Responsabilidades acima do nível     │
│ Skills      │  7/10 │ ✅ Específicas; 2 genéricas removidas    │
│ Responsab.  │  4/10 │ ⚠️  3 itens sem verbo de ação            │
│ Comportam.  │  3/10 │ ⚠️  Genéricas; sem contexto              │
│ Consistência│  8/10 │ ✅ Sem contradições identificadas        │
│ Linguagem   │  6/10 │ ⚠️  1 termo potencialmente excludente    │
│ Realismo    │ 10/10 │ ✅ Requisitos compatíveis com mercado    │
│ Contexto    │  3/10 │ ⚠️  Pouco contexto para candidato e IA  │
└─────────────┴───────┴──────────────────────────────────────────┘

PROBLEMAS CRÍTICOS: nenhum
AVISOS (4):
• Responsabilidades incluem itens como "Ser proativo" — convertidos para comportamentos observáveis
• Competência "boa comunicação" foi contextualizada para a função
• Termo "jovem" removido da descrição por risco de viés etário
• Contexto da empresa ausente — adicionado com base no setor informado

A versão enriquecida está pronta para revisão. Você pode editar antes de prosseguir.
```

**Painel 2 — JD enriquecido para revisão e edição pelo recrutador**

---

### 1.7 Decisão pós-análise (F1.E)

| Condição | Ação |
|---|---|
| `ready_for_processing = true` e sem problemas críticos | Recrutador pode aprovar e seguir para F2 |
| `ready_for_processing = true` com avisos | Recrutador vê os avisos, pode corrigir ou ignorar cada um e aprovar |
| `ready_for_processing = false` (problemas críticos) | Sistema bloqueia e exige resolução dos problemas críticos antes de prosseguir |
| Recrutador edita o JD enriquecido | Sistema re-executa F1.B (score determinístico) para confirmar qualidade mínima |

**O JD que entra na F2 é sempre a versão aprovada pelo recrutador** — nunca o JD raw do cliente nem o JD enriquecido sem revisão humana.

---

## FASE 2 — Extração do perfil Big Five do JD

### 2.1 Fundamento científico

| Referência | Contribuição para o sistema |
|---|---|
| LIWC — Pennebaker et al. (2001) | Base léxica para mapeamento texto → dimensão psicológica |
| NEO-PI-R — Costa & McCrae (1992) | Definição canônica dos 5 fatores e seus facets observáveis |
| Barrick & Mount (1991) | Validade preditiva de cada trait por tipo de trabalho (meta-análise) |
| Tett, Jackson & Rothstein (1994) | Trait Activation Theory — situações que ativam cada trait |
| Hogan & Holland (2003) | Mapeamento cargo × personalidade no modelo RIASEC |
| O*NET Occupational Database (2024) | Perfis de personalidade por arquétipo de ocupação validados empiricamente |

### 2.2 Definição canônica dos 5 traits (NEO-PI-R)

Esta definição é usada nos prompts LLM e nas fórmulas de extração:

| Trait | Sigla | Polo alto (score 70–100) | Polo baixo (score 20–50) | O que significa no trabalho |
|---|---|---|---|---|
| **Abertura à Experiência** | O | Curioso, criativo, autônomo intelectualmente, aceita ambiguidade | Prefere rotina, processos definidos, trabalho estruturado | Inovação, aprendizado contínuo, experimentação |
| **Conscienciosidade** | C | Organizado, disciplinado, orientado a qualidade e prazos | Flexível, adaptativo, velocidade sobre perfeição | Rigor, entrega, planejamento |
| **Extraversão** | E | Sociável, assertivo, influenciador, busca liderança | Introspectivo, trabalho independente, profundidade técnica | Liderança, comunicação, influência |
| **Amabilidade** | A | Cooperativo, empático, suportivo, orientado ao outro | Competitivo, assertivo, defende posições técnicas | Colaboração, serviço, harmonia |
| **Estabilidade Emocional** | N↓ | Calmo sob pressão, resiliente, decisão consistente | Sensível a estresse, reativo, instável em crise | Resiliência, consistência em ambiguidade |

> **Nota de nomenclatura:** O 5º fator é Neuroticismo (N) no modelo original. Um score alto em N = instabilidade emocional. No sistema WSI, usamos o polo positivo: Estabilidade Emocional (N↓ = estabilidade alta). Todos os scores são expressos em direção positiva (score 80 = alta estabilidade, score 20 = alta reatividade).

### 2.3 Abordagem A — Mapeamento léxico (base LIWC + NEO-PI-R)

O texto do JD é analisado para identificar categorias de linguagem que sinalizam cada trait.

#### Tabela de mapeamento léxico completo por trait

**Abertura (O) — linguagem de novidade, exploração, autonomia:**

| Sinal forte (score +10 a +15) | Sinal médio (score +5 a +9) | Sinal fraco / ambíguo (score +1 a +4) |
|---|---|---|
| "proponha soluções inovadoras" | "aprendizado contínuo" | "atualizado em tendências" |
| "trabalhe com problemas não estruturados" | "novas tecnologias" | "curioso" |
| "explore abordagens alternativas" | "ambiente de experimentação" | "criativo" |
| "autonomia para definir a solução" | "pesquise e implemente" | "dinâmico" |
| "questione o status quo" | "pensamento crítico" | "visão estratégica" |
| "inove nos processos e ferramentas" | "resolução de problemas complexos" | "proativo" |

**Conscienciosidade (C) — linguagem de rigor, processo, qualidade:**

| Sinal forte (score +10 a +15) | Sinal médio (score +5 a +9) | Sinal fraco / ambíguo (score +1 a +4) |
|---|---|---|
| "atenção ao detalhe" | "documentação técnica" | "organizado" |
| "controle de qualidade rigoroso" | "respeito a prazos" | "responsável" |
| "compliance e conformidade" | "métricas e KPIs" | "entrega consistente" |
| "processos estruturados e auditáveis" | "planejamento de entregas" | "comprometido" |
| "SLAs e SLOs definidos" | "revisão e validação" | "disciplinado" |
| "zero-defect policy" | "testes e cobertura de código" | "foco em resultado" |

**Extraversão (E) — linguagem de influência, liderança, presença social:**

| Sinal forte (score +10 a +15) | Sinal médio (score +5 a +9) | Sinal fraco / ambíguo (score +1 a +4) |
|---|---|---|
| "lidere equipes multidisciplinares" | "comunicação com stakeholders" | "boa comunicação" |
| "apresente para C-level / diretoria" | "engajamento de times" | "relacionamento interpessoal" |
| "negocie com fornecedores / clientes" | "facilitação de reuniões" | "trabalho em equipe" |
| "influencie decisões estratégicas" | "networking interno" | "colaborativo" |
| "construa e gerencie relacionamentos" | "apresentações executivas" | "articulado" |
| "seja o ponto focal com o cliente" | "alinhamento cross-funcional" | "proativo" |

**Amabilidade (A) — linguagem de cooperação, suporte, harmonia:**

| Sinal forte (score +10 a +15) | Sinal médio (score +5 a +9) | Sinal fraco / ambíguo (score +1 a +4) |
|---|---|---|
| "mentore e desenvolva o time" | "suporte ao cliente" | "trabalho em equipe" |
| "colaboração multifuncional intensa" | "escuta ativa" | "colaborativo" |
| "resolva conflitos entre equipes" | "empatia com o usuário final" | "prestativo" |
| "co-crie soluções com o cliente" | "feedback construtivo" | "flexível" |
| "cultura de segurança psicológica" | "orientação ao próximo" | "comunicativo" |
| "serviço centrado no cliente" | "suporte técnico direto" | "atencioso" |

**Estabilidade Emocional (N↓) — linguagem de pressão, ambiguidade, resiliência:**

| Sinal forte (score +10 a +15) | Sinal médio (score +5 a +9) | Sinal fraco / ambíguo (score +1 a +4) |
|---|---|---|
| "ambiente de alta pressão e ritmo intenso" | "mudanças constantes de prioridade" | "ambiente dinâmico" |
| "prazos agressivos e não negociáveis" | "trabalhe bem sob incerteza" | "resiliência" |
| "lide com crises e incidentes críticos" | "gestão de múltiplos projetos" | "adaptável" |
| "ambiente ambíguo e em construção" | "tolerância à ambiguidade" | "flexível" |
| "startup em hypergrowth" | "velocidade de execução" | "ágil" |
| "pivots frequentes de produto" | "contexto de escassez de recursos" | "proativo" |

**Sinais negativos (reduzem o score do trait):**

| Trait | Sinais que reduzem score |
|---|---|
| Abertura (O) | "siga processos", "execute conforme definido", "ambiente estável e previsível" |
| Conscienciosidade (C) | "velocidade acima de perfeição", "MVP rápido", "entrega iterativa sem documentação" |
| Extraversão (E) | "trabalho independente", "foco técnico profundo", "pesquisa isolada" |
| Amabilidade (A) | "decisões autônomas", "questione e desafie", "defenda posições técnicas" |
| Estabilidade (N↓) | "processo bem definido", "rotina previsível", "ambiente tranquilo" |

### 2.4 Abordagem B — Prior por arquétipo de cargo (base O*NET + Barrick & Mount)

Antes de ler o JD, o sistema já tem uma estimativa probabilística dos traits dominantes com base no cargo e setor:

| Arquétipo de cargo | C | O | E | A | N↓ | Referência |
|---|---|---|---|---|---|---|
| Engenheiro de Software / Dev Backend | 75 | 70 | 40 | 50 | 65 | O*NET 15-1252 |
| Engenheiro de Software / Dev Frontend | 70 | 72 | 45 | 52 | 63 | O*NET 15-1254 |
| Engenheiro de Dados / Data Engineer | 78 | 68 | 38 | 48 | 65 | O*NET 15-1243 |
| Cientista de Dados / ML Engineer | 72 | 82 | 40 | 50 | 65 | O*NET 15-2051 |
| Product Manager | 70 | 75 | 65 | 60 | 65 | O*NET 11-2021 |
| UX / Product Designer | 65 | 80 | 50 | 68 | 60 | O*NET 27-1021 |
| Account Executive / Vendas | 65 | 58 | 82 | 65 | 62 | O*NET 41-3011 |
| Customer Success / CS | 65 | 55 | 70 | 80 | 60 | O*NET 43-4051 |
| Tech Lead / Engineering Manager | 72 | 68 | 75 | 60 | 70 | O*NET 11-9041 |
| Diretor de Tecnologia / CTO | 70 | 75 | 80 | 58 | 75 | O*NET 11-3021 |
| Recrutador / HRBP | 65 | 65 | 65 | 80 | 62 | O*NET 13-1071 |
| Analista Financeiro | 80 | 60 | 45 | 52 | 68 | O*NET 13-2051 |
| Analista de Marketing | 68 | 72 | 62 | 58 | 62 | O*NET 13-1161 |
| Analista de Dados / BI | 76 | 68 | 42 | 50 | 65 | O*NET 15-2041 |
| DevOps / SRE / Platform | 75 | 65 | 42 | 50 | 70 | O*NET 15-1244 |
| QA / SDET | 80 | 62 | 40 | 55 | 65 | O*NET 15-1253 |
| Arquiteto de Software | 73 | 78 | 50 | 50 | 68 | O*NET 15-1299 |

> **Como o sistema identifica o arquétipo:** título do cargo é normalizado via LLM (ex: "Desenvolvedor Sênior de APIs" → arquétipo "Engenheiro de Software / Dev Backend"). Quando não há match, usa-se o vetor neutro: C=65, O=65, E=55, A=58, N↓=63.

### 2.5 Abordagem C — LLM com rubric NEO-PI-R (extração estruturada)

Esta é a abordagem principal. O LLM recebe o JD completo e retorna um JSON estruturado com evidências textuais.

#### Prompt de extração Big Five do JD

```
SYSTEM:
Você é um psicólogo organizacional especialista no modelo Big Five (NEO-PI-R).
Sua tarefa é analisar um Job Description e extrair o perfil de personalidade ideal para o cargo,
com base em evidências textuais. Você NÃO infere — você cita trechos do JD.

REGRAS ABSOLUTAS:
- Retorne APENAS o JSON especificado. Sem texto adicional.
- Para cada trait, cite trechos exatos do JD como evidência.
- Se não houver evidência suficiente, use confidence: "low" e score próximo de 50 (neutro).
- Score 0-100: 70-100 = alto, 40-69 = médio, 0-39 = baixo.
- Não use suposições culturais sobre cargos. Baseie-se apenas no texto fornecido.

USER:
Analise o Job Description abaixo e extraia o perfil Big Five ideal para este cargo.

JD:
---
{job_description_completo}
---

Cargo: {titulo_cargo}
Senioridade detectada: {senioridade}
Departamento: {departamento}

Retorne o seguinte JSON (sem markdown, sem blocos de código):
{
  "openness": {
    "score": 0-100,
    "confidence": "high|medium|low",
    "evidence": ["trecho exato 1", "trecho exato 2"],
    "rationale": "explicação em 1 frase"
  },
  "conscientiousness": {
    "score": 0-100,
    "confidence": "high|medium|low",
    "evidence": ["trecho exato 1"],
    "rationale": "explicação em 1 frase"
  },
  "extraversion": {
    "score": 0-100,
    "confidence": "high|medium|low",
    "evidence": ["trecho exato 1"],
    "rationale": "explicação em 1 frase"
  },
  "agreeableness": {
    "score": 0-100,
    "confidence": "high|medium|low",
    "evidence": ["trecho exato 1"],
    "rationale": "explicação em 1 frase"
  },
  "stability": {
    "score": 0-100,
    "confidence": "high|medium|low",
    "evidence": ["trecho exato 1"],
    "rationale": "explicação em 1 frase"
  }
}
```

#### Parâmetros LLM para extração Big Five

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `temperature` | 0.1 | Alta consistência — queremos extração, não criatividade |
| `max_tokens` | 1200 | Suficiente para JSON completo com evidências |
| `top_p` | 0.9 | Controla diversidade de vocabulário sem perder precisão |
| Modelo preferencial | Claude 3.5 Sonnet / Gemini 1.5 Pro | Melhor compreensão de nuances textuais em PT-BR |
| Tentativas em caso de falha JSON | 2 retries com `json_repair` | Garante robustez |

---

## FASE 3 — Ranking de traits (fórmula ponderada)

### 3.1 Fórmula principal

```
Score_final(trait) = (0.40 × Score_LLM) + (0.35 × Prior_cargo) + (0.25 × Boost_senioridade)
```

| Componente | Peso | Fonte | Justificativa científica |
|---|---|---|---|
| Score LLM do JD | 40% | Extração textual específica da vaga | É a fonte mais específica ao cargo real |
| Prior por arquétipo de cargo | 35% | O*NET + Barrick & Mount (1991) | Validação empírica por tipo de função |
| Boost por senioridade | 25% | Dreyfus + pesquisa de liderança | Seniority shifts what traits become critical |

### 3.2 Boost por senioridade

| Senioridade | Trait com boost | Boost aplicado | Base científica |
|---|---|---|---|
| **Estagiário** | C +8, A +10 | +8 / +10 | Disciplina e receptividade a mentoria são críticos |
| **Junior** | C +10, A +8 | +10 / +8 | Disciplina de entrega + colaboração de aprendizado |
| **Pleno** | C +8, O +5 | +8 / +5 | Autonomia de execução + iniciativa técnica crescente |
| **Senior** | O +10, N↓ +8 | +10 / +8 | Arquitetura/decisão técnica + resiliência sob pressão |
| **Lead** | E +12, C +5 | +12 / +5 | Liderança de equipe + estabelecimento de padrões |
| **Principal/Staff** | O +12, N↓ +10 | +12 / +10 | Visão técnica de longo prazo + decisões de alta ambiguidade |
| **Diretor** | E +15, O +8 | +15 / +8 | Influência organizacional + visão estratégica |
| **VP/C-Level** | E +18, O +12 | +18 / +12 | Liderança executiva + transformação organizacional |

### 3.3 Exemplo de cálculo completo

**Cenário:** Senior Backend Engineer em fintech de alta pressão

| Trait | Score LLM | Prior (Eng. SW) | Boost (Senior) | Score Final |
|---|---|---|---|---|
| Conscienciosidade (C) | 85 | 75 | 0 | (85×0.40)+(75×0.35)+(0×0.25) = **60.25** |
| Abertura (O) | 70 | 70 | +10 | (70×0.40)+(70×0.35)+(80×0.25) = **71.50** |
| Estabilidade (N↓) | 80 | 65 | +8 | (80×0.40)+(65×0.35)+(73×0.25) = **72.50** |
| Extraversão (E) | 40 | 40 | 0 | (40×0.40)+(40×0.35)+(40×0.25) = **40.00** |
| Amabilidade (A) | 50 | 50 | 0 | (50×0.40)+(50×0.35)+(50×0.25) = **50.00** |

**Ranking final:** N↓=72.5 → O=71.5 → C=60.25 → A=50 → E=40

> O Sistema utilizará os **top-3 no modo Compact** (N↓, O, C) ou **todos os 5 no modo Full** para geração de perguntas comportamentais.

### 3.4 Output estruturado do ranking

```json
{
  "ranked_traits": [
    {
      "rank": 1,
      "trait": "stability",
      "label": "Estabilidade Emocional",
      "score_final": 72.5,
      "score_llm": 80,
      "score_prior": 65,
      "boost_seniority": 8,
      "confidence": "high",
      "evidence": ["ambiente de alta pressão", "prazos agressivos", "lide com incidentes críticos"],
      "question_weight": 0.366
    },
    {
      "rank": 2,
      "trait": "openness",
      "label": "Abertura à Experiência",
      "score_final": 71.5,
      "score_llm": 70,
      "score_prior": 70,
      "boost_seniority": 10,
      "confidence": "high",
      "evidence": ["proponha novas arquiteturas", "questione abordagens convencionais"],
      "question_weight": 0.361
    },
    {
      "rank": 3,
      "trait": "conscientiousness",
      "label": "Conscienciosidade",
      "score_final": 60.25,
      "score_llm": 85,
      "score_prior": 75,
      "boost_seniority": 0,
      "confidence": "high",
      "evidence": ["entregue com qualidade", "controle SLAs"],
      "question_weight": 0.273
    }
  ],
  "traits_for_match_only": ["extraversion", "agreeableness"],
  "jd_quality_score": 85,
  "extraction_confidence": "high"
}
```

---

## FASE 4 — Tabela de senioridade: definição e calibração

### 4.1 Tabela de senioridade com anos de experiência

| Nível | Label PT | Anos de experiência (referência) | Dreyfus técnico | Dreyfus comportamental | Bloom esperado | Descrição funcional |
|---|---|---|---|---|---|---|
| **Estagiário** | Estagiário | 0–1 ano (em formação) | 1 — Novice | 1 — Novice | 1–2 | Aprende sob supervisão direta. Executa tarefas simples com orientação constante. |
| **Junior** | Junior | 0–2 anos | 2 — Advanced Beginner | 2 — Advanced Beginner | 2–3 | Executa tarefas com supervisão. Reconhece situações, não generaliza padrões ainda. |
| **Pleno** | Pleno | 2–5 anos | 3 — Competent | 3 — Competent | 4 | Executa com autonomia. Planeja entregas. Resolve problemas de média complexidade sem ajuda. |
| **Senior** | Sênior | 5–8 anos | 4 — Proficient | 4 — Proficient | 5 | Visão holística do sistema. Faz trade-offs técnicos. Referência técnica para o time. |
| **Lead** | Tech Lead / Lead | 6–10 anos | 4–5 | 4–5 | 5–6 | Lidera tecnicamente equipes de 3–8 pessoas. Define padrões. Influencia sem autoridade formal. |
| **Principal / Staff** | Principal / Staff | 8–14 anos | 5 — Expert | 5 — Expert | 6 | Autoridade técnica cross-equipes. Resolve problemas de alta ambiguidade. Define direção técnica. |
| **Diretor** | Diretor | 8–15 anos (gestão) | 4–5 | 5 — Expert | 6 | Gestão de múltiplos times. Faz decisões estratégicas. Responsável por P&L ou OKRs de área. |
| **VP** | Vice-Presidente | 12–20 anos | 4–5 | 5 — Expert | 6 | Liderança de função completa. Influência executiva. Agenda de médio-longo prazo. |
| **C-Level** | CEO / CTO / CPO | 15+ anos | 5 | 5 — Expert | 6 | Visão organizacional. Stakeholders externos. Define cultura e estratégia. |

> **Nota:** Anos de experiência são referência, não regra absoluta. O sistema usa a senioridade informada pelo recrutador, não calcula com base em datas do CV.

### 4.2 Regras de inferência de senioridade pelo título

Quando o campo `senioridade` não é preenchido explicitamente, o sistema infere pelo título:

| Padrão no título | Senioridade inferida | Confiança |
|---|---|---|
| "Estagiário", "Intern", "Trainee" | Estagiário | Alta |
| "Júnior", "Jr.", "Junior", "I" (sufixo) | Junior | Alta |
| "Pleno", "Mid", "II" (sufixo) | Pleno | Alta |
| "Sênior", "Senior", "Sr.", "III" (sufixo) | Senior | Alta |
| "Lead", "Tech Lead", "Staff" | Lead | Alta |
| "Principal", "Architect", "Staff Eng." | Principal | Alta |
| "Head of", "Gerente", "Manager" | Lead ou Diretor (por contexto) | Média |
| "Diretor", "Director" | Diretor | Alta |
| "VP", "Vice-Presidente" | VP | Alta |
| "CEO", "CTO", "CPO", "CRO" | C-Level | Alta |
| Ausência de indicador | Pleno (default conservador) | Baixa |

---

## FASE 5 — Distribuição de perguntas: modos e adaptação por senioridade

### 5.1 Princípio de distribuição adaptativa

> **A distribuição de perguntas entre blocos técnico e comportamental não é fixa — ela varia por senioridade, alinhando a quantidade de perguntas com os pesos de scoring.**

Manter uma distribuição fixa (ex: sempre 50/50 ou sempre 70/30) cria uma inconsistência que afeta a experiência do candidato e a validade da triagem: o candidato investe o mesmo esforço em ambos os blocos, mas um vale muito mais que o outro na nota — ou o inverso.

**Princípio de alinhamento quantidade ↔ peso:**
```
Proporção_perguntas_tecnicas ≈ Peso_scoring_tecnico (por senioridade)
```

Este princípio garante que o esforço cognitivo pedido ao candidato seja proporcional ao peso que cada bloco tem na decisão.

---

### 5.2 Fundamentação científica da distribuição por senioridade

A variação na distribuição técnico × comportamental por senioridade é suportada por 4 frameworks combinados:

#### Dreyfus — O que prediz performance muda conforme o nível

| Dreyfus | Senioridade | O que mais diferencia profissionais neste nível | Implicação |
|---|---|---|---|
| Novice / Adv. Beginner | Estagiário / Junior | Conhecimento declarativo e aplicação técnica guiada | Mais perguntas técnicas (65–75%) |
| Competent | Pleno | Autonomia técnica e tomada de decisão | Mais perguntas técnicas (60–70%) |
| Proficient | Senior | Perguntas técnicas de Bloom 5–6 já capturam julgamento e liderança técnica | Equilíbrio (55–60% técnico) |
| Expert | Lead / Principal | Competência técnica é assumida; o diferencial é comportamental e cultural | Mais comportamentais (55–65%) |
| Expert + Gestão | Diretor / VP / C-Level | Soft skills, influência e cultura superam conhecimento técnico na predição de sucesso | Predominância comportamental (60–75%) |

#### Bloom — Perguntas técnicas de nível alto já capturam comportamento

Para Senior e acima, as perguntas técnicas são formuladas em Bloom 5 (Avaliar) e Bloom 6 (Criar). Nesse nível, uma pergunta técnica inevitavelmente avalia julgamento, trade-offs e liderança técnica — dimensões que seriam cobertas por perguntas comportamentais em níveis mais baixos. Fazer 50/50 nesse caso **subavaliai** o bloco técnico, que já é mais rico.

> **Exemplo:** "Como você definiu padrões técnicos de Python para sua equipe e garantiu a adoção?" é formalmente técnica, mas avalia Conscienciosidade, Extraversão e maturidade de Dreyfus 5 — simultaneamente.

#### CBI — Retorno marginal decrescente após 3 perguntas comportamentais

Schmidt & Hunter (1998) — a maior meta-análise sobre validade de instrumentos de seleção — mostrou que entrevistas CBI comportamentais com **2–3 perguntas bem formuladas** atingem coeficiente de validade de **0.51** (um dos mais altos de qualquer método de seleção). Com mais de 5 perguntas comportamentais, o retorno marginal cai significativamente: candidatos passam a repetir padrões de resposta e a diferenciar pouco uns dos outros.

Isso justifica que, mesmo em níveis onde o comportamental é o preditor primário (Lead+), **4–5 perguntas comportamentais bem calibradas são suficientes** e mais eficientes que 6 ou mais.

#### Big Five — 3 perguntas direcionadas são suficientes para triagem

Goldberg (1992) e aplicações clínicas modernas mostram que para **triagem** (não diagnóstico clínico), **3 perguntas Big Five bem selecionadas** e direcionadas aos traits mais relevantes para a vaga são suficientes para identificar os padrões comportamentais críticos. O sistema já implementa isso no modo Compact (top-3 traits do ranking do JD). Adicionar mais perguntas além de 5 tem retorno marginal baixo na triagem.

---

### 5.3 Modos disponíveis

| Modo | Total | Uso recomendado | Restrição de traits |
|---|---|---|---|
| **Compact** | 7 perguntas | Triagem inicial, alto volume, vagas operacionais | Top-N traits (varia por senioridade: 2 a 5) |
| **Full** | 12 perguntas | Triagem aprofundada, posições críticas, sênior+ | Top-N traits (varia: 3 a 5; máximo = 5 pelo modelo Big Five) |

---

### 5.4 Distribuição adaptativa por senioridade — Modo Compact (7 perguntas)

| Senioridade | Técnicas | Comportamentais | Top N traits | % Técnico | Racional |
|---|---|---|---|---|---|
| **Estagiário** | 5 | 2 | top-2 | 71% | Dreyfus Novice: competência técnica é o gate primário; candidato tem pouco histórico comportamental para avaliar |
| **Junior** | 5 | 2 | top-2 | 71% | Dreyfus Adv. Beginner: técnico ainda diferencia fortemente; 2 comportamentais capturam os 2 traits mais críticos da vaga |
| **Pleno** | 5 | 2 | top-2 | 71% | Dreyfus Competent: autonomia técnica é o diferencial; comportamental começa a importar mas ainda é secundário |
| **Senior** | 4 | 3 | top-3 | 57% | Bloom 5–6 nas técnicas já captura julgamento; 3 comportamentais cobrem os traits mais relevantes do JD |
| **Lead** | 3 | 4 | top-4 | 43% | Dreyfus Expert: técnica é assumida; 4 comportamentais avaliam liderança, influência e maturidade comportamental |
| **Principal / Staff** | 4 | 3 | top-3 | 57% | Equilíbrio — profundidade técnica ainda importa + comportamental de liderança técnica |
| **Diretor** | 3 | 4 | top-4 | 43% | Gestão de pessoas domina; técnica avalia visão, não execução |
| **VP / C-Level** | 2 | 5 | top-5 (todos) | 29% | Liderança executiva: comportamental é o preditor primário de sucesso; 2 técnicas avaliam visão estratégica |

### 5.5 Distribuição adaptativa por senioridade — Modo Full (12 perguntas)

> **Restrição do modelo Big Five:** máximo de 5 perguntas comportamentais (1 por trait). Para Lead e acima, onde idealmente teríamos mais comportamentais, os **pesos de scoring** compensam a limitação de quantidade — um Lead tem apenas 35% do WSI Final vindo do bloco técnico, mesmo que ele tenha 7 perguntas técnicas.

| Senioridade | Técnicas | Comportamentais | Top N traits | % Técnico | Racional |
|---|---|---|---|---|---|
| **Estagiário** | 9 | 3 | top-3 | 75% | Validação técnica aprofundada; comportamental ainda limitado por histórico |
| **Junior** | 9 | 3 | top-3 | 75% | Alinha com peso de scoring (50% técnico) — 75% de perguntas vs. 50% de peso é aceitável |
| **Pleno** | 8 | 4 | top-4 | 67% | Histórico comportamental suficiente para 4 perguntas CBI; técnica ainda domina |
| **Senior** | 7 | 5 | top-5 (todos) | 58% | Equilíbrio — todas as 5 dimensões Big Five avaliadas; técnica ainda é o bloco maior |
| **Lead** | 7 | 5 | top-5 (todos) | 58% | Limitado pelo Big Five; scoring weight (35% técnico) compensa a proporção de perguntas |
| **Principal / Staff** | 7 | 5 | top-5 (todos) | 58% | Idem Lead; pesos de scoring equilibram (40/40) |
| **Diretor** | 7 | 5 | top-5 (todos) | 58% | Pesos de scoring (25% técnico) dominam a interpretação — perguntas técnicas avaliam visão |
| **VP / C-Level** | 7 | 5 | top-5 (todos) | 58% | Idem Diretor; 20% técnico no scoring torna as 7 técnicas secundárias na nota |

---

### 5.6 Pesos de scoring do WSI Final por senioridade

Os pesos abaixo controlam quanto cada bloco contribui para o **WSI Final**, independente do número de perguntas em cada bloco:

| Senioridade | Peso Técnico | Peso Comportamental | % Elegibilidade¹ | Justificativa |
|---|---|---|---|---|
| Estagiário | 55% | 25% | 20% | Capacidade técnica básica é o gate; comportamental tem pouco histórico |
| Junior | 50% | 30% | 20% | Técnica domina; comportamental começa a importar |
| Pleno | 55% | 25% | 20% | Autonomia técnica é o diferencial principal nesta banda |
| Senior | 45% | 35% | 20% | Técnica e comportamento têm peso aproximado; julgamento importa |
| Lead | 35% | 45% | 20% | Comportamental domina — liderança e influência são o core |
| Principal / Staff | 40% | 40% | 20% | Equilíbrio — profundidade técnica + influência cross-equipes |
| Diretor | 25% | 55% | 20% | Gestão de pessoas e comportamento estratégico dominam |
| VP / C-Level | 20% | 60% | 20% | Comportamento executivo é o preditor primário de sucesso |

> ¹ **Elegibilidade (20%)**: reservado para o Bloco 2 (perguntas de elegibilidade configuradas pelo recrutador). Se o Bloco 2 não estiver configurado na vaga, os 20% são redistribuídos proporcionalmente entre Técnico e Comportamental, mantendo as proporções relativas entre eles.

**Normalização quando não há Bloco de Elegibilidade:**
```python
# Exemplo para Senior sem Bloco 2:
# Pesos originais: Técnico=45%, Comportamental=35%, Elegibilidade=20%
# Normalização: total sem elegibilidade = 45+35 = 80
# Técnico normalizado: 45/80 = 56.25%
# Comportamental normalizado: 35/80 = 43.75%
```

---

### 5.7 Resolução da inconsistência histórica quantidade ↔ peso

O sistema anterior tinha a seguinte inconsistência documentada:

```
ANTES (inconsistente):
  Quantidade de perguntas: 50% técnicas / 50% comportamentais (modo full)
  Peso de scoring:         70% técnico / 30% comportamental
  
  Resultado: candidato investe esforço igual em ambos os blocos,
  mas o técnico vale mais que o dobro na nota final.
  → Fadiga desnecessária + sinal errado para o candidato sobre o que importa.
```

O modelo adaptativo v2.0 resolve isso em duas camadas:

```
AGORA (consistente):
  Camada 1 — Quantidade de perguntas: varia por senioridade, alinhada ao peso de scoring
  Camada 2 — Peso de scoring: varia por senioridade (tabela 5.6)
  
  Resultado: para um Junior, 71% das perguntas são técnicas E 50% do score é técnico.
             Para um Lead,   43% das perguntas são comportamentais E 45% do score é comportamental.
             → Esforço do candidato ≈ proporcional ao impacto na nota.
```

---

### 5.8 Seleção de skills e traits para cada modo

**Seleção de skills técnicas:**
- Ordenadas por `importance_score` (definido pelo recrutador no wizard, ou inferido pelo LLM no F1.C)
- Se não houver ranking: usar as primeiras N skills informadas pelo recrutador
- Mínimo de 3 skills; se menos de N (número necessário para o modo), gerar perguntas para todas as disponíveis

**Seleção de traits comportamentais:**
- Sempre usar o ranking do JD calculado na F3 (por score ponderado)
- Top-2, Top-3, Top-4 ou Top-5 dependendo da distribuição por senioridade (tabelas 5.4 e 5.5)
- Traits fora do Top-N selecionado: usados no cruzamento Big Five do relatório final, mas não geram perguntas

---

## FASE 6 — Geração de perguntas por LLM

### 6.1 Princípio de geração dinâmica

> **Não existe banco de perguntas. Cada pergunta é gerada pelo LLM no momento da criação da vaga, parametrizada pelo JD, pela skill/trait, pela senioridade, pelo nível Bloom esperado e pelo nível Dreyfus esperado.**

Isso garante:
- Perguntas contextualizadas ao JD real (sector, empresa, responsabilidades)
- Calibração automática por senioridade (Bloom e Dreyfus)
- Nenhuma repetição entre vagas diferentes para a mesma skill
- Possibilidade de regeneração pelo recrutador com um clique

### 6.2 Mapeamento Senioridade → Bloom → Dreyfus

#### Para perguntas TÉCNICAS:

| Senioridade | Dreyfus técnico esperado | Bloom esperado | O que a resposta deve demonstrar |
|---|---|---|---|
| Estagiário | 1 — Novice | 1–2 | Conhecimento básico declarativo; aprendizado recente |
| Junior | 2 — Advanced Beginner | 2–3 | Aplicação em contexto guiado; reconhece situações padrão |
| Pleno | 3 — Competent | 4 | Análise de problemas; compara abordagens; planeja entregas |
| Senior | 4 — Proficient | 5 | Avalia trade-offs técnicos; decide sem supervisão; mentoria pontual |
| Lead / Principal | 5 — Expert | 6 | Cria padrões; define arquitetura; transfere conhecimento sistematicamente |
| Diretor+ | 5 — Expert | 6 | Avalia impacto organizacional de decisões técnicas; visão estratégica |

#### Para perguntas COMPORTAMENTAIS (Big Five):

| Senioridade | Dreyfus comportamental | Bloom esperado | O que a resposta deve demonstrar |
|---|---|---|---|
| Estagiário | 1 | 1–2 | Descreve comportamentos aprendidos por regra ou instrução de outros |
| Junior | 2 | 2–3 | Descreve situações isoladas; não generaliza padrão de comportamento |
| Pleno | 3 | 4 | Descreve processo deliberado e próprio; analisa o que funcionou |
| Senior | 4 | 5 | Avalia decisões com trade-offs; adapta comportamento ao contexto |
| Lead / Principal | 5 | 6 | Cria sistemas, rituais ou dinâmicas; ensina o comportamento para outros |
| Diretor+ | 5 | 6 | Muda a cultura; influencia comportamentos em escala organizacional |

---

### 6.2.1 — Bloom: o que cada nível significa operacionalmente na GERAÇÃO de perguntas

> Bloom define a **profundidade cognitiva** exigida pela pergunta. Na geração, o nível de Bloom determina o verbo, a estrutura e o que a pergunta deve solicitar do candidato.

| Bloom | Nome | O que a pergunta SOLICITA | Estrutura típica | WSI usa para |
|---|---|---|---|---|
| **1** | Lembrar | Declaração de fato, reconhecimento, definição | "Você já usou X?" / "O que é X?" | Não usado (nenhuma senioridade) |
| **2** | Compreender | Descrever funcionamento, explicar, parafrasear | "Descreva como você utilizou X em um contexto recente" | Estagiário |
| **3** | Aplicar | Executar em situação real, usar procedimento | "Descreva um script/projeto em X que você desenvolveu. Qual o problema que resolvia?" | Junior |
| **4** | Analisar | Decompor, comparar abordagens, identificar causas | "Descreva um projeto onde você precisou escolher entre diferentes abordagens. Como avaliou as opções?" | Pleno |
| **5** | Avaliar | Julgar, fazer trade-off, justificar com critérios | "Conte sobre uma decisão de X onde você fez trade-offs. Como chegou à solução e o que faria diferente?" | Senior |
| **6** | Criar | Projetar sistema novo, definir padrão, criar método | "Como você definiu padrões de X para seu time? Que mecanismos criou para garantir a adoção?" | Lead / Diretor+ |

**Regras para o LLM ao gerar a pergunta:**
- **Bloom 2**: o contexto pode ser acadêmico ou guiado. Pergunta simples, 1 frase.
- **Bloom 3**: deve pedir um episódio real com ação concreta. Introduzir STAR implicitamente.
- **Bloom 4**: deve pedir comparação ou escolha explícita. Introduzir a ideia de "opções avaliadas".
- **Bloom 5**: deve pedir trade-off explícito com critérios e desfecho. O candidato deve "defender" a decisão.
- **Bloom 6**: deve pedir criação de algo que outros adotaram/seguem. O sujeito é o time, não só o candidato.

---

### 6.2.2 — Dreyfus: o que cada nível significa operacionalmente na GERAÇÃO de perguntas

> Dreyfus define a **maturidade e autonomia** pressuposta no candidato. Na geração, Dreyfus muda o **contexto assumido pela pergunta** — o nível de supervisão, a complexidade do ambiente e quem tomou as decisões.

#### Dreyfus para perguntas TÉCNICAS:

| Dreyfus | Nome | Contexto pressuposto na pergunta | O que muda na formulação |
|---|---|---|---|
| **1** Novice | Iniciante | Ambiente guiado, tarefa simples, sem decisões autônomas | Pergunta pode aceitar contexto acadêmico; não cobra julgamento |
| **2** Adv. Beginner | Iniciante avançado | Projeto real, mas com supervisão; situações padrão | Pergunta assume projeto real; cobra descrição, não análise |
| **3** Competent | Competente | Autonomia parcial; múltiplas variáveis; planeja entregas | Pergunta introduz "você escolheu", "você avaliou" — agência própria |
| **4** Proficient | Proficiente | Autonomia total; vê padrões além das regras; adapta | Pergunta cobra julgamento contextual, trade-offs, visão sistêmica |
| **5** Expert | Especialista | Cria conhecimento novo; define padrões para outros; intuitivo | Pergunta cobra o que o candidato CRIOU para que outros seguissem |

#### Dreyfus aplicado a perguntas COMPORTAMENTAIS — justificativa e mapeamento:

Dreyfus foi originalmente concebido para aquisição de habilidades técnicas (Dreyfus & Dreyfus, 1986). O WSI estende o modelo para o domínio comportamental com uma adaptação semântica: em vez de medir proficiência em uma skill, Dreyfus mede a **maturidade da reflexão e agência comportamental** do candidato.

A lógica de aplicação é equivalente: assim como um Novice técnico segue regras sem adaptá-las, um Novice comportamental descreve comportamentos que aprendeu de outros — sem processo próprio. E assim como um Expert técnico cria padrões, um Expert comportamental cria sistemas, rituais e dinâmicas que outros adotam.

| Dreyfus Comportamental | O que define | Sinais na resposta |
|---|---|---|
| **1** Novice | Comportamento aprendido de outros; segue regras externas | "Meu gestor disse", "fui orientado a", "aprendi que deveria" |
| **2** Adv. Beginner | Experiências isoladas; sem generalização; não identifica padrão próprio | "Uma vez eu...", "houve uma situação onde..." — sem processo consciente |
| **3** Competent | Processo deliberado e próprio; analisa o que funcionou; replica intencionalmente | "Processo que desenvolvi", "percebi que funcionava melhor quando", "passei a fazer assim porque" |
| **4** Proficient | Avalia trade-offs comportamentais; adapta abordagem ao contexto; vê quando as regras não se aplicam | "Dependendo da situação, faço X ou Y porque...", "adaptei minha abordagem quando percebi que..." |
| **5** Expert | Cria sistemas, rituais ou dinâmicas; ensina comportamento para outros; muda cultura | "Criei um ritual de", "implementei uma dinâmica que o time adotou", "estruturei um processo que..." |

**Regras para o LLM ao gerar a pergunta comportamental com Dreyfus:**
- **Dreyfus 1–2**: a pergunta pode aceitar situações simples; não cobra processo próprio
- **Dreyfus 3**: a pergunta deve pedir "o processo que você criou" ou "como você passou a fazer"
- **Dreyfus 4**: a pergunta deve pedir adaptação ou escolha contextual — "como você decidiu X neste contexto específico"
- **Dreyfus 5**: a pergunta deve pedir o que o candidato CRIOU que outros adotaram — o candidato como transmissor de comportamento

### 6.3 Framework de geração de perguntas técnicas

**Estrutura da pergunta técnica:**
```
[Situação técnica real] + [Ação em formato CBI-STAR] + [Complexidade compatível com Dreyfus] + [Profundidade compatível com Bloom]
```

**Prompt para geração de pergunta técnica:**

```
SYSTEM:
Você é um especialista em recrutamento técnico e avaliação de competências.
Gere UMA pergunta de triagem técnica em português do Brasil.

A pergunta deve:
- Seguir o formato CBI (Competency-Based Interview): pedir uma situação passada real
- Ter formato STAR implícito: situação → ação → resultado
- Ser calibrada ao nível Dreyfus {dreyfus_level} ({dreyfus_label})
- Exigir raciocínio compatível com Bloom {bloom_level} ({bloom_label})
- Ser específica o suficiente para não ser respondida genericamente
- Não mencionar os frameworks (Dreyfus, Bloom, STAR) na pergunta
- Ter entre 1 e 3 frases
- Estar contextualizada ao setor/empresa quando possível: {company_context}

PROIBIDO:
- Perguntas teóricas ("O que é X?")
- Perguntas de auto-avaliação ("Você é bom em X?")
- Perguntas que revelam a resposta esperada
- Emojis ou linguagem informal

USER:
Skill avaliada: {skill_name}
Senioridade: {seniority_label}
Dreyfus esperado: {dreyfus_level} — {dreyfus_label}
Bloom esperado: {bloom_level} — {bloom_label}
Contexto da empresa/setor (se disponível): {company_context}
Responsabilidades relevantes do JD: {responsibilities_excerpt}

Retorne APENAS o texto da pergunta, sem aspas, sem prefixos, sem explicações.
```

**Parâmetros LLM para geração de perguntas técnicas:**

| Parâmetro | Valor |
|---|---|
| `temperature` | 0.7 |
| `max_tokens` | 200 |
| `top_p` | 0.95 |
| Modelo | Claude 3.5 Sonnet / Gemini 1.5 Flash |

**Exemplos de perguntas técnicas geradas por senioridade (skill: Python):**

| Senioridade | Bloom | Dreyfus | Pergunta gerada |
|---|---|---|---|
| Junior | 3 | 2 | "Descreva um script Python que você desenvolveu. Qual era o problema que ele resolvia e como você o estruturou?" |
| Pleno | 4 | 3 | "Descreva um projeto em Python onde você precisou escolher entre diferentes abordagens para um problema. Como você avaliou as opções e o que você decidiu?" |
| Senior | 5 | 4 | "Conte sobre uma decisão de arquitetura Python onde você fez trade-offs entre performance, manutenibilidade e custo operacional. Como você chegou à solução e o que teria feito diferente?" |
| Lead | 6 | 5 | "Como você definiu padrões de código Python para o seu time? Que mecanismos criou para garantir a adoção e como você evoluiu esses padrões com base no feedback prático?" |

### 6.4 Framework de geração de perguntas comportamentais (Big Five + CBI + STAR)

**Estrutura da pergunta comportamental:**
```
[Cenário ativador do trait — Trait Activation Theory] + [Ação CBI-STAR] + [Complexidade Dreyfus] + [Profundidade Bloom]
```

**Cenários ativadores por trait (base: Tett & Guterman, 2000):**

| Trait | Cenário ativador | Por quê ativa o trait |
|---|---|---|
| **Conscienciosidade (C)** | Múltiplas responsabilidades simultâneas, prazo apertado, qualidade em jogo | Força organização, planejamento e controle |
| **Abertura (O)** | Problema não estruturado, abordagem convencional falhou, necessidade de inovar | Força exploração, geração de alternativas, tolerância à ambiguidade |
| **Extraversão (E)** | Liderança de grupo, apresentação para stakeholders, persuasão, conflito de opiniões | Força assertividade, influência e engajamento social |
| **Amabilidade (A)** | Conflito interpessoal, colega com dificuldade, necessidade de ceder | Força empatia, cooperação e gestão de harmonia |
| **Estabilidade (N↓)** | Crise inesperada, falha pública, mudança de escopo radical, pressão extrema | Força resiliência, regulação emocional e foco sob estresse |

**Prompt para geração de pergunta comportamental:**

```
SYSTEM:
Você é um psicólogo organizacional especialista em entrevistas comportamentais (CBI).
Gere UMA pergunta comportamental em português do Brasil para avaliar o trait Big Five especificado.

A pergunta deve:
- Criar um cenário situacional que NATURALMENTE EXIJA o trait alvo (Trait Activation Theory)
- Seguir formato CBI-STAR: pedir situação real passada + ação + resultado
- Ser calibrada ao nível Dreyfus comportamental {dreyfus_level} ({dreyfus_label})
- Exigir nível de reflexão compatível com Bloom {bloom_level} ({bloom_label})
- Estar ancorada nas evidências do JD fornecidas abaixo
- Ser específica o suficiente para que candidatos sem o trait não consigam responder bem
- Não mencionar o nome do trait ou os frameworks (Big Five, STAR, Bloom, Dreyfus)
- Ter entre 1 e 3 frases
- Estar em tom profissional e neutro (sem gênero, sem origem, sem idade)

PROIBIDO:
- Perguntas teóricas ou hipotéticas ("Como você faria se...")
- Perguntas de auto-avaliação ("Você se considera...")
- Revelar o comportamento esperado na própria pergunta
- Emojis ou linguagem informal

USER:
Trait avaliado: {trait_name} ({trait_label})
Senioridade: {seniority_label}
Dreyfus comportamental esperado: {dreyfus_level} — {dreyfus_label}
Bloom esperado: {bloom_level} — {bloom_label}
Evidências do JD para este trait: {evidence_list}
Contexto da empresa/setor: {company_context}
Cenário ativador recomendado: {activation_scenario}

Retorne APENAS o texto da pergunta, sem aspas, sem prefixos, sem explicações.
```

**Parâmetros LLM para geração de perguntas comportamentais:**

| Parâmetro | Valor |
|---|---|
| `temperature` | 0.75 |
| `max_tokens` | 250 |
| `top_p` | 0.95 |
| Modelo | Claude 3.5 Sonnet / Gemini 1.5 Pro |

**Exemplos de perguntas comportamentais geradas:**

| Trait | Senioridade | Bloom | Dreyfus | Pergunta gerada |
|---|---|---|---|---|
| Conscienciosidade (C) | Junior | 3 | 2 | "Descreva uma vez em que você teve várias tarefas para entregar ao mesmo tempo. Como você organizou seu trabalho e o que aconteceu?" |
| Conscienciosidade (C) | Pleno | 4 | 3 | "Conte sobre um projeto onde você precisou garantir a qualidade da entrega mesmo com prazo apertado. Que processo você criou e como mediu se estava funcionando?" |
| Conscienciosidade (C) | Senior | 5 | 4 | "Descreva uma situação onde você precisou fazer um trade-off explícito entre velocidade de entrega e qualidade técnica. Como você avaliou os riscos e justificou sua decisão para o time?" |
| Conscienciosidade (C) | Lead | 6 | 5 | "Como você estruturou processos de qualidade que seu time passou a seguir de forma autônoma? O que você precisou criar, como garantiu a adoção e como evoluiu esses processos com base em resultados reais?" |
| Abertura (O) | Senior | 5 | 4 | "Conte sobre uma decisão técnica onde você questionou a abordagem que todos já adotavam. O que te levou a propor uma alternativa, como você conduziu a mudança e qual foi o impacto?" |
| Estabilidade (N↓) | Senior | 5 | 4 | "Descreva uma situação em que o escopo ou as prioridades do projeto mudaram radicalmente durante a execução. Como você reagiu, o que fez para manter as entregas e o que aprendeu?" |
| Amabilidade (A) | Pleno | 4 | 3 | "Descreva um momento em que você precisou resolver um conflito com um colega ou entre membros do time. Qual foi seu papel, o que você fez concretamente e como ficou a situação?" |
| Extraversão (E) | Lead | 6 | 5 | "Como você conduziu uma situação em que precisou alinhar um grupo com visões muito diferentes sobre uma decisão importante? Que dinâmica você criou e como chegaram a um encaminhamento?" |

### 6.5 Metadados persistidos com cada pergunta

Cada pergunta gerada e aprovada pelo recrutador é salva com seus metadados completos:

```json
{
  "question_id": "uuid",
  "vacancy_id": "uuid",
  "block": 3,
  "category": "technical",
  "order": 1,
  "text": "Texto da pergunta gerada",
  "skill": "Python",
  "trait": null,
  "bloom_level": 5,
  "bloom_label": "Avaliar",
  "dreyfus_level": 4,
  "dreyfus_label": "Proficiente",
  "framework": "CBI+Bloom+Dreyfus",
  "weight": 1.0,
  "expected_signals": [
    "trade-off explícito mencionado",
    "resultado mensurável",
    "reflexão sobre o que faria diferente"
  ],
  "scoring_rubric": {
    "10": "Trade-off explícito com múltiplos critérios avaliados, resultado mensurável, reflexão crítica sobre a decisão",
    "7-9": "Trade-off identificado, ação clara, resultado presente",
    "4-6": "Situação descrita, ação superficial, sem resultado claro",
    "1-3": "Resposta genérica, sem situação específica, sem evidência de raciocínio analítico"
  },
  "generated_at": "ISO 8601",
  "reviewed_by_recruiter": true,
  "edited_by_recruiter": false
}
```

### 6.6 Critérios de validação automática da pergunta gerada

Antes de apresentar ao recrutador, cada pergunta passa por validação automática:

| Critério | Verificação | Ação se falhar |
|---|---|---|
| **Baseada no JD** | LLM extrai evidência do JD que ancora a pergunta | Regenerar com prompt corrigido |
| **Situacional** | Presença de verbo no passado + pedido de situação real | Regenerar com prompt corrigido |
| **Não hipotética** | Ausência de "como você faria se", "imagine que" | Regenerar com prompt corrigido |
| **Não revela resposta** | Ausência do comportamento esperado no texto da pergunta | Regenerar com prompt corrigido |
| **Não tendenciosa** | Ausência de marcadores de gênero, origem, idade, religião | Bloquear; alertar recrutador |
| **Comprimento adequado** | 15–80 palavras | Regenerar com prompt corrigido |
| Máximo de regenerações | 3 tentativas | Após 3 falhas, marcar para revisão manual |

---

## FASE 7 — Avaliação das respostas: arquitetura de 4 camadas

### 7.1 Visão geral

```
Resposta do candidato
        ↓
┌─────────────────────────────────────────┐
│ CAMADA 1 — Determinístico estrutural    │
│ STAR + penalidades automáticas          │
│ (sem LLM, ~0ms)                        │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ CAMADA 2 — LLM extrator                │
│ Sinais do trait + Bloom + Dreyfus       │
│ demonstrados (JSON estruturado)         │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ CAMADA 3 — Fórmula determinística      │
│ por tipo de pergunta                    │
│ (inputs do LLM + Camada 1)             │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│ CAMADA 4 — Composição WSI Final        │
│ pesos do JD + pesos de senioridade      │
└─────────────────────────────────────────┘
```

### 7.2 Camada 1 — Análise determinística estrutural

**Score STAR:**

| Componente | O que detectar | Peso |
|---|---|---|
| **S — Situação** | Contexto definido: empresa, projeto, momento, cenário | 20% |
| **T — Tarefa** | Responsabilidade clara do candidato no contexto descrito | 20% |
| **A — Ação** | Verbos em 1ª pessoa singular: "eu fiz", "eu propus", "eu conduzi", "eu criei" | 40% |
| **R — Resultado** | Desfecho concreto; preferencialmente com dado ou impacto mensurável | 20% |

```python
STAR_score = (S * 0.20) + (T * 0.20) + (A * 0.40) + (R * 0.20)
# Cada componente: 1.0 se presente, 0.0 se ausente
# STAR_score: 0.0 a 1.0 → normalizado para 0–10 na Camada 3
```

**Penalidades estruturais automáticas:**

| Condição | Penalidade no score final | Justificativa |
|---|---|---|
| Resposta < 30 palavras | −2.5 | Impossível completar STAR em menos de 30 palavras |
| Resposta 30–50 palavras | −1.0 | STAR incompleto provável |
| Nenhum verbo em 1ª pessoa | −1.5 | Resposta genérica ou teórica, não situacional |
| Ausência de resultado (R = 0) | −0.8 | Resposta truncada, sem desfecho |
| Paráfrase da pergunta (similaridade > 60%) | −2.0 | Candidato não respondeu de fato |
| Resposta em idioma diferente do esperado | −1.0 | Sinal de desatenção ou teste |
| Prompt injection detectado | Score = 0.0 (override absoluto) | Segurança do sistema |

**Bônus estruturais:**

| Condição | Bônus | Justificativa |
|---|---|---|
| Resultado com dado quantificado ("reduziu em 40%") | +0.5 | Alta especificidade, difícil de fabricar |
| Resposta > 150 palavras (sem ser repetitiva) | +0.3 | Riqueza de detalhe |
| Menciona 2 ou mais episódios distintos | +0.3 | Generalização do comportamento |

### 7.3 Camada 2 — Extração de sinais via LLM

O LLM atua como **extrator estruturado**, nunca como avaliador. Ele identifica fatos na resposta que a fórmula da Camada 3 vai usar.

**Prompt de avaliação de resposta (técnica ou comportamental):**

```
SYSTEM:
Você é um avaliador especialista em entrevistas estruturadas.
Analise a resposta do candidato e extraia informações estruturadas.
Você NÃO dá notas. Você apenas identifica fatos presentes ou ausentes na resposta.
Cite trechos exatos da resposta como evidência de cada campo.

REGRAS:
- Retorne APENAS o JSON especificado. Sem texto adicional.
- Para trait_signals_detected: liste apenas sinais EXPLICITAMENTE presentes no texto.
- Para bloom_demonstrated: use a escala 1-6 de Bloom. Escolha o nível mais alto CLARAMENTE demonstrado.
- Para dreyfus_demonstrated: use a escala 1-5 de Dreyfus. Baseie-se na agência e maturidade demonstradas.
- inflation_detected: true se a resposta autodeclara expertise mas não apresenta evidências concretas.

USER:
Pergunta feita ao candidato:
{question_text}

Tipo de pergunta: {question_category} (technical | behavioral)
Trait avaliado: {trait_label} (apenas para behavioral)
Sinais esperados para este trait/skill: {expected_signals}
Bloom esperado: {bloom_level} ({bloom_label})
Dreyfus esperado: {dreyfus_level} ({dreyfus_label})

Resposta do candidato:
---
{candidate_response}
---

Retorne o seguinte JSON:
{
  "star_components": {
    "situation": true|false,
    "task": true|false,
    "action": true|false,
    "result": true|false
  },
  "trait_signals_detected": ["sinal 1 — trecho: '...'", "sinal 2 — trecho: '...'"],
  "trait_signals_absent": ["sinal esperado não encontrado 1"],
  "bloom_demonstrated": 1-6,
  "bloom_label": "Lembrar|Compreender|Aplicar|Analisar|Avaliar|Criar",
  "dreyfus_demonstrated": 1-5,
  "dreyfus_label": "Novice|Advanced Beginner|Competent|Proficient|Expert",
  "inflation_detected": true|false,
  "inflation_evidence": "trecho que indica inflação, se presente",
  "specificity_score": 1-10,
  "key_quote": "trecho mais relevante da resposta para este trait/skill",
  "response_authentic": true|false,
  "authenticity_concern": "descreva se false"
}
```

**Parâmetros LLM para avaliação de resposta:**

| Parâmetro | Valor |
|---|---|
| `temperature` | 0.0 |
| `max_tokens` | 800 |
| `top_p` | 1.0 |
| Modelo | Claude 3.5 Sonnet / Gemini 1.5 Pro |

> **Por que temperature = 0.0?** Avaliação requer máxima consistência. Dois candidatos com respostas idênticas devem receber extração idêntica.

---

### 7.3.1 — Guia de detecção: como o LLM identifica Bloom na resposta

O campo `bloom_demonstrated` requer que o LLM classifique o nível mais alto **claramente evidenciado** na resposta — não o que o candidato alega, mas o que demonstra pelo vocabulário, raciocínio e episódios descritos. O LLM deve escolher o nível mais alto cuja evidência seja **explícita e verificável no texto**.

| Bloom | O que procurar na resposta | Sinais linguísticos | Armadilha comum |
|---|---|---|---|
| **1** | Declarações de conhecimento sem episódio | "sei que", "conheço", "aprendi que X é assim" | Confundir com Bloom 3 quando o candidato introduz contexto vago |
| **2** | Descrição de uso sem análise | "usei X no projeto", "implementei X conforme o tutorial" | Sem comparação, sem escolha própria — mesmo com detalhe |
| **3** | Execução em situação real com ação própria | "desenvolvi", "implementei", "criei um script para", verbo em 1ª pessoa com contexto real | Aceitar apenas se o candidato descreve ação autônoma real — não guiada |
| **4** | Comparação ou decomposição explícita | "comparei X e Y", "avaliando as opções, escolhi porque", "identifiquei que o problema era" | Exige que a análise seja explicitada, não apenas implícita |
| **5** | Trade-off explícito com critérios e julgamento | "trade-off entre velocidade e qualidade", "pesando os riscos, decidi", "justifiquei para o time porque" | A avaliação deve ser explícita, não inferida |
| **6** | Criação que outros adotaram | "defini padrão que o time passou a usar", "criei um processo de", "estruturei uma forma de trabalho" | Exige agência criadora + adoção por outros — não apenas fazer algo novo para si |

**Regra crítica para o LLM:** classificar Bloom com base no **nível mais alto com evidência explícita**, não no nível mais alto plausível. Se a resposta menciona "trade-off" mas não explicita critérios ou julgamento, classificar como Bloom 4, não 5.

---

### 7.3.2 — Guia de detecção: como o LLM identifica Dreyfus na resposta

`dreyfus_demonstrated` mede o nível de **autonomia e agência** demonstrado — tanto para respostas técnicas quanto comportamentais.

| Dreyfus | O que procurar | Sinais linguísticos | Distinção-chave |
|---|---|---|---|
| **1** Novice | Segue regras de outros; contexto guiado | "meu líder me pediu", "segui o tutorial", "fui orientado a", "no curso aprendi" | A decisão não foi do candidato |
| **2** Adv. Beginner | Experiência real, mas episódica e sem processo | "uma vez eu fiz isso", "quando me pediram para", sem reflexão sobre padrão | Fez algo real, mas não generalizou ou replicou intencionalmente |
| **3** Competent | Processo próprio deliberado; replica intencionalmente | "processo que desenvolvi", "passei a fazer assim porque funcionou", "minha abordagem é" | O candidato tem um método próprio consciente |
| **4** Proficient | Adapta ao contexto; vê padrões além das regras | "dependendo do contexto, faço X ou Y", "percebi que neste caso as regras normais não se aplicavam", "adaptei quando..." | A adaptação é explícita e baseada em leitura do contexto |
| **5** Expert | Cria para outros; intuitivo; sistematiza | "criei uma forma de trabalho que o time adotou", "ensinei meu time a", "defini padrão que", "implementei um ritual de" | O candidato é TRANSMISSOR, não apenas praticante |

**Para respostas comportamentais**, aplicar o mesmo critério adaptado:
- Dreyfus 1 comportamental: o comportamento foi aprendido de outros ou exigido externamente
- Dreyfus 3 comportamental: o candidato tem uma abordagem própria e consciente para situações daquele tipo
- Dreyfus 5 comportamental: o candidato criou sistemas, rituais ou dinâmicas que outros seguem

### 7.4 Camada 3 — Fórmulas de score por tipo de pergunta

#### Autodeclaração técnica — coleta e escala

Para perguntas **técnicas**, antes de responder a pergunta em texto, o candidato informa sua autopercepção de domínio da skill avaliada naquela pergunta. A coleta ocorre como parte do fluxo de triagem (chat ou interface):

```
"Em uma escala de 1 a 5, como você avalia seu domínio de {skill_name}?
  1 = Nunca usei / conheço apenas o básico teórico
  2 = Usei em projetos guiados ou acadêmicos
  3 = Trabalho com isso no dia a dia de forma independente
  4 = Referência técnica nesta skill na minha equipe
  5 = Especialista — já ensinei ou defini padrões com esta skill"
```

Esta autodeclaração vale **35% do score bruto da pergunta técnica**. O objetivo é criar uma dimensão de calibração — candidatos que se autodeclaram 5 mas demonstram Bloom 1 na resposta recebem penalidade por `inflation_detected`. Candidatos que se autodeclaram 2 mas demonstram Bloom 5 recebem bônus.

> Perguntas **comportamentais** não usam autodeclaração — a fórmula delas é baseada inteiramente no STAR + sinais do trait detectados pelo LLM.

#### Função de alinhamento Bloom (usada em ambos os tipos):

```python
def calcular_bloom_alinhamento(esperado: int, demonstrado: int) -> float:
    """
    Retorna 0.0–1.0. Positivo quando candidato atinge ou supera o esperado.
    A função é assimétrica intencionalmente: superar é bom, estar abaixo penaliza.
    """
    diff = esperado - demonstrado  # positivo = abaixo do esperado
    if diff <= 0:   return 1.00   # atingiu ou superou: score máximo desta componente
    if diff == 1:   return 0.70   # um nível abaixo: adequado com ressalvas
    if diff == 2:   return 0.40   # dois níveis abaixo: insuficiente
    return          0.15          # três ou mais níveis abaixo: muito abaixo do esperado
```

#### Para perguntas TÉCNICAS:

```python
# Inputs normalizados 0.0–1.0
autodeclaracao_norm   = autodeclaracao_raw / 5.0       # 1-5 do candidato, coletado antes da resposta
evidencias_tecnicas   = specificity_score / 10.0       # 1-10 extraído pelo LLM (specificidade das evidências)
bloom_alinhamento     = calcular_bloom_alinhamento(bloom_esperado, bloom_demonstrado)

score_bruto = (
    autodeclaracao_norm  * 0.35 +   # autodeclaração: sinaliza confiança e calibração
    evidencias_tecnicas  * 0.40 +   # evidências concretas: preditor mais forte
    bloom_alinhamento    * 0.25     # profundidade cognitiva demonstrada
) * 10.0  # normaliza para 0–10
```

#### Para perguntas COMPORTAMENTAIS (Big Five):

```python
# Inputs normalizados 0.0–1.0
STAR_score_norm       = STAR_score                              # 0.0–1.0 da Camada 1
sinais_trait_norm     = len(sinais_detectados) / max(len(sinais_esperados), 1)  # cobertura dos sinais esperados
bloom_alinhamento     = calcular_bloom_alinhamento(bloom_esperado, bloom_demonstrado)
# Dreyfus é capturado via bônus/penalidades na seção de ajustes abaixo

score_bruto = (
    STAR_score_norm    * 0.35 +   # estrutura da resposta: base de validade comportamental
    sinais_trait_norm  * 0.40 +   # cobertura dos sinais do trait: preditor mais forte
    bloom_alinhamento  * 0.25     # sofisticação da reflexão comportamental
) * 10.0  # normaliza para 0–10
```

#### Ajustes comuns (aplicados após score_bruto nos dois tipos):

```python
ajustes = 0.0

# Penalidades (já podem ter sido aplicadas na Camada 1, verificar duplicação)
if inflation_detected:
    ajustes -= 1.5

if len(sinais_detectados) == 0:
    ajustes -= 2.0  # nenhum sinal do trait alvo

if dreyfus_demonstrado < dreyfus_esperado - 1:
    ajustes -= 0.8  # maturidade comportamental/técnica abaixo do esperado

# Bônus
if bloom_demonstrado > bloom_esperado:
    ajustes += 0.6  # candidato supera expectativa cognitiva

if resultado_quantificado:
    ajustes += 0.5  # métrica concreta ("reduziu em 40%")

if len(sinais_detectados) > len(sinais_esperados):
    ajustes += 0.4  # sinais além dos esperados (riqueza comportamental)

if dreyfus_demonstrado > dreyfus_esperado:
    ajustes += 0.5  # maturidade acima do esperado

score_final_pergunta = max(0.0, min(10.0, score_bruto + ajustes))
```

### 7.5 Camada 4 — Composição do WSI Final

#### Score do Bloco Técnico:

```python
# Média simples entre skills técnicas — pesos iguais independente da skill
# num_perguntas_tecnicas varia por seniority e modo (ver tabelas 5.4 e 5.5)
WSI_tecnico = sum(score_pergunta_tecnica) / num_perguntas_tecnicas
```

#### Score do Bloco Comportamental:

```python
# ranked_traits = apenas os top-N traits SELECIONADOS para esta vaga/seniority/modo
# (top-2, top-3, top-4 ou top-5 conforme tabelas 5.4 e 5.5)
# Pesos PROPORCIONAIS ao score do trait no ranking do JD (F3)
soma_scores_traits = sum(trait["score_final"] for trait in ranked_traits)

WSI_comportamental = sum(
    score_pergunta_i * (trait_i["score_final"] / soma_scores_traits)
    for trait_i, score_pergunta_i in zip(ranked_traits, scores_comportamentais)
)
```

> `ranked_traits` contém apenas os traits que geraram perguntas — nunca todos os 5 em Compact para Junior/Pleno. Isso garante que o peso de cada trait reflete apenas o contexto avaliado.

#### Score do Bloco de Elegibilidade (quando configurado):

```python
# Bloco de Elegibilidade = perguntas binárias (sim/não) configuradas pelo recrutador
# Exemplos: "Você tem disponibilidade para viagens?", "Possui CNH B?"
# Cada pergunta de elegibilidade é obrigatória — qualquer "não" ativa gate G1 (reprovação automática)

# Score de elegibilidade (apenas informativo — o decisor real é o gate G1):
perguntas_elegibilidade = [p for p in perguntas if p["category"] == "eligibility"]
if perguntas_elegibilidade:
    # Todas as respostas devem ser "sim" para score = 10.0
    # Se todas sim: WSI_elegibilidade = 10.0
    # Se qualquer não: gate G1 já reprovou antes desta linha
    WSI_elegibilidade = 10.0 if all(r["answer"] == True for r in respostas_eligibilidade) else 0.0
else:
    WSI_elegibilidade = 0.0   # Bloco não configurado; peso será 0
```

#### Dict completo de pesos por senioridade (pós-normalização sem Bloco 2):

```python
# Fonte: tabela 5.6
# Pesos já normalizados para somar 1.0 quando sem elegibilidade
# Cálculo: peso_normalizado = peso_original / (peso_tecnico + peso_comportamental)

SENIORITY_WEIGHTS = {
    #                    técnico    comportamental   elegibilidade (quando configurado)
    "estagiario":    {"technical": 0.6875, "behavioral": 0.3125, "eligibility": 0.20},
    "junior":        {"technical": 0.6250, "behavioral": 0.3750, "eligibility": 0.20},
    "pleno":         {"technical": 0.6875, "behavioral": 0.3125, "eligibility": 0.20},
    "senior":        {"technical": 0.5625, "behavioral": 0.4375, "eligibility": 0.20},
    "lead":          {"technical": 0.4375, "behavioral": 0.5625, "eligibility": 0.20},
    "principal":     {"technical": 0.5000, "behavioral": 0.5000, "eligibility": 0.20},
    "diretor":       {"technical": 0.3125, "behavioral": 0.6875, "eligibility": 0.20},
    "vp_clevel":     {"technical": 0.2500, "behavioral": 0.7500, "eligibility": 0.20},
}

# Quando Bloco de Elegibilidade está configurado na vaga:
# os pesos acima são multiplicados por 0.80, e 0.20 vai para elegibilidade
# Exemplo Senior COM elegibilidade:
#   técnico = 0.5625 × 0.80 = 0.45
#   comportamental = 0.4375 × 0.80 = 0.35
#   elegibilidade = 0.20
```

#### Fórmula do WSI Final:

```python
def calcular_wsi_final(
    WSI_tecnico: float,
    WSI_comportamental: float,
    WSI_elegibilidade: float,
    seniority: str,
    tem_bloco_elegibilidade: bool
) -> float:

    weights = SENIORITY_WEIGHTS[seniority]

    if tem_bloco_elegibilidade:
        peso_tech  = weights["technical"]    * 0.80
        peso_comp  = weights["behavioral"]   * 0.80
        peso_elig  = weights["eligibility"]  # = 0.20
    else:
        peso_tech  = weights["technical"]    # já normalizado sem elig
        peso_comp  = weights["behavioral"]   # já normalizado sem elig
        peso_elig  = 0.0

    return (
        WSI_tecnico        * peso_tech  +
        WSI_comportamental * peso_comp  +
        WSI_elegibilidade  * peso_elig
    )
```

#### Tratamento de falha do extrator LLM (Camada 2):

```python
# Se o LLM retornar JSON inválido, timeout ou resposta fora do schema:
def handle_llm_failure(question_type: str, fallback_policy: str = "conservative") -> dict:
    if fallback_policy == "conservative":
        # Valores mínimos seguros — não pune candidato além do que o determinístico já capturou
        return {
            "star_components": None,        # usar os detectados na Camada 1
            "trait_signals_detected": [],
            "bloom_demonstrated": max(1, bloom_esperado - 2),  # assume 2 níveis abaixo
            "dreyfus_demonstrated": max(1, dreyfus_esperado - 1),
            "inflation_detected": False,
            "specificity_score": 3,         # penaliza levemente mas não zera
            "response_authentic": True,
            "_llm_fallback": True,          # flag para auditoria
            "_fallback_reason": "llm_extraction_failed"
        }
    # Política conservadora é o padrão — nunca descartar candidato por falha técnica do sistema
```

> **Regra**: falha do LLM nunca descarta ou reprova um candidato automaticamente. O sistema usa o fallback conservador e registra `_llm_fallback: true` para revisão humana.

---

#### Exemplos completos com distribuição adaptativa (nova metodologia v2)

**Exemplo 1 — Junior, modo Compact (5T + 2B), sem Bloco 2:**

```
Distribuição: 5 técnicas + 2 comportamentais (top-2 traits)
Seniority weights: técnico=62.5%, comportamental=37.5%

Scores técnicos (5 perguntas):
  Python:        6.5
  FastAPI:       7.2
  PostgreSQL:    8.0
  Git/CI:        5.8
  Docker basics: 6.0
  WSI_tecnico = (6.5 + 7.2 + 8.0 + 5.8 + 6.0) / 5 = 6.70

Scores comportamentais (top-2 traits):
  Conscienciosidade (score JD: 78.0, peso: 55.3%):  pergunta → 7.5
  Estabilidade/N↓  (score JD: 63.0, peso: 44.7%):  pergunta → 6.2
  WSI_comportamental = (7.5 × 0.553) + (6.2 × 0.447) = 4.148 + 2.771 = 6.92

WSI_final = (6.70 × 0.625) + (6.92 × 0.375)
          = 4.188 + 2.595
          = 6.78  → Classificação: Médio (Em avaliação)
```

**Exemplo 2 — Lead, modo Compact (3T + 4B), sem Bloco 2:**

```
Distribuição: 3 técnicas + 4 comportamentais (top-4 traits)
Seniority weights: técnico=43.75%, comportamental=56.25%

Scores técnicos (3 perguntas — Bloom 6, Dreyfus 5):
  System Design:    8.5
  Architecture:     9.0
  Tech Strategy:    8.2
  WSI_tecnico = (8.5 + 9.0 + 8.2) / 3 = 8.57

Scores comportamentais (top-4 traits):
  Abertura/O       (score JD: 85.0, peso: 29.8%):  pergunta → 9.1
  Extraversão/E    (score JD: 80.5, peso: 28.2%):  pergunta → 7.8
  Conscienciosidade(score JD: 70.0, peso: 24.6%):  pergunta → 8.5
  Estabilidade/N↓  (score JD: 49.5, peso: 17.4%):  pergunta → 7.2
  soma_scores = 285.0
  WSI_comportamental = (9.1×0.298) + (7.8×0.282) + (8.5×0.246) + (7.2×0.174)
                     = 2.712 + 2.200 + 2.091 + 1.253
                     = 8.256

WSI_final = (8.57 × 0.4375) + (8.256 × 0.5625)
          = 3.750 + 4.644
          = 8.39  → Classificação: Excelente (Aprovado)
```

#### Tabela de classificação e decisão:

| WSI Final | Classificação | Cor | Decisão automática |
|---|---|---|---|
| 9.0 – 10.0 | Excepcional | 🟢 Verde escuro | Aprovado direto — entrevista recomendada |
| 8.0 – 8.9 | Excelente | 🟢 Verde | Aprovado — revisão humana opcional |
| 7.0 – 7.9 | Alto | 🟡 Amarelo-verde | Aprovado condicional — revisão recomendada |
| 6.0 – 6.9 | Médio | 🟡 Amarelo | Em avaliação — compare com pool |
| 4.5 – 5.9 | Abaixo da média | 🟠 Laranja | Reprovado — salvo exceções do recrutador |
| 0.0 – 4.4 | Regular / Baixo | 🔴 Vermelho | Reprovado automático |

---

### 7.6 — Trace completo ponta-a-ponta: geração → avaliação → score

Este exemplo mostra o ciclo completo de **uma pergunta técnica** — desde a geração até o score final, ilustrando como Bloom e Dreyfus operam em cada fase.

**Contexto da vaga:**
```
Cargo: Engenheiro de Software Senior
Skill avaliada: Python
Senioridade: Senior → Bloom esperado: 5 (Avaliar), Dreyfus esperado: 4 (Proficiente)
Modo: Compact | Pesos: técnico=56.25%, comportamental=43.75%
```

---

**Passo 1 — F6: LLM gera a pergunta técnica**

Inputs enviados ao LLM (temp=0.7):
```
Skill: Python
Senioridade: Senior
Dreyfus: 4 — Proficient
Bloom: 5 — Avaliar
Contexto empresa: startup de fintech, time de 12 engenheiros
Responsabilidades JD: "liderança técnica de microsserviços críticos, decisões de arquitetura"
```

Pergunta gerada pelo LLM:
> *"Conte sobre uma decisão de arquitetura em Python — microsserviços, bibliotecas ou padrões — onde você precisou fazer trade-offs entre performance, manutenibilidade e custo operacional. Como você chegou à solução e o que faria diferente hoje?"*

Validação automática:
- ✅ Situacional (verbo no passado + situação real pedida)
- ✅ Não hipotética (sem "imagine" ou "como você faria se")
- ✅ Não revela resposta
- ✅ Comprimento: 43 palavras

Metadados persistidos com a pergunta: `bloom_level=5, dreyfus_level=4, expected_signals=["trade-off explícito", "critérios de decisão nomeados", "resultado mensurável", "reflexão crítica"]`

---

**Passo 2 — Coleta da autodeclaração e resposta (F7, runtime)**

O candidato informa antes de responder:
```
Autodeclaração Python: 4 de 5
("Referência técnica nesta skill na minha equipe")
```

Resposta do candidato (92 palavras):
> *"Na nossa plataforma de pagamentos, precisávamos processar 50k transações/hora. Avaliamos Celery vs. Ray para processamento assíncrono. Celery era mais maduro e com melhor suporte da equipe, mas o Ray oferecia melhor performance horizontal. Escolhi Celery porque o custo de onboarding do Ray para um time inexperiente era alto — estimei 3 meses de adaptação. Em produção, reduzimos a latência média de 800ms para 180ms. Se fizesse hoje, teria feito um PoC de 2 semanas com Ray antes de decidir, para ter dados reais de performance antes de assumir o custo de onboarding."*

---

**Passo 3 — Camada 1: STAR determinístico**

```
S — Situação: ✅ "plataforma de pagamentos, 50k transações/hora"
T — Tarefa:   ✅ "precisávamos processar" (responsabilidade implícita do time)
A — Ação:     ✅ "Avaliamos", "Escolhi Celery porque" (1ª pessoa, decisão própria)
R — Resultado: ✅ "reduzimos a latência de 800ms para 180ms" (dado quantificado)

STAR_score = (1×0.20) + (1×0.20) + (1×0.40) + (1×0.20) = 1.00

Penalidades:
  - Resposta 92 palavras: nenhuma (> 50 palavras)
  - Verbos em 1ª pessoa: ✅ presente
  - Resultado: ✅ com dado quantificado

Bônus:
  + 0.5 — resultado quantificado ("reduzimos de 800ms para 180ms")
  + 0.0 — sem segundo episódio
```

---

**Passo 4 — Camada 2: LLM extrator (temp=0.0)**

JSON retornado:
```json
{
  "star_components": {"situation": true, "task": true, "action": true, "result": true},
  "trait_signals_detected": [
    "trade-off explícito — trecho: 'Celery era mais maduro... mas o Ray oferecia melhor performance'",
    "critérios de decisão nomeados — trecho: 'custo de onboarding... estimei 3 meses de adaptação'",
    "resultado mensurável — trecho: 'reduzimos a latência média de 800ms para 180ms'",
    "reflexão crítica — trecho: 'Se fizesse hoje, teria feito um PoC...'"
  ],
  "trait_signals_absent": [],
  "bloom_demonstrated": 5,
  "bloom_label": "Avaliar",
  "dreyfus_demonstrated": 4,
  "dreyfus_label": "Proficient",
  "inflation_detected": false,
  "specificity_score": 9,
  "key_quote": "Escolhi Celery porque o custo de onboarding do Ray para um time inexperiente era alto — estimei 3 meses de adaptação",
  "response_authentic": true,
  "authenticity_concern": null
}
```

**Aplicação dos guias de detecção:**
- Bloom 5 confirmado: trade-off explícito com múltiplos critérios (performance × onboarding × custo) + julgamento justificado → evidência explícita, não apenas plausível
- Dreyfus 4 confirmado: decisão autônoma, vê além da regra técnica (performance) para considerar fator organizacional (onboarding), adaptação contextual explícita

---

**Passo 5 — Camada 3: fórmula técnica**

```python
# Inputs
autodeclaracao_norm  = 4 / 5.0 = 0.80
evidencias_tecnicas  = 9 / 10.0 = 0.90
bloom_alinhamento    = calcular_bloom_alinhamento(esperado=5, demonstrado=5)
                     = 1.00  # atingiu exatamente o esperado

score_bruto = (0.80 × 0.35) + (0.90 × 0.40) + (1.00 × 0.25) × 10.0
            = (0.280 + 0.360 + 0.250) × 10.0
            = 0.890 × 10.0
            = 8.90

# Ajustes
ajustes = 0.0
if inflation_detected: False → sem penalidade
if dreyfus_demonstrado (4) < dreyfus_esperado (4) - 1: False → sem penalidade
if bloom_demonstrado (5) > bloom_esperado (5): False → sem bônus Bloom
if resultado_quantificado: True → ajustes += 0.5  (Camada 1 também registrou)

score_final_pergunta = max(0.0, min(10.0, 8.90 + 0.5)) = 9.40
```

---

**Passo 6 — Contribuição no WSI Final (Compact, Senior)**

```
Esta pergunta (Python) contribui para:
  WSI_tecnico = média das 4 perguntas técnicas (esta = 9.40)

Supondo:  FastAPI: 7.8, PostgreSQL: 8.2, Docker: 6.5, Python: 9.4
  WSI_tecnico = (9.40 + 7.80 + 8.20 + 6.50) / 4 = 7.975

Pesos Senior sem elegibilidade: técnico=56.25%, comportamental=43.75%
  WSI_final = (7.975 × 0.5625) + (WSI_comportamental × 0.4375)
```

> Este trace demonstra como Bloom e Dreyfus saem de parâmetros abstratos e se tornam operadores concretos: definem a pergunta gerada, são detectados na resposta pelo LLM, e entram na fórmula via `bloom_alinhamento` e nos ajustes de Dreyfus — tudo de forma determinística e auditável.

---

## FASE 8 — Output, explicabilidade e auditabilidade

### 8.1 Relatório por pergunta (para recrutador)

```
─────────────────────────────────────────────
COMPETÊNCIA: Conscienciosidade (peso 36.6% no score comportamental)
Pergunta: "Conte sobre um projeto onde você precisou garantir qualidade técnica sob pressão..."
Score: 7.2 / 10
─────────────────────────────────────────────
✓ Estrutura STAR: Situação ✓ | Tarefa ✓ | Ação ✓ | Resultado ✗
✓ Sinais detectados:
  → "estabeleceu protocolo de revisão" — trecho: "criei um checklist antes de cada deploy"
  → "mediu impacto" — trecho: "reduziu bugs em produção em 40%"
✗ Sinais ausentes:
  → sem menção a processo de priorização entre entregas simultâneas

Nível cognitivo (Bloom):
  → Demonstrado: Analisar (4) | Esperado: Avaliar (5) → abaixo do esperado (−0.30 pts)
Maturidade comportamental (Dreyfus):
  → Demonstrado: Competente (3) | Esperado: Proficiente (4) → abaixo do esperado (−0.80 pts)
Inflação detectada: Não

Trecho chave: "Eu criei um protocolo de revisão que reduziu bugs em produção em 40%"
─────────────────────────────────────────────
```

### 8.2 Relatório para o candidato (transparência EU AI Act)

```
Sua resposta sobre gestão de qualidade foi avaliada em 7.2 de 10.

Pontos fortes identificados:
• Você descreveu um processo concreto que criou (checklist antes do deploy)
• Mencionou um resultado mensurável (40% de redução de bugs)

Pontos a desenvolver:
• A situação poderia estar mais contextualizada (período, tamanho do projeto)
• Não ficou claro como você priorizou entre múltiplas entregas simultâneas

Profundidade de análise: você demonstrou capacidade de analisar o que funcionou (Bloom 4).
Para o nível Senior, esperamos avaliação de trade-offs e justificativa de decisões (Bloom 5).
```

### 8.3 Perfil Big Five observado no candidato

Ao final de todas as respostas comportamentais, o sistema calcula o perfil Big Five **demonstrado** pelo candidato, comparando com o perfil ideal extraído do JD:

```json
{
  "candidate_big_five_observed": {
    "openness":          { "score_demonstrated": 78, "score_required": 74, "gap": +4 },
    "conscientiousness": { "score_demonstrated": 62, "score_required": 82, "gap": -20 },
    "stability":         { "score_demonstrated": 70, "score_required": 72, "gap": -2 }
  },
  "overall_behavioral_fit": "medium-high",
  "critical_gaps": ["conscientiousness"],
  "strengths": ["openness", "stability"]
}
```

---

## FASE 10 — Critérios de aprovação e reprovação

### 10.1 Decisão em duas camadas

A decisão final sobre um candidato opera em duas camadas independentes:

```
Camada de Gates (bloqueios absolutos)
        ↓ se nenhum gate for ativado
Camada de Score (aprovação por nota)
```

> Um candidato pode ter WSI Final 8.5 e ainda ser **reprovado** se um gate absoluto for ativado. Gates têm precedência sobre o score.

---

### 10.2 Gates absolutos (reprovação imediata, independente do score)

| Gate | Condição de ativação | Justificativa |
|---|---|---|
| **G1 — Elegibilidade** | Qualquer pergunta de elegibilidade obrigatória respondida negativamente | Ex: candidato não tem CNH exigida pela vaga |
| **G2 — Prompt Injection** | Resposta com tentativa detectada de manipular o sistema | Segurança — score = 0.0 nessa pergunta; se reincidente, reprovação da triagem |
| **G3 — Score técnico mínimo** | WSI_tecnico < 4.0 (qualquer modo) | Competência técnica abaixo do mínimo absoluto para a função |
| **G4 — Skill crítica zerada** | Qualquer skill marcada como `critical = true` com score < 3.0 | Competência inegociável para a vaga com performance inaceitável |
| **G5 — Resposta insuficiente** | ≥ 50% das perguntas com resposta < 30 palavras | Candidato não se engajou com a triagem de forma séria |
| **G6 — Inflação sistemática** | `inflation_detected = true` em ≥ 3 perguntas | Padrão de inflação — autodeclara expertise sem evidências repetidamente |

> **G4 — Como marcar skill como crítica:** no JD, o recrutador pode marcar até 2 skills como `critical`. Se não marcada, todas as skills têm peso igual e nenhuma tem gate individual.

---

### 10.3 Critérios de aprovação por score (após gates)

#### Thresholds de decisão automática

| Dimensão | Aprovado automático | Revisão manual | Reprovado automático |
|---|---|---|---|
| **WSI Final** | ≥ 7.5 | 6.0 – 7.4 | < 6.0 |
| **WSI Técnico** | ≥ 7.0 | 5.5 – 6.9 | < 5.5 |
| **WSI Comportamental** | ≥ 7.0 | 5.5 – 6.9 | < 5.5 |
| **Gap Big Five crítico** | Nenhum gap > 20pts | Gap 15–20pts em top-1 trait | Gap > 20pts no trait de maior peso |

#### Lógica de decisão completa

```python
def calcular_decisao(candidato: CandidatoWSI) -> Decisao:

    # CAMADA 1: Gates absolutos
    for gate in GATES_ABSOLUTOS:
        if gate.ativado(candidato):
            return Decisao(
                resultado="REPROVADO",
                motivo=gate.nome,
                gate_ativado=True,
                revisao_humana=False
            )

    # CAMADA 2: Score Final
    wsi = candidato.wsi_final

    if wsi >= 7.5 and wsi_tecnico >= 6.5 and wsi_comportamental >= 6.5:
        return Decisao(resultado="APROVADO", confianca="alta", revisao_humana=False)

    if wsi >= 7.0 and wsi_tecnico >= 5.5:
        return Decisao(resultado="APROVADO", confianca="media", revisao_humana=True)

    if wsi >= 6.0:
        # Verificar gap em trait crítico
        gap_critico = max(
            trait.score_required - trait.score_demonstrated
            for trait in candidato.big_five_ranked[:1]  # top-1 trait
        )
        if gap_critico > 20:
            return Decisao(resultado="REPROVADO", motivo="gap_trait_critico", revisao_humana=True)
        return Decisao(resultado="REVISAO", confianca="baixa", revisao_humana=True)

    # wsi < 6.0
    return Decisao(resultado="REPROVADO", confianca="alta", revisao_humana=False)
```

---

### 10.4 Matriz de decisão completa (visão do consultor)

| WSI Final | WSI Técnico | WSI Comportamental | Gap trait top-1 | Gate ativado | Decisão final |
|---|---|---|---|---|---|
| ≥ 7.5 | ≥ 6.5 | ≥ 6.5 | ≤ 15pts | Não | ✅ Aprovado (alta confiança) |
| ≥ 7.5 | ≥ 6.5 | 5.5–6.4 | ≤ 20pts | Não | ✅ Aprovado (revisão opcional) |
| 7.0–7.4 | ≥ 5.5 | ≥ 5.5 | ≤ 20pts | Não | ✅ Aprovado (revisão recomendada) |
| 6.0–6.9 | ≥ 5.5 | ≥ 5.5 | ≤ 15pts | Não | ⚠️ Em avaliação (revisão obrigatória) |
| 6.0–6.9 | ≥ 5.5 | ≥ 5.5 | > 20pts | Não | ❌ Reprovado (gap comportamental crítico) |
| 5.5–5.9 | qualquer | qualquer | qualquer | Não | ❌ Reprovado |
| < 5.5 | qualquer | qualquer | qualquer | Não | ❌ Reprovado |
| qualquer | < 4.0 | qualquer | qualquer | Não | ❌ Reprovado (gate G3) |
| qualquer | qualquer | qualquer | qualquer | Sim | ❌ Reprovado (gate ativo) |

---

### 10.5 Sinais de alerta (red flags) para o consultor

Mesmo candidatos aprovados podem ter sinais de alerta que o consultor deve considerar. Esses sinais não reprovam automaticamente, mas são destacados no relatório:

| Código | Sinal | Descrição | Nível |
|---|---|---|---|
| RF-01 | Inflação isolada | `inflation_detected = true` em 1–2 perguntas | Médio |
| RF-02 | Gap de Bloom sistemático | Bloom demonstrado < esperado em ≥ 3 perguntas | Alto |
| RF-03 | Gap de Dreyfus em técnica | Dreyfus técnico demonstrado < esperado em ≥ 2 skills | Alto |
| RF-04 | Assimetria técnica/comportamental | Diferença > 2.0 pontos entre WSI_tecnico e WSI_comportamental | Médio |
| RF-05 | Sem resultado em STAR | R ausente em ≥ 50% das respostas | Médio |
| RF-06 | Respostas curtas consistentes | 30–60 palavras em ≥ 3 perguntas | Médio |
| RF-07 | Trait crítico abaixo | Score_demonstrado < score_required − 15 no top-1 trait | Alto |
| RF-08 | Autenticidade questionável | `response_authentic = false` em qualquer resposta | Alto |

---

## FASE 11 — Relatório completo do consultor (template)

### 11.1 Propósito e audiência

O relatório do consultor é o **documento de decisão** gerado ao final de cada triagem WSI. Ele tem dois objetivos:

1. **Apoiar a decisão** de aprovação/reprovação com dados estruturados e cruzamento explícito com o perfil da vaga
2. **Registrar rastreabilidade** para auditoria (EU AI Act, LGPD) — toda decisão tem justificativa documentada e evidências textuais

**Audiência:** Consultor/recrutador WeDOTalent e, quando aplicável, o gestor da vaga do cliente.

---

### 11.2 Estrutura completa do relatório

```
═══════════════════════════════════════════════════════════════════
RELATÓRIO DE TRIAGEM WSI — AVALIAÇÃO DE CANDIDATO
WeDOTalent · Powered by LIA
Gerado em: {data_hora} | Versão metodologia: 2.0
═══════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 1 — CABEÇALHO: VAGA E CANDIDATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VAGA
  Título:            {titulo_cargo}
  Empresa / Cliente: {nome_empresa}
  Senioridade:       {senioridade} ({dreyfus_tecnico_esperado} Dreyfus técnico | Bloom {bloom_esperado})
  Modo de triagem:   {Compact 7q | Full 12q}
  JD Quality Score:  {score_qualidade_jd}/100

CANDIDATO
  Nome:             {nome_candidato}
  Canal de triagem: {WhatsApp | Web chat}
  Data da triagem:  {data_hora_inicio} → {data_hora_fim}
  Tempo total:      {tempo_total_minutos} minutos
  ID da avaliação:  {uuid}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 2 — RESULTADO E DECISÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  WSI FINAL:  {wsi_final}/10  →  [{APROVADO | EM AVALIAÇÃO | REPROVADO}]

  ┌─────────────────────────────┐
  │  DECISÃO: APROVADO          │   ← ou: EM AVALIAÇÃO / REPROVADO
  │  Confiança: Alta            │   ← ou: Média / Baixa
  │  Revisão humana: Não        │   ← ou: Recomendada / Obrigatória
  └─────────────────────────────┘

  Motivo da decisão (quando EM AVALIAÇÃO ou REPROVADO):
  → {motivo legível: ex: "WSI Comportamental abaixo do threshold (5.2 < 5.5)"}
  → {gate ativado, se houver: ex: "Gate G3: WSI Técnico = 3.8 < 4.0"}

  Gates verificados:
  G1 Elegibilidade:        ✓ Não ativado
  G2 Prompt Injection:     ✓ Não detectado
  G3 WSI Técnico mínimo:   ✓ {wsi_tecnico} ≥ 4.0
  G4 Skill crítica:        ✓ Não marcada / {skill}: {score} ≥ 3.0
  G5 Engajamento mínimo:   ✓ {N}% de respostas com ≥ 30 palavras
  G6 Inflação sistemática: ✓ {n_inflacoes} ocorrência(s) detectada(s)

  Sinais de alerta: {lista de red flags detectados, ou "Nenhum"}
  → RF-02: Gap de Bloom sistemático (3 de 7 perguntas abaixo do esperado)
  → RF-07: Trait Conscienciosidade: demonstrado 55 vs. requerido 82 (gap −27pts)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 3 — VISÃO GERAL DOS SCORES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Bloco Técnico       WSI: {wsi_tecnico}/10   Peso: {peso_tecnico}%
  Bloco Comportamental WSI: {wsi_comp}/10    Peso: {peso_comp}%
  ─────────────────────────────────────────
  WSI FINAL                 {wsi_final}/10

  Composição visual:
  Técnico      [████████░░] {wsi_tecnico}/10
  Comportamental [███████░░░] {wsi_comp}/10
  FINAL        [████████░░] {wsi_final}/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 4 — CRUZAMENTO: COMPETÊNCIAS TÉCNICAS (vaga × candidato)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Perfil técnico exigido pela vaga | Senioridade: {senioridade}
  Dreyfus esperado: {dreyfus_esperado} — {dreyfus_label}
  Bloom esperado:   {bloom_esperado} — {bloom_label}

  ┌──────────────────────┬──────────┬────────────┬────────────┬───────────┬────────┐
  │ Skill                │ Crítica? │ Score vaga │ Score cand.│ Gap       │ Status │
  ├──────────────────────┼──────────┼────────────┼────────────┼───────────┼────────┤
  │ Python               │ ✓ Sim    │ Dreyfus 4  │ Dreyfus 4  │ 0        │ ✅ OK  │
  │ FastAPI              │ ✓ Sim    │ Dreyfus 4  │ Dreyfus 3  │ −1 nível  │ ⚠️ Gap │
  │ PostgreSQL           │ Não      │ Dreyfus 3  │ Dreyfus 4  │ +1 nível  │ ✅ Sup │
  │ Docker               │ Não      │ Dreyfus 3  │ Dreyfus 2  │ −1 nível  │ ⚠️ Gap │
  └──────────────────────┴──────────┴────────────┴────────────┴───────────┴────────┘

  Bloom demonstrado por skill:
  ┌──────────────────────┬──────────────┬──────────────────┬──────────────┐
  │ Skill                │ Bloom esper. │ Bloom demonstrado │ Alinhamento  │
  ├──────────────────────┼──────────────┼──────────────────┼──────────────┤
  │ Python               │ 5 (Avaliar)  │ 5 (Avaliar)      │ ✅ Alinhado  │
  │ FastAPI              │ 5 (Avaliar)  │ 4 (Analisar)     │ ⚠️ −1 nível  │
  │ PostgreSQL           │ 4 (Analisar) │ 5 (Avaliar)      │ ✅ Superior  │
  │ Docker               │ 4 (Analisar) │ 3 (Aplicar)      │ ⚠️ −1 nível  │
  └──────────────────────┴──────────────┴──────────────────┴──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 5 — CRUZAMENTO: PERFIL BIG FIVE (vaga × candidato)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Perfil comportamental extraído do JD (ranking por relevância):

  ┌──────────────────────────┬──────────┬──────────┬────────┬──────────┬────────────┐
  │ Trait                    │ Rank JD  │ Req. JD  │ Cand.  │ Gap      │ Status     │
  ├──────────────────────────┼──────────┼──────────┼────────┼──────────┼────────────┤
  │ Estabilidade Emocional   │ 1 (36.6%)│ 72       │ 70     │ −2       │ ✅ Atende  │
  │ Abertura à Experiência   │ 2 (36.1%)│ 74       │ 78     │ +4       │ ✅ Supera  │
  │ Conscienciosidade        │ 3 (27.3%)│ 82       │ 55     │ −27 ⚠️   │ ❌ Gap     │
  │ Amabilidade              │ — (match)│ 50       │ 58     │ +8       │ ✅ Atende  │
  │ Extraversão              │ — (match)│ 45       │ 42     │ −3       │ ✅ Atende  │
  └──────────────────────────┴──────────┴──────────┴────────┴──────────┴────────────┘

  Legenda: Req. JD = score do trait no ranking do JD | Cand. = score observado nas respostas
  Gap positivo = candidato supera o requerido | Gap negativo = candidato abaixo do requerido

  Dreyfus comportamental:
  ┌──────────────────────────┬──────────────────┬──────────────────┬──────────────┐
  │ Trait                    │ Dreyfus esperado │ Dreyfus demonstr.│ Alinhamento  │
  ├──────────────────────────┼──────────────────┼──────────────────┼──────────────┤
  │ Estabilidade Emocional   │ 4 (Proficiente)  │ 4 (Proficiente)  │ ✅ Alinhado  │
  │ Abertura à Experiência   │ 4 (Proficiente)  │ 5 (Expert)       │ ✅ Superior  │
  │ Conscienciosidade        │ 4 (Proficiente)  │ 3 (Competente)   │ ⚠️ −1 nível  │
  └──────────────────────────┴──────────────────┴──────────────────┴──────────────┘

  Bloom comportamental:
  ┌──────────────────────────┬──────────────┬──────────────────┬──────────────┐
  │ Trait                    │ Bloom esper. │ Bloom demonstr.  │ Alinhamento  │
  ├──────────────────────────┼──────────────┼──────────────────┼──────────────┤
  │ Estabilidade Emocional   │ 5 (Avaliar)  │ 5 (Avaliar)      │ ✅ Alinhado  │
  │ Abertura à Experiência   │ 5 (Avaliar)  │ 6 (Criar)        │ ✅ Superior  │
  │ Conscienciosidade        │ 5 (Avaliar)  │ 4 (Analisar)     │ ⚠️ −1 nível  │
  └──────────────────────────┴──────────────┴──────────────────┴──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 6 — ANÁLISE DETALHADA POR PERGUNTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ─── BLOCO TÉCNICO ────────────────────────────────────────────────

  [P1] Python — Score: 8.4/10
  Pergunta: "Conte sobre uma decisão de arquitetura Python onde você fez
             trade-offs entre performance, manutenibilidade e custo..."
  STAR: S✓ T✓ A✓ R✓ | Bloom demonstrado: 5 (Avaliar) ✅ | Dreyfus: 4 ✅
  Sinais detectados: "avaliou 3 opções de ORM", "mediu latência em produção"
  Trecho chave: "Testei SQLAlchemy e Tortoise ORM e escolhi com base em benchmarks próprios"
  Ajustes: +0.5 resultado quantificado | sem penalidades
  ─────────────────────────────────────────────────────────────────

  [P2] FastAPI — Score: 6.1/10
  Pergunta: "Descreva um projeto FastAPI onde você garantiu performance..."
  STAR: S✓ T✓ A✓ R✗ | Bloom demonstrado: 4 (Analisar) ⚠️ | Dreyfus: 3 ⚠️
  Sinais detectados: "configurou middleware de autenticação"
  Sinais ausentes: "sem menção a resultado mensurável", "sem comparação de abordagens"
  Trecho chave: "Configurei o JWT middleware e funcionou bem"
  Ajustes: −0.8 Dreyfus abaixo | −0.5 ausência de resultado
  ─────────────────────────────────────────────────────────────────

  [P3–P4] ... (idem para demais skills)

  ─── BLOCO COMPORTAMENTAL ─────────────────────────────────────────

  [P5] Estabilidade Emocional — Score: 7.8/10 (peso: 36.6%)
  Pergunta: "Descreva uma situação em que o escopo mudou radicalmente..."
  STAR: S✓ T✓ A✓ R✓ | Bloom: 5 ✅ | Dreyfus comportamental: 4 ✅
  Sinais detectados: "manteve calma ao comunicar mudanças", "reestruturou sprint em 24h"
  Trecho chave: "Quando o cliente mudou o escopo na véspera do release, reuni o time..."
  ─────────────────────────────────────────────────────────────────

  [P6] Abertura à Experiência — Score: 8.6/10 (peso: 36.1%)
  Pergunta: "Conte sobre uma decisão técnica onde você questionou..."
  STAR: S✓ T✓ A✓ R✓ | Bloom: 6 ✅ Superior | Dreyfus: 5 ✅ Superior
  Sinais detectados: "questionou abordagem estabelecida", "construiu prova de conceito",
                     "apresentou resultados e convenceu o time"
  Trecho chave: "Propus trocar o ORM por queries raw em endpoints críticos e reduzi latência em 60%"
  Ajustes: +0.6 Bloom superior | +0.5 dado quantificado
  ─────────────────────────────────────────────────────────────────

  [P7] Conscienciosidade — Score: 5.2/10 (peso: 27.3%)
  Pergunta: "Conte sobre um projeto onde você garantiu qualidade técnica..."
  STAR: S✓ T✗ A✓ R✗ | Bloom: 4 ⚠️ | Dreyfus comportamental: 3 ⚠️
  Sinais detectados: "mencionou checklist"
  Sinais ausentes: "sem processo documentado", "sem métrica de qualidade", "sem resultado"
  Trecho chave: "Sempre tenho um checklist antes de fazer deploy"
  Ajustes: −0.8 Dreyfus abaixo | −0.5 ausência de resultado | −0.5 STAR incompleto
  ⚠️ Red Flag RF-07: gap de 27pts no trait de maior peso (C: 55 vs 82 requerido)
  ─────────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 7 — ANÁLISE DE GAPS E RECOMENDAÇÕES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PONTOS FORTES DO CANDIDATO:
  ✓ Abertura à Experiência acima do requerido (+4pts, Dreyfus 5, Bloom 6)
  ✓ Estabilidade Emocional alinhada (gap −2pts, dentro da margem)
  ✓ Python: proficiência demonstrada condizente com o nível Senior
  ✓ Respostas longas e específicas (média {N} palavras por resposta)

  GAPS IDENTIFICADOS:
  ⚠️ [ALTO]  Conscienciosidade: gap −27pts — traço mais crítico para a vaga
             candidato demonstra Dreyfus 3 em contexto que requer Dreyfus 4
             Recomendação: validar com exemplos concretos na entrevista presencial
  ⚠️ [MÉDIO] FastAPI: Dreyfus 3 vs. esperado 4 — skill marcada como crítica
             Bloom 4 vs. esperado 5 — candidato analisa mas não avalia trade-offs
             Recomendação: teste técnico prático ou pair programming
  ⚠️ [BAIXO] Docker: Dreyfus 2 vs. esperado 3 — skill não-crítica, treinavél

  PERGUNTAS RECOMENDADAS PARA ENTREVISTA PRESENCIAL (baseadas nos gaps):
  1. [Conscienciosidade] "Descreva como você garante a qualidade técnica em
     entregas de alta pressão — quais são seus critérios inegociáveis e como
     você mede se estão sendo cumpridos?"
  2. [FastAPI — técnica] "Como você abordaria a otimização de endpoints lentos
     em uma API FastAPI com alto volume de requisições?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 8 — PERFIL RADAR (resumo visual para o consultor)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  TÉCNICO por skill (score /10):
  Python       ████████░░  8.4  ✅
  FastAPI      ██████░░░░  6.1  ⚠️
  PostgreSQL   █████████░  9.0  ✅
  Docker       ████░░░░░░  4.8  ⚠️

  COMPORTAMENTAL por trait (score /10 | gap vs. requerido):
  Estabilidade ████████░░  7.8  req:72  gap:−2   ✅
  Abertura     █████████░  8.6  req:74  gap:+4   ✅
  Conscienc.   █████░░░░░  5.2  req:82  gap:−27  ❌

  NOTA FINAL:  ████████░░  7.2  →  EM AVALIAÇÃO (revisão recomendada)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEÇÃO 9 — AUDITABILIDADE E RASTREABILIDADE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ID da triagem:          {uuid}
  Versão metodologia:     WSI v2.0
  Modelo LLM extração JD: {model_name} @ {model_version}
  Modelo LLM geração Qs:  {model_name} @ {model_version}
  Modelo LLM avaliação:   {model_name} @ {model_version}
  Temperatura extração:   0.1
  Temperatura avaliação:  0.0
  Data da triagem:        {ISO 8601}
  Hash das respostas:     {sha256 das respostas bruta — integridade}

  Este relatório foi gerado automaticamente pelo sistema LIA (WeDOTalent).
  A decisão final é responsabilidade do consultor humano.
  Conforme EU AI Act (High-Risk AI) — rastreabilidade completa disponível.

═══════════════════════════════════════════════════════════════════
FIM DO RELATÓRIO
═══════════════════════════════════════════════════════════════════
```

---

### 11.3 Campos obrigatórios para geração do relatório

Todo relatório deve ser gerado a partir do seguinte objeto de dados:

```json
{
  "report_id": "uuid",
  "generated_at": "ISO 8601",
  "methodology_version": "2.0",

  "vacancy": {
    "id": "uuid",
    "title": "string",
    "company": "string",
    "seniority": "string",
    "mode": "compact | full",
    "jd_quality_score": 0-100,
    "bloom_expected": 1-6,
    "dreyfus_technical_expected": 1-5,
    "dreyfus_behavioral_expected": 1-5,
    "technical_skills": [
      { "name": "string", "critical": true|false, "dreyfus_required": 1-5 }
    ],
    "big_five_ranked": [
      { "rank": 1, "trait": "stability", "score_required": 72, "weight": 0.366 }
    ]
  },

  "candidate": {
    "id": "uuid",
    "name": "string",
    "screening_duration_minutes": 0,
    "response_count": 7
  },

  "scores": {
    "wsi_final": 0.0-10.0,
    "wsi_technical": 0.0-10.0,
    "wsi_behavioral": 0.0-10.0,
    "weight_technical": 0.0-1.0,
    "weight_behavioral": 0.0-1.0
  },

  "decision": {
    "result": "APROVADO | EM_AVALIACAO | REPROVADO",
    "confidence": "alta | media | baixa",
    "human_review_required": true|false,
    "reason": "string",
    "gate_triggered": "G1|G2|G3|G4|G5|G6 | null"
  },

  "red_flags": ["RF-01", "RF-07"],

  "questions": [
    {
      "order": 1,
      "block": 3,
      "category": "technical",
      "skill": "Python",
      "trait": null,
      "question_text": "string",
      "candidate_response": "string",
      "score": 0.0-10.0,
      "star": { "situation": true, "task": true, "action": true, "result": true },
      "bloom_expected": 5,
      "bloom_demonstrated": 5,
      "dreyfus_expected": 4,
      "dreyfus_demonstrated": 4,
      "signals_detected": ["string"],
      "signals_absent": ["string"],
      "inflation_detected": false,
      "key_quote": "string",
      "adjustments": ["+0.5 resultado quantificado"]
    }
  ],

  "big_five_crossref": [
    {
      "trait": "stability",
      "rank": 1,
      "weight": 0.366,
      "score_required": 72,
      "score_demonstrated": 70,
      "gap": -2,
      "bloom_expected": 5,
      "bloom_demonstrated": 5,
      "dreyfus_expected": 4,
      "dreyfus_demonstrated": 4,
      "status": "OK | GAP | SUPERADO"
    }
  ],

  "interview_recommendations": [
    { "area": "conscientiousness", "question": "string" },
    { "area": "fastapi", "question": "string" }
  ],

  "audit": {
    "llm_jd_model": "string",
    "llm_question_model": "string",
    "llm_evaluation_model": "string",
    "responses_hash": "sha256",
    "regulation": "EU AI Act High-Risk | LGPD"
  }
}
```

---

### 11.4 Regras de geração do relatório

| Regra | Descrição |
|---|---|
| **Sempre gerado** | O relatório é gerado independente da decisão — aprovados e reprovados têm relatório completo |
| **Imutável após geração** | O relatório não pode ser editado retroativamente. Ajustes do consultor geram uma versão 2 com flag `human_override = true` |
| **Hash de integridade** | As respostas brutas do candidato são hasheadas (SHA-256) e incluídas no relatório para garantir que não foram alteradas |
| **Prazo de retenção** | Conforme LGPD: dados do candidato são anonimizados após 2 anos se não contratado; relatório de scoring é retido por 5 anos para auditoria |
| **Geração de perguntas para entrevista** | Sempre gerar 2 perguntas recomendadas focadas nos maiores gaps identificados — formato CBI, calibradas para aprofundamento |

---

## FASE 12 — Fluxo completo integrado

```
┌─────────────────────────────────────────────────────────────────────┐
│ JOB CREATION (ocorre uma vez por vaga)                              │
│                                                                     │
│  F1: Recrutador preenche JD                                         │
│       ↓ Score de qualidade ≥ 50                                     │
│  F2: LLM extrai Big Five do JD                                      │
│       ↓ JSON com score + evidências por trait                       │
│  F3: Fórmula calcula ranking ponderado                              │
│       (0.40 LLM + 0.35 Prior + 0.25 Boost seniority)               │
│       ↓ Top-3 (Compact) ou Top-5 (Full) traits selecionados         │
│  F4: LLM gera perguntas (uma por skill técnica + uma por trait)     │
│       ↓ Validação automática de cada pergunta                       │
│  F5: Recrutador revisa, edita ou regenera perguntas                 │
│       ↓ Perguntas aprovadas persistidas na vaga                     │
│  Vaga ativada para triagem                                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ TRIAGEM (ocorre para cada candidato)                                │
│                                                                     │
│  F6: Candidato recebe e responde as perguntas (chat/WhatsApp)       │
│       ↓ Cada resposta processada ao receber                         │
│  F7: Para cada resposta:                                            │
│       Camada 1: STAR + penalidades automáticas (determinístico)     │
│       Camada 2: LLM extrai sinais, Bloom e Dreyfus demonstrados     │
│       Camada 3: Fórmula calcula score por tipo de pergunta          │
│       ↓ score_final_pergunta (0–10)                                 │
│  F8: Após todas as respostas:                                       │
│       WSI_tecnico = média simples das perguntas técnicas            │
│       WSI_comportamental = média ponderada pelo ranking de traits   │
│       WSI_final = WSI_tecnico × peso_seniority + WSI_comp × peso   │
│       ↓ WSI_final (0–10) + classificação                            │
│  F9: Output:                                                        │
│       Relatório por pergunta (recrutador)                           │
│       Feedback explicável (candidato)                               │
│       Perfil Big Five observado vs. requerido                       │
│       Gaps Bloom e Dreyfus identificados                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Referências bibliográficas

| Referência | Aplicação no sistema |
|---|---|
| Barrick, M. R., & Mount, M. K. (1991). The Big Five personality dimensions and job performance. *Personnel Psychology, 44*, 1–26. | Prior por arquétipo de cargo; validade preditiva por tipo de função |
| Bloom, B. S. et al. (1956). *Taxonomy of Educational Objectives.* | Calibração do nível cognitivo de perguntas e avaliação de respostas; calibração de sofisticação de reflexão comportamental |
| Campion, M. A., Pursell, E. D., & Brown, B. K. (1994). Structured interviewing: Raising the psychometric properties of the employment interview. *Personnel Psychology, 47*, 25–42. | Critérios de qualidade de perguntas; peso STAR; estrutura de entrevista padronizada |
| Costa, P. T., & McCrae, R. R. (1992). *NEO PI-R Professional Manual.* | Definição canônica dos 5 traits e seus facets; rubric de extração Big Five do JD |
| Dreyfus, H. L., & Dreyfus, S. E. (1986). *Mind over Machine.* | Calibração de proficiência técnica; maturidade comportamental; distribuição adaptativa de perguntas por senioridade |
| Flanagan, J. C. (1954). The critical incident technique. *Psychological Bulletin, 51*, 327–358. | Base do formato CBI situacional |
| Goldberg, L. R. (1992). The development of markers for the Big-Five factor structure. *Psychological Assessment, 4*, 26–42. | Fundamento para 3 perguntas direcionadas como suficientes para triagem Big Five; justificativa do modo Compact |
| Hogan, J., & Holland, B. (2003). Using theory to evaluate personality and job-performance relations. *Journal of Applied Psychology, 88*, 100–112. | Mapeamento cargo × personalidade |
| Huffcutt, A. I., et al. (2001). Identification and meta-analytic assessment of psychological constructs measured in employment interviews. *Journal of Applied Psychology, 86*, 897–913. | Justificativa para remoção de perguntas de fit cultural |
| Janz, T. (1982). Initial comparisons of patterned behavior description interviews versus unstructured interviews. *Journal of Applied Psychology, 67*, 577–580. | Peso STAR; validade preditiva do CBI |
| McClelland, D. C. (1973). Testing for competence rather than for "intelligence." *American Psychologist, 28*, 1–14. | Fundamento do modelo CBI |
| O*NET Resource Center (2024). *O*NET Occupational Database.* onetcenter.org | Prior por arquétipo de cargo; perfis de personalidade por ocupação |
| Pennebaker, J. W., Francis, M. E., & Booth, R. J. (2001). *Linguistic Inquiry and Word Count.* | Mapeamento léxico para extração Big Five; análise de categorias linguísticas no JD |
| Rivera, L. A. (2012). Hiring as cultural matching: The case of elite professional service firms. *American Sociological Review, 77*, 999–1022. | Risco de viés em avaliações de "fit cultural" |
| Schmidt, F. L., & Hunter, J. E. (1998). The validity and utility of selection methods in personnel psychology. *Psychological Bulletin, 124*, 262–274. | Validade preditiva de CBI (0.51); retorno marginal decrescente de perguntas comportamentais; base para distribuição adaptativa |
| Tett, R. P., & Guterman, H. A. (2000). Situation trait relevance, trait expression, and cross-situational consistency. *Journal of Research in Personality, 34*, 397–423. | Trait Activation Theory — cenários ativadores por trait; design de perguntas comportamentais |
| Tett, R. P., Jackson, D. N., & Rothstein, M. (1994). Personality measures as predictors of job performance: A meta-analytic review. *Personnel Psychology, 47*, 157–172. | Validade preditiva por trait em contexto organizacional |

---

*Documento gerado em: 2026-03-24*  
*Próxima revisão recomendada: após ciclo de validação com dados reais de triagem*
