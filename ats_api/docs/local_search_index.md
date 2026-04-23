# Local Search - Índice de Documentação

> **Documentação Completa do Sistema de Busca Híbrida**  
> **Versão:** 2.0  
> **Data:** 2026-02-01  
> **Status:** ✅ Completo e Validado

---

## 📚 Documentos Disponíveis

Este índice organiza toda a documentação do sistema Local Search. Os documentos estão ordenados por público-alvo e nível de detalhe.

---

## 🎯 Por Público-Alvo

### Para Executivos e Product Owners

1. **[local_search_executive_summary.md](local_search_executive_summary.md)** ⭐ **COMECE AQUI**
   - Resumo executivo
   - ROI e impacto esperado
   - Checklist de implementação
   - Roadmap futuro
   - **Tempo de leitura:** 10 minutos

### Para Desenvolvedores

2. **[local_search_overview.md](local_search_overview.md)** ⭐ **LEIA PRIMEIRO**
   - Visão geral completa do sistema
   - Fluxos de busca explicados
   - Componentes principais
   - Melhorias implementadas
   - **Tempo de leitura:** 30 minutos

3. **[local_search_architecture.md](local_search_architecture.md)** 🔧 **TÉCNICO**
   - Arquitetura técnica detalhada
   - Diagramas de fluxo (ASCII)
   - Fórmulas e algoritmos
   - Exemplos de cálculos
   - Performance e otimizações
   - **Tempo de leitura:** 45 minutos

4. **[local_search_api_guide.md](local_search_api_guide.md)** 📖 **REFERÊNCIA**
   - Guia de uso da API
   - Parâmetros e retornos
   - Configurações
   - Troubleshooting
   - Best practices
   - **Tempo de leitura:** 20 minutos
   - **Uso:** Consulta rápida

5. **[local_search_examples.md](local_search_examples.md)** 💡 **PRÁTICO**
   - Exemplos de código completos
   - Casos de uso reais
   - Integração com frontend
   - Otimizações de performance
   - Debug helpers
   - **Tempo de leitura:** 30 minutos
   - **Uso:** Copy-paste de código

### Para Designers e Visualização

6. **[local_search_diagrams.md](local_search_diagrams.md)** 🎨 **VISUAL**
   - 10 diagramas Mermaid
   - Fluxos visuais
   - Arquitetura de classes
   - Renderizável no GitHub
   - **Tempo de leitura:** 15 minutos
   - **Uso:** Apresentações e Wiki

---

## 📖 Por Tópico

### Introdução e Conceitos

- **Visão Geral:** [local_search_overview.md](local_search_overview.md) → Seção 1
- **Problema que Resolve:** [local_search_overview.md](local_search_overview.md) → Introdução
- **Casos de Uso:** [local_search_overview.md](local_search_overview.md) → Introdução

### Arquitetura

- **Diagrama de Alto Nível:** [local_search_architecture.md](local_search_architecture.md) → Diagrama 1
- **Componentes Principais:** [local_search_overview.md](local_search_overview.md) → Seção 4
- **Fluxo de Dados:** [local_search_diagrams.md](local_search_diagrams.md) → Diagrama 10
- **Classes e Services:** [local_search_diagrams.md](local_search_diagrams.md) → Diagrama 9

### Detecção de Query

- **Como Funciona:** [local_search_overview.md](local_search_overview.md) → Seção 3.1
- **Fluxograma:** [local_search_diagrams.md](local_search_diagrams.md) → Diagrama 2
- **Padrões de Detecção:** [local_search_architecture.md](local_search_architecture.md) → JobDescriptionProcessor

### Resume Search (Multi-Query)

- **Visão Geral:** [local_search_overview.md](local_search_overview.md) → Seção 3.3
- **Fluxo Detalhado:** [local_search_architecture.md](local_search_architecture.md) → Diagrama 2
- **ProfileExtractor:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.1
- **MultiQueryGenerator:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.2
- **Deduplication:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.5
- **Diagrama Mermaid:** [local_search_diagrams.md](local_search_diagrams.md) → Diagrama 3

### Job Description Search

- **Visão Geral:** [local_search_overview.md](local_search_overview.md) → Seção 3.4
- **Fluxo Detalhado:** [local_search_architecture.md](local_search_architecture.md) → Diagrama 3
- **JobDescriptionProcessor:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.4
- **Custom Boost:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.5
- **Diagrama Mermaid:** [local_search_diagrams.md](local_search_diagrams.md) → Diagrama 4

### HyDE Generation

- **Conceito:** [local_search_overview.md](local_search_overview.md) → Seção 4.3
- **Templates:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.3
- **Implementação:** [local_search_architecture.md](local_search_architecture.md) → HydeDocumentGenerator

### Fusion e Ranking

- **Weighted Rank Fusion:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.6
- **Fórmula RRF:** [local_search_architecture.md](local_search_architecture.md) → Weighted Rank Fusion
- **Reranking:** [local_search_architecture.md](local_search_architecture.md) → Seção 4.5
- **Diagrama Fusion:** [local_search_diagrams.md](local_search_diagrams.md) → Diagrama 7
- **Diagrama Reranking:** [local_search_diagrams.md](local_search_diagrams.md) → Diagrama 8

### API e Uso

- **Quick Start:** [local_search_api_guide.md](local_search_api_guide.md) → Quick Start
- **Parâmetros:** [local_search_api_guide.md](local_search_api_guide.md) → API de Busca
- **User Filters:** [local_search_api_guide.md](local_search_api_guide.md) → User Filters
- **Metadados:** [local_search_api_guide.md](local_search_api_guide.md) → Metadados de Resposta
- **Configurações:** [local_search_api_guide.md](local_search_api_guide.md) → Configurações

### Exemplos Práticos

- **Busca Simples:** [local_search_examples.md](local_search_examples.md) → Exemplo 1
- **Upload de CV:** [local_search_examples.md](local_search_examples.md) → Exemplo 2
- **Busca por JD:** [local_search_examples.md](local_search_examples.md) → Exemplo 3
- **Background Jobs:** [local_search_examples.md](local_search_examples.md) → Exemplo 4
- **Integração React:** [local_search_examples.md](local_search_examples.md) → Integração Frontend

### Performance e Otimização

- **Latency Breakdown:** [local_search_architecture.md](local_search_architecture.md) → Performance
- **Caching Strategy:** [local_search_architecture.md](local_search_architecture.md) → Caching
- **Parallel Execution:** [local_search_examples.md](local_search_examples.md) → Otimizações
- **Batch Embedding:** [local_search_examples.md](local_search_examples.md) → Otimizações

### Debugging e Troubleshooting

- **Debug Helper:** [local_search_examples.md](local_search_examples.md) → Debugging
- **Problemas Comuns:** [local_search_api_guide.md](local_search_api_guide.md) → Troubleshooting
- **Performance Monitor:** [local_search_examples.md](local_search_examples.md) → Monitoring

### Métricas e Monitoramento

- **KPIs:** [local_search_executive_summary.md](local_search_executive_summary.md) → Métricas
- **Dashboards:** [local_search_overview.md](local_search_overview.md) → Seção 6.4
- **Telemetry:** [local_search_api_guide.md](local_search_api_guide.md) → Metadados

### Testes

- **Estratégia de Testes:** [local_search_architecture.md](local_search_architecture.md) → Testing Strategy
- **Unit Tests:** [local_search_architecture.md](local_search_architecture.md) → Unit Tests
- **Integration Tests:** [local_search_architecture.md](local_search_architecture.md) → Integration Tests

### Roadmap e Futuro

- **Curto Prazo:** [local_search_executive_summary.md](local_search_executive_summary.md) → Roadmap
- **Médio Prazo:** [local_search_executive_summary.md](local_search_executive_summary.md) → Roadmap
- **Longo Prazo:** [local_search_executive_summary.md](local_search_executive_summary.md) → Roadmap

---

## 🚀 Jornadas de Aprendizado

### Jornada 1: Entendimento Rápido (30 min)

Para alguém que precisa entender o sistema rapidamente:

1. 📄 [Executive Summary](local_search_executive_summary.md) (10 min)
   - Resumo executivo
   - Impacto e ROI
   
2. 📄 [Overview](local_search_overview.md) → Seções 1-2 (10 min)
   - Introdução
   - Arquitetura geral
   
3. 🎨 [Diagrams](local_search_diagrams.md) → Diagrama 1 (5 min)
   - Fluxo principal
   
4. 💡 [Examples](local_search_examples.md) → Exemplo 1 (5 min)
   - Código de exemplo simples

### Jornada 2: Implementação Básica (2 horas)

Para desenvolver que vai implementar features:

1. 📄 [Overview](local_search_overview.md) (30 min)
   - Leitura completa
   
2. 📖 [API Guide](local_search_api_guide.md) (20 min)
   - Quick Start
   - API de Busca
   - Configurações
   
3. 💡 [Examples](local_search_examples.md) → Exemplos 1-4 (40 min)
   - Código completo
   - Casos de uso
   
4. 🎨 [Diagrams](local_search_diagrams.md) (15 min)
   - Diagramas relevantes
   
5. 🧪 Hands-on (15 min)
   - Rodar no console
   - Testar endpoints

### Jornada 3: Domínio Completo (1 dia)

Para tech lead ou arquiteto que precisa dominar o sistema:

1. 📄 [Executive Summary](local_search_executive_summary.md) (15 min)
2. 📄 [Overview](local_search_overview.md) (45 min)
3. 🔧 [Architecture](local_search_architecture.md) (2 horas)
4. 📖 [API Guide](local_search_api_guide.md) (30 min)
5. 💡 [Examples](local_search_examples.md) (1 hora)
6. 🎨 [Diagrams](local_search_diagrams.md) (30 min)
7. 💻 Code Review (2 horas)
   - Ler código-fonte
   - Entender implementação
8. 🧪 Testes práticos (1 hora)
   - Rodar cenários
   - Debug

---

## 🔍 Referência Rápida

### Encontrar Informação por Palavra-chave

| Palavra-chave | Documento | Seção |
|---------------|-----------|-------|
| **confidence** | architecture.md | ProfileExtractor |
| **multi-query** | overview.md | Seção 5.1 |
| **deduplication** | architecture.md | Diagrama 2 |
| **boost** | architecture.md | Seção 4.5 |
| **JD detection** | architecture.md | JobDescriptionProcessor |
| **RRF** | architecture.md | Weighted Rank Fusion |
| **HyDE** | overview.md | Seção 4.3 |
| **cache** | architecture.md | Performance |
| **troubleshooting** | api_guide.md | Troubleshooting |
| **examples** | examples.md | Todos |

### Comandos Úteis

```bash
# Buscar por termo em todos os docs
grep -r "multi-query" docs/local_search_*.md

# Gerar TOC de um documento
gh-md-toc docs/local_search_overview.md

# Converter Mermaid para imagem
mmdc -i docs/local_search_diagrams.md -o output/diagrams.png

# Contar linhas de documentação
wc -l docs/local_search_*.md
```

---

## 📊 Estatísticas da Documentação

### Tamanho dos Documentos

| Documento | Tamanho | Linhas | Diagramas | Exemplos |
|-----------|---------|--------|-----------|----------|
| executive_summary.md | 11 KB | 350 | 0 | 0 |
| overview.md | 18 KB | 600 | 1 | 5 |
| architecture.md | 44 KB | 1400 | 3 | 20 |
| api_guide.md | 22 KB | 750 | 0 | 15 |
| examples.md | 24 KB | 850 | 0 | 30 |
| diagrams.md | 14 KB | 500 | 10 | 0 |
| **TOTAL** | **133 KB** | **4450** | **14** | **70** |

### Cobertura

- ✅ **Conceitos:** 100%
- ✅ **API:** 100%
- ✅ **Arquitetura:** 100%
- ✅ **Exemplos:** 100%
- ✅ **Diagramas:** 100%
- ✅ **Troubleshooting:** 100%

---

## 🆘 Suporte

### Dúvidas Frequentes

**"Por onde começar?"**
→ Leia o [Executive Summary](local_search_executive_summary.md)

**"Preciso implementar uma busca, o que fazer?"**
→ Siga o [API Guide](local_search_api_guide.md) → Quick Start

**"Como funciona o multi-query?"**
→ Leia [Overview](local_search_overview.md) → Seção 5.1

**"Quero ver o código"**
→ Veja [Examples](local_search_examples.md) → Todos os exemplos

**"Preciso entender a arquitetura"**
→ Leia [Architecture](local_search_architecture.md) completo

**"Tenho um erro, e agora?"**
→ [API Guide](local_search_api_guide.md) → Troubleshooting

### Contatos

- **Documentação:** Este índice
- **Código:** `app/services/candidates/search/`
- **Slack:** #local-search-support
- **Email:** dev-team@empresa.com

---

## 🎓 Contribuindo

### Atualizando Documentação

1. Edite o documento relevante
2. Atualize a data "Última atualização"
3. Incremente versão se mudança significativa
4. Atualize este índice se necessário
5. Commit com mensagem descritiva

### Padrões

- **Formato:** Markdown
- **Encoding:** UTF-8
- **Line endings:** LF
- **Max line length:** Nenhum (flow text)
- **Diagramas:** Mermaid ou ASCII

---

## 📅 Histórico de Versões

| Versão | Data | Mudanças |
|--------|------|----------|
| **2.0** | 2026-02-01 | ✅ Implementação completa + documentação |
| 1.0 | 2025-12-01 | Sistema original (sem multi-query, sem JD) |

---

**Versão deste índice:** 2.0  
**Última atualização:** 2026-02-01  
**Próxima revisão:** 2026-03-01  
**Mantenedor:** Dev Team

---

**Total de documentação:** 133 KB, 4450 linhas, 14 diagramas, 70 exemplos  
**Status:** ✅ Completo e Validado
