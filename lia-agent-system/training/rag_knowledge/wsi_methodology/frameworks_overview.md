# WSI — Frameworks Overview

Base científica e operacional que a LIA usa para gerar perguntas de triagem
calibradas, avaliar respostas e produzir pareceres consistentes. Este
documento é carregado em runtime pelo `WSIQuestionGenerator` e injetado no
prompt do LLM como contexto autoritativo. Mantenha-o conciso, citável e em
PT-BR.

---

## 1. CBI — Competency-Based Interviewing

**Princípio central.** Comportamentos passados em contextos similares são
os melhores preditores de performance futura (meta-análises Hunter & Hunter,
Schmidt & Hunter). Perguntas comportamentais bem feitas têm validade
preditiva ~0.51, ~3x maior que entrevista não-estruturada (~0.18).

**Estrutura STAR (obrigatória nas respostas).**
- **S — Situation:** qual era o cenário, restrições, stakeholders.
- **T — Task:** o que era esperado da pessoa especificamente (não do time).
- **A — Action:** o que ela fez, com que ferramentas, em que ordem.
- **R — Result:** outcome quantificado (ou justificativa para a falta).

**Padrões de pergunta CBI canônicos.**
- "Conte sobre uma situação em que você {comportamento_alvo}. Qual era o
  contexto, sua ação específica e o resultado?"
- "Descreva o projeto mais complexo que você liderou envolvendo {skill}.
  Quais decisões você tomou e qual foi o impacto?"
- "Cite uma vez em que você teve que {handle_difficulty}. Como conduziu e
  o que aprendeu?"

**Anti-padrões (devem ser evitados ao gerar perguntas).**
- Perguntas hipotéticas sem âncora ("Como você reagiria se..."). Não geram
  evidência comportamental, só intenção declarada.
- Perguntas duplas ("Conte sobre liderança E sobre como você lida com
  conflito"). Dividir.
- Perguntas dirigidas ("Você concorda que ownership é importante?").
  Levam à resposta socialmente aceitável.

---

## 2. Dreyfus Model (Brothers Dreyfus, 1980)

Escala de 5 níveis de proficiência usada para mapear o domínio técnico
declarado contra o domínio exigido pela vaga.

| Nível | Nome              | Característica observável                                                 |
|:-----:|:------------------|:--------------------------------------------------------------------------|
| 1     | Novice            | Depende de regras explícitas; não reconhece contexto.                     |
| 2     | Advanced Beginner | Reconhece padrões; precisa de supervisão para decisões.                   |
| 3     | Competent         | Planeja conscientemente; assume responsabilidade pelo resultado.          |
| 4     | Proficient        | Vê a situação como um todo; ajusta planos de forma fluida.                |
| 5     | Expert            | Intuição contextual; rompe regras quando necessário; mentora.             |

**Como inferir o nível a partir de uma resposta.**
- Volume de evidência concreta (projetos citados, métricas, tradeoffs).
- Granularidade do vocabulário técnico ("usei FastAPI" vs "escolhi FastAPI
  sobre Litestar por causa de X, e contornei a limitação Y com Z").
- Capacidade de discutir falhas e tradeoffs sem postura defensiva.
- Disposição a mentora/elevar pares (sinal de níveis 4-5).

**Padrões de pergunta Dreyfus.**
- "De 1 a 5, quanto você se considera em {skill}? Cite um projeto recente
  onde aplicou e o tradeoff técnico mais difícil que precisou resolver."
- "Qual foi a última vez que você ensinou {skill} para alguém? Como
  estruturou o aprendizado?"

---

## 3. Bloom's Taxonomy (Anderson & Krathwohl, 2001 — revisada)

Escala cognitiva usada para calibrar a complexidade das perguntas
técnicas — evitando que todas sejam de nível "lembrar" (factual) ou
todas de nível "criar" (open-ended demais para triagem).

| Nível | Verbo-chave | Exemplo aplicado a Python                                  |
|:-----:|:------------|:-----------------------------------------------------------|
| 1     | Lembrar     | "O que é GIL?"                                             |
| 2     | Compreender | "Por que o GIL afeta CPU-bound mas não I/O-bound?"         |
| 3     | Aplicar     | "Como você paralelizaria uma rotina CPU-bound em Python?"  |
| 4     | Analisar    | "Diagnostique por que esta função está 10x mais lenta."    |
| 5     | Avaliar     | "Qual abordagem você escolheria para este workload e por quê?" |
| 6     | Criar       | "Projete um sistema de processamento distribuído para X."  |

**Distribuição recomendada por senioridade (triagem WSI).**
- Júnior: 40% L2-L3, 40% L3-L4, 20% L4.
- Pleno:  20% L2-L3, 50% L3-L4, 30% L4-L5.
- Sênior: 10% L3,    40% L4,    50% L5-L6.

Perguntas devem subir gradualmente — nunca abrir com L6 logo de saída.

---

## 4. Big Five / OCEAN — NEO-PI-R

Modelo dimensional de personalidade com maior evidência empírica
transcultural. A LIA usa o Big Five para mapear o **perfil requerido pela
vaga** (extraído do JD com evidências literais) e comparar com o **perfil
observado nas respostas** do candidato.

| Trait              | Sigla | Alto pontua quando…                                       |
|:-------------------|:-----:|:----------------------------------------------------------|
| Openness           | O     | Busca novidade, abstração, ambiguidade tolerada.          |
| Conscientiousness  | C     | Disciplina, organização, follow-through.                  |
| Extraversion       | E     | Energia em interação social, assertividade.               |
| Agreeableness      | A     | Cooperação, empatia, evita conflito gratuito.             |
| Neuroticism (Estabilidade) | N | Calma sob pressão (alta estabilidade = baixo N).      |

**Regras de evidência (obrigatórias na extração do perfil-vaga).**
- Citações **literais** do JD entre aspas duplas — paráfrase não conta.
- Sem trecho literal → `score ≤ 30`, `confidence = "low"`, `evidence = []`.
- Nunca inferir trait a partir de nome de empresa, setor ou cargo.

**Padrões de pergunta Big Five (comportamentais, não diretas).**
- O — "Conte sobre a última vez que você teve que aprender algo
  completamente novo sob pressão. Como abordou?"
- C — "Descreva como você organiza um projeto longo (3+ meses) com
  múltiplos stakeholders."
- E — "Cite uma situação em que você precisou convencer um grupo
  resistente a mudar de direção."
- A — "Conte sobre um desentendimento técnico forte com um colega. Como
  resolveu sem perder a relação?"
- N — "Descreva um momento em que algo crítico falhou na sua mão.
  Como você reagiu nas primeiras 24h?"

---

## 5. WSI — composição final

O WSI Score (0.0 — 5.0) é a média ponderada de 4 dimensões:

```
WSI = 0.35 * technical_score
    + 0.30 * behavioral_score
    + 0.20 * cultural_fit_score
    + 0.15 * communication_score
```

**Bandas de decisão.**

| Faixa     | Banda          | Recomendação padrão                              |
|:----------|:---------------|:-------------------------------------------------|
| ≥ 4.5     | Excelente      | APROVADO — fast-track para entrevista técnica.   |
| 3.5 — 4.4 | Bom            | APROVADO — entrevista padrão.                    |
| 2.5 — 3.4 | Médio          | REVISAR — segunda opinião humana obrigatória.    |
| 1.5 — 2.4 | Baixo          | REPROVADO — feedback estruturado e construtivo.  |
| < 1.5     | Inadequado     | REPROVADO — comunicação respeitosa, sem detalhe. |

**Compliance.**
- FairnessGuard sempre rodado sobre input do recrutador (não sobre output
  da LIA, que é apenas texto educacional/informacional).
- Four-Fifths Rule monitorada agregadamente por gênero/raça/idade.
- Auditoria SOX 7 anos para qualquer decisão de aprovação/reprovação.
- LGPD: PII mascarada antes de qualquer chamada LLM.
