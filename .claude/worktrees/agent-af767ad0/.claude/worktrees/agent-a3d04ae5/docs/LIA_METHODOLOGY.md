# Metodologia de Análise LIA

## Visão Geral

A LIA (Learning Intelligence Assistant) utiliza uma metodologia estruturada e baseada em evidências para avaliar candidatos. O sistema combina múltiplas dimensões de análise para gerar scores transparentes e explicáveis.

---

## 1. Framework Big Five (OCEAN)

### 1.1 As 5 Dimensões de Personalidade

| Dimensão | Sigla | Descrição | Indicadores Comportamentais |
|----------|-------|-----------|----------------------------|
| **Abertura** | O | Curiosidade intelectual, criatividade, receptividade a novas ideias | Projetos inovadores, diversidade de experiências, formação contínua |
| **Conscienciosidade** | C | Organização, disciplina, orientação a resultados | Entregas consistentes, progressão de carreira, certificações |
| **Extroversão** | E | Sociabilidade, assertividade, energia social | Liderança de equipes, apresentações, networking |
| **Amabilidade** | A | Cooperação, empatia, orientação ao coletivo | Trabalho em equipe, mentoria, resolução de conflitos |
| **Neuroticismo** | N | Estabilidade emocional (inverso: baixo N = estável) | Resiliência, gestão de pressão, adaptabilidade |

### 1.2 Arquétipos Derivados

Com base nas combinações das 5 dimensões, definimos 8 arquétipos principais:

| Arquétipo | Perfil OCEAN | Características | Roles Ideais |
|-----------|--------------|-----------------|--------------|
| **Catalisador Visionário** | Alto O/E, Baixo N | Inovador, inspirador, busca mudanças | Fundador, Product Manager, Diretor de Inovação |
| **Executor Confiável** | Alto C/A, Baixo N | Metódico, colaborativo, entrega consistente | Gerente de Projetos, Analista Sênior, Ops Manager |
| **Guardião de Clientes** | Alto A/E, Médio O | Empático, comunicativo, orientado ao cliente | Customer Success, Account Manager, Suporte Sênior |
| **Estrategista Analítico** | Alto O/C, Baixo E | Pensador profundo, orientado a dados | Data Scientist, Arquiteto, Pesquisador |
| **Mediador Adaptável** | Alto A/O, Médio C | Flexível, harmonizador, diplomático | HRBP, Scrum Master, Consultor |
| **Rainmaker Audacioso** | Alto E/O, Baixo A | Persuasivo, ambicioso, orientado a resultados | Vendedor, BD, Founder |
| **Operador Resiliente** | Alto C, N controlado | Estável sob pressão, focado, persistente | SRE, Suporte Crítico, Operações 24/7 |
| **Arquiteto Metódico** | Alto C/O, Baixo E | Detalhista, sistemático, qualidade | Engenheiro Sênior, QA Lead, Arquiteto de Software |

### 1.3 Mapeamento de Traços

Cada traço é mapeado em uma escala de 0-100:
- **0-30**: Baixo
- **31-50**: Médio-Baixo
- **51-70**: Médio-Alto
- **71-100**: Alto

---

## 2. Metodologia WSI (Work Sample Interview)

### 2.1 Fundamentos

O WSI é baseado em duas estruturas complementares:

#### Taxonomia de Bloom (Níveis Cognitivos)
1. **Lembrar** - Recordar fatos e conceitos básicos
2. **Compreender** - Explicar ideias e conceitos
3. **Aplicar** - Usar informações em novas situações
4. **Analisar** - Estabelecer conexões entre ideias
5. **Avaliar** - Justificar decisões ou posições
6. **Criar** - Produzir trabalho novo ou original

#### Modelo Dreyfus (Níveis de Proficiência)
1. **Novato** - Segue regras rígidas, pouca contextualização
2. **Iniciante Avançado** - Reconhece aspectos situacionais
3. **Competente** - Planejamento consciente, priorização
4. **Proficiente** - Visão holística, adaptação fluida
5. **Expert** - Intuição profunda, transcende regras

### 2.2 Matriz de Avaliação WSI

```
                    Bloom Level
              Lembrar → → → Criar
Dreyfus    ┌─────────────────────┐
Novato     │  1  │  2  │  3  │  4 │
           ├─────┼─────┼─────┼────┤
Competente │  3  │  4  │  5  │  6 │
           ├─────┼─────┼─────┼────┤
Expert     │  5  │  6  │  7  │  8 │
           └─────────────────────┘
           (Scores de 1-8 por resposta)
```

### 2.3 Correlação WSI → Big Five

| Evidência WSI | Indicador Big Five |
|---------------|-------------------|
| Bloom "Criar" + Dreyfus "Expert" | Alta Abertura (O), Baixo Neuroticismo (N) |
| Bloom "Analisar" + Dreyfus "Proficiente" | Alta Conscienciosidade (C), Alta Abertura (O) |
| Respostas colaborativas, menção a equipe | Alta Amabilidade (A) |
| Liderança proativa, iniciativa | Alta Extroversão (E) |
| Gestão de pressão, adaptação a mudanças | Baixo Neuroticismo (N) |

---

## 3. Sistema de Competências

### 3.1 Frameworks de Referência

| Domínio | Framework | Aplicação |
|---------|-----------|-----------|
| **Técnico** | SFIA v8 + IEEE SWEBOK | Habilidades de tecnologia e engenharia |
| **Geral** | O*NET + ESCO | Competências ocupacionais universais |
| **Cultural** | Competing Values Framework | Alinhamento organizacional |
| **Liderança** | Korn Ferry Leadership Architect | Potencial de liderança |
| **Emocional** | Modelo Goleman | Inteligência emocional |

### 3.2 Categorias de Competências

1. **Competências Técnicas (Hard Skills)**
   - Linguagens de programação
   - Ferramentas e tecnologias
   - Metodologias (Agile, DevOps, etc.)
   - Certificações

2. **Competências Comportamentais (Soft Skills)**
   - Comunicação
   - Liderança
   - Resolução de problemas
   - Trabalho em equipe

3. **Competências Específicas do Role**
   - Definidas por cada vaga
   - Ponderadas conforme requisitos
   - Validadas via WSI

---

## 4. Sistema de Rubricas Estruturadas para Avaliação CV vs Vaga

A metodologia de Rubricas Estruturadas é baseada em pesquisas acadêmicas consolidadas sobre validação preditiva em seleção de pessoal. Este sistema avalia exclusivamente o **match entre CV e requisitos da vaga**, sem incluir Big Five, WSI ou Cultural Fit (que requerem assessments separados).

### 4.1 Fundamentos Científicos

| Referência | Contribuição |
|------------|--------------|
| **Schmidt & Hunter (1998)** | Meta-análise demonstrou que estruturação em seleção aumenta validade preditiva de 0.38 para 0.51 |
| **BARS - Behaviorally Anchored Rating Scales** | Escala com âncoras comportamentais específicas reduz viés de avaliador |
| **Campion et al. (1997)** | Documentou 15 componentes que aumentam validade de entrevistas estruturadas |

### 4.2 Escala de Avaliação (4 Níveis)

Cada requisito é avaliado em uma escala ancorada comportamentalmente:

| Nível | Pontos | Descrição | Âncora Comportamental |
|-------|--------|-----------|----------------------|
| **Exceeds (Excede)** | 100 | Experiência excepcional | Evidência de resultados superiores, liderança na área, ou experiência >50% acima do requisito |
| **Meets (Atende)** | 75 | Atende plenamente | CV demonstra claramente a competência/experiência requerida |
| **Partial (Parcial)** | 40 | Atende parcialmente | Evidência relacionada mas não direta, ou experiência inferior ao requisito |
| **Missing (Ausente)** | 0 | Não demonstrado | Nenhuma evidência encontrada no CV |

### 4.3 Prioridades de Requisitos (Multiplicadores)

| Prioridade | Multiplicador | Uso |
|------------|---------------|-----|
| **Essential (Essencial)** | 3x | Requisitos eliminatórios, sem os quais o candidato não pode exercer a função |
| **Important (Importante)** | 2x | Requisitos significativos que impactam diretamente a performance |
| **Nice to Have (Desejável)** | 1x | Diferenciais que agregam valor mas não são críticos |

### 4.4 Fórmula de Cálculo

```
Score = Σ(Pontos × Multiplicador) / Σ(100 × Multiplicador) × 100

Onde:
- Pontos = Nível de avaliação (100, 75, 40 ou 0)
- Multiplicador = Prioridade do requisito (3, 2 ou 1)
- Denominador = Pontuação máxima possível (100 × multiplicador para cada requisito)
```

### 4.5 Exemplo Prático de Cálculo

**Vaga:** Desenvolvedor Python Sênior

| Requisito | Prioridade | Mult. | Avaliação | Pontos | Weighted |
|-----------|------------|-------|-----------|--------|----------|
| Python 5+ anos | Essential | 3x | Meets (8 anos) | 75 | 225 |
| Django/FastAPI | Essential | 3x | Exceeds (líder técnico) | 100 | 300 |
| PostgreSQL | Important | 2x | Meets | 75 | 150 |
| AWS | Important | 2x | Partial (experiência limitada) | 40 | 80 |
| Docker/K8s | Nice to Have | 1x | Meets | 75 | 75 |
| Liderança técnica | Nice to Have | 1x | Exceeds | 100 | 100 |

**Cálculo:**
- Pontos obtidos: 225 + 300 + 150 + 80 + 75 + 100 = **930**
- Pontos máximos: (100×3) + (100×3) + (100×2) + (100×2) + (100×1) + (100×1) = **1200**
- Score = 930 / 1200 × 100 = **77.5%**

**Evidências (extraídas do CV):**
- Python: "8 anos desenvolvendo sistemas em Python, incluindo microsserviços de alta escala"
- Django/FastAPI: "Tech Lead responsável pela arquitetura FastAPI do sistema de pagamentos"
- AWS: "Experiência básica com EC2 e S3 em projeto de 6 meses"

### 4.6 Análise Semântica via LLM

O sistema utiliza Claude AI para análise semântica profunda, não apenas keywords:

1. **Extração de Evidências**: Identifica citações específicas do CV que suportam cada avaliação
2. **Avaliação de Relevância**: Considera contexto e transferibilidade de experiências
3. **Detecção de Gaps**: Identifica requisitos não atendidos e seu impacto
4. **Reasoning Explicável**: Gera justificativa detalhada para cada avaliação

### 4.7 Níveis de Recomendação

| Score | Nível | Ação Recomendada |
|-------|-------|------------------|
| 85-100% | **Altamente Recomendado** | Priorizar para entrevista |
| 70-84% | **Recomendado** | Considerar para processo |
| 55-69% | **Potencial** | Avaliar gaps específicos |
| 40-54% | **Baixo Match** | Arquivar para futuras vagas |
| 0-39% | **Não Recomendado** | Não prosseguir |

### 4.8 Separação de Dimensões de Avaliação

> **Importante:** Este sistema avalia APENAS match CV vs Vaga. As dimensões abaixo requerem assessments separados:

| Dimensão | Método | Quando Aplicar |
|----------|--------|----------------|
| **CV vs Requisitos** | Rubricas Estruturadas | Triagem inicial (automático) |
| **Big Five / Personalidade** | Assessment OCEAN | Após triagem, candidatos selecionados |
| **WSI (Work Sample)** | Entrevista estruturada | Fase de entrevistas |
| **Cultural Fit** | Assessment + Entrevista | Fases finais |

### 4.9 Referências Acadêmicas

- Schmidt, F. L., & Hunter, J. E. (1998). The validity and utility of selection methods in personnel psychology. *Psychological Bulletin, 124*(2), 262-274.
- Smith, P. C., & Kendall, L. M. (1963). Retranslation of expectations: An approach to the construction of unambiguous anchors for rating scales. *Journal of Applied Psychology, 47*(2), 149-155.
- Campion, M. A., Palmer, D. K., & Campion, J. E. (1997). A review of structure in the selection interview. *Personnel Psychology, 50*(3), 655-702.
- Huffcutt, A. I., & Arthur, W. (1994). Hunter and Hunter (1984) revisited: Interview validity for entry-level jobs. *Journal of Applied Psychology, 79*(2), 184-190.

---

## 5. Análise Contextual vs. Geral

### 5.1 Análise Contextual (Com Vaga)

Quando vinculada a uma vaga específica:

1. **Requisitos da Vaga** são extraídos:
   - Skills obrigatórias e desejáveis
   - Anos de experiência
   - Arquétipo ideal (Big Five)
   - Cultura do time/departamento

2. **Match é calculado** comparando:
   - CV do candidato ↔ Requisitos técnicos
   - Big Five inferido ↔ Arquétipo ideal
   - Experiências ↔ Contexto da vaga

3. **Explicabilidade**:
   - "Match 92% porque: 5/5 skills, 8 anos experiência (req: 5+), perfil Executor Confiável alinhado"

### 5.2 Análise Geral (Sem Vaga)

Quando não há vaga vinculada:

1. **Perfil Completo** é gerado:
   - Arquétipo Big Five predominante
   - Competências principais
   - Nível de senioridade estimado

2. **Potencial de Mercado**:
   - Roles mais adequados
   - Setores com maior fit
   - Pontos fortes e áreas de desenvolvimento

3. **Recomendações**:
   - Tipos de vaga mais compatíveis
   - Sugestão de arquétipos complementares

---

## 6. Conformidade e Ética

### 6.1 Anti-Viés

- Não considerar idade, gênero, raça, religião, orientação
- Focar exclusivamente em competências e fit
- Auditoria periódica de resultados por demografia

### 6.2 Transparência

- Scores são explicáveis
- Candidato pode solicitar razões
- Recrutador pode ajustar com justificativa

### 6.3 LGPD/GDPR

- Consentimento para análise automatizada
- Direito de opt-out
- Dados retidos por período definido

---

## 7. Calibração Contínua

### 7.1 Feedback Loop

1. Recrutador avalia precisão do score (1-5)
2. Sistema ajusta pesos via ML constrained
3. Métricas de acurácia são monitoradas

### 7.2 Métricas de Qualidade

- Taxa de contratação por faixa de score
- Tempo de permanência por score
- Performance (quando disponível) vs. score inicial

---

## Referências

- Costa, P. T., & McCrae, R. R. (1992). Revised NEO Personality Inventory
- Bloom, B. S. (1956). Taxonomy of Educational Objectives
- Dreyfus, S. E., & Dreyfus, H. L. (1980). A Five-Stage Model of Mental Activities
- SFIA Foundation. Skills Framework for the Information Age v8
- Cameron, K. S., & Quinn, R. E. (2011). Competing Values Framework
