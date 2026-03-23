# Metodologia Unificada LIA - WeDoTalent

## Referencia Tecnica para Implementacao

**Versao:** 1.1  
**Data:** Janeiro 2026  
**Status:** Documento oficial consolidado  
**Fonte:** Consolidacao de WSI_METHODOLOGY_REFERENCE.md + LIA_METHODOLOGY.md  
**Atualizacao:** Adicionada secao 4.11 (Saturacao Inteligente)

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

### 4.6 Estrutura de 7 Blocos

| Bloco | Objetivo | Duracao |
|-------|----------|---------|
| Bloco 0 | Abertura e contexto | 0:30 min |
| Bloco 1 | Elegibilidade (disponibilidade, salario) | 1:00 min |
| Bloco 2 | Competencias Tecnicas (3-6 perguntas) | 3-4 min |
| Bloco 3 | Competencias Comportamentais (2-4 perguntas) | 2-3 min |
| Bloco 4 | Cultural Fit | 1:00 min |
| Bloco 5 | Fechamento e score | 0:30 min |
| Resultado | Apresentacao do WSI | - |

### 4.7 Formula do WSI

```
Score_skill = (0.6 × Autodeclaracao) + (0.4 × Contexto)
WSI_final = Σ(Peso_skill × Score_skill) / 100

Distribuicao de Pesos Recomendada:
- Competencias Tecnicas: 70%
- Competencias Comportamentais: 30%
```

### 4.8 Faixas de WSI

| Faixa | Interpretacao | Descricao |
|-------|---------------|-----------|
| 4.5 - 5.0 | Excelente | Especialista |
| 4.0 - 4.4 | Alto | Profissional autonomo |
| 3.0 - 3.9 | Medio | Profissional competente |
| 2.0 - 2.9 | Regular | Iniciante tecnico |
| < 2.0 | Baixo | Gap critico |

### 4.9 Penalidades e Bonus

**Penalidades:**

| Situacao | Penalidade |
|----------|------------|
| Inflacao de score (autodeclara alto, contexto pobre) | -0.5 a -1.5 |
| Resposta generica | -0.5 |
| Falta de contexto | -0.3 |
| Resposta aparenta ser copiada | -1.0 |

**Bonus:**

| Situacao | Bonus |
|----------|-------|
| Humildade (autodeclara baixo, contexto alto) | +0.5 |
| Evidencias excepcionais | +0.3 |

### 4.10 Regras de Aprovacao Automatica

**Corte Inicial (Sem Historico)** - Aplicado quando vaga tem menos de 30-50 triagens:

| Faixa WSI | Decisao |
|-----------|---------|
| >= 4.2 | Aprovado automatico |
| 3.8 - 4.1 | Revisao manual |
| 3.0 - 3.7 | Aguardando comparacao |
| < 3.0 | Nao aprovado |

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

#### Etapa 1 — Extracao de Competencias do Job Description

Antes de gerar qualquer pergunta, a LIA analisa o JD com LLM (Claude) e extrai um conjunto de competencias com pesos atribuidos. O resultado e um objeto `CompetencySuggestion` com tres tipos de competencias:

| Tipo | Quantidade extraida | Peso Total |
|------|---------------------|------------|
| `technical` | 5 competencias tecnicas (hard skills) | 70% |
| `behavioral` | 2 competencias comportamentais/culturais — o LLM decide a divisao entre os dois tipos | 30% |
| `cultural` | (incluido no grupo acima — pode ser 0, 1 ou 2 conforme o JD e a cultura da empresa) | parte dos 30% |

> **Nota:** o prompt instrui o LLM a extrair "2 competencias COMPORTAMENTAIS/CULTURAIS" com 30% de peso total, mas o JSON de resposta tem arrays separados para `behavioral_competencies` e `cultural_competencies`. O LLM distribui entre os dois conforme o conteudo do JD e a cultura da empresa fornecida.

Cada competencia recebe um peso individual que soma 100% dentro do seu tipo. Exemplo para vaga de Desenvolvedor Python Senior:

```
Tecnicas (70%):
  Python          → peso 0.25  critical: true
  Django/FastAPI  → peso 0.20  critical: true
  PostgreSQL      → peso 0.10
  AWS             → peso 0.10
  Docker          → peso 0.05

Comportamentais/Culturais (30%):
  Colaboracao em Equipe  → tipo behavioral  → peso 0.15
  Inovacao Continua      → tipo cultural    → peso 0.15
```

O campo `is_critical = true` indica que a competencia e eliminatoria — candidatos com score < 3.0 nessa competencia podem ter a decisao rebaixada independente do WSI geral. Este campo e exclusivo de competencias tecnicas (`is_critical` e sempre `false` para behavioral e cultural).

> **Nota sobre responsabilidades:** o sistema extrai apenas competencias (capacidades avaliadas durante a triagem). Responsabilidades do cargo descritas no JD sao usadas como contexto para o LLM inferir o nivel de senioridade e as competencias criticas, mas nao sao criadas como entidade avaliavel separada.

#### Etapa 2 — Geracao de Perguntas por Competencia

Para cada competencia extraida, o `WSIQuestionGenerator` cria perguntas usando os 4 frameworks em proporcoes fixas:

| Framework | Proporcao | Tipo de Pergunta |
|-----------|-----------|-----------------|
| CBI (Competency-Based Interviewing) | 60% | Situacionais STAR — "Conte sobre uma situacao onde voce usou X..." |
| Dreyfus | 20% | Autodeclaracao — "De 1 a 5, quanto voce domina X? Cite um projeto recente." |
| Bloom | 15% | Microcase — "Como voce implementaria/diagnosticaria [cenario]?" |
| Big Five | 5% | Situacional comportamental — "Como voce reage quando [situacao de pressao]?" |

**Volume de perguntas por modo:**

| Modo | Target interno (codigo) | Duracao Estimada | Canal |
|------|------------------------|-----------------|-------|
| `compact` | **6 perguntas** (fixo — `target_count = 6`) | 5 a 7 minutos | WhatsApp |
| `compact_plus` | **8 perguntas** (fixo — `target_count = 8`) | 7 a 10 minutos | WhatsApp |

> **Nota:** os docstrings do codigo descrevem "6-8" e "8-10" como faixas, mas o target e fixo em 6 ou 8. O retorno e sempre cortado em `questions[:target_count]`. Se o LLM gerar menos perguntas que o target (por falta de competencias suficientes), um warning e emitido mas sem fallback automatico.

> **Modo com 10-12 perguntas:** nao existe hoje no codigo. Para suportar triagens mais longas com mais competencias comportamentais/culturais seria necessario um terceiro modo (`full` ou `extended`) com `target_count >= 10`. Com target=8, o slot de Big Five comportamental ja e apenas 1 pergunta (5% de 8), o que limita a cobertura comportamental independente de quantas competencias comportamentais forem extraidas do JD.

#### Vinculo Pergunta → Competencia → Score

Cada pergunta gerada carrega internamente a competencia a que pertence. Quando o candidato responde, o scorer determinístico calcula o score usando **o nome da competencia como contexto**. Isso garante que o resultado final saiba exatamente qual competencia cada score representa:

```
Pergunta: "De 1 a 5, quanto voce domina Python? Cite um projeto."
  └─ competency: "Python"
  └─ framework: "Dreyfus"
  └─ bloom_level: 4 (Analisar — nivel pleno/senior)

Resposta do candidato avaliada:
  └─ autodeclaracao_score: 4.0
  └─ context_score: 4.2
  └─ final_score: 4.1 (formula deterministica)
  └─ registrado como: ResponseAnalysis(competency="Python", score=4.1)
```

O `WSI Final = (0.70 × média_técnica_ponderada) + (0.30 × média_comportamental_ponderada)` usa os pesos definidos na Etapa 1 para ponderar cada competencia no calculo final.

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
│  Output: Score WSI 0-5 + Perfil Big Five                                    │
│  Se < 3.0 → Revisar com explicacao                                          │
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
    "reasoning": "Candidato 1 supera em competencias tecnicas (WSI 4.2 vs 3.8) e alinhamento cultural"
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
        { "name": "Python", "level": "expert", "wsi_score": 4.5 },
        { "name": "Django", "level": "advanced", "wsi_score": 4.2 }
      ]
    },
    "behavioral_competencies": {
      "available": true,
      "source": "wsi+big_five",
      "big_five": { "O": 72, "C": 85, "E": 65, "A": 78, "N": 30 },
      "highlights": ["Alta conscienciosidade", "Colaborativo"]
    },
    "screening_results": {
      "available": true,
      "wsi_score": 4.2,
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
    "Python (4.5/5)",
    "Django/FastAPI (4.2/5)"
  ],
  "gaps": [
    "AWS (2.1/5)"
  ],
  "evidencias": [
    "Candidato mencionou deploy em producao com 50k usuarios",
    "Descreveu migracao de banco com zero downtime"
  ]
}
```

O criterio de classificacao no parecer e:
- `pontos_fortes`: competencias com score >= 4.0
- `gaps`: competencias com score < 3.0
- Competencias entre 3.0 e 3.9 nao aparecem em nenhum dos dois grupos (faixa media)

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
  "score": 4.1,
  "valores_alinhados": ["Colaboracao", "Inovacao continua"],
  "atencoes": ["Preferencia por trabalho individual em contextos colaborativos"]
}
```

O campo `atencoes` e obrigatorio quando WSI geral < 4.0.

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
- Convertido de escala 0-5 para 0-100: `WSI_100 = WSI_5 × 20`
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

---

## 13. Documentos Arquivados

Os seguintes documentos foram consolidados neste documento:
- `docs/WSI_METHODOLOGY_REFERENCE.md` - Mantido como referencia detalhada de WSI
- `docs/LIA_METHODOLOGY.md` - Mantido como referencia detalhada de Rubricas
- `docs/archived/SIMILAR_SEARCH_LLM_METHODOLOGY.md.archived` - Arquivado (substituido por Rubricas)
