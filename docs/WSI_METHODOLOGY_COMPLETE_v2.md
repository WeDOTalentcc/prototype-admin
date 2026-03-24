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

| Fase | Nome | Quando ocorre | Quem executa |
|---|---|---|---|
| **F1** | Criação e qualidade do JD | Job creation | Recrutador + sistema |
| **F2** | Extração do perfil Big Five | Job creation | LLM + fórmula determinística |
| **F3** | Ranking de traits | Job creation | Fórmula determinística |
| **F4** | Geração de perguntas | Job creation | LLM (por pergunta) |
| **F5** | Revisão humana | Job creation | Recrutador |
| **F6** | Triagem do candidato | Screening runtime | Chat/WhatsApp |
| **F7** | Avaliação das respostas | Screening runtime | Determinístico + LLM extrator |
| **F8** | Score WSI final | Screening runtime | Fórmula determinística |
| **F9** | Output e explicabilidade | Screening runtime | Sistema |

---

## FASE 1 — Criação e qualidade do Job Description

### 1.1 Inputs obrigatórios e opcionais

| Campo | Obrigatoriedade | Impacto se ausente |
|---|---|---|
| Título do cargo | Obrigatório | Sem título, senioridade e arquétipo não são inferidos |
| Senioridade | Obrigatório | Calibração de Bloom, Dreyfus e pesos de score impossível |
| Skills técnicas (lista) | Obrigatório (mín. 3) | Abaixo de 3, perguntas técnicas ficam genéricas |
| Responsabilidades (texto) | Obrigatório (mín. 3) | Principal fonte para extração Big Five via LLM |
| Competências comportamentais esperadas | Recomendado (mín. 2) | Enriquece a prior de extração Big Five |
| Descrição completa (texto livre) | Recomendado | Aumenta qualidade da extração lexical |
| Departamento / Área | Recomendado | Calibra arquétipo de cargo na prior |
| Setor da empresa | Opcional | Melhora precisão do prior O*NET |

### 1.2 Limites de competências processadas pelo WSI

| Tipo | Mínimo | Máximo processado pelo WSI |
|---|---|---|
| Skills técnicas | 3 | 7 (compact) ou 7 (full) |
| Traits comportamentais | — | 3 (compact) ou 5 (full) — extraídos automaticamente |

Skills além do máximo são armazenadas na vaga mas não geram perguntas WSI.

### 1.3 Score de qualidade do JD (gate de aprovação)

Antes de prosseguir para a extração Big Five, o sistema calcula um score de qualidade:

```
Score_JD = (responsabilidades ≥ 3  → 30pts)
         + (skills técnicas ≥ 3    → 30pts)
         + (comp. comportamentais ≥ 2 → 25pts)
         + (senioridade definida   → 10pts)
         + (descrição presente     → 5pts)

Score_JD ≥ 70  → prossegue normalmente
Score_JD 50–69 → prossegue com aviso de qualidade (flag: jd_quality = "low")
Score_JD < 50  → bloqueado; sistema solicita enriquecimento do JD
```

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

## FASE 5 — Distribuição de perguntas por modo

### 5.1 Modos disponíveis

| Modo | Total de perguntas | Bloco Técnico | Bloco Comportamental | Uso recomendado |
|---|---|---|---|---|
| **Compact** | 7 | 4 técnicas | 3 comportamentais (top-3 traits) | Triagem inicial, alto volume, posições júnior-pleno |
| **Full** | 12 | 7 técnicas | 5 comportamentais (todos os 5 traits) | Triagem aprofundada, posições sênior+, roles críticos |

### 5.2 Pesos do WSI Final por senioridade (sem alteração no número de perguntas)

O número de perguntas é fixo por modo. O que varia por senioridade são os **pesos** de cada bloco no score final:

| Senioridade | Peso Bloco Técnico | Peso Bloco Comportamental | Justificativa |
|---|---|---|---|
| Estagiário | 55% | 25% | Capacidade técnica inicial é o gate principal |
| Junior | 50% | 30% | Técnica domina, comportamental começa a importar |
| Pleno | 55% | 25% | Autonomia técnica é o diferencial nesta banda |
| Senior | 45% | 35% | Técnica e comportamento têm peso equivalente |
| Lead | 35% | 45% | Comportamental domina — liderança é o core |
| Principal / Staff | 40% | 40% | Equilíbrio — profundidade técnica + influência |
| Diretor | 25% | 55% | Gestão e comportamento dominam |
| VP / C-Level | 20% | 60% | Comportamento estratégico é o diferencial |

> Os percentuais restantes até 100% (ex: Estagiário: 55%+25%=80%) são reservados para eventual bloco de elegibilidade (Bloco 2), quando configurado pelo recrutador. Se não houver Bloco 2, os pesos são normalizados para 100%.

### 5.3 Distribuição de skills por modo

**Modo Compact (4 técnicas + 3 comportamentais):**
- Técnicas: selecionar as 4 skills com maior `importance_score` do JD (se não houver ranking, usar as 4 primeiras informadas pelo recrutador)
- Comportamentais: top-3 traits do ranking Big Five

**Modo Full (7 técnicas + 5 comportamentais):**
- Técnicas: até 7 skills informadas pelo recrutador; se menos de 7, usar todas disponíveis
- Comportamentais: todos os 5 traits, com pesos proporcionais ao score de cada um

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

### 7.4 Camada 3 — Fórmulas de score por tipo de pergunta

#### Para perguntas TÉCNICAS:

```python
# Inputs normalizados 0.0–1.0
autodeclaracao_norm   = autodeclaracao_raw / 5.0   # input 1-5 do candidato
evidencias_tecnicas   = specificity_score / 10.0   # score 1-10 do LLM
bloom_alinhamento     = calcular_bloom_alinhamento(bloom_esperado, bloom_demonstrado)

score_bruto = (
    autodeclaracao_norm  * 0.35 +
    evidencias_tecnicas  * 0.40 +
    bloom_alinhamento    * 0.25
) * 10.0  # normaliza para 0-10

def calcular_bloom_alinhamento(esperado: int, demonstrado: int) -> float:
    diff = esperado - demonstrado
    if diff <= 0:   return 1.00   # demonstrou igual ou mais que esperado
    if diff == 1:   return 0.70   # um nível abaixo
    if diff == 2:   return 0.40   # dois níveis abaixo
    return          0.15          # três ou mais níveis abaixo
```

#### Para perguntas COMPORTAMENTAIS (Big Five):

```python
# Inputs normalizados 0.0–1.0
STAR_score_norm       = STAR_score                          # já é 0.0–1.0 da Camada 1
sinais_trait_norm     = len(sinais_detectados) / max(len(sinais_esperados), 1)
bloom_alinhamento     = calcular_bloom_alinhamento(bloom_esperado, bloom_demonstrado)
# dreyfus_alinhamento é capturado via bônus/penalidades abaixo

score_bruto = (
    STAR_score_norm    * 0.35 +
    sinais_trait_norm  * 0.40 +
    bloom_alinhamento  * 0.25
) * 10.0  # normaliza para 0-10
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

#### Score do Bloco Técnico (Bloco 3):

```python
# Pesos iguais entre skills técnicas (no modo atual)
WSI_tecnico = sum(score_pergunta_tecnica) / num_perguntas_tecnicas
```

#### Score do Bloco Comportamental (Bloco 4):

```python
# Pesos PROPORCIONAIS ao score do trait no ranking do JD
soma_scores_traits = sum(trait["score_final"] for trait in ranked_traits)

WSI_comportamental = sum(
    score_pergunta_i * (trait_i["score_final"] / soma_scores_traits)
    for trait_i, score_pergunta_i in zip(ranked_traits, scores_comportamentais)
)
```

**Exemplo de cálculo comportamental (modo Compact, 3 traits):**

| Trait | Score trait (ranking JD) | Peso normalizado | Score pergunta | Contribuição |
|---|---|---|---|---|
| Estabilidade (N↓) | 72.5 | 36.6% | 7.8 | 2.855 |
| Abertura (O) | 71.5 | 36.1% | 8.2 | 2.960 |
| Conscienciosidade (C) | 54.0 | 27.3% | 6.5 | 1.775 |
| **Total** | **198** | **100%** | — | **7.59** |

**WSI_comportamental = 7.59**

#### Score WSI Final:

```python
# Pesos de senioridade (ver tabela 5.2)
peso_tecnico         = SENIORITY_WEIGHTS[seniority]["technical"]
peso_comportamental  = SENIORITY_WEIGHTS[seniority]["behavioral"]
peso_elegibilidade   = SENIORITY_WEIGHTS[seniority].get("eligibility", 0.0)

WSI_final = (
    WSI_tecnico         * peso_tecnico +
    WSI_comportamental  * peso_comportamental +
    WSI_elegibilidade   * peso_elegibilidade   # 0 se Bloco 2 não configurado
)
```

**Exemplo completo (Senior, modo Compact, sem Bloco 2):**

```
WSI_tecnico         = 7.85 (média de 4 skills técnicas)
WSI_comportamental  = 7.59 (3 traits ponderados pelo JD)
Peso técnico        = 45% (Senior, normalizado sem elegibilidade)
Peso comportamental = 55% (Senior, normalizado)

WSI_final = (7.85 × 0.45) + (7.59 × 0.55) = 3.53 + 4.17 = 7.70
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

## FASE 9 — Fluxo completo integrado

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
| Bloom, B. S. et al. (1956). *Taxonomy of Educational Objectives.* | Calibração do nível cognitivo de perguntas e avaliação de respostas |
| Campion, M. A., Pursell, E. D., & Brown, B. K. (1994). Structured interviewing: Raising the psychometric properties of the employment interview. *Personnel Psychology, 47*, 25–42. | Critérios de qualidade de perguntas; peso STAR |
| Costa, P. T., & McCrae, R. R. (1992). *NEO PI-R Professional Manual.* | Definição canônica dos 5 traits e seus facets |
| Dreyfus, H. L., & Dreyfus, S. E. (1986). *Mind over Machine.* | Calibração de proficiência técnica e maturidade comportamental |
| Flanagan, J. C. (1954). The critical incident technique. *Psychological Bulletin, 51*, 327–358. | Base do formato CBI situacional |
| Hogan, J., & Holland, B. (2003). Using theory to evaluate personality and job-performance relations. *Journal of Applied Psychology, 88*, 100–112. | Mapeamento cargo × personalidade |
| Huffcutt, A. I., et al. (2001). Identification and meta-analytic assessment of psychological constructs measured in employment interviews. *Journal of Applied Psychology, 86*, 897–913. | Justificativa para remoção de perguntas de fit cultural |
| Janz, T. (1982). Initial comparisons of patterned behavior description interviews versus unstructured interviews. *Journal of Applied Psychology, 67*, 577–580. | Peso STAR; validade preditiva do CBI |
| McClelland, D. C. (1973). Testing for competence rather than for "intelligence." *American Psychologist, 28*, 1–14. | Fundamento do modelo CBI |
| O*NET Resource Center (2024). *O*NET Occupational Database.* onetcenter.org | Prior por arquétipo de cargo |
| Pennebaker, J. W., Francis, M. E., & Booth, R. J. (2001). *Linguistic Inquiry and Word Count.* | Mapeamento léxico para extração Big Five |
| Rivera, L. A. (2012). Hiring as cultural matching: The case of elite professional service firms. *American Sociological Review, 77*, 999–1022. | Risco de viés em avaliações de "fit cultural" |
| Tett, R. P., & Guterman, H. A. (2000). Situation trait relevance, trait expression, and cross-situational consistency. *Journal of Research in Personality, 34*, 397–423. | Trait Activation Theory — cenários ativadores por trait |
| Tett, R. P., Jackson, D. N., & Rothstein, M. (1994). Personality measures as predictors of job performance: A meta-analytic review. *Personnel Psychology, 47*, 157–172. | Validade preditiva por trait em contexto organizacional |

---

*Documento gerado em: 2026-03-24*  
*Próxima revisão recomendada: após ciclo de validação com dados reais de triagem*
