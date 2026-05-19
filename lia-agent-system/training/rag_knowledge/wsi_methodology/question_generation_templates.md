# WSI — Question Generation Templates

Biblioteca de templates de perguntas usadas pelo `WSIQuestionGenerator` para
gerar triagens científicas. Cada template aponta para um framework
(CBI/Dreyfus/Bloom/Big Five), declara o trait/skill que mede e a
calibração esperada (eliminatória vs. informativa, tempo estimado, nível
Dreyfus alvo).

Os templates abaixo são injetados no prompt do LLM como referência. O LLM
ADAPTA o template ao contexto específico da vaga — não copia literal — e
deve sempre devolver as perguntas em PT-BR neutro, sem gírias, sem
condescendência, sem expressões que dependam de contexto cultural anglo.

---

## 1. Bloco 1 — Eliminatórias (Hard Requirements)

**Objetivo.** Validar bloqueadores objetivos (visto, disponibilidade,
modelo de trabalho, experiência mínima medida em anos). Sempre sim/não ou
numérica. Falha = candidato fora do funil.

**Templates.**

```
[E01] Você tem autorização para trabalhar no Brasil (CLT/PJ/MEI)?
[E02] Está disponível para iniciar nos próximos {N} dias?
[E03] Aceita o modelo de trabalho {modelo}? (remoto/híbrido/presencial)
[E04] Possui pelo menos {anos} anos de experiência prática com {skill_chave}?
[E05] Sua pretensão salarial está na faixa de R$ {min} a R$ {max}?
```

**Calibração.** Tempo: ≤ 30s cada. Tipo: eliminatória. Bloom: L1
(lembrar/factual). Nunca usar template eliminatório para skills
qualitativas (essas vão para Bloco 3).

---

## 2. Bloco 2 — Cultura e Default da Empresa

Perguntas vindas do banco de perguntas da empresa (DEI, valores, fit
cultural). NÃO geradas pelo LLM — apenas selecionadas. Templates aqui
servem só de referência para quando a empresa não tem banco próprio:

```
[C01] Conte sobre uma situação em que você precisou colaborar com um time
      que tinha valores ou prioridades diferentes dos seus. Como navegou?
[C02] Cite um momento profissional em que você ficou mais orgulhoso(a).
      O que isso revela sobre o que te motiva no dia a dia?
[C03] Como você gostaria que seu próximo gestor descrevesse seu estilo de
      trabalho daqui a 6 meses?
```

**Calibração.** Tempo: 90-120s. Tipo: informativa. Bloom: L4-L5.

---

## 3. Bloco 3 — Técnicas (CBI + Dreyfus + Bloom)

Geradas para cada skill técnica do JD, calibradas pela senioridade declarada.

**Padrão de geração.**

```
Para cada skill em {technical_skills}:
  - Selecionar 1 pergunta Dreyfus (auto-avaliação ancorada em projeto)
  - Selecionar 1 pergunta CBI (evidência comportamental STAR)
  - Selecionar 1 pergunta Bloom L3+ (aplicação/análise/avaliação)
```

**Templates Dreyfus por skill.**

```
[T-DRY] De 1 a 5, quanto você domina {skill}? Cite o projeto recente mais
        complexo em que aplicou e descreva o tradeoff técnico mais difícil
        que precisou resolver.
[T-DRY-LEAD] Você já ensinou {skill} para outras pessoas? Como
        estruturou o aprendizado e qual foi a maior dúvida que surgiu?
```

**Templates CBI por skill.**

```
[T-CBI] Conte sobre um projeto onde {skill} foi central. Qual era o
        contexto, qual decisão técnica específica você tomou e qual foi o
        resultado mensurável?
[T-CBI-FAIL] Descreva uma situação envolvendo {skill} em que algo deu
        errado. O que aconteceu, como você diagnosticou e o que mudou na
        sua prática depois?
```

**Templates Bloom L3-L5 por contexto.**

```
[T-BL3] Você está implementando {scenario_técnico_realista}. Como você
        abordaria? Mencione tecnologias, tradeoffs e como validaria.
[T-BL4] Recebe um sistema legado com {sintoma_realista_de_problema}.
        Como você diagnosticaria a causa raiz? Quais hipóteses descartaria
        primeiro e por quê?
[T-BL5] Entre {abordagem_A} e {abordagem_B} para {problema_realista},
        qual você escolheria neste contexto e por quê? Cite critérios.
```

**Distribuição por senioridade (12 perguntas técnicas no modo completo).**

| Senioridade | Dreyfus | CBI | Bloom L3 | Bloom L4 | Bloom L5 |
|:-----------:|:-------:|:---:|:--------:|:--------:|:--------:|
| Júnior      | 3       | 3   | 4        | 2        | 0        |
| Pleno       | 2       | 3   | 3        | 3        | 1        |
| Sênior      | 2       | 3   | 2        | 3        | 2        |
| Especialista| 1       | 3   | 1        | 3        | 4        |

**Calibração.** Tempo: 90-180s por pergunta. Tipo: informativa
(eliminatórias técnicas vão no Bloco 1).

---

## 4. Bloco 4 — Comportamentais (Big Five via CBI)

Para cada trait dominante extraído do JD (top-N por senioridade), gerar
1-2 perguntas comportamentais. Nunca usar perguntas diretas tipo "Você é
organizado?" — sempre CBI com STAR.

**Templates por trait.**

```
[B-O] Conte sobre a última vez que você teve que aprender algo
      completamente novo em prazo curto. Como abordou o aprendizado e
      como mediu seu progresso? (Openness)

[B-C] Descreva como você organiza um projeto longo com múltiplos
      stakeholders e prazos competindo entre si. Use um exemplo real
      recente. (Conscientiousness)

[B-E] Cite uma situação em que você precisou convencer um grupo
      resistente a mudar de direção técnica ou de processo. Como
      conduziu? (Extraversion / Assertividade)

[B-A] Conte sobre um desentendimento forte com um colega — técnico ou
      de processo. Como resolveu mantendo a relação profissional?
      (Agreeableness)

[B-N] Descreva um momento em que algo crítico falhou na sua mão (bug em
      produção, deploy mal, decisão errada). Como você reagiu nas
      primeiras 24h e o que mudou depois? (Estabilidade / baixo Neuroticism)
```

**Calibração.** Tempo: 120-180s. Tipo: informativa. Sempre exigir STAR
no critério de avaliação.

**Modo completo (Big Five top-5 com 1 pergunta cada = 5 perguntas).**
**Modo compacto (Big Five top-3 com 1 pergunta cada = 3 perguntas).**

---

## 5. Bloco 5 — Encerramento e Próximos Passos

Mensagens fixas (não geradas pelo LLM), apenas formatadas com variáveis
da vaga. Veja `WSI_AUTOMATIC_MESSAGES` no frontend.

---

## 6. Distribuição final por modo

| Modo      | Bloco 1 (Elim.) | Bloco 2 (Cultura) | Bloco 3 (Téc.) | Bloco 4 (Comp.) | Total |
|:----------|:---------------:|:------------------:|:--------------:|:---------------:|:-----:|
| Compacto  | 3               | 2                  | 4              | 3               | 12    |
| Completo  | 5               | 3                  | 12             | 5               | 25    |

O `WSIQuestionGenerator` em **modo completo** deve gerar **pelo menos
10 perguntas** no Bloco 3 + Bloco 4 combinados, mesmo se o JD tem poucas
skills declaradas — nesse caso, ampliar a profundidade Bloom de cada skill
em vez de pular perguntas.

---

## 7. Regras de qualidade (rejeição automática)

Uma pergunta gerada é REJEITADA e regenerada se:

1. Contém gírias ou expressões anglo intraduzíveis ("rockstar", "ninja",
   "10x developer", "cool", "legal demais").
2. É dupla — mede dois construtos em uma única frase.
3. É dirigida — sugere a resposta socialmente aceitável.
4. É hipotética sem âncora comportamental ("Como você reagiria se...").
5. Menciona dados pessoais protegidos (idade, gênero, estado civil,
   filhos, religião, orientação) — viola Lei 9.029/95 e CLT 373-A.
6. Tem menos de 8 palavras ou mais de 60 (sinal de prompt mal-formado).
7. Não cita {skill} nem {scenario} quando o template exige.
