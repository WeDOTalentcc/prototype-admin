# Futuras Features para IRMOS

Este documento lista as features planejadas para implementação futura na plataforma LIA.

---

## 1. Preview do Candidato - Tab de Mapa de Skills (estilo Juicebox)

**Descrição:** Adicionar uma nova aba no preview do candidato com visualização de mapa de skills no estilo Juicebox.

**Detalhes:**
- Nova tab no preview lateral do candidato
- Visualização gráfica/visual das skills do candidato
- Mapeamento de competências técnicas e comportamentais
- Estilo inspirado no Juicebox (visualização intuitiva e interativa)

**Status:** Planejado

---

## 2. Resumo Inteligente do Candidato (estilo Juicebox) ✅

**Descrição:** Resumo em linguagem natural gerado por IA no topo do card "Análise da LIA" no preview do candidato.

**Detalhes:**
- Ícone sparkles (✨) indicando conteúdo gerado por IA
- Texto em linguagem natural destacando: nome, anos de experiência, skill principal (com destaque visual), empresas relevantes e cargo atual
- Termos-chave destacados com background ciano suave
- Estilo visual inspirado no Juicebox

**Status:** ✅ Implementado (03/12/2025)

---

## 3. Configuração de Busca Global (Admin) ✅

**Descrição:** Nova seção no painel administrativo para configurar limites e opções da busca global Pearch AI.

**Localização:** Configurações → Busca Global

### Detalhes:

#### Limites de Candidatos (faixas de 50 em 50):
| Limite | Descrição | Recomendado |
|--------|-----------|-------------|
| 50 candidatos | Ideal para buscas exploratórias e vagas específicas | ✅ Sim |
| 100 candidatos | Bom para vagas com alta demanda de candidatos | - |
| 150 candidatos | Para processos seletivos de grande volume | - |
| 200 candidatos | Máximo recomendado - projetos de sourcing massivo | - |

#### Custos Estimados por Busca:
| Limite | Busca Fast (~1 créd/cand) | Busca Pro (~7 créd/cand) |
|--------|---------------------------|--------------------------|
| 50     | ~50 créditos              | ~350 créditos            |
| 100    | ~100 créditos             | ~700 créditos            |
| 150    | ~150 créditos             | ~1.050 créditos          |
| 200    | ~200 créditos             | ~1.400 créditos          |

#### Tipos de Busca:
- **Fast** (~1 crédito/candidato): Resultados rápidos sem insights avançados
- **Pro** (~7 créditos/candidato): Inclui scoring avançado e insights IA

#### Opções de Busca:
- Revelar emails automaticamente (+2 créd/candidato)
- Revelar telefones automaticamente (+2 créd/candidato)
- Priorizar perfis atualizados recentemente (últimos 90 dias)

#### Controle de Gastos:
- Confirmar antes de cada busca global (exibe estimativa de créditos)
- Sugerir expansão global automaticamente (quando busca local retorna poucos resultados)

#### Organização em 3 Abas:
1. **Limites**: Configuração do limite padrão de candidatos
2. **Opções**: Controles de gastos e preferências de busca
3. **Custos**: Tabela detalhada de custos Pearch AI

#### Componente:
- `GlobalSearchHub.tsx` em `/src/components/settings/`
- Salva configurações no localStorage
- Dispara evento `globalSearchSettingsUpdate` para sincronização

**Status:** ✅ Implementado (04/12/2025)

---
