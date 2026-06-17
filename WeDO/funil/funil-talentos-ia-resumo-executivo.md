# RESUMO EXECUTIVO - ARQUITETURA DE IA DO FUNIL DE TALENTOS

> **Para:** Consultor de IA  
> **De:** Equipe WedoTalent / Plataforma LIA  
> **Data:** Dezembro 2024  
> **Objetivo:** Avaliar arquitetura de IA do modulo Funil de Talentos

---

## 1. VISAO GERAL

O **Funil de Talentos** e o modulo central de busca e gestao de candidatos da plataforma LIA (Learning Intelligence Assistant). Utiliza **Claude Sonnet (Anthropic)** como modelo principal e **Google Gemini** como fallback para voz.

### Numeros-Chave

| Metrica | Valor |
|---------|-------|
| Total de pontos de IA | **32 funcionalidades** |
| Comandos/queries disponiveis | **146 prompts** |
| Agentes especializados | 3 (Sourcing, Recruiter Assistant, Conversation) |
| Servicos de IA | 25 |
| Chamadas diretas | 4 |

---

## 2. DISTRIBUICAO POR TIPO

```
Servicos (78%)  ████████████████████████░░░░░░  25 funcionalidades
Agentes (16%)   █████░░░░░░░░░░░░░░░░░░░░░░░░░   5 funcionalidades
Chamadas (6%)   ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2 funcionalidades
```

### Por Localizacao

| Area | Qtd | % do Total |
|------|-----|------------|
| Tab Busca | 13 | 41% |
| Modais | 6 | 19% |
| Preview/Pagina Candidato | 5 | 16% |
| Prompt Expandido (Chat) | 4 | 12% |
| Acoes em Lote | 2 | 6% |
| Outras Tabs | 2 | 6% |

---

## 3. FUNCIONALIDADES PRINCIPAIS DE IA

### 3.1 Busca Inteligente (5 modos)

| Modo | Tipo | Complexidade | Uso de IA |
|------|------|--------------|-----------|
| IA Natural | Servico | Media | NLU + Query Expansion |
| Job Description | Agente | Alta | Extracao + Matching |
| Perfil Similar | Agente | Alta | Embedding + Similarity |
| Arquetipos Big Five | Servico | Media | Pattern Matching |
| Boolean Assistido | Servico | Baixa | Validacao sintaxe |

### 3.2 Scoring e Parecer LIA

- **LIA Score**: Composicao de 4 criterios (Tecnico, Personalidade, Experiencia, Cultural)
- **Parecer LIA**: Texto gerado com pontos fortes, preocupacoes e recomendacao
- **Big Five Mapping**: Arquetipo de personalidade do candidato

### 3.3 Chat Conversacional (Super Chat)

- 146 comandos/queries pre-definidos
- 8 contextos de uso (Dashboard, Busca, Candidatos, Vagas, etc.)
- Agente Conversation como orquestrador

---

## 4. ANALISE CRITICA

### 4.1 O que E IA e NAO deveria ser (Over-engineering)

| Funcionalidade | Problema | Alternativa |
|----------------|----------|-------------|
| Autocomplete de busca | Custo alto, latencia | Cache + frequencia |
| Ordenacao de resultados | IA desnecessaria | Algoritmo deterministico |
| Extracao de filtros basicos | Regex basta | Regex + regras |
| Contagens simples | "Quantos candidatos?" | Query SQL |
| Navegacao CRUD | "Adicionar candidato" | Formulario UI |

**Impacto estimado:** ~30% dos comandos poderiam ser executados sem IA

### 4.2 O que NAO E IA e poderia ser (Oportunidades)

| Funcionalidade | Valor Potencial | Prioridade |
|----------------|-----------------|------------|
| Predicao de aceite do candidato | Alto | P1 |
| Deteccao de candidatos duplicados | Alto | P1 |
| Analise de sentimento em notas | Medio | P2 |
| Sugestao de proxima acao | Alto | P1 |
| Auto-tags de skills | Alto | P1 |
| Deteccao de vieses | Alto | P1 |
| Predicao de tempo de contratacao | Medio | P2 |
| Matching automatico vaga-candidato | Alto | P1 |

---

## 5. MATRIZ DE DECISAO: AGENTE vs SERVICO

### Quando usar AGENTE

- Multiplas etapas de raciocinio
- Necessidade de memoria de contexto longo
- Orquestracao de multiplos servicos
- Conversacao multi-turno

### Quando usar SERVICO

- Tarefa unica e bem definida
- Input/output previsivel
- Latencia critica (<500ms)
- Alto volume de chamadas

### Quando usar CHAMADA DIRETA

- Prompt simples e estatico
- Sem necessidade de memoria
- Custo como prioridade

---

## 6. ARQUITETURA DE COMANDOS (146 total)

| Contexto | Componente | Qtd |
|----------|------------|-----|
| Dashboard/Chat vazio | PromptSuggestionsDock | 8 |
| Dicas gerais | LIATipsModal | 48 |
| Queries gerais | LiaQueriesGuide | 33 |
| Pos-busca | LiaSearchQueriesGuide | 27 |
| Analise candidatos | CandidateQueriesGuide | 30 |

### Distribuicao por Tipo de IA Necessaria

| Tipo | Exemplos | % |
|------|----------|---|
| Busca semantica | "Encontre candidatos React" | 14% |
| Analise de dados | "Compare candidatos por score" | 24% |
| Geracao de texto | "Sugira mensagem de abordagem" | 7% |
| Predicao | "Quando devo fechar a vaga?" | 3% |
| Recomendacao | "Principais recomendacoes para hoje" | 10% |
| **Nao precisa de IA** | Contagens, filtros, CRUD | **30%** |
| Hibrido | Parte IA, parte regras | 12% |

---

## 7. RECOMENDACOES PARA AVALIACAO

### 7.1 Pontos de Atencao

1. **Custo vs Valor**: ~30% das chamadas de IA poderiam ser queries SQL
2. **Latencia**: Autocomplete com IA adiciona 200-500ms desnecessarios
3. **Consistencia**: Scoring usa IA mas poderia ter formula deterministica
4. **Duplicacao**: Varios pontos fazem tarefas similares (extracao de entidades)

### 7.2 Perguntas para o Consultor

1. A arquitetura de 3 agentes + 25 servicos esta adequada para escala?
2. Devemos consolidar servicos similares (extracao, parsing, matching)?
3. Qual o modelo de caching recomendado para reduzir chamadas?
4. Como implementar observabilidade (custo, latencia, qualidade) por funcionalidade?
5. Faz sentido usar fine-tuning para casos especificos (scoring, parsing)?

### 7.3 Metricas Sugeridas para Monitoramento

| Metrica | Por que medir |
|---------|---------------|
| Tokens consumidos por funcionalidade | Identificar maiores custos |
| P95 latencia por endpoint | Detectar gargalos |
| Taxa de fallback Gemini | Disponibilidade Claude |
| Satisfacao por resposta (feedback) | Qualidade percebida |
| Taxa de retry | Problemas de confiabilidade |

---

## 8. DOCUMENTACAO COMPLETA

Para analise detalhada, consultar:

| Documento | Conteudo |
|-----------|----------|
| `docs/funil-talentos-ia-architecture.md` | Documentacao completa (1700+ linhas) |
| `docs/funil-talentos-fluxos.md` | 7 fluxos com 77 funcionalidades |
| `docs/funil-talentos-cards-jira.md` | 61 cards de desenvolvimento |
| `docs/funil-talentos-tasks.csv` | 110 tarefas para import |

---

## 9. PROXIMOS PASSOS

1. **Revisao com consultor** - Apresentar este resumo
2. **Auditoria de custos** - Mapear gastos por funcionalidade
3. **Benchmark de latencia** - Medir P50/P95 por endpoint
4. **Priorizar otimizacoes** - Implementar alternativas para os 30% sem IA
5. **Definir metricas** - Implementar observabilidade

---

*Documento preparado para analise externa da arquitetura de IA.*
*Versao: 1.0 | Dezembro 2024*
