# Metodologia Unificada LIA - WeDoTalent

## Referencia Tecnica para Implementacao

**Versao:** 1.2  
**Data:** Marco 2026  
**Status:** Documento oficial consolidado  
**Fonte:** Consolidacao de WSI_METHODOLOGY_REFERENCE.md + LIA_METHODOLOGY.md  
**Atualizacao 1.1:** Adicionada secao 4.11 (Saturacao Inteligente)  
**Atualizacao 1.2:** Secao 4.6 corrigida (blocos reais do pipeline), secao 4.13 reescrita com dados reais do codigo, adicionado Pipeline WSI End-to-End completo (Fase 1 e Fase 2) como secao 4.14

---

## 1. Visao Geral

A metodologia unificada LIA combina **4 camadas complementares** para avaliacao cientifica de candidatos:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    METODOLOGIA UNIFICADA LIA                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CAMADA 1: PRE-REQUISITOS (Filtros Eliminatorios)                           │
│  ─────────────────────────────────────────────────                          │
│  Validacao de criterios obrigatorios antes de qualquer avaliacao            │
│                                                                              │
│  CAMADA 2: RUBRICAS BARS (Avaliacao CV vs Vaga)                             │
│  ───────────────────────────────────────────────                            │
│  Score determinístico baseado em requisitos estruturados                    │
│  Base: Schmidt & Hunter (1998)                                              │
│                                                                              │
│  CAMADA 3: WSI (Validacao Conversacional)                                   │
│  ──────────────────────────────────────────                                 │
│  Triagem por chat/voz com frameworks cientificos                            │
│  Base: Bloom + Dreyfus + Big Five + CBI                                     │
│                                                                              │
│  CAMADA 4: CALIBRATION LOOP (Aprendizado Continuo)                          │
│  ──────────────────────────────────────────────────                         │
│  Ajuste de pesos baseado em feedback do recrutador                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Camada 1: Pre-Requisitos

### 2.1 Proposito

Filtrar candidatos que **nao atendem criterios eliminatorios** antes de investir tempo em avaliacao detalhada.

### 2.2 Tipos de Pre-Requisitos

| Tipo | Descricao | Comportamento |
|------|-----------|---------------|
| **Idiomas Obrigatorios** | Nivel minimo de proficiencia exigido | Reprovado se nao atender |
| **Vagas Afirmativas** | PcD, Mulheres, 50+, Pretos/Pardos | Verificacao de elegibilidade |
| **Disponibilidade** | Imediata, 15d, 30d, 60d, 90d | Match com urgencia da vaga |
| **Pretensao Salarial** | Dentro da faixa oferecida | Alerta se fora da faixa |
| **Localizacao** | Presencial, Hibrido, Remoto | Match com modelo de trabalho |

### 2.3 Logica de Aplicacao

```
SE pre_requisito.obrigatorio = TRUE
   E candidato.atende = FALSE
ENTAO
   status = "NAO_ELEGIVEL"
   score_final = 0
   motivo = "Nao atende: {pre_requisito.nome}"
FIM
```

### 2.4 Transparencia (EU AI Act)

Cada pre-requisito reprovado gera explicacao clara:
- "Candidato nao atende requisito de Ingles Fluente (obrigatorio)"
- "Pretensao salarial R$15.000 acima da faixa maxima R$12.000"

---

## 3. Camada 2: Rubricas BARS

### 3.1 Fundamentacao Cientifica

| Referencia | Contribuicao |
|------------|--------------|
| **Schmidt & Hunter (1998)** | Meta-analise: estruturacao aumenta validade preditiva de 0.38 para 0.51 |
| **BARS - Behaviorally Anchored Rating Scales** | Escala com ancoras comportamentais reduz vies de avaliador |
| **Campion et al. (1997)** | 15 componentes que aumentam validade de entrevistas estruturadas |
| **Smith & Kendall (1963)** | Retranslation method para ancoras inequivocas |

### 3.2 Escala de Avaliacao (4 Niveis)

| Nivel | Pontos | Descricao | Ancora Comportamental |
|-------|--------|-----------|----------------------|
| **Exceeds** | 100 | Experiencia excepcional | Evidencia de resultados superiores, lideranca na area, ou experiencia >50% acima do requisito |
| **Meets** | 75 | Atende plenamente | CV demonstra claramente a competencia/experiencia requerida |
| **Partial** | 40 | Atende parcialmente | Evidencia relacionada mas nao direta, ou experiencia inferior ao requisito |
| **Missing** | 0 | Nao demonstrado | Nenhuma evidencia encontrada no CV |

### 3.3 Prioridades de Requisitos (Multiplicadores)

| Prioridade | Multiplicador | Uso |
|------------|---------------|-----|
| **Essential** | 3x | Requisitos eliminatorios, sem os quais o candidato nao pode exercer a funcao |
| **Important** | 2x | Requisitos significativos que impactam diretamente a performance |
| **Nice to Have** | 1x | Diferenciais que agregam valor mas nao sao criticos |

### 3.4 Formula de Calculo

```
Score = Σ(Pontos × Multiplicador) / Σ(100 × Multiplicador) × 100

Onde:
- Pontos = Nivel de avaliacao (100, 75, 40 ou 0)
- Multiplicador = Prioridade do requisito (3, 2 ou 1)
- Denominador = Pontuacao maxima possivel
```

### 3.5 Exemplo Pratico

**Vaga:** Desenvolvedor Python Senior

| Requisito | Prioridade | Mult. | Avaliacao | Pontos | Weighted |
|-----------|------------|-------|-----------|--------|----------|
| Python 5+ anos | Essential | 3x | Meets (8 anos) | 75 | 225 |
| Django/FastAPI | Essential | 3x | Exceeds (tech lead) | 100 | 300 |
| PostgreSQL | Important | 2x | Meets | 75 | 150 |
| AWS | Important | 2x | Partial | 40 | 80 |
| Docker/K8s | Nice to Have | 1x | Meets | 75 | 75 |
| Lideranca | Nice to Have | 1x | Exceeds | 100 | 100 |

**Calculo:**
- Pontos obtidos: 225 + 300 + 150 + 80 + 75 + 100 = **930**
- Pontos maximos: (100×3) + (100×3) + (100×2) + (100×2) + (100×1) + (100×1) = **1200**
- Score = 930 / 1200 × 100 = **77.5%**

### 3.6 Niveis de Recomendacao

| Score | Nivel | Acao Recomendada |
|-------|-------|------------------|
| 85-100% | **Altamente Recomendado** | Priorizar para entrevista |
| 70-84% | **Recomendado** | Considerar para processo |
| 55-69% | **Potencial** | Avaliar gaps especificos |
| 40-54% | **Baixo Match** | Arquivar para futuras vagas |
| 0-39% | **Nao Recomendado** | Nao prosseguir |

---

## 4. Camada 3: WSI (WeDoTalent Skill Index)

### 4.1 Visao Geral

O WSI e um sistema de triagem conversacional (chat ou voz) que valida competencias tecnicas e comportamentais atraves de perguntas estruturadas.

### 4.2 Frameworks Cientificos Integrados

| Framework | Base Academica | Aplicacao |
|-----------|----------------|-----------|
| **CBI** | McClelland (Harvard, 1973) | Perguntas situacionais com analise STAR |
| **Taxonomia de Bloom** | Anderson et al., 2001 | Niveis cognitivos (Lembrar → Criar) |
| **Modelo Dreyfus** | Dreyfus & Dreyfus, 1980 | Escala 1-5 de proficiencia |
| **Big Five (OCEAN)** | Goldberg, 1992 | Tracos comportamentais |

### 4.3 Taxonomia de Bloom Revisada (6 Niveis Cognitivos)

| Nivel | Descricao | Equivalencia na Triagem |
|-------|-----------|------------------------|
| 1 - Lembrar | Recordar fatos e conceitos | Autodeclaracao simples |
| 2 - Compreender | Explicar ideias | Perguntas teoricas |
| 3 - Aplicar | Usar conhecimento na pratica | Microcases |
| 4 - Analisar | Diferenciar e relacionar conceitos | Contexto real |
| 5 - Avaliar | Julgar e justificar decisoes | Perguntas de julgamento |
| 6 - Criar | Gerar solucoes novas | Respostas de inovacao/lideranca |

> **Referencia:** Anderson, L. W., et al. (2001). A Taxonomy for Learning, Teaching, and Assessing - Revisao da taxonomia original de Bloom (1956).

### 4.4 Modelo Dreyfus (Niveis de Proficiencia)

| Score | Nivel | Interpretacao |
|-------|-------|---------------|
| 1 | Novice | Conhecimento basico, teorico |
| 2 | Advanced Beginner | Aplicacao parcial e guiada |
| 3 | Competent | Execucao estavel e consistente |
| 4 | Proficient | Aplicacao autonoma e adaptativa |
| 5 | Expert | Dominio intuitivo e contextual |

### 4.5 Big Five (OCEAN Model)

| Fator | Significado | Validacao na Triagem |
|-------|-------------|---------------------|
| O - Abertura | Curiosidade, inovacao | Inovacao e aprendizado |
| C - Conscienciosidade | Organizacao, foco em resultado | Entregabilidade e rigor tecnico |
| E - Extroversao | Energia e assertividade | Comunicacao e lideranca |
| A - Amabilidade | Empatia e colaboracao | Trabalho em equipe |
| N - Estabilidade Emocional | Controle sob pressao | Tomada de decisao e resiliencia |

### 4.6 Estrutura de 6 Blocos do Pipeline WSI

O pipeline WSI e estruturado em 6 blocos sequenciais, identificados por `block_id` de 0 a 5. Cada bloco tem tipo de gerenciamento distinto:

| Bloco | Nome | Tipo | Editavel | Origem |
|-------|------|------|----------|--------|
| **0** | Abordagem Inicial | `template` | Nao | Template WhatsApp pre-aprovado enviado automaticamente |
| **1** | Apresentacao da Oportunidade | `presentation` | Nao | Pitch gerado automaticamente a partir dos dados da vaga |
| **2** | Perguntas Padrao da Empresa | `company` | Sim | Configurado pelo recrutador (elegibilidade + empresa + acao afirmativa) |
| **3** | Competencias Tecnicas | `technical` | Sim | Gerado pelo WSI pipeline — CBI + Bloom + Dreyfus por skill |
| **4** | Competencias Comportamentais e Fit | `situational` | Sim | Gerado pelo WSI pipeline — Big Five + CBI cultural |
| **5** | Resultado e Encerramento | `result` | Nao | Score WSI calculado automaticamente + feedback ao candidato |

**Blocos automaticos (0, 1, 5):** conteudo fixo gerenciado pelo sistema, o recrutador nao pode editar.  
**Blocos editaveis (2, 3, 4):** o recrutador visualiza, aceita, rejeita ou edita as perguntas na aba "Perguntas de Triagem" antes de salvar.

**Duracao estimada por bloco:**

| Bloco | Duracao |
|-------|---------|
| 0 — Abordagem | menos de 1 min |
| 1 — Apresentacao | 3 min |
| 2 — Empresa | 3 min |
| 3 — Tecnico | 5 min |
| 4 — Comportamental | 4 min |
| 5 — Resultado | 3 min |
| **Total estimado** | **~18 min (full) / ~13 min (compact)** |

### 4.7 Formula do WSI

**Pontuacao por resposta (escala 0–10):**

```
normalized = (score_bruto / max_score) × 10.0

Se bloco tecnico:
    technical_score = (technical_score_acumulado + normalized) / 2

Se bloco comportamental ou situacional:
    behavioral_score = (behavioral_score_acumulado + normalized) / 2
```

**Score final (generate_feedback):**

```python
wsi_final_score = calculate_final_wsi_score(
    technical_scores  = [("technical",   technical_score,  1.0)],
    behavioral_scores = [("behavioral",  behavioral_score, 0.6),
                         ("situational", situational_score, 0.4)],
)
```

O scorer determinístico (`wsi_deterministic_scorer.py`) calcula cada resposta com base em:
- `expected_bloom` (1–6) — nivel cognitivo esperado na resposta
- `expected_dreyfus` (1–5) — proficiencia esperada na resposta
- `competency` — nome da competencia avaliada
- `max_score = 10.0` (padrao)

### 4.8 Faixas de Classificacao WSI

| Score Final | Classificacao | Acao Automatica |
|-------------|---------------|-----------------|
| >= 7.0 | **aprovado** | Avanca no pipeline |
| 5.0 – 6.9 | **aguardando** | Revisao manual recomendada |
| < 5.0 | **reprovado** | Email de feedback (nao bloqueante) |

> Nota: A escala operacional do scorer e 0–10 por pergunta. O `wsi_final_score` consolidado herda esta escala e e comparado aos thresholds acima.

### 4.9 Penalidades e Bonus

> Nota: Esta secao descreve ajustes conceituais aplicados pelo scorer deterministico (`wsi_deterministic_scorer.py`) na escala 0–10 por resposta. Os valores abaixo sao ranges de impacto na pontuacao individual.

**Penalidades:**

| Situacao | Impacto na Pontuacao (escala 0–10) |
|----------|-----------------------------------|
| Inflacao de score (autodeclara alto, contexto pobre) | -1.0 a -3.0 |
| Resposta generica sem evidencias concretas | -1.0 |
| Falta de contexto situacional (formato STAR incompleto) | -0.6 |
| Resposta bloqueada por PromptInjectionGuard (SEG-1) | score = 0.0 (zero absoluto) |

**Bonus:**

| Situacao | Impacto na Pontuacao (escala 0–10) |
|----------|-----------------------------------|
| Humildade calibrada (autodeclara moderado, contexto detalhado) | +1.0 |
| Evidencias excepcionais com impacto mensuravel | +0.6 |

### 4.10 Regras de Aprovacao Automatica

> Nota: As faixas abaixo descrevem a camada de calibracao dinamica (ranking dentro de uma vaga com historico de triagens). Sao complementares aos thresholds operacionais de 0–10 documentados na secao 4.8, que determinam aprovado/aguardando/reprovado no nivel individual. As duas camadas coexistem.

**Corte Inicial (Sem Historico)** - Aplicado quando vaga tem menos de 30-50 triagens:

| Faixa WSI (0–10) | Decisao |
|------------------|---------|
| >= 8.4 | Aprovado automatico |
| 7.6 – 8.3 | Revisao manual |
| 6.0 – 7.5 | Aguardando comparacao |
| < 6.0 | Nao aprovado |

**Corte Dinamico (Com Historico)** - Apos 30-50 triagens por funcao:

| Percentil | Decisao |
|-----------|---------|
| Top 25% | Aprovado automatico |
| 25% - 60% | Revisao manual |
| < 60% | Reprovado |

> A LIA recalibra automaticamente os percentis a cada nova triagem.

### 4.11 Saturacao Inteligente

A Saturacao Inteligente pausa a triagem automatica quando o pipeline atinge um numero maximo de candidatos aprovados, evitando gargalos e garantindo foco na avaliacao dos candidatos ja triados.

#### Parametros

| Parametro | Valor Padrao | Descricao |
|-----------|--------------|-----------|
| `saturation_threshold` | 20 | Numero maximo de aprovados antes de pausar |
| `is_saturated` | false/true | Flag de saturacao ativa |
| `slots_remaining` | calculado | Vagas restantes ate saturacao |

#### Logica de Decisao

```
SE approved_count >= saturation_threshold:
    is_saturated = TRUE
    recommendation = "pause_screening"
    ACOES:
    - Pausar triagem automatica
    - Notificar recrutador
    - Sugerir: "Agendar entrevistas" ou "Desbloquear pipeline"
SENAO:
    is_saturated = FALSE
    recommendation = "continue_screening"
    INFORMAR: "{slots_remaining} vagas restantes ate saturacao"
```

#### Override Manual

O recrutador pode desbloquear o pipeline a qualquer momento:
- Aumentar `saturation_threshold` para a vaga especifica
- Executar acao "Desbloquear pipeline" no painel
- Todas as acoes de override sao registradas para calibration

### 4.12 Governanca Humana

| Situacao | Acao |
|----------|------|
| Candidato solicita revisao | Recrutador deve revisar manualmente |
| Score proximo ao limiar (±0.2) | Sugerir revisao humana |
| Override do recrutador | Registrar justificativa para calibration |
| Discordancia sistematica | Alertar coordenador de RH |

### 4.13 Geracao de Perguntas WSI por Competencia

> Esta secao descreve como o pipeline gera perguntas para os Blocos 3 e 4, com dados extraidos diretamente do codigo (`wsi_question_generator.py` e `wsi_screening_pipeline.py`). O Bloco 2 (empresa/elegibilidade) e gerenciado separadamente — veja secao 4.14.

#### Etapa 1 — Extracao de Competencias do Job Description

O recrutador cola o JD na aba "Descricao". O backend (Claude Sonnet via `wsi.py` linhas 189–330) extrai:

| Campo extraido | Descricao | Onde usado |
|----------------|-----------|-----------|
| Titulo + senioridade | Cargo e nivel (junior/pleno/senior/lead/executive) | Calibra Bloom e Dreyfus |
| Hard skills tecnicas | Ate 5 skills priorizadas das responsabilidades | Bloco 3 — 1 pergunta por skill |
| Soft skills comportamentais | Traits esperados pelo JD | Informa o perfil Big Five |
| Requisitos eliminatorios | Disponibilidade, localizacao, elegibilidade | Bloco 2 |

O resultado e salvo no objeto `job` no frontend (`job.technicalRequirements`, `job.behavioralCompetencies`) e alimenta a geracao de perguntas.

#### Etapa 2 — Modos de Geracao e Distribuicao

**Definicao no codigo (`MODEL_DISTRIBUTIONS` em `wsi_screening_pipeline.py`):**

```python
MODEL_DISTRIBUTIONS = {
    "compact": {"technical": 3, "behavioral": 3, "total": 6},
    "full":    {"technical": 5, "behavioral": 5, "total": 10},
}
```

| Modo | Bloco 3 (Tecnico) | Bloco 4 (Comportamental) | Total |
|------|-------------------|--------------------------|-------|
| **compact** | 3 perguntas | 3 perguntas | **6 perguntas** |
| **full** | 5 perguntas | 5 perguntas | **10 perguntas** |

#### Etapa 3 — Bloco 3: Geracao de Perguntas Tecnicas

**Arquivo:** `wsi_question_generator.py` → `_generate_technical_questions()`  
**Arquivo de destino:** `block_id = 3`, `category = "technical"`, `weight = 0.9`

O gerador pega ate 5 skills do JD e aplica templates STAR por senioridade, rotacionando entre os disponiveis:

```python
skills = context.skills[:5]
for i, skill in enumerate(skills):
    template_data = templates[i % len(templates)]  # rotaciona templates
    texto = template_data["template"].format(skill=skill)
```

O campo `framework` de cada template indica qual referencial cientifico guiou sua formulacao:

| Senioridade | Templates disponiveis | % CBI | % Bloom | % Dreyfus |
|-------------|----------------------|-------|---------|-----------|
| junior | 2 | 100% | 0% | 0% |
| pleno | 3 | ~67% | ~33% | 0% |
| senior | 3 | ~33% | ~33% | ~33% |
| lead | 2 | 50% | 50% | 0% |
| executive | 2 | 50% | 50% | 0% |

> Importante: independente do `framework` que gerou a pergunta, **todas** as perguntas tecnicas recebem `bloom_level` (nivel cognitivo da pergunta) e `dreyfus_stage` (proficiencia esperada na resposta). Estes valores sao usados pelo scorer na Fase 2.

**Exemplos de perguntas geradas por senioridade:**

| Senioridade | Pergunta gerada (template) | Bloom | Framework |
|-------------|---------------------------|-------|-----------|
| Junior | "Voce ja utilizou {skill}? Descreva sua experiencia" | 2 — Compreender | CBI |
| Pleno | "Descreva um projeto onde voce utilizou {skill}. Contexto, acao, resultado" | 4 — Analisar | CBI |
| Pleno | "Compare diferentes abordagens relacionadas a {skill}. Quando usaria cada uma?" | 5 — Avaliar | Bloom |
| Senior | "Descreva uma arquitetura usando {skill}. Quais trade-offs considerou?" | 5 — Avaliar | CBI |
| Senior | "Como avalia a melhor abordagem ao usar {skill}? Exemplo de decisao dificil" | 5 — Avaliar | Bloom |
| Senior | "Conte sobre uma vez em que voce mentorou alguem em {skill}" | 6 — Criar | Dreyfus |
| Lead/Exec | "Como definiu padroes tecnicos relacionados a {skill} para sua equipe?" | 6 — Criar | CBI |

#### Etapa 4 — Bloco 4: Geracao de Perguntas Comportamentais

**Arquivo:** `wsi_question_generator.py` → `_generate_behavioral_questions()` + `_generate_cultural_questions()`  
**Arquivo de destino:** `block_id = 4`, `category = "behavioral"` (Big Five) ou `"cultural"` (CBI fit)

O Bloco 4 e montado em dois passos e concatenado:

```python
behavioral_raw = _generate_behavioral_questions(ctx)  # Big Five — ate 3 perguntas
cultural_raw   = _generate_cultural_questions(ctx)    # CBI cultural fit — 2 perguntas fixas
combined       = behavioral_raw + cultural_raw
questions      = combined[:target_count]              # corta no target do modo
```

**Parte 4a — Big Five (top-3 traits por score):**

O gerador ordena os 5 traits do perfil Big Five por score decrescente e seleciona **1 pergunta por cada um dos top-3 traits**:

```python
sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)
for trait, score in sorted_traits[:3]:
    for q_data in BIG_FIVE_QUESTIONS[trait]:
        if score >= q_data["threshold"]:  # threshold varia por pergunta
            # seleciona esta pergunta e avanca para o proximo trait
            break
```

Cada trait tem 3 perguntas pre-definidas no banco `BIG_FIVE_QUESTIONS`. A selecao e determinada pelo threshold de score:

| Trait | Threshold baixo | Threshold medio | Threshold alto | Peso da pergunta |
|-------|----------------|-----------------|----------------|-----------------|
| Openness (abertura) | 50 | 60 | 70 | 0.6 a 0.8 |
| Conscientiousness (organizacao) | 50 | 60 | 70 | 0.6 a 0.8 |
| Extraversion (assertividade) | 50 | 60 | 70 | 0.6 a 0.8 |
| Agreeableness (empatia) | 40 | 60 | — | 0.6 a 0.8 |
| Stability (resiliencia emocional) | 50 | 60 | 70 | 0.6 a 0.8 |

> Peso: `0.8` se score do trait >= 70 (trait dominante), `0.6` se score < 70.

**Parte 4b — CBI Cultural Fit (2 perguntas fixas):**

O gerador tem 3 templates culturais pre-definidos e sempre usa os primeiros 2:

1. "O que voce busca em uma cultura de empresa? Quais valores sao importantes para voce?"
2. "Descreva o ambiente de trabalho ideal para voce. Como voce contribui para criar esse ambiente?"

`framework = "CBI"`, `category = "cultural"`, peso calibrado por senioridade.

#### Distribuicao Final por Modo

| Modo | Bloco 3 (Tecnico) | Bloco 4 (Comportamental) | Detalhe do Bloco 4 |
|------|-------------------|--------------------------|-------------------|
| **compact (6q)** | 3 perguntas | 3 perguntas | **3 Big Five (100%)** — CBI cultural nao e incluido |
| **full (10q)** | 5 perguntas | 5 perguntas | **3 Big Five (60%) + 2 CBI cultural (40%)** |

> No modo compact, `combined[:3]` retorna apenas as 3 perguntas Big Five — as 2 CBI culturais ficam de fora.  
> No modo full, `combined[:5]` inclui as 3 Big Five + 2 CBI culturais = 5 comportamentais.

#### Papel dos Frameworks no Pipeline — Resumo

| Framework | Bloco | Categoria DB | Papel na geracao | Papel no scoring |
|-----------|-------|-------------|------------------|-----------------|
| CBI (STAR) | 3 | `technical` | Estrutura STAR aplicada a hard skills | Detector de evidencias STAR na resposta |
| Bloom | 3 | `technical` | Define profundidade cognitiva da pergunta | Compara bloom esperado vs. demonstrado |
| Dreyfus | 3 e 4 | ambos | Calibra nivel de proficiencia exigido | Avalia proficiencia demonstrada na resposta |
| Big Five | 4 | `behavioral` | Seleciona trait prioritario e pergunta adequada | Nao entra no scorer deterministico |
| CBI cultural | 4 | `cultural` | Perguntas fixas de fit/motivacao | Detector de evidencias STAR na resposta |

> Bloom e Dreyfus sao atribuidos a **todas** as perguntas (tecnicos E comportamentais) no momento da geracao. Na Fase 2, o scorer usa `expected_bloom` e `expected_dreyfus` de cada pergunta para calcular o score da resposta.

#### Vinculo Pergunta → Skill → Score

Cada pergunta tecnica carrega a skill a que pertence. Quando o candidato responde, o scorer usa o nome da competencia como contexto:

```
Pergunta: "Descreva um projeto onde voce utilizou React de forma significativa."
  ├── skill:         "React"
  ├── framework:     "CBI"
  ├── bloom_level:   4 (Analisar)
  ├── dreyfus_stage: 3 (Competente — pleno)
  └── weight:        0.9

Resposta avaliada:
  ├── score:           7.5 / 10.0
  ├── bloom_achieved:  4
  ├── dreyfus_achieved: 3
  └── reasoning:       "Candidato descreveu projeto real com contexto claro..."
```

### 4.14 Pipeline WSI End-to-End — Fluxo Completo

O pipeline WSI tem **2 fases distintas**: configuracao (feita uma vez pelo recrutador) e triagem (executada em tempo real por candidato). A fonte unica de verdade e a tabela `job_screening_questions`.

---

#### FASE 1 — Configuracao da Vaga (Recrutador)

##### Passo 1 — Criacao do Job Description

**Interface:** `ScreeningConfigManager.tsx` → aba "Descricao" (componente `JDEvaluationPanel`)  
**Endpoint:** `POST /api/v1/wsi/generate-questions`  
**Arquivo:** `lia-agent-system/app/api/v1/wsi.py` (linhas 189–330)

O recrutador cola o texto do cargo. O backend chama Claude Sonnet com prompt que extrai:
- Cargo + senioridade
- Competencias tecnicas (hard skills)
- Competencias comportamentais (soft skills / traits)
- Requisitos eliminatorios (elegibilidade)

O resultado e salvo no objeto `job` no frontend e alimenta o Passo 2.

##### Passo 2 — Geracao das Perguntas de Triagem

**Interface:** aba "Perguntas de Triagem" — botao "Gerar WSI Compacto" ou "Gerar WSI Completo"  
**Endpoint frontend:** `POST /api/backend-proxy/wsi/generate-batch` (proxy Next.js)  
**Endpoint backend:** `POST /api/v1/wsi/screening-pipeline`  
**Arquivo proxy:** `route.ts` (generate-batch) — normaliza senioridade antes de repassar

```
"sr"     → "senior"
"jr"     → "junior"
"pl"     → "pleno"
```

**Passo 2a — Resolucao de Senioridade**  
`wsi_screening_pipeline.py` (linhas 101–157) — Servico: `SeniorityResolver`

| Modo | Fonte |
|------|-------|
| Explicito | Usa o informado pelo recrutador, valida com cross-check |
| Inferido | `multi_signal` — cruza titulo do cargo + texto do JD |
| Padrao | `pleno` (se nada disponivel) |

O resultado (`effective_seniority`) calibra os niveis Bloom e Dreyfus para toda a geracao.

**Passo 2b — Distribuicao por Modo**  
`wsi_screening_pipeline.py` (linhas 65–68)

```python
MODEL_DISTRIBUTIONS = {
    "compact": {"technical": 3, "behavioral": 3, "total": 6},
    "full":    {"technical": 5, "behavioral": 5, "total": 10},
}
```

**Passo 2c — Bloco 2: Empresa + Elegibilidade + Acao Afirmativa**  
`wsi_screening_pipeline.py` (linhas 188–223)

- Perguntas da empresa — carregadas do banco (`company_questions_raw`). Peso: `0.9` se eliminatoria, `0.7` se nao. `block_id = 2`
- Acao afirmativa — se `is_affirmative = true`, pergunta pre-definida injetada (PCD, racial, genero, 50+, LGBTQIA+). Resposta nao elimina o candidato

**Passo 2d — Bloco 3: Perguntas Tecnicas**  
`wsi_screening_pipeline.py` → `_build_technical_block()`  
`wsi_question_generator.py` → `_generate_technical_questions()`

- 1 pergunta CBI-STAR por skill (ate 5 skills)
- Templates rotacionam por senioridade (veja tabela em 4.13)
- Bloom level + Dreyfus stage atribuidos a cada pergunta
- `block_id = 3`, `source = "wsi_generated"`

```
Bloco 3 por senioridade — proporcao de frameworks:
  junior:    100% CBI
  pleno:     ~67% CBI + ~33% Bloom
  senior:    ~33% CBI + ~33% Bloom + ~33% Dreyfus
  lead/exec: 50% CBI + 50% Bloom
```

**Passo 2e — Bloco 4: Perguntas Comportamentais**  
`wsi_screening_pipeline.py` → `_build_behavioral_block()`  
`wsi_question_generator.py` → `_generate_behavioral_questions()` + `_generate_cultural_questions()`

```
compact (3q): 3 Big Five (top-3 traits por score do perfil)
full    (5q): 3 Big Five + 2 CBI cultural fit
```

- Big Five: 1 pergunta por trait, selecionada por threshold de score (veja tabela em 4.13)
- CBI cultural: 2 perguntas fixas de fit/motivacao
- `block_id = 4`, `source = "wsi_generated"`

**Passo 2f — Deduplicacao**  
`wsi_screening_pipeline.py` (linhas 79–87)

`SequenceMatcher` com threshold `0.65`. Perguntas com similaridade >= 65% sao descartadas. Se houver deficit apos deduplicacao, o pipeline gera extras e rebalanceia.

##### Passo 3 — Revisao e Salvamento pelo Recrutador

**Interface:** aba "Perguntas de Triagem" — accordion com 6 blocos  
**Endpoint:** `POST /api/backend-proxy/wsi/questions/save` → `POST /api/v1/wsi/questions/save`

O recrutador pode:
- Aceitar ou rejeitar perguntas individuais
- Reordenar perguntas
- Adicionar perguntas manuais
- Marcar como eliminatoria

Apos validacao, o frontend persiste em `job_screening_questions`:

```sql
INSERT INTO job_screening_questions (
  job_vacancy_id, question_text, category, question_type,
  weight, skill_targeted, block_id, is_active, created_at
)
```

**Este e o momento em que a fonte unica de verdade e criada.** A partir daqui, qualquer sessao de triagem para essa vaga le exatamente essas perguntas — sem geracao on-the-fly.

```
RECRUTADOR
    │
    ├─[1] Cola JD → extrai competencias tecnicas + comportamentais
    │
    ├─[2] Clica "Gerar WSI Compacto (6q) ou Completo (10q)"
    │       │
    │       └─→ screening-pipeline
    │               ├── resolve senioridade (multi-signal)
    │               ├── Bloco 2: elegibilidade + empresa + acao afirmativa
    │               │
    │               ├── Bloco 3 — Tecnico (3q compact / 5q full)
    │               │     ├── 1 pergunta CBI-STAR por skill (ate 5 skills)
    │               │     ├── template rotaciona por seniority:
    │               │     │     junior:    100% CBI
    │               │     │     pleno:    ~67% CBI + ~33% Bloom
    │               │     │     senior:   ~33% CBI + ~33% Bloom + ~33% Dreyfus
    │               │     │     lead/exec: 50% CBI + 50% Bloom
    │               │     └── Bloom level + Dreyfus stage atribuidos a cada pergunta
    │               │
    │               ├── Bloco 4 — Comportamental (3q compact / 5q full)
    │               │     ├── compact: 3 Big Five (top-3 traits por score)
    │               │     └── full:    3 Big Five + 2 CBI cultural fit
    │               │           Big Five: 1 pergunta por trait, selecionada por threshold
    │               │           CBI cultural: 2 perguntas fixas de fit/motivacao
    │               │
    │               └── deduplicacao SequenceMatcher >= 65%
    │
    └─[3] Revisa perguntas → salva em job_screening_questions
              (fonte unica de verdade criada aqui)
```

---

#### FASE 2 — Triagem do Candidato (Execucao em Tempo Real)

##### Passo 4 — Inicio da Sessao WSI

**Arquivo:** `wsi_interview_graph.py`  
**Tecnologia:** LangGraph (grafo de estado deterministico)

Quando um candidato inicia a triagem (via `/pub/triagem` ou link enviado), o sistema cria um `WSIInterviewState`:

```python
@dataclass
class WSIInterviewState:
    session_id: str         # UUID unico por sessao
    company_id: str
    candidate_id: str
    job_id: str             # Chave para buscar as perguntas salvas
    interview_level: str    # "quick" | "standard" | "full"
    question_blocks: List[WSIQuestionBlock]  # preenchido no load_context
    current_question_index: int
    responses: List[WSIResponseRecord]
    technical_score: float
    behavioral_score: float
    wsi_final_score: Optional[float]
```

O estado e serializado em JSON e persistido via `PostgresSaver` do LangGraph a cada no, garantindo retomada em caso de falha.

##### Passo 5 — No load_context: Carregamento das Perguntas

**Arquivo:** `wsi_interview_graph.py` → `load_context()` (linhas 276–432)

Dois gates de seguranca sao executados antes de qualquer pergunta:

**SEG-4 — Gate de Consentimento LGPD:**

```python
consent = await ConsentCheckerService.check_candidate_consent(
    candidate_id, company_id, purpose="ai_screening"
)
if not consent.allowed:
    state.error = "LGPD_CONSENT_REVOKED"
    state.stage = ERROR
    return state  # sessao abortada
```

**Hierarquia de carregamento das perguntas:**

```
1. saved_db          ← FONTE UNICA DE VERDADE (caminho normal)
   SELECT * FROM job_screening_questions
   WHERE job_vacancy_id = :job_id AND is_active = true
   ORDER BY created_at ASC

2. fallback_pipeline ← WARNING no log (recrutador nao configurou)
   WSIScreeningPipeline.build_pipeline() on-the-fly

3. hardcoded_fallback ← 2 perguntas genericas de emergencia
```

O `source` e logado em `state.execution_log` para auditoria:

```json
{"node": "load_context", "source": "saved_db", "questions_loaded": 10}
```

##### Passo 6 — Loop de Perguntas

```
load_context
    ↓
generate_question ──→ (apresenta pergunta N ao candidato)
    ↓
[candidato responde no chat]
    ↓
validate_response
    ├── skip/vazio → score=0, avanca
    ├── SEG-1: PromptInjectionGuard → bloqueia se risco "high"
    └── valida → score_response
                     ↓
                  advance
                     ├── mais perguntas → generate_question
                     └── fim → generate_feedback
```

**SEG-1 — Injecao de Prompt:**

```python
result = PromptInjectionGuard().check(response_clean)
if result.risk_level == "high":
    score = 0.0, reasoning = "bloqueada por seguranca"
```

##### Passo 7 — No score_response: Pontuacao de cada Resposta

**Arquivo:** `wsi_interview_graph.py` → `score_response()` (linhas 528–607)  
**Servico:** `wsi_deterministic_scorer.py`

```python
score_result = await calculate_wsi_deterministic(
    candidate_response=response_text,
    expected_bloom=block.bloom_level,    # 1–6
    expected_dreyfus=block.dreyfus_level, # 1–5
    competency=block.competency,
    max_score=block.max_score,            # 10.0 padrao
)
```

O resultado retorna: `score`, `bloom_achieved`, `dreyfus_achieved`, `reasoning`.

**Acumulacao de score por dimensao:**

```python
normalized = (score / max_score) * 10.0
if block_type == "technical":
    state.technical_score = (state.technical_score + normalized) / 2
elif block_type in ("behavioral", "situational"):
    state.behavioral_score = (state.behavioral_score + normalized) / 2
```

**Audit trail automatico (BCB 498 / SOX):**

```python
await audit_service.log_decision(
    domain="cv_screening",
    decision_type="wsi_score",
    decision=f"block_{block.block_id}_scored",
    metadata={"score": ..., "bloom_achieved": ..., "competency": ...}
)
```

##### Passo 8 — No generate_feedback: Score Final e Recomendacao

**Arquivo:** `wsi_interview_graph.py` → `generate_feedback()` (linhas 623–721)

```python
wsi_final_score = calculate_final_wsi_score(
    technical_scores  = [("technical",   technical_score,  1.0)],
    behavioral_scores = [("behavioral",  behavioral_score, 0.6),
                         ("situational", situational_score, 0.4)],
)
```

**Classificacao automatica:**

| Score Final | Classificacao | Acao Automatica |
|-------------|---------------|-----------------|
| >= 7.0 | aprovado | Avanca no pipeline |
| 5.0 – 6.9 | aguardando | Revisao manual |
| < 5.0 | reprovado | Email de feedback (nao bloqueante) |

**Acoes automaticas ao finalizar:**
- Audit log final com metadados completos
- Metrica Prometheus: `record_confidence(domain="cv_screening", confidence=score/10)`
- Email de feedback: se `recommendation == "reprovado"` e candidato tem email, `candidate_feedback_service.send_gate_feedback()` (asyncio.ensure_future)

---

#### Tabelas de Banco Envolvidas

| Tabela | Papel |
|--------|-------|
| `job_vacancies` | Dados da vaga (titulo, senioridade, departamento) |
| `job_screening_questions` | Fonte unica de verdade — perguntas salvas pelo recrutador |
| `wsi_sessions` | Estado serializado de cada sessao (LangGraph PostgresSaver) |
| `audit_log` | Trail de cada decisao de score e avaliacao final |
| `candidate_consents` | Verificacao LGPD antes de iniciar entrevista |

#### Mapa de Arquivos por Responsabilidade

| Arquivo | Responsabilidade |
|---------|-----------------|
| `ScreeningConfigManager.tsx` | UI do recrutador — JD, geracao, selecao e salvamento |
| `route.ts` (generate-batch) | Proxy Next.js → normaliza senioridade → screening-pipeline |
| `route.ts` (questions/save) | Proxy Next.js → persiste perguntas selecionadas no DB |
| `wsi.py` | Router FastAPI — endpoints `/generate-questions`, `/screening-pipeline`, `/questions/save` |
| `wsi_screening_pipeline.py` | Orquestrador — resolve senioridade, gera Blocos 3 e 4, deduplica |
| `wsi_question_generator.py` | Gerador de perguntas tecnicas/comportamentais/culturais por skill |
| `wsi_service.py` | Analise de JD, extracao de competencias, schemas Bloom/Dreyfus/Big Five |
| `wsi_interview_graph.py` | Grafo LangGraph — conduz a entrevista, pontua, gera recomendacao |
| `wsi_deterministic_scorer.py` | Calculo deterministico de score por resposta |

---

## 5. Camada 4: Calibration Loop

### 5.1 Proposito

Ajustar continuamente os pesos e thresholds com base no feedback do recrutador e resultados de contratacao.

### 5.2 Tipos de Feedback

| Tipo | Descricao | Exemplo |
|------|-----------|---------|
| **Explicito** | Thumbs up/down do recrutador | Concordar ou discordar da recomendacao LIA |
| **Implicito** | Acoes do recrutador | Avancar candidato com score baixo = feedback positivo |
| **Pos-Contratacao** | Sucesso da contratacao | Candidato performou bem apos 6 meses |

### 5.3 Logica de Ajuste

```
SE recrutador.avanca(candidato) E lia.score < 60
   ENTAO aumentar peso dos fatores que candidato pontuou bem
   
SE recrutador.reprova(candidato) E lia.score > 80
   ENTAO diminuir peso dos fatores que candidato pontuou bem
   
SE pos_contratacao.sucesso = TRUE E lia.score era baixo
   ENTAO recalibrar thresholds de aprovacao
```

### 5.4 Metricas de Qualidade

| Metrica | Descricao | Meta |
|---------|-----------|------|
| Taxa de concordancia | % de vezes que recrutador concorda com LIA | > 80% |
| Taxa de contratacao por faixa | Candidatos contratados por faixa de score | Correlacao positiva |
| Tempo de permanencia | Duracao na empresa por score inicial | Correlacao positiva |

---

## 6. Integracao das Camadas

### 6.1 Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE AVALIACAO                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ETAPA 1: PRE-REQUISITOS                                                    │
│  ────────────────────────                                                   │
│  Input: Dados do candidato                                                  │
│  Output: Elegivel/Nao Elegivel + Motivo                                     │
│  Se NAO ELEGIVEL → Encerra com explicacao                                   │
│                                                                              │
│        ↓ (se elegivel)                                                      │
│                                                                              │
│  ETAPA 2: RUBRICAS BARS (CV)                                                │
│  ────────────────────────────                                               │
│  Input: CV + Requisitos da vaga                                             │
│  Output: Score 0-100% + Recomendacao                                        │
│  Se < 40% → Arquivar com explicacao                                         │
│                                                                              │
│        ↓ (se >= 40%)                                                        │
│                                                                              │
│  ETAPA 3: TRIAGEM WSI (Opcional)                                            │
│  ─────────────────────────────────                                          │
│  Input: Candidato + Competencias da vaga                                    │
│  Output: Score WSI 0-10 + Classificacao + Perfil Big Five                   │
│  Se < 5.0 → Reprovado | 5.0-6.9 → Aguardando | >= 7.0 → Aprovado           │
│                                                                              │
│        ↓                                                                    │
│                                                                              │
│  ETAPA 4: SCORE FINAL AGREGADO                                              │
│  ─────────────────────────────────                                          │
│  Se tem WSI: Score = (Rubricas × 0.5) + (WSI × 0.5)                         │
│  Se nao tem WSI: Score = Rubricas × 1.0                                     │
│  Output: Recomendacao final + Parecer estruturado                           │
│                                                                              │
│        ↓                                                                    │
│                                                                              │
│  ETAPA 5: CALIBRATION (Continuo)                                            │
│  ─────────────────────────────────                                          │
│  Coleta feedback do recrutador                                              │
│  Ajusta pesos para proximas avaliacoes                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Cenarios de Aplicacao

| Cenario | Camadas Aplicadas | Dados Disponiveis |
|---------|-------------------|-------------------|
| **Triagem inicial (CV)** | Pre-req + Rubricas | Apenas CV |
| **Triagem completa** | Pre-req + Rubricas + WSI | CV + Respostas triagem |
| **Comparacao de candidatos (triados)** | Todas as camadas | CV + WSI + Big Five |
| **Comparacao de candidatos (nao triados)** | Pre-req + Rubricas | Apenas CV |
| **Parecer automatico** | Todas disponiveis | Variavel por candidato |

---

## 7. Compliance e Etica

### 7.1 Anti-Vies

**Criterios NAO Considerados:**
- Idade, genero, raca, religiao, orientacao sexual
- Estado civil, numero de filhos
- Endereco/bairro de residencia
- Aparencia fisica (quando via video)

**Regras de Protecao:**
- Focar exclusivamente em competencias e fit para a funcao
- Auditoria periodica de resultados por demografia
- Gaps de carreira NAO sao penalizados (contexto informativo apenas)
- Transicoes frequentes NAO sao penalizadas
- Auditoria externa de bias planejada (Warden AI - Q3 2026)

### 7.2 Transparencia (EU AI Act)

**Explicabilidade:**
- Scores sao explicaveis por fator individual
- Cada dimensao do score e visivel para recrutador
- Candidato pode solicitar razoes da decisao (Art. 22 GDPR)

**Interface:**
- Botao "Solicitar Revisao Humana" disponivel em todas as decisoes
- Recrutador pode ajustar score com justificativa registrada
- Override requer motivo (auditoria de compliance)

### 7.3 LGPD/GDPR

**Consentimento:**
- Consentimento explicito antes de analise automatizada
- Termo de uso apresentado no inicio da triagem
- Candidato pode recusar triagem automatizada (processo manual alternativo)

**Direitos do Titular:**
- Direito de opt-out a qualquer momento
- Direito de acesso aos dados coletados
- Direito de explicacao da decisao (Art. 20 LGPD / Art. 22 GDPR)
- Direito de correcao de dados incorretos
- Direito de eliminacao (dentro do periodo de retencao legal)

**Retencao de Dados:**
- Dados de triagem: 2 anos apos encerramento do processo
- Dados de contratados: periodo do contrato + 5 anos
- Logs de auditoria: 5 anos

### 7.4 Conformidade Regulatoria

| Regulacao | Requisito | Implementacao | Status |
|-----------|-----------|---------------|--------|
| **EU AI Act Art. 13** | Transparencia | Explicacao de cada fator do score | ✅ Implementado |
| **EU AI Act Art. 14** | Supervisao humana | Revisao humana disponivel | ✅ Implementado |
| **LGPD Art. 20** | Decisoes automatizadas | Explicacao + opt-out | ✅ Implementado |
| **GDPR Art. 22** | Direito de explicacao | Parecer estruturado | ✅ Implementado |
| **NYC LL144** | Auditoria de bias | Auditoria externa | 🟡 Planejado Q3 2026 |
| **SOC 2 Type II** | Controles de seguranca | Logs de auditoria | ✅ Implementado |

### 7.5 Auditoria e Monitoramento

| Metrica | Frequencia | Responsavel |
|---------|------------|-------------|
| Distribuicao de scores por genero | Mensal | Data Science |
| Distribuicao de scores por idade | Mensal | Data Science |
| Taxa de override por recrutador | Semanal | RH Ops |
| Solicitacoes de revisao humana | Diario | Sistema |
| Reclamacoes de candidatos | Continuo | DPO |

---

## 8. Referencias Academicas

### Rubricas e Estruturacao
- Schmidt, F. L., & Hunter, J. E. (1998). The validity and utility of selection methods in personnel psychology. *Psychological Bulletin, 124*(2), 262-274.
- Campion, M. A., Palmer, D. K., & Campion, J. E. (1997). A review of structure in the selection interview. *Personnel Psychology, 50*(3), 655-702.
- Smith, P. C., & Kendall, L. M. (1963). Retranslation of expectations. *Journal of Applied Psychology, 47*(2), 149-155.

### Frameworks Cognitivos e Comportamentais
- Bloom, B. S. (1956). Taxonomy of Educational Objectives.
- Anderson, L. W., et al. (2001). A Taxonomy for Learning, Teaching, and Assessing.
- Dreyfus, S. E., & Dreyfus, H. L. (1980). A Five-Stage Model of Mental Activities.
- McClelland, D. C. (1973). Testing for competence rather than for intelligence. *American Psychologist, 28*(1), 1-14.

### Personalidade
- Goldberg, L. R. (1992). The development of markers for the Big-Five factor structure. *Psychological Assessment, 4*(1), 26-42.
- Costa, P. T., & McCrae, R. R. (1992). Revised NEO Personality Inventory.

### Competencias
- SFIA Foundation. Skills Framework for the Information Age v8.
- Cameron, K. S., & Quinn, R. E. (2011). Competing Values Framework.

---

## 9. Comparacao de Candidatos

### 9.1 Visao Geral

A comparacao de candidatos utiliza metodologias adaptativas baseadas nos dados disponiveis. O sistema detecta automaticamente o cenario e aplica a metodologia apropriada.

### 9.2 Deteccao de Cenario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE DETECCAO DE CENARIO                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SE candidatos.todos têm vacancy_candidate.wsi_completed = true             │
│     PARA a mesma job_vacancy_id                                             │
│  ENTAO → Cenario A (metodologia completa)                                   │
│                                                                              │
│  SENAO SE job_vacancy_id especificado                                       │
│        MAS candidatos NAO tem triagem WSI para esta vaga                    │
│  ENTAO → Cenario B (apenas Rubricas)                                        │
│                                                                              │
│  SENAO SE nenhuma job_vacancy_id especificada                               │
│  ENTAO → Cenario C (comparacao geral por perfil)                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Cenarios de Comparacao

#### Cenario A: Candidatos Triados na Mesma Vaga

**Dados Disponiveis:** CV + WSI + Big Five + Respostas de triagem

| Dimensao | Peso | Fonte de Dados |
|----------|------|----------------|
| Rubricas BARS | 40% | CV vs Requisitos da vaga |
| Score WSI | 25% | Respostas da triagem |
| Big Five | 15% | Inferido das respostas |
| Pre-requisitos | 10% | Validacao explicita |
| Historico LIA | 10% | Triagens anteriores |

#### Cenario B: Candidatos Nao Triados para a Vaga

**Dados Disponiveis:** Apenas CV/LinkedIn

| Dimensao | Peso | Fonte de Dados |
|----------|------|----------------|
| **Rubricas BARS** | 60% | CV vs Requisitos do perfil |
| **Pre-requisitos** | 25% | Idiomas, Disponibilidade, etc. |
| **Historico LIA** | 15% | Triagens anteriores em OUTRAS vagas (se houver) |
| ~~WSI~~ | N/A | Nao disponivel |
| ~~Big Five~~ | N/A | Nao disponivel |

**Alerta na UI:**
> "Comparacao parcial: candidatos nao foram triados para esta vaga. A comparacao usa apenas dados de CV. [Iniciar Triagem WSI] para dados mais precisos."

#### Cenario C: Comparacao Geral (Sem Vaga)

**Dados Disponiveis:** CV/LinkedIn + historico de triagens

| Dimensao | Peso | Fonte de Dados |
|----------|------|----------------|
| **Historico LIA** | 50% | Media de scores em vagas anteriores |
| **Completude do Perfil** | 30% | Qualidade dos dados disponiveis |
| **Recencia** | 20% | Ultima atividade/atualizacao |

### 9.4 Estrutura de Resposta da Comparacao

```json
{
  "comparison_id": "comp_uuid",
  "scenario": "A|B|C",
  "scenario_description": "Candidatos triados na mesma vaga",
  "methodology_used": ["rubricas_bars", "wsi", "big_five"],
  "data_completeness": {
    "candidate_1": { "cv": true, "wsi": true, "big_five": true },
    "candidate_2": { "cv": true, "wsi": true, "big_five": true }
  },
  "winner": {
    "candidate_id": "uuid",
    "confidence": 0.85,
    "reasoning": "Candidato 1 supera em competencias tecnicas (WSI 7.8 vs 6.9) e alinhamento cultural"
  },
  "dimension_comparison": {
    "technical": { "candidate_1": 85, "candidate_2": 72, "winner": "candidate_1" },
    "behavioral": { "candidate_1": 78, "candidate_2": 82, "winner": "candidate_2" },
    "cultural": { "candidate_1": 90, "candidate_2": 75, "winner": "candidate_1" }
  },
  "scenarios_recommendation": {
    "short_term": { "best": "candidate_1", "reason": "Maior fit tecnico imediato" },
    "long_term": { "best": "candidate_2", "reason": "Maior potencial de crescimento" },
    "leadership": { "best": "candidate_1", "reason": "Perfil mais assertivo (Big Five E=75)" }
  }
}
```

---

## 10. Parecer Automatico

### 10.1 Visao Geral

O Parecer Automatico (LIA Opinion) e um documento estruturado que resume a avaliacao de um candidato para uma vaga especifica. A estrutura e adaptativa baseada nos dados disponiveis.

### 10.2 Estrutura de 7 Secoes

| Secao | Descricao | Dados Requeridos | Obrigatorio |
|-------|-----------|------------------|-------------|
| 1. Resumo Executivo | Sintese de 2-3 linhas | CV | Sim |
| 2. Experiencia Profissional | Analise de trajetoria | CV | Sim |
| 3. Competencias Tecnicas | Avaliacao de hard skills | CV + WSI (se houver) | Sim |
| 4. Competencias Comportamentais | Avaliacao de soft skills | WSI + Big Five (se houver) | Condicional |
| 5. Resultados da Triagem | Detalhes da triagem WSI/voz | Triagem completa | Condicional |
| 6. Pontos Fortes e Atencao | Destaques e gaps | CV + Triagem | Sim |
| 7. Recomendacao Final | Decisao estruturada | Todos disponiveis | Sim |

### 10.3 Geracao Adaptativa por Cenario

#### Cenario: Apenas CV

```
SECOES GERADAS:
✅ 1. Resumo Executivo
✅ 2. Experiencia Profissional
✅ 3. Competencias Tecnicas (inferidas do CV)
❌ 4. Competencias Comportamentais (indisponivel)
❌ 5. Resultados da Triagem (indisponivel)
✅ 6. Pontos Fortes e Atencao
✅ 7. Recomendacao Final (parcial)

NOTA NO PARECER:
"Este parecer foi gerado com base apenas no CV. Para uma avaliacao mais 
completa, recomenda-se realizar a triagem WSI com o candidato."
```

#### Cenario: CV + Triagem Texto

```
SECOES GERADAS:
✅ 1. Resumo Executivo
✅ 2. Experiencia Profissional
✅ 3. Competencias Tecnicas (CV + WSI)
✅ 4. Competencias Comportamentais (inferido)
✅ 5. Resultados da Triagem (texto)
✅ 6. Pontos Fortes e Atencao
✅ 7. Recomendacao Final
```

#### Cenario: CV + Triagem Voz + Entrevista

```
SECOES GERADAS:
✅ Todas as 7 secoes
✅ Analise de tom e confianca (voz)
✅ Big Five completo
✅ Transcricao de entrevista
✅ Recomendacao com alta confianca
```

### 10.4 Estrutura de Resposta

```json
{
  "parecer_id": "par_uuid",
  "candidate_id": "uuid",
  "job_id": "uuid",
  "generated_at": "2026-01-22T10:00:00Z",
  "data_sources": ["cv", "wsi_text", "wsi_voice", "interview"],
  "completeness_score": 0.95,
  "sections": {
    "executive_summary": {
      "available": true,
      "content": "Candidato senior com 8 anos de experiencia em Python...",
      "confidence": 0.92
    },
    "professional_experience": {
      "available": true,
      "years_total": 8,
      "progression": "linear_ascending",
      "highlights": ["Tech Lead na XYZ", "Projeto de ML em producao"]
    },
    "technical_competencies": {
      "available": true,
      "source": "cv+wsi",
      "skills": [
        { "name": "Python", "level": "expert", "wsi_score": 8.5 },
        { "name": "Django", "level": "advanced", "wsi_score": 8.0 }
      ]
    },
    "behavioral_competencies": {
      "available": true,
      "source": "wsi+big_five",
      "big_five": { "O": 72, "C": 85, "E": 65, "A": 78, "stability": 70 },
      "highlights": ["Alta conscienciosidade", "Colaborativo"]
    },
    "screening_results": {
      "available": true,
      "wsi_score": 7.8,
      "responses_summary": "Respostas consistentes e detalhadas..."
    },
    "strengths_attention": {
      "strengths": ["Experiencia solida", "Boa comunicacao"],
      "attention_points": ["Experiencia limitada em cloud"]
    },
    "final_recommendation": {
      "decision": "RECOMMENDED",
      "confidence": 0.88,
      "reasoning": "Candidato atende requisitos tecnicos e comportamentais...",
      "suggested_next_step": "Agendar entrevista tecnica"
    }
  }
}
```

### 10.5 Niveis de Recomendacao

| Nivel | Descricao | Acao Sugerida |
|-------|-----------|---------------|
| **HIGHLY_RECOMMENDED** | Score >= 85%, sem gaps criticos | Agendar entrevista imediatamente |
| **RECOMMENDED** | Score 70-84%, gaps menores | Prosseguir no processo |
| **POTENTIAL** | Score 55-69%, gaps a avaliar | Avaliar gaps em entrevista |
| **NOT_RECOMMENDED** | Score < 55% ou gap critico | Nao prosseguir |
| **INCOMPLETE** | Dados insuficientes | Solicitar mais informacoes |

### 10.6 Score por Competencia no Parecer

#### Competencias Tecnicas — score individual por competencia do JD

Cada competencia tecnica extraida do JD na Etapa 1 (secao 4.13) recebe um score individual calculado deterministicamente. O parecer cita cada competencia pelo nome original com seu score:

```json
"technical_competencies": {
  "source": "wsi",
  "pontos_fortes": [
    "Python (8.5/10)",
    "Django/FastAPI (8.0/10)"
  ],
  "gaps": [
    "AWS (4.2/10)"
  ],
  "evidencias": [
    "Candidato mencionou deploy em producao com 50k usuarios",
    "Descreveu migracao de banco com zero downtime"
  ]
}
```

O criterio de classificacao no parecer e (escala 0–10):
- `pontos_fortes`: competencias com score >= 7.0
- `gaps`: competencias com score < 5.0
- Competencias entre 5.0 e 6.9 nao aparecem em nenhum dos dois grupos (faixa media)

#### Competencias Comportamentais — mapeamento para 4 dimensoes fixas

As competencias comportamentais extraidas do JD (ex: "Lideranca", "Comunicacao Assertiva") sao avaliadas durante a triagem e alimentam o `behavioral_wsi` geral. No entanto, o bloco `behavioral_analysis` do parecer nao exibe as competencias comportamentais especificas do JD — ele exibe **4 dimensoes fixas** inferidas pelo LLM a partir das respostas comportamentais:

| Dimensao Fixa | Score | Origem |
|---------------|-------|--------|
| `colaboracao` | 0–5.0 | Inferida pelo LLM das respostas comportamentais |
| `inovacao` | 0–5.0 | Inferida pelo LLM das respostas comportamentais |
| `organizacao` | 0–5.0 | Inferida pelo LLM das respostas comportamentais |
| `resiliencia` | 0–5.0 | Inferida pelo LLM das respostas comportamentais |

> **Nota arquitetural:** O cruzamento JD ↔ avaliacao e completo no lado tecnico (competencias nomeadas com score) e parcial no lado comportamental (score WSI comportamental geral existe, mas o parecer exibe dimensoes fixas, nao as competencias especificas da vaga).

#### Fit Cultural

Avaliado separadamente com score geral e lista de valores alinhados/pontos de atencao:

```json
"cultural_fit": {
  "score": 7.8,
  "valores_alinhados": ["Colaboracao", "Inovacao continua"],
  "atencoes": ["Preferencia por trabalho individual em contextos colaborativos"]
}
```

O campo `atencoes` e obrigatorio quando WSI geral < 5.0 (threshold de reprovado).

### 10.7 Feedback ao Candidato (PersonalizedFeedbackService)

Apos a decisao final da triagem WSI, a LIA gera um feedback estruturado e personalizado para o candidato. Este feedback **nao e enviado automaticamente** — passa por um fluxo de aprovacao do recrutador.

#### Fluxo de Geracao e Envio

```
[Decisao WSI] → [LLM gera rascunho] → [FairnessGuard verifica conteudo]
      → [Salvo como DRAFT para aprovacao] → [Recrutador aprova ou edita]
      → [Enviado via email e/ou WhatsApp]
```

Se o FairnessGuard detectar conteudo discriminatorio no rascunho, o texto e substituido por aviso de revisao de compliance antes de ser apresentado ao recrutador.

#### Canais Suportados

| Canal | Formato |
|-------|---------|
| Email | Assunto personalizado + corpo HTML + corpo texto puro |
| WhatsApp | Mensagem compacta (limite de caracteres para o canal) |
| Ambos | Envio simultaneo nos dois canais |

#### Campos Gerados

| Campo | Descricao |
|-------|-----------|
| `subject` | Linha de assunto do email (personalizada com nome da vaga) |
| `body_text` | Corpo completo em texto puro |
| `body_html` | Corpo completo em HTML formatado |
| `whatsapp_message` | Versao compacta para WhatsApp |
| `key_points` | 3-5 pontos principais do desempenho avaliado |
| `development_suggestions` | Sugestoes especificas por competencia com gap |
| `recommended_resources` | Cursos, projetos e referencias por area de desenvolvimento |
| `development_plan.curto_prazo` | Acoes para os proximos 30-60 dias |
| `development_plan.medio_prazo` | Acoes para os proximos 3-6 meses |

#### Tom Configuravel

| Tom | Descricao | Uso Recomendado |
|-----|-----------|----------------|
| `warm` | Empatico e encorajador | Candidatos com WSI medio, com potencial |
| `professional` | Formal e objetivo | Padrao para a maioria dos casos |
| `encouraging` | Motivacional com foco em desenvolvimento | Candidatos jovens ou com gaps identificados |

#### Exemplo de Estrutura de Resposta

```json
{
  "subject": "Feedback da sua triagem — Vaga Desenvolvedor Python Senior",
  "body_text": "Ola [Nome], agradecemos sua participacao...",
  "key_points": [
    "Forte dominio de Python com evidencias praticas solidas",
    "AWS ainda em desenvolvimento — oportunidade de crescimento"
  ],
  "development_suggestions": [
    "Aprofundar AWS com foco em servicos de compute e storage"
  ],
  "recommended_resources": [
    "AWS Certified Solutions Architect — Associate (AWS Training)",
    "Projeto pratico: deploy de aplicacao containerizada na AWS"
  ],
  "development_plan": {
    "curto_prazo": ["Completar modulo basico de EC2 e S3 em 30 dias"],
    "medio_prazo": ["Obter certificacao AWS Associate em 4 meses"]
  }
}
```

> O feedback e baseado nos scores reais por competencia (`ResponseAnalysis`) e na decisao final do WSI. Candidatos aprovados recebem feedback de reforco; candidatos em aguardo ou nao aprovados recebem plano de desenvolvimento detalhado.

---

## 11. Ranking LIA

### 11.1 Visao Geral

O Ranking LIA ordena candidatos em uma vaga ou busca baseado em uma formula ponderada que integra todas as camadas de avaliacao.

### 11.2 Formula de Ranking

```
Ranking_Score = (
    Rubricas_Score × W_rubricas +
    WSI_Score × W_wsi +
    Prerequisites_Score × W_prereq +
    Recency_Boost × W_recency +
    Calibration_Adjustment
) × Completeness_Factor

Onde:
- W_rubricas = 0.40 (40%)
- W_wsi = 0.30 (30%) - aplicado apenas se WSI disponivel
- W_prereq = 0.15 (15%)
- W_recency = 0.15 (15%)
- Calibration_Adjustment = -5 a +5 pontos baseado em historico
- Completeness_Factor = 1.0 (dados completos) a 0.7 (apenas CV)
```

### 11.3 Componentes do Score

#### Rubricas Score (0-100)
- Calculado conforme Secao 3 (BARS)
- Normalizado para escala 0-100

#### WSI Score (0-100)
- Convertido de escala 0–10 para 0–100: `WSI_100 = WSI_10 × 10`
- Se nao disponivel, redistribui peso para Rubricas

#### Prerequisites Score (0-100)
- 100 se atende todos os pre-requisitos
- Penalidade de -20 por cada pre-requisito nao atendido
- Minimo = 0

#### Recency Boost (0-100)
| Ultima Atividade | Boost |
|------------------|-------|
| Ultimos 7 dias | 100 |
| 8-30 dias | 80 |
| 31-90 dias | 60 |
| 91-180 dias | 40 |
| > 180 dias | 20 |

### 11.4 Redistribuicao de Pesos por Disponibilidade

| Dados Disponiveis | Rubricas | WSI | Prereq | Recency |
|-------------------|----------|-----|--------|---------|
| **CV + WSI + Prereq** | 40% | 30% | 15% | 15% |
| **CV + Prereq (sem WSI)** | 55% | 0% | 25% | 20% |
| **Apenas CV** | 60% | 0% | 20% | 20% |

### 11.5 Calibration Adjustment

O ajuste de calibracao e aplicado baseado no historico de feedback:

```
SE candidato.feedback_positivo > candidato.feedback_negativo
   Calibration_Adjustment = +min(5, feedback_positivo × 0.5)
   
SE candidato.feedback_negativo > candidato.feedback_positivo
   Calibration_Adjustment = -min(5, feedback_negativo × 0.5)
```

### 11.6 Ordenacao Final

1. Candidatos sao ordenados por `Ranking_Score` decrescente
2. Em caso de empate, usar `WSI_Score` como desempate
3. Em caso de empate persistente, usar `Recency` como desempate
4. Candidatos com pre-requisitos criticos nao atendidos vao para o final

### 11.7 Estrutura de Resposta

```json
{
  "ranking": [
    {
      "position": 1,
      "candidate_id": "uuid",
      "ranking_score": 87.5,
      "components": {
        "rubricas_score": 85,
        "wsi_score": 84,
        "prerequisites_score": 100,
        "recency_boost": 80,
        "calibration_adjustment": 2.5
      },
      "completeness_factor": 1.0,
      "data_sources": ["cv", "wsi", "prereq"],
      "recommendation": "HIGHLY_RECOMMENDED"
    },
    {
      "position": 2,
      "candidate_id": "uuid2",
      "ranking_score": 72.3,
      "components": {
        "rubricas_score": 78,
        "wsi_score": null,
        "prerequisites_score": 100,
        "recency_boost": 60
      },
      "completeness_factor": 0.85,
      "data_sources": ["cv", "prereq"],
      "note": "WSI nao disponivel - score parcial"
    }
  ],
  "metadata": {
    "total_candidates": 25,
    "ranked_candidates": 25,
    "methodology_version": "1.0",
    "weights_used": { "rubricas": 0.40, "wsi": 0.30, "prereq": 0.15, "recency": 0.15 }
  }
}
```

---

## 12. Historico de Versoes

| Versao | Data | Alteracoes |
|--------|------|------------|
| 1.0 | Janeiro 2026 | Consolidacao de WSI + Rubricas + Pre-requisitos + Calibration. Remocao de Similar Search (metodologia arquivada). |
| 1.1 | Janeiro 2026 | Adicionadas metodologias: Comparacao de Candidatos, Parecer Automatico, Ranking LIA. |
| 1.2 | Marco 2026 | Secao 4.6 corrigida para refletir a estrutura real de 6 blocos (0–5) com tipos e origens de cada bloco. Secao 4.7 e 4.8 atualizadas com formula real do codigo e escala 0–10 por resposta. Secao 4.13 reescrita com dados extraidos diretamente do codigo: MODEL_DISTRIBUTIONS (compact=6q / full=10q), proporcao de frameworks CBI/Bloom/Dreyfus por senioridade no Bloco 3, logica Big Five top-3 traits + threshold por pergunta no Bloco 4, distribuicao por modo (compact = 3 Big Five 100%; full = 3 Big Five + 2 CBI cultural). Adicionada secao 4.14 com Pipeline WSI End-to-End completo (Fase 1: passos 1-3 de configuracao; Fase 2: passos 4-8 de triagem), incluindo diagrama de fluxo, tabelas de banco e mapa de arquivos por responsabilidade. |

---

## 13. Documentos Arquivados

Os seguintes documentos foram consolidados neste documento:
- `docs/WSI_METHODOLOGY_REFERENCE.md` - Mantido como referencia detalhada de WSI
- `docs/LIA_METHODOLOGY.md` - Mantido como referencia detalhada de Rubricas
- `docs/archived/SIMILAR_SEARCH_LLM_METHODOLOGY.md.archived` - Arquivado (substituido por Rubricas)
