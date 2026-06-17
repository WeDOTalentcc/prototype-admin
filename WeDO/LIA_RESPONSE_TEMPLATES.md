# Templates de Resposta Padronizados da LIA

**Data**: 2026-01-20  
**Versão**: 1.0  
**Objetivo**: Padronizar as respostas da LIA para garantir experiência consistente e profissional para recrutadores.

---

## Índice

1. [Princípios de Design](#princípios-de-design)
2. [Templates de Análise](#templates-de-análise)
3. [Templates de Métricas](#templates-de-métricas)
4. [Templates de Funil](#templates-de-funil)
5. [Templates de Ações](#templates-de-ações)
6. [Templates de Relatórios](#templates-de-relatórios)
7. [Templates de Ações Rápidas](#templates-de-ações-rápidas)
8. [Referências de Mercado](#referências-de-mercado)

---

## Mapeamento de Sugestões para Templates

Esta tabela mapeia todas as 26 sugestões disponíveis nos componentes de interface para seus respectivos templates de resposta.

### Sugestões do Guia de Consultas (lia-vacancy-queries-guide)

| # | Sugestão | Categoria | Template |
|---|----------|-----------|----------|
| 1 | Listar vagas abertas | Análise | Template 1 - Listar Vagas Abertas |
| 2 | Quais vagas precisam de atenção urgente? | Análise | Template 2 - Vagas que Precisam de Atenção |
| 3 | Qual vaga tem a melhor taxa de conversão? | Análise | Template 3 - Ranking de Conversão |
| 4 | Comparar performance das vagas ativas | Análise | Template 4 - Performance Comparativa |
| 5 | Sugerir melhorias para minhas vagas | Análise | Template 5 - Sugestões de Melhoria |
| 6 | Quais vagas estão sem candidatos? | Análise | Template 6 - Vagas Sem Candidatos |
| 7 | Vagas abertas há mais de 30 dias | Análise | Template 7 - Vagas Antigas |
| 8 | Buscar candidatos para vaga de... | Análise | Template 30 - Buscar Candidatos |
| 9 | Qual é a taxa de conversão geral do funil? | Métricas | Template 8 - Taxa de Conversão do Funil |
| 10 | Tempo médio para fechar uma vaga | Métricas | Template 9 - Time to Fill |
| 11 | Performance das vagas este mês vs anterior | Métricas | Template 10 - Performance Comparativa Mensal |
| 12 | Quantas contratações fizemos este trimestre? | Métricas | Template 11 - Contratações do Trimestre |
| 13 | Quantas vagas estão atrasadas no SLA? | Métricas | Template 12 - Vagas Atrasadas no SLA |
| 14 | Quantas vagas temos por departamento? | Métricas | Template 13 - Vagas por Departamento |
| 15 | Onde está o gargalo do processo seletivo? | Funil | Template 14 - Gargalos do Processo |
| 16 | Qual etapa tem maior taxa de rejeição? | Funil | Template 15 - Taxa de Rejeição por Etapa |
| 17 | Vagas com deadline próximo | Funil | Template 16 - Vagas com Deadline Próximo |
| 18 | Performance dos últimos 30 dias | Funil | Template 17 - Performance 30 Dias |

### Sugestões do Dock de Ações Rápidas (prompt-suggestions-dock)

| # | Sugestão | Categoria | Template |
|---|----------|-----------|----------|
| 19 | Criar uma nova vaga | Vagas | Template 23 - Criar Nova Vaga |
| 20 | Solicite aprovação de nova vaga | Vagas | Template 24 - Solicitar Aprovação de Vaga |
| 21 | Compartilhe candidatos com gestor | Candidatos | Template 25 - Compartilhar Candidatos |
| 22 | Buscar candidatos | Candidatos | Template 30 - Buscar Candidatos |
| 23 | Consulte informações sobre candidato | Candidatos | Template 26 - Consultar Informações de Candidato |
| 24 | Adicione novo candidato | Candidatos | Template 27 - Adicionar Novo Candidato |
| 25 | Reagende uma entrevista | Entrevistas | Template 28 - Reagendar Entrevista |
| 26 | Atualize status do candidato | Candidatos | Template 29 - Atualizar Status de Candidato |

---

## Princípios de Design

### Estrutura Padrão de Resposta

Toda resposta da LIA deve seguir esta estrutura:

```
1. RESUMO EXECUTIVO (1-2 linhas)
   - Resposta direta à pergunta
   - Insight principal

2. DADOS E INDICADORES
   - Métricas quantitativas
   - Visualização (tabelas, listas)
   - Comparativos (vs. período anterior, vs. benchmark)

3. ANÁLISE/PARECER (quando aplicável)
   - Interpretação dos dados
   - Pontos de atenção
   - Oportunidades identificadas

4. AÇÕES SUGERIDAS
   - Quick actions clicáveis
   - Próximos passos recomendados
```

### Formatação

- **Emojis**: Usar com moderação para indicadores visuais (🟢 🟡 🔴 📊 📈 📉 ⚠️)
- **Tabelas**: Para comparativos e listas com múltiplas dimensões
- **Listas**: Para itens sequenciais ou pontos de atenção
- **Negrito**: Para destacar números importantes e conclusões
- **Cores de Status**: Verde (bom), Amarelo (atenção), Vermelho (crítico)

---

## Templates de Análise

### 1. Listar Vagas Abertas

**Trigger**: "Listar vagas abertas", "Quais vagas estão abertas?"

```markdown
## 📋 Vagas Abertas

Você tem **{total_vagas}** vagas abertas no momento.

### Resumo por Status

| Status | Quantidade | % do Total |
|--------|------------|------------|
| 🟢 Ativas | {ativas} | {%} |
| 🟡 Urgentes | {urgentes} | {%} |
| 🔴 Atrasadas (SLA) | {atrasadas} | {%} |
| ⏸️ Paralisadas | {paralisadas} | {%} |

### Vagas por Prioridade

**Urgentes (deadline < 7 dias)**
1. **{vaga_1}** - {departamento} | {candidatos} candidatos | Deadline: {data}
2. **{vaga_2}** - {departamento} | {candidatos} candidatos | Deadline: {data}

**Em andamento**
1. **{vaga_3}** - {departamento} | {candidatos} candidatos | Aberta há {dias} dias
2. **{vaga_4}** - {departamento} | {candidatos} candidatos | Aberta há {dias} dias

### Indicadores Rápidos

| Métrica | Valor | Benchmark |
|---------|-------|-----------|
| Tempo médio aberta | {dias} dias | 42 dias |
| Candidatos/vaga | {media} | 25 |
| Taxa de conversão geral | {%} | 15% |

---

**Ações Sugeridas:**
[Ver detalhes das urgentes] [Comparar performance] [Gerar relatório]
```

---

### 2. Quais Vagas Precisam de Atenção Urgente?

**Trigger**: "Quais vagas precisam de atenção urgente?", "Vagas críticas"

```markdown
## ⚠️ Vagas que Precisam de Atenção

Identifiquei **{total}** vagas que requerem ação imediata:

### 🔴 Críticas (Ação Imediata)

| Vaga | Problema | Impacto | Ação Recomendada |
|------|----------|---------|------------------|
| {vaga_1} | SLA excedido ({dias}d) | Alto | Revisar sourcing |
| {vaga_2} | 0 candidatos há 15d | Alto | Ampliar divulgação |
| {vaga_3} | Candidatos parados >7d | Médio | Dar feedback |

### 🟡 Atenção (Próximos 7 dias)

| Vaga | Situação | Dias até Deadline |
|------|----------|-------------------|
| {vaga_4} | Deadline próximo | 5 dias |
| {vaga_5} | Poucas entrevistas agendadas | 7 dias |

### Parecer LIA

**Análise de Risco:**
- {analise_risco_1}
- {analise_risco_2}

**Recomendação Principal:**
{recomendacao_principal}

---

**Ações Sugeridas:**
[Contatar gestores] [Reabrir sourcing] [Ver candidatos parados]
```

---

### 3. Qual Vaga Tem a Melhor Taxa de Conversão?

**Trigger**: "Qual vaga tem a melhor taxa de conversão?", "Vaga com melhor performance"

```markdown
## 🏆 Ranking de Conversão das Vagas

### Top 5 Melhores Taxas de Conversão

| # | Vaga | Departamento | Taxa de Conversão | Aplicações→Contratação |
|---|------|--------------|-------------------|------------------------|
| 🥇 | **{vaga_1}** | {dept} | **{%}%** | {n}/{total} |
| 🥈 | {vaga_2} | {dept} | {%}% | {n}/{total} |
| 🥉 | {vaga_3} | {dept} | {%}% | {n}/{total} |
| 4 | {vaga_4} | {dept} | {%}% | {n}/{total} |
| 5 | {vaga_5} | {dept} | {%}% | {n}/{total} |

### Análise: Por que {vaga_1} performa bem?

**Fatores de Sucesso Identificados:**
1. ✅ Descrição detalhada ({palavras} palavras vs. média de {media})
2. ✅ Faixa salarial competitiva (P{percentil} do mercado)
3. ✅ Tempo de resposta aos candidatos: {horas}h (média: {media_horas}h)
4. ✅ {fator_adicional}

### Comparativo com Benchmark

| Métrica | {vaga_1} | Média Empresa | Benchmark Mercado |
|---------|----------|---------------|-------------------|
| Taxa Conversão | {%}% | {%}% | 15% |
| Tempo até Oferta | {dias}d | {dias}d | 42d |
| Qualidade Candidatos | {score}/5 | {score}/5 | 3.5/5 |

### Replicar Sucesso

**Aplique estas práticas nas outras vagas:**
- {pratica_1}
- {pratica_2}
- {pratica_3}

---

**Ações Sugeridas:**
[Copiar template da vaga] [Aplicar às vagas urgentes] [Ver relatório completo]
```

---

### 4. Comparar Performance das Vagas Ativas

**Trigger**: "Comparar performance das vagas ativas", "Performance comparativa"

```markdown
## 📊 Performance Comparativa das Vagas Ativas

### Visão Geral ({n} vagas ativas)

| Indicador | Média | Melhor | Pior | Benchmark |
|-----------|-------|--------|------|-----------|
| Taxa de Conversão | {%}% | {%}% ({vaga}) | {%}% ({vaga}) | 15% |
| Tempo no Pipeline | {dias}d | {dias}d ({vaga}) | {dias}d ({vaga}) | 14d |
| Candidatos/Vaga | {n} | {n} ({vaga}) | {n} ({vaga}) | 25 |
| Custo/Contratação | R${valor} | R${valor} ({vaga}) | R${valor} ({vaga}) | R$2.500 |

### Ranking de Performance (Score LIA)

| Posição | Vaga | Score LIA | Conversão | Velocidade | Qualidade |
|---------|------|-----------|-----------|------------|-----------|
| 1 | {vaga_1} | ⭐ {score}/100 | {%}% | {dias}d | {score}/5 |
| 2 | {vaga_2} | {score}/100 | {%}% | {dias}d | {score}/5 |
| 3 | {vaga_3} | {score}/100 | {%}% | {dias}d | {score}/5 |
| 4 | {vaga_4} | {score}/100 | {%}% | {dias}d | {score}/5 |
| 5 | {vaga_5} | {score}/100 | {%}% | {dias}d | {score}/5 |

### Análise por Departamento

| Departamento | Vagas | Conversão Média | Tempo Médio | Tendência |
|--------------|-------|-----------------|-------------|-----------|
| {dept_1} | {n} | {%}% | {dias}d | 📈 +{%}% |
| {dept_2} | {n} | {%}% | {dias}d | 📉 -{%}% |
| {dept_3} | {n} | {%}% | {dias}d | ➡️ estável |

### Parecer LIA

**Pontos Fortes:**
- {ponto_forte_1}
- {ponto_forte_2}

**Oportunidades de Melhoria:**
- {oportunidade_1}
- {oportunidade_2}

**Recomendação:**
{recomendacao_principal}

---

**Ações Sugeridas:**
[Exportar relatório] [Ver detalhes por vaga] [Compartilhar com gestores]
```

---

### 5. Sugerir Melhorias para Minhas Vagas

**Trigger**: "Sugerir melhorias para minhas vagas", "Como melhorar minhas vagas?"

```markdown
## 💡 Sugestões de Melhoria para Suas Vagas

Analisei suas **{n}** vagas ativas e identifiquei oportunidades de melhoria:

### 🎯 Impacto Alto (Implementar Primeiro)

#### 1. {vaga_1} - Descrição Incompleta
**Problema:** Descrição com apenas {palavras} palavras (recomendado: 600-800)
**Impacto Estimado:** +{%}% em candidaturas

**Sugestões:**
- Adicionar seção "O que você vai fazer" (responsabilidades do dia-a-dia)
- Incluir stack tecnológico detalhado
- Mencionar cultura e benefícios da equipe

[Otimizar descrição agora]

---

#### 2. {vaga_2} - Faixa Salarial Não Competitiva
**Problema:** Salário abaixo do P25 do mercado para esta senioridade
**Impacto Estimado:** +{%}% em candidatos qualificados

**Sugestões:**
- Revisar faixa para R${min} - R${max} (P50 do mercado)
- Ou destacar benefícios diferenciados para compensar

[Ajustar salário] [Destacar benefícios]

---

#### 3. {vaga_3} - Processo Seletivo Longo
**Problema:** Média de {dias} dias no pipeline (benchmark: 14 dias)
**Impacto Estimado:** -{%}% de desistências

**Sugestões:**
- Consolidar etapas de entrevista (atual: {n} → sugerido: {n})
- Reduzir tempo entre etapas (atual: {dias}d → sugerido: 3d)

[Ver funil detalhado] [Ajustar etapas]

---

### 🟡 Impacto Médio

| Vaga | Problema | Sugestão Rápida |
|------|----------|-----------------|
| {vaga_4} | Poucas competências técnicas definidas | Adicionar 3-5 skills específicas |
| {vaga_5} | Sem perguntas de triagem WSI | Configurar roteiro de screening |
| {vaga_6} | Título genérico | Usar título mais específico e atrativo |

### Scorecard de Qualidade

| Vaga | Descrição | Salário | Pipeline | Divulgação | Score Total |
|------|-----------|---------|----------|------------|-------------|
| {vaga_1} | 🔴 {score}/5 | 🟢 {score}/5 | 🟡 {score}/5 | 🟢 {score}/5 | {total}/20 |
| {vaga_2} | 🟢 {score}/5 | 🔴 {score}/5 | 🟢 {score}/5 | 🟡 {score}/5 | {total}/20 |

### Resumo de Impacto

Se implementar todas as sugestões de alto impacto:
- **Aumento estimado em candidaturas:** +{%}%
- **Redução no tempo de contratação:** -{dias} dias
- **Melhoria na qualidade de candidatos:** +{%}%

---

**Ações Sugeridas:**
[Aplicar melhorias automaticamente] [Ver por prioridade] [Exportar checklist]
```

---

### 6. Quais Vagas Estão Sem Candidatos?

**Trigger**: "Quais vagas estão sem candidatos?", "Vagas sem candidatos", "Sem candidatos"

```markdown
## 🚨 Vagas Sem Candidatos

Você tem **{n}** vagas sem nenhum candidato:

### Lista de Vagas Sem Candidatos

| Vaga | Departamento | Dias Aberta | Visualizações | Problema Provável |
|------|--------------|-------------|---------------|-------------------|
| {vaga_1} | {dept} | {dias}d | {n} views | Baixa visibilidade |
| {vaga_2} | {dept} | {dias}d | {n} views | Título pouco atrativo |
| {vaga_3} | {dept} | {dias}d | {n} views | Salário não divulgado |

### Diagnóstico por Vaga

#### {vaga_1}
**Análise:**
- 📊 {n} visualizações, 0 candidaturas (0% conversão)
- 📍 Publicada em: {canais}
- ⏱️ Última atualização: há {dias} dias

**Problemas Identificados:**
1. ⚠️ {problema_1}
2. ⚠️ {problema_2}

**Ações Recomendadas:**
- {acao_1}
- {acao_2}

[Otimizar esta vaga]

---

### Comparativo com Vagas Similares

| Métrica | Suas Vagas (sem candidatos) | Vagas Similares (com sucesso) |
|---------|----------------------------|-------------------------------|
| Palavras na descrição | {n} | {n} |
| Divulgação salário | {sim/não} | Sim |
| Canais de publicação | {n} | 4+ |
| Tempo de resposta | {horas}h | <24h |

### Plano de Ação Urgente

1. **Hoje:** Revisar e melhorar descrições
2. **Amanhã:** Ampliar canais de divulgação (LinkedIn, Indeed)
3. **Esta semana:** Ativar busca ativa de candidatos
4. **Se persistir:** Considerar ajuste na faixa salarial

---

**Ações Sugeridas:**
[Otimizar todas] [Ativar sourcing] [Publicar em mais canais]
```

---

### 7. Vagas Abertas Há Mais de 30 Dias

**Trigger**: "Vagas abertas há mais de 30 dias", "Vagas antigas"

```markdown
## ⏰ Vagas Abertas Há Mais de 30 Dias

Você tem **{n}** vagas abertas há mais de 30 dias:

### Visão Geral

| Faixa de Tempo | Quantidade | % do Total | Status Médio |
|----------------|------------|------------|--------------|
| 30-45 dias | {n} | {%}% | 🟡 Atenção |
| 46-60 dias | {n} | {%}% | 🟠 Alerta |
| 60+ dias | {n} | {%}% | 🔴 Crítico |

### Detalhamento

| Vaga | Dias Aberta | Candidatos | Etapa Atual | Ação Sugerida |
|------|-------------|------------|-------------|---------------|
| 🔴 {vaga_1} | {dias}d | {n} | {etapa} | Revisão urgente |
| 🔴 {vaga_2} | {dias}d | {n} | {etapa} | Reabrir sourcing |
| 🟠 {vaga_3} | {dias}d | {n} | {etapa} | Acelerar feedback |
| 🟡 {vaga_4} | {dias}d | {n} | {etapa} | Monitorar |

### Análise de Causa Raiz

**Por que essas vagas estão demorando?**

| Causa | Qtd Vagas | Impacto | Solução |
|-------|-----------|---------|---------|
| Requisitos muito específicos | {n} | Alto | Flexibilizar critérios |
| Salário abaixo do mercado | {n} | Alto | Revisar remuneração |
| Processo seletivo longo | {n} | Médio | Otimizar etapas |
| Falta de candidatos | {n} | Alto | Intensificar sourcing |
| Gestor indisponível | {n} | Médio | Alinhar agenda |

### Impacto no Negócio

| Métrica | Valor | Custo Estimado |
|---------|-------|----------------|
| Vagas atrasadas | {n} | - |
| Dias totais de atraso | {n} | - |
| Custo de não ter profissional | ~R${valor}/mês por vaga |
| Impacto em produtividade | {%}% |

### Recomendação LIA

**Prioridade 1 - Ação Imediata ({n} vagas):**
{recomendacao_1}

**Prioridade 2 - Esta Semana ({n} vagas):**
{recomendacao_2}

---

**Ações Sugeridas:**
[Gerar relatório para diretoria] [Agendar revisão com gestores] [Reabrir sourcing em massa]
```

---

## Templates de Métricas

### 8. Qual é a Taxa de Conversão Geral do Funil?

**Trigger**: "Qual é a taxa de conversão geral do funil?", "Taxa de conversão"

```markdown
## 📈 Taxa de Conversão do Funil

### Funil Geral (Últimos 30 dias)

```
Candidaturas    ████████████████████████████  {n} (100%)
        ↓ {%}%
Triagem         ██████████████████            {n} ({%}%)
        ↓ {%}%
Entrevistas     ████████████                  {n} ({%}%)
        ↓ {%}%
Ofertas         ██████                        {n} ({%}%)
        ↓ {%}%
Contratações    ████                          {n} ({%}%)
```

### Taxas de Conversão por Etapa

| Etapa | Candidatos | Taxa Conversão | Benchmark | Status |
|-------|------------|----------------|-----------|--------|
| Candidatura → Triagem | {n} → {n} | {%}% | 50% | 🟢 |
| Triagem → Entrevista | {n} → {n} | {%}% | 30% | 🟡 |
| Entrevista → Oferta | {n} → {n} | {%}% | 50% | 🟢 |
| Oferta → Contratação | {n} → {n} | {%}% | 85% | 🔴 |

### Taxa de Conversão Geral

**{taxa_geral}%** (Candidatura → Contratação)

| Comparativo | Taxa |
|-------------|------|
| Sua empresa | {%}% |
| Benchmark do setor | 15% |
| Meta definida | {%}% |
| Variação vs. mês anterior | {+/-}% |

### Análise por Tipo de Vaga

| Tipo | Conversão | Volume | Tendência |
|------|-----------|--------|-----------|
| Tecnologia | {%}% | {n} | 📈 |
| Comercial | {%}% | {n} | 📉 |
| Administrativo | {%}% | {n} | ➡️ |
| Operacional | {%}% | {n} | 📈 |

### Pontos de Atenção

🔴 **Gargalo identificado:** {etapa_gargalo}
- Taxa atual: {%}%
- Benchmark: {%}%
- Perda de candidatos: {n} nesta etapa

**Possíveis causas:**
- {causa_1}
- {causa_2}

**Ações recomendadas:**
- {acao_1}
- {acao_2}

---

**Ações Sugeridas:**
[Ver detalhes por vaga] [Comparar com período anterior] [Exportar análise]
```

---

### 9. Tempo Médio para Fechar uma Vaga

**Trigger**: "Tempo médio para fechar uma vaga", "Time to fill", "Quanto tempo para contratar?"

```markdown
## ⏱️ Tempo Médio para Fechar Vagas

### Resumo Executivo

**Tempo médio atual:** **{dias} dias**
*vs. benchmark de mercado: 42 dias*

### Histórico dos Últimos 6 Meses

| Mês | Vagas Fechadas | Tempo Médio | Variação |
|-----|----------------|-------------|----------|
| {mes_atual} | {n} | {dias}d | {+/-}% |
| {mes-1} | {n} | {dias}d | {+/-}% |
| {mes-2} | {n} | {dias}d | {+/-}% |
| {mes-3} | {n} | {dias}d | {+/-}% |
| {mes-4} | {n} | {dias}d | {+/-}% |
| {mes-5} | {n} | {dias}d | {+/-}% |

### Breakdown por Etapa

| Etapa | Tempo Médio | Benchmark | Status |
|-------|-------------|-----------|--------|
| Publicação → Primeira Triagem | {dias}d | 3d | 🟢 |
| Triagem → Primeira Entrevista | {dias}d | 5d | 🟡 |
| Entrevistas (total) | {dias}d | 10d | 🔴 |
| Última Entrevista → Oferta | {dias}d | 3d | 🟢 |
| Oferta → Aceite | {dias}d | 5d | 🟢 |
| **TOTAL** | **{dias}d** | **42d** | - |

### Por Senioridade

| Nível | Tempo Médio | Volume | Tendência |
|-------|-------------|--------|-----------|
| Júnior | {dias}d | {n} vagas | 📉 Melhorando |
| Pleno | {dias}d | {n} vagas | ➡️ Estável |
| Sênior | {dias}d | {n} vagas | 📈 Piorando |
| Especialista | {dias}d | {n} vagas | ➡️ Estável |
| Liderança | {dias}d | {n} vagas | 📈 Piorando |

### Por Departamento

| Departamento | Tempo Médio | Vagas | Observação |
|--------------|-------------|-------|------------|
| {dept_1} | {dias}d | {n} | Mais rápido |
| {dept_2} | {dias}d | {n} | Na média |
| {dept_3} | {dias}d | {n} | Mais lento |

### Análise LIA

**O que está funcionando bem:**
- ✅ {ponto_positivo_1}
- ✅ {ponto_positivo_2}

**Oportunidades de melhoria:**
- ⚠️ {oportunidade_1}: Potencial de reduzir {dias}d
- ⚠️ {oportunidade_2}: Potencial de reduzir {dias}d

**Impacto estimado das melhorias:**
Se implementadas, tempo médio pode cair para **{dias}d** (-{%}%)

---

**Ações Sugeridas:**
[Ver vagas mais lentas] [Otimizar etapas] [Definir SLAs por tipo]
```

---

### 10. Performance das Vagas Este Mês vs. Anterior

**Trigger**: "Performance das vagas este mês vs anterior", "Comparativo mensal"

```markdown
## 📊 Performance: {mes_atual} vs. {mes_anterior}

### Resumo Comparativo

| Métrica | {mes_anterior} | {mes_atual} | Variação | Tendência |
|---------|----------------|-------------|----------|-----------|
| Vagas Abertas | {n} | {n} | {+/-n} | 📈/📉 |
| Vagas Fechadas | {n} | {n} | {+/-n} | 📈/📉 |
| Candidaturas | {n} | {n} | {+/-n} ({%}%) | 📈/📉 |
| Contratações | {n} | {n} | {+/-n} ({%}%) | 📈/📉 |
| Taxa de Conversão | {%}% | {%}% | {+/-}pp | 📈/📉 |
| Tempo Médio | {dias}d | {dias}d | {+/-}d | 📈/📉 |
| Custo/Contratação | R${valor} | R${valor} | {+/-}% | 📈/📉 |

### Análise Visual

**Candidaturas por Semana**
```
Semana 1: ████████████████ {n}
Semana 2: ████████████████████ {n}
Semana 3: ██████████████ {n}
Semana 4: ██████████████████ {n}

Mês anterior (média): ████████████████ {n}
```

### Destaques do Mês

**🏆 Melhores Resultados:**
1. {destaque_1} (+{%}% vs. mês anterior)
2. {destaque_2} (+{%}% vs. mês anterior)
3. {destaque_3} (+{%}% vs. mês anterior)

**⚠️ Pontos de Atenção:**
1. {atencao_1} (-{%}% vs. mês anterior)
2. {atencao_2} (-{%}% vs. mês anterior)

### Funil Comparativo

| Etapa | {mes_anterior} | {mes_atual} | Var. |
|-------|----------------|-------------|------|
| Candidaturas | {n} | {n} | {+/-}% |
| Triagem | {n} ({%}%) | {n} ({%}%) | {+/-}pp |
| Entrevistas | {n} ({%}%) | {n} ({%}%) | {+/-}pp |
| Ofertas | {n} ({%}%) | {n} ({%}%) | {+/-}pp |
| Contratações | {n} ({%}%) | {n} ({%}%) | {+/-}pp |

### Análise LIA

**Resumo:**
{resumo_analise}

**O que explica a variação:**
- {explicacao_1}
- {explicacao_2}

**Previsão para próximo mês:**
Baseado nas tendências atuais, estimo:
- Contratações: {n} ({+/-}% vs. {mes_atual})
- Tempo médio: {dias}d
- Taxa de conversão: {%}%

---

**Ações Sugeridas:**
[Exportar relatório] [Ver tendência 6 meses] [Compartilhar com diretoria]
```

---

### 11. Quantas Contratações Fizemos Este Trimestre?

**Trigger**: "Quantas contratações fizemos este trimestre?", "Contratações do trimestre"

```markdown
## 🎯 Contratações do Trimestre ({trimestre})

### Resumo Executivo

**Total de Contratações:** **{n}** profissionais

| Comparativo | Valor |
|-------------|-------|
| Meta do trimestre | {n} |
| Realizado | {n} |
| Atingimento | {%}% |
| vs. Trimestre anterior | {+/-}% |

### Contratações por Mês

| Mês | Contratações | Meta | Atingimento | Acumulado |
|-----|--------------|------|-------------|-----------|
| {mes_1} | {n} | {n} | {%}% | {n} |
| {mes_2} | {n} | {n} | {%}% | {n} |
| {mes_3} | {n} | {n} | {%}% | {n} |
| **Total** | **{n}** | **{n}** | **{%}%** | - |

### Por Departamento

| Departamento | Contratações | Meta | Status | Custo Total |
|--------------|--------------|------|--------|-------------|
| {dept_1} | {n} | {n} | 🟢 {%}% | R${valor} |
| {dept_2} | {n} | {n} | 🟡 {%}% | R${valor} |
| {dept_3} | {n} | {n} | 🔴 {%}% | R${valor} |
| **Total** | **{n}** | **{n}** | **{%}%** | **R${valor}** |

### Por Tipo de Contratação

| Tipo | Quantidade | % do Total | Custo Médio |
|------|------------|------------|-------------|
| CLT | {n} | {%}% | R${valor} |
| PJ | {n} | {%}% | R${valor} |
| Estágio | {n} | {%}% | R${valor} |
| Temporário | {n} | {%}% | R${valor} |

### Por Senioridade

| Nível | Quantidade | Salário Médio | Tempo Médio |
|-------|------------|---------------|-------------|
| Júnior | {n} | R${valor} | {dias}d |
| Pleno | {n} | R${valor} | {dias}d |
| Sênior | {n} | R${valor} | {dias}d |
| Especialista | {n} | R${valor} | {dias}d |
| Liderança | {n} | R${valor} | {dias}d |

### Indicadores de Qualidade

| Métrica | Valor | Benchmark |
|---------|-------|-----------|
| Tempo médio de contratação | {dias}d | 42d |
| Taxa de aceite de ofertas | {%}% | 85% |
| Custo médio por contratação | R${valor} | R$2.500 |
| Diversidade (% mulheres) | {%}% | 40% |
| Qualidade (performance 90 dias) | {score}/5 | 3.5/5 |

### Fontes de Contratação

| Fonte | Contratações | % | Custo/Hire | Qualidade |
|-------|--------------|---|------------|-----------|
| LinkedIn | {n} | {%}% | R${valor} | {score}/5 |
| Indicação | {n} | {%}% | R${valor} | {score}/5 |
| Site Carreiras | {n} | {%}% | R${valor} | {score}/5 |
| Indeed | {n} | {%}% | R${valor} | {score}/5 |
| Outros | {n} | {%}% | R${valor} | {score}/5 |

---

**Ações Sugeridas:**
[Exportar relatório executivo] [Ver detalhes por área] [Planejar próximo trimestre]
```

---

### 12. Quantas Vagas Estão Atrasadas no SLA?

**Trigger**: "Quantas vagas estão atrasadas no SLA?", "Vagas fora do SLA"

```markdown
## ⚠️ Vagas Atrasadas no SLA

### Resumo

**{n}** vagas estão fora do SLA definido.

| Status SLA | Quantidade | % do Total |
|------------|------------|------------|
| 🟢 Dentro do SLA | {n} | {%}% |
| 🟡 Próximo do limite | {n} | {%}% |
| 🔴 Fora do SLA | {n} | {%}% |

### Vagas Fora do SLA

| Vaga | SLA | Dias Aberta | Atraso | Responsável | Motivo |
|------|-----|-------------|--------|-------------|--------|
| {vaga_1} | {dias}d | {dias}d | +{dias}d | {nome} | {motivo} |
| {vaga_2} | {dias}d | {dias}d | +{dias}d | {nome} | {motivo} |
| {vaga_3} | {dias}d | {dias}d | +{dias}d | {nome} | {motivo} |

### SLAs por Tipo de Vaga

| Tipo de Vaga | SLA Definido | Tempo Real Médio | Status |
|--------------|--------------|------------------|--------|
| Júnior/Estágio | 30 dias | {dias}d | 🟢/🔴 |
| Pleno | 45 dias | {dias}d | 🟢/🔴 |
| Sênior | 60 dias | {dias}d | 🟢/🔴 |
| Especialista | 75 dias | {dias}d | 🟢/🔴 |
| Liderança | 90 dias | {dias}d | 🟢/🔴 |

### Análise de Causas

| Causa do Atraso | Qtd Vagas | % |
|-----------------|-----------|---|
| Poucos candidatos qualificados | {n} | {%}% |
| Gestor indisponível para entrevistas | {n} | {%}% |
| Processo de aprovação demorado | {n} | {%}% |
| Requisitos muito específicos | {n} | {%}% |
| Candidatos rejeitando ofertas | {n} | {%}% |

### Impacto no Negócio

| Métrica | Valor |
|---------|-------|
| Dias totais de atraso | {n} dias |
| Custo estimado (produtividade perdida) | R${valor} |
| Impacto em projetos | {n} projetos afetados |

### Plano de Ação Recomendado

**Para vagas críticas (atraso > 30 dias):**
1. Reunião de alinhamento com gestor
2. Revisão de requisitos e flexibilização
3. Intensificar sourcing ativo

**Para vagas em alerta (atraso 15-30 dias):**
1. Acelerar processo de entrevistas
2. Aumentar canais de divulgação
3. Considerar headhunter externo

---

**Ações Sugeridas:**
[Enviar alerta aos gestores] [Revisar requisitos] [Intensificar sourcing]
```

---

### 13. Quantas Vagas Temos por Departamento?

**Trigger**: "Quantas vagas temos por departamento?", "Vagas por área"

```markdown
## 🏢 Distribuição de Vagas por Departamento

### Visão Geral

**Total de Vagas:** {n} ({n} ativas, {n} em aprovação, {n} paralisadas)

### Por Departamento

| Departamento | Total | Ativas | Aprovação | Paralisadas | Preenchidas (YTD) |
|--------------|-------|--------|-----------|-------------|-------------------|
| {dept_1} | {n} | {n} | {n} | {n} | {n} |
| {dept_2} | {n} | {n} | {n} | {n} | {n} |
| {dept_3} | {n} | {n} | {n} | {n} | {n} |
| {dept_4} | {n} | {n} | {n} | {n} | {n} |
| {dept_5} | {n} | {n} | {n} | {n} | {n} |
| **Total** | **{n}** | **{n}** | **{n}** | **{n}** | **{n}** |

### Visualização

```
{dept_1}:     ████████████████████ {n} vagas ({%}%)
{dept_2}:     ██████████████ {n} vagas ({%}%)
{dept_3}:     ████████████ {n} vagas ({%}%)
{dept_4}:     ████████ {n} vagas ({%}%)
{dept_5}:     ██████ {n} vagas ({%}%)
Outros:       ████ {n} vagas ({%}%)
```

### Performance por Departamento

| Departamento | Vagas Ativas | Taxa Conversão | Tempo Médio | Score LIA |
|--------------|--------------|----------------|-------------|-----------|
| {dept_1} | {n} | {%}% | {dias}d | {score}/100 |
| {dept_2} | {n} | {%}% | {dias}d | {score}/100 |
| {dept_3} | {n} | {%}% | {dias}d | {score}/100 |

### Demanda vs. Capacidade

| Departamento | Vagas Abertas | Recrutadores Alocados | Carga Média |
|--------------|---------------|----------------------|-------------|
| {dept_1} | {n} | {n} | {n} vagas/recrutador |
| {dept_2} | {n} | {n} | {n} vagas/recrutador |
| {dept_3} | {n} | {n} | {n} vagas/recrutador |

**Benchmark de carga:** 8-10 vagas ativas por recrutador

### Insights

**Departamentos com maior demanda:**
- {dept_1}: {n} vagas ({%}% do total)

**Departamentos com melhor performance:**
- {dept_2}: {%}% de conversão, {dias}d tempo médio

**Departamentos que precisam de atenção:**
- {dept_3}: Taxa de conversão {%}% (abaixo da média de {%}%)

---

**Ações Sugeridas:**
[Ver detalhes por departamento] [Realocar recursos] [Exportar dados]
```

---

## Templates de Funil

### 14. Onde Está o Gargalo do Processo Seletivo?

**Trigger**: "Onde está o gargalo do processo seletivo?", "Gargalo do funil"

```markdown
## 🔍 Análise de Gargalos do Processo Seletivo

### Diagnóstico do Funil

```
Candidaturas    ████████████████████████████  {n} (100%)
        ↓ {%}% ✅
Triagem         ██████████████████            {n}
        ↓ {%}% ⚠️ GARGALO IDENTIFICADO
Entrevistas     ████████                      {n}
        ↓ {%}% ✅
Ofertas         ██████                        {n}
        ↓ {%}% ✅
Contratações    ████                          {n}
```

### 🔴 Gargalo Principal: {etapa_gargalo}

**Diagnóstico:**
- Taxa de conversão atual: **{%}%**
- Benchmark esperado: **{%}%**
- Gap: **{n} pontos percentuais**
- Candidatos perdidos: **{n}** nesta etapa

### Análise Detalhada do Gargalo

| Indicador | Valor Atual | Benchmark | Status |
|-----------|-------------|-----------|--------|
| Tempo médio na etapa | {dias}d | {dias}d | 🔴 |
| Taxa de conversão | {%}% | {%}% | 🔴 |
| Candidatos parados >7 dias | {n} | <5 | 🔴 |
| Feedback em até 48h | {%}% | 90% | 🟡 |

### Causas Identificadas

| Causa | Frequência | Impacto | Ação Recomendada |
|-------|------------|---------|------------------|
| {causa_1} | {%}% | Alto | {acao_1} |
| {causa_2} | {%}% | Médio | {acao_2} |
| {causa_3} | {%}% | Médio | {acao_3} |

### Tempo por Etapa (Dias)

| Etapa | Atual | Ideal | Diferença |
|-------|-------|-------|-----------|
| Triagem | {dias}d | 3d | +{dias}d |
| 1ª Entrevista | {dias}d | 5d | +{dias}d 🔴 |
| 2ª Entrevista | {dias}d | 5d | +{dias}d |
| Oferta | {dias}d | 3d | +{dias}d |

### Impacto Financeiro

| Métrica | Valor |
|---------|-------|
| Candidatos perdidos por mês | {n} |
| Custo de retrabalho | R${valor}/mês |
| Impacto em produtividade | ~R${valor}/mês |
| **Custo total do gargalo** | **R${valor}/mês** |

### Plano de Ação

**Semana 1:**
1. {acao_semana_1}

**Semana 2:**
2. {acao_semana_2}

**Semana 3-4:**
3. {acao_semana_3}

**Meta:** Aumentar conversão de {%}% para {%}% em 30 dias

---

**Ações Sugeridas:**
[Implementar melhorias] [Ver candidatos parados] [Agendar entrevistas pendentes]
```

---

### 15. Qual Etapa Tem Maior Taxa de Rejeição?

**Trigger**: "Qual etapa tem maior taxa de rejeição?", "Taxa de rejeição por etapa"

```markdown
## 📉 Análise de Taxa de Rejeição por Etapa

### Resumo

**Etapa com maior rejeição:** **{etapa}** ({%}% de rejeição)

### Taxa de Rejeição por Etapa

| Etapa | Entradas | Rejeições | Taxa | Benchmark | Status |
|-------|----------|-----------|------|-----------|--------|
| Triagem Curricular | {n} | {n} | {%}% | 50% | 🟢/🔴 |
| Screening Telefônico | {n} | {n} | {%}% | 30% | 🟢/🔴 |
| Entrevista RH | {n} | {n} | {%}% | 25% | 🟢/🔴 |
| Entrevista Técnica | {n} | {n} | {%}% | 40% | 🟢/🔴 |
| Entrevista Gestor | {n} | {n} | {%}% | 20% | 🟢/🔴 |
| Oferta | {n} | {n} | {%}% | 15% | 🟢/🔴 |

### 🔴 Foco: {etapa} - Maior Taxa de Rejeição

**Taxa atual:** {%}% (benchmark: {%}%)

**Motivos de Rejeição (Top 5):**

| Motivo | Quantidade | % | Evitável? |
|--------|------------|---|-----------|
| {motivo_1} | {n} | {%}% | Sim/Não |
| {motivo_2} | {n} | {%}% | Sim/Não |
| {motivo_3} | {n} | {%}% | Sim/Não |
| {motivo_4} | {n} | {%}% | Sim/Não |
| {motivo_5} | {n} | {%}% | Sim/Não |

### Rejeições Evitáveis vs. Esperadas

**Evitáveis ({%}%):** {n} candidatos
- Poderiam ser filtrados antes com melhor triagem
- Custo de processamento desperdiçado: R${valor}

**Esperadas ({%}%):** {n} candidatos
- Fazem parte do processo normal de seleção
- Indicam que o funil está funcionando

### Recomendações

**Para reduzir rejeições evitáveis:**
1. {recomendacao_1}
2. {recomendacao_2}
3. {recomendacao_3}

**Impacto estimado:**
- Redução de {%}% nas rejeições
- Economia de {horas}h por semana em triagem
- Melhoria na experiência do candidato

---

**Ações Sugeridas:**
[Ajustar critérios de triagem] [Revisar perguntas de screening] [Ver análise por vaga]
```

---

### 16. Vagas com Deadline Próximo

**Trigger**: "Vagas com deadline próximo", "Deadline esta semana"

```markdown
## 📅 Vagas com Deadline Próximo

### Próximos 7 Dias

| Vaga | Deadline | Dias Restantes | Candidatos | Status | Ação Necessária |
|------|----------|----------------|------------|--------|-----------------|
| 🔴 {vaga_1} | {data} | {n}d | {n} | Em risco | Acelerar |
| 🔴 {vaga_2} | {data} | {n}d | {n} | Em risco | Priorizar |
| 🟡 {vaga_3} | {data} | {n}d | {n} | Atenção | Monitorar |
| 🟢 {vaga_4} | {data} | {n}d | {n} | No prazo | OK |

### Próximos 14 Dias

| Vaga | Deadline | Dias Restantes | Candidatos | Etapa Avançada |
|------|----------|----------------|------------|----------------|
| {vaga_5} | {data} | {n}d | {n} | {n} em entrevista |
| {vaga_6} | {data} | {n}d | {n} | {n} em entrevista |
| {vaga_7} | {data} | {n}d | {n} | {n} em entrevista |

### Análise de Viabilidade

| Vaga | Probabilidade de Fechamento | Justificativa |
|------|----------------------------|---------------|
| {vaga_1} | 🔴 Baixa ({%}%) | Poucos candidatos qualificados |
| {vaga_2} | 🟡 Média ({%}%) | Precisa acelerar entrevistas |
| {vaga_3} | 🟢 Alta ({%}%) | Candidato em fase de oferta |

### Plano de Ação Prioritário

**Hoje:**
- [ ] {acao_1}
- [ ] {acao_2}

**Amanhã:**
- [ ] {acao_3}
- [ ] {acao_4}

**Esta semana:**
- [ ] {acao_5}
- [ ] {acao_6}

### Comunicação Necessária

| Stakeholder | Vaga | Mensagem | Urgência |
|-------------|------|----------|----------|
| {gestor_1} | {vaga_1} | Solicitar priorização de entrevistas | Alta |
| {gestor_2} | {vaga_2} | Alinhar expectativas de deadline | Média |

---

**Ações Sugeridas:**
[Enviar alertas] [Agendar entrevistas] [Solicitar extensão de prazo]
```

---

### 17. Performance dos Últimos 30 Dias

**Trigger**: "Performance dos últimos 30 dias", "Resumo do mês"

```markdown
## 📊 Performance dos Últimos 30 Dias

**Período:** {data_inicio} a {data_fim}

### Resumo Executivo

| Indicador | Valor | vs. Período Anterior | Meta | Status |
|-----------|-------|---------------------|------|--------|
| Vagas Abertas | {n} | {+/-}% | {n} | 🟢/🔴 |
| Vagas Fechadas | {n} | {+/-}% | {n} | 🟢/🔴 |
| Candidaturas | {n} | {+/-}% | {n} | 🟢/🔴 |
| Entrevistas | {n} | {+/-}% | {n} | 🟢/🔴 |
| Ofertas | {n} | {+/-}% | {n} | 🟢/🔴 |
| Contratações | {n} | {+/-}% | {n} | 🟢/🔴 |

### Métricas Chave

| KPI | Valor | Benchmark | Tendência |
|-----|-------|-----------|-----------|
| Taxa de Conversão | {%}% | 15% | 📈/📉 |
| Time to Fill | {dias}d | 42d | 📈/📉 |
| Cost per Hire | R${valor} | R$2.500 | 📈/📉 |
| Offer Acceptance Rate | {%}% | 85% | 📈/📉 |
| Quality of Hire (90d) | {score}/5 | 3.5/5 | 📈/📉 |

### Funil dos Últimos 30 Dias

```
Candidaturas    ████████████████████████████  {n}
        ↓ {%}%
Triagem         ██████████████████            {n}
        ↓ {%}%
Entrevistas     ████████████                  {n}
        ↓ {%}%
Ofertas         ██████                        {n}
        ↓ {%}%
Contratações    ████                          {n}
```

### Top 5 Vagas por Performance

| Posição | Vaga | Score | Conversão | Tempo | Status |
|---------|------|-------|-----------|-------|--------|
| 🥇 | {vaga_1} | {score}/100 | {%}% | {dias}d | Fechada |
| 🥈 | {vaga_2} | {score}/100 | {%}% | {dias}d | Em andamento |
| 🥉 | {vaga_3} | {score}/100 | {%}% | {dias}d | Em andamento |
| 4 | {vaga_4} | {score}/100 | {%}% | {dias}d | Em andamento |
| 5 | {vaga_5} | {score}/100 | {%}% | {dias}d | Em andamento |

### Atividade do Time

| Recrutador | Vagas Ativas | Contratações | Candidatos Processados |
|------------|--------------|--------------|------------------------|
| {nome_1} | {n} | {n} | {n} |
| {nome_2} | {n} | {n} | {n} |
| {nome_3} | {n} | {n} | {n} |

### Análise LIA

**Destaques Positivos:**
- ✅ {destaque_1}
- ✅ {destaque_2}

**Pontos de Atenção:**
- ⚠️ {atencao_1}
- ⚠️ {atencao_2}

**Recomendações para o Próximo Período:**
1. {recomendacao_1}
2. {recomendacao_2}
3. {recomendacao_3}

---

**Ações Sugeridas:**
[Exportar relatório PDF] [Enviar para diretoria] [Definir metas próximo mês]
```

---

## Templates de Ações

### 18. Analisar Pipeline de Candidatos

**Trigger**: "Analisar pipeline de candidatos", "Status do pipeline"

```markdown
## 👥 Análise do Pipeline de Candidatos

### Visão Geral

**Total de Candidatos Ativos:** {n}

| Etapa | Candidatos | % | Tempo Médio | Ação Pendente |
|-------|------------|---|-------------|---------------|
| Aplicados (novos) | {n} | {%}% | {dias}d | Triagem |
| Em Triagem | {n} | {%}% | {dias}d | Análise de CV |
| Screening | {n} | {%}% | {dias}d | Entrevista inicial |
| Entrevista RH | {n} | {%}% | {dias}d | Avançar ou rejeitar |
| Entrevista Técnica | {n} | {%}% | {dias}d | Avaliação técnica |
| Entrevista Gestor | {n} | {%}% | {dias}d | Decisão final |
| Proposta | {n} | {%}% | {dias}d | Aguardando resposta |
| **Total Ativos** | **{n}** | **100%** | - | - |

### Candidatos que Precisam de Atenção

**Parados há mais de 7 dias:**

| Candidato | Vaga | Etapa | Dias Parado | Ação Sugerida |
|-----------|------|-------|-------------|---------------|
| {nome_1} | {vaga} | {etapa} | {n}d | {acao} |
| {nome_2} | {vaga} | {etapa} | {n}d | {acao} |
| {nome_3} | {vaga} | {etapa} | {n}d | {acao} |

### Distribuição por Vaga

| Vaga | Total | Triagem | Entrevista | Proposta |
|------|-------|---------|------------|----------|
| {vaga_1} | {n} | {n} | {n} | {n} |
| {vaga_2} | {n} | {n} | {n} | {n} |
| {vaga_3} | {n} | {n} | {n} | {n} |

### Qualidade do Pipeline

| Indicador | Valor | Status |
|-----------|-------|--------|
| Score LIA médio | {score}/100 | 🟢/🔴 |
| % candidatos qualificados | {%}% | 🟢/🔴 |
| % com entrevista agendada | {%}% | 🟢/🔴 |
| Previsão de fechamentos | {n} | - |

### Próximas Ações

**Alta Prioridade:**
1. {acao_1} - {n} candidatos afetados
2. {acao_2} - {n} candidatos afetados

**Média Prioridade:**
3. {acao_3}
4. {acao_4}

---

**Ações Sugeridas:**
[Enviar feedback em massa] [Agendar entrevistas] [Ver candidatos por vaga]
```

---

### 19. Gerar Relatório de Vagas

**Trigger**: "Gerar relatório de vagas", "Relatório completo"

```markdown
## 📋 Relatório de Vagas

**Gerado em:** {data_hora}
**Período:** {periodo}
**Preparado por:** LIA (Learning Intelligence Assistant)

---

### 1. Sumário Executivo

Este relatório apresenta a análise completa das vagas do período, incluindo métricas de performance, análise de funil e recomendações estratégicas.

**Principais Achados:**
- {achado_1}
- {achado_2}
- {achado_3}

---

### 2. Visão Geral das Vagas

| Métrica | Valor |
|---------|-------|
| Total de vagas no período | {n} |
| Vagas ativas | {n} |
| Vagas fechadas | {n} |
| Vagas canceladas | {n} |
| Taxa de sucesso | {%}% |

---

### 3. Performance por Status

| Status | Quantidade | % do Total | Tempo Médio |
|--------|------------|------------|-------------|
| Rascunho | {n} | {%}% | - |
| Em Aprovação | {n} | {%}% | {dias}d |
| Ativas | {n} | {%}% | {dias}d |
| Paralisadas | {n} | {%}% | {dias}d |
| Concluídas | {n} | {%}% | {dias}d |
| Canceladas | {n} | {%}% | {dias}d |

---

### 4. Métricas de Recrutamento

| KPI | Valor Atual | Meta | Variação | Status |
|-----|-------------|------|----------|--------|
| Time to Fill | {dias} dias | {dias} dias | {+/-}% | 🟢/🔴 |
| Time to Hire | {dias} dias | {dias} dias | {+/-}% | 🟢/🔴 |
| Cost per Hire | R${valor} | R${valor} | {+/-}% | 🟢/🔴 |
| Quality of Hire | {score}/5 | {score}/5 | {+/-}% | 🟢/🔴 |
| Offer Acceptance | {%}% | {%}% | {+/-}pp | 🟢/🔴 |
| Conversion Rate | {%}% | {%}% | {+/-}pp | 🟢/🔴 |

---

### 5. Análise de Funil

| Etapa | Volume | Taxa Conversão | Benchmark | Gap |
|-------|--------|----------------|-----------|-----|
| Aplicações | {n} | - | - | - |
| Triagem | {n} | {%}% | 50% | {+/-}pp |
| Entrevistas | {n} | {%}% | 30% | {+/-}pp |
| Ofertas | {n} | {%}% | 50% | {+/-}pp |
| Contratações | {n} | {%}% | 85% | {+/-}pp |

---

### 6. Performance por Departamento

| Departamento | Vagas | Fechadas | Abertas | Time to Fill | Conversão |
|--------------|-------|----------|---------|--------------|-----------|
| {dept_1} | {n} | {n} | {n} | {dias}d | {%}% |
| {dept_2} | {n} | {n} | {n} | {dias}d | {%}% |
| {dept_3} | {n} | {n} | {n} | {dias}d | {%}% |

---

### 7. Fontes de Candidatos

| Fonte | Aplicações | Contratações | Taxa | Custo/Hire | ROI |
|-------|------------|--------------|------|------------|-----|
| LinkedIn | {n} | {n} | {%}% | R${valor} | {x}x |
| Indeed | {n} | {n} | {%}% | R${valor} | {x}x |
| Indicação | {n} | {n} | {%}% | R${valor} | {x}x |
| Site | {n} | {n} | {%}% | R${valor} | {x}x |

---

### 8. Análise de Diversidade

| Dimensão | % Pipeline | % Contratações | Meta | Status |
|----------|------------|----------------|------|--------|
| Gênero feminino | {%}% | {%}% | 40% | 🟢/🔴 |
| PcD | {%}% | {%}% | 5% | 🟢/🔴 |
| 50+ anos | {%}% | {%}% | 10% | 🟢/🔴 |

---

### 9. Recomendações

**Ações Imediatas:**
1. {recomendacao_1}
2. {recomendacao_2}

**Melhorias de Médio Prazo:**
3. {recomendacao_3}
4. {recomendacao_4}

**Iniciativas Estratégicas:**
5. {recomendacao_5}

---

### 10. Próximos Passos

- [ ] {proximo_passo_1}
- [ ] {proximo_passo_2}
- [ ] {proximo_passo_3}

---

*Relatório gerado automaticamente pela LIA. Para dúvidas, consulte seu Gerente de Recrutamento.*

---

**Ações Sugeridas:**
[Exportar PDF] [Exportar Excel] [Enviar por email] [Agendar relatório recorrente]
```

---

### 20. Otimizar Descrição de Vaga

**Trigger**: "Otimizar descrição de vaga", "Melhorar descrição"

```markdown
## ✨ Análise e Otimização da Descrição

### Vaga Analisada: {titulo_vaga}

### Score de Qualidade Atual

**Score Geral:** {score}/100

| Critério | Score | Status | Peso |
|----------|-------|--------|------|
| Clareza do título | {n}/10 | 🟢/🔴 | Alto |
| Descrição de responsabilidades | {n}/10 | 🟢/🔴 | Alto |
| Requisitos técnicos | {n}/10 | 🟢/🔴 | Alto |
| Benefícios e cultura | {n}/10 | 🟢/🔴 | Médio |
| SEO e palavras-chave | {n}/10 | 🟢/🔴 | Médio |
| Atratividade geral | {n}/10 | 🟢/🔴 | Alto |

### Diagnóstico Detalhado

**✅ Pontos Fortes:**
- {ponto_forte_1}
- {ponto_forte_2}

**⚠️ Oportunidades de Melhoria:**
- {oportunidade_1}
- {oportunidade_2}
- {oportunidade_3}

### Comparativo com Vagas Similares

| Métrica | Sua Vaga | Média do Mercado | Top 10% |
|---------|----------|------------------|---------|
| Palavras | {n} | 650 | 800 |
| Benefícios listados | {n} | 8 | 12 |
| Skills mencionadas | {n} | 10 | 15 |
| Seções estruturadas | {n} | 5 | 7 |

### Sugestões de Otimização

**1. Título**
- Atual: "{titulo_atual}"
- Sugerido: "{titulo_sugerido}"
- Impacto: +{%}% em visualizações

**2. Resumo Inicial**
- Adicionar: {sugestao_resumo}
- Impacto: +{%}% em candidaturas

**3. Responsabilidades**
- Atualmente: {n} itens
- Sugerido: Adicionar {sugestao_responsabilidades}

**4. Requisitos**
- Separar em "Obrigatórios" e "Diferenciais"
- Adicionar senioridade esperada para cada skill

**5. Benefícios**
- Destacar: {beneficios_destacar}
- Adicionar: {beneficios_adicionar}

**6. Palavras-chave SEO**
- Adicionar: {keywords}
- Para melhor ranqueamento em job boards

### Versão Otimizada (Preview)

```
{preview_otimizado}
```

### Impacto Estimado

| Métrica | Antes | Depois (estimado) |
|---------|-------|-------------------|
| Visualizações | {n}/dia | +{%}% |
| Candidaturas | {n}/semana | +{%}% |
| Qualidade candidatos | {score}/5 | +{%}% |

---

**Ações Sugeridas:**
[Aplicar otimizações] [Editar manualmente] [Ver versão completa]
```

---

### 21. Sugerir Perguntas de Entrevista

**Trigger**: "Sugerir perguntas de entrevista", "Perguntas para entrevista"

```markdown
## 🎤 Perguntas Sugeridas para Entrevista

### Vaga: {titulo_vaga}
**Baseado em:** Competências técnicas e comportamentais da vaga

---

### Perguntas Técnicas (Validação de Hard Skills)

#### 1. {competencia_tecnica_1}
**Pergunta:** "{pergunta_tecnica_1}"

**O que avaliar:**
- {criterio_1}
- {criterio_2}

**Resposta esperada (nível sênior):**
- {resposta_esperada}

**Sinais de alerta:**
- 🔴 {sinal_alerta}

---

#### 2. {competencia_tecnica_2}
**Pergunta:** "{pergunta_tecnica_2}"

**O que avaliar:**
- {criterio_1}
- {criterio_2}

---

### Perguntas Comportamentais (Metodologia STAR)

#### 1. {competencia_comportamental_1}
**Pergunta:** "Conte-me sobre uma situação em que {situacao}..."

**Estrutura STAR esperada:**
- **S**ituação: Contexto claro
- **T**arefa: Responsabilidade específica
- **A**ção: O que o candidato fez
- **R**esultado: Impacto mensurável

**Indicadores positivos:**
- ✅ {indicador_1}
- ✅ {indicador_2}

**Indicadores negativos:**
- ⚠️ {indicador_negativo}

---

#### 2. {competencia_comportamental_2}
**Pergunta:** "{pergunta_comportamental_2}"

---

### Perguntas de Fit Cultural

#### 1. Alinhamento com valores
**Pergunta:** "Nossos valores incluem {valores}. Como você demonstra isso no dia a dia?"

#### 2. Expectativas de carreira
**Pergunta:** "Onde você se vê em 3 anos e como essa posição se encaixa?"

---

### Perguntas Situacionais (Micro Cases)

#### Cenário: {cenario}
**Pergunta:** "Imagine que {situacao_hipotetica}. O que você faria?"

**Avaliar:**
- Raciocínio lógico
- Capacidade de priorização
- Alinhamento com a cultura

---

### Roteiro Sugerido (60 min)

| Tempo | Etapa | Perguntas |
|-------|-------|-----------|
| 0-5min | Abertura | Apresentação, quebra-gelo |
| 5-20min | Técnico | Perguntas 1-3 |
| 20-40min | Comportamental | Perguntas STAR |
| 40-50min | Fit Cultural | Valores e expectativas |
| 50-60min | Fechamento | Dúvidas do candidato |

---

**Ações Sugeridas:**
[Salvar roteiro] [Personalizar perguntas] [Enviar ao gestor]
```

---

### 22. Calcular Métricas de Recrutamento

**Trigger**: "Calcular métricas de recrutamento", "Dashboard de métricas"

```markdown
## 📊 Dashboard de Métricas de Recrutamento

**Período:** {periodo}
**Atualizado em:** {data_hora}

---

### Métricas de Eficiência

| Métrica | Fórmula | Valor | Benchmark | Status |
|---------|---------|-------|-----------|--------|
| **Time to Fill** | Data fechamento - Data abertura | **{dias}d** | 42d | 🟢/🔴 |
| **Time to Hire** | Data aceite - Data aplicação | **{dias}d** | 36d | 🟢/🔴 |
| **Time in Stage** | Tempo médio por etapa | **{dias}d** | 5d | 🟢/🔴 |

---

### Métricas de Qualidade

| Métrica | Fórmula | Valor | Benchmark | Status |
|---------|---------|-------|-----------|--------|
| **Quality of Hire** | Performance 90d + Retenção 1 ano | **{score}/5** | 3.5/5 | 🟢/🔴 |
| **Offer Acceptance Rate** | Ofertas aceitas / Ofertas feitas | **{%}%** | 85% | 🟢/🔴 |
| **First-Year Retention** | Contratados ativos após 1 ano | **{%}%** | 80% | 🟢/🔴 |

---

### Métricas de Custo

| Métrica | Fórmula | Valor | Benchmark | Status |
|---------|---------|-------|-----------|--------|
| **Cost per Hire** | Custos totais / Contratações | **R${valor}** | R$2.500 | 🟢/🔴 |
| **Cost per Application** | Custos marketing / Aplicações | **R${valor}** | R$15 | 🟢/🔴 |
| **Source Cost** | Custo por canal / Contratações do canal | **R${valor}** | Varia | - |

---

### Métricas de Volume

| Métrica | Fórmula | Valor | Benchmark | Status |
|---------|---------|-------|-----------|--------|
| **Application Rate** | Aplicações / Visualizações | **{%}%** | 8% | 🟢/🔴 |
| **Interview to Offer** | Ofertas / Entrevistas | **{%}%** | 33% | 🟢/🔴 |
| **Yield Ratio** | Contratações / Aplicações | **{%}%** | 5% | 🟢/🔴 |

---

### Métricas de Produtividade

| Métrica | Fórmula | Valor | Benchmark | Status |
|---------|---------|-------|-----------|--------|
| **Requisitions per Recruiter** | Vagas ativas / Recrutadores | **{n}** | 8-10 | 🟢/🔴 |
| **Hires per Recruiter** | Contratações / Recrutadores (mês) | **{n}** | 3-5 | 🟢/🔴 |
| **Candidates Processed** | Candidatos triados / Recrutador | **{n}** | 50-80 | 🟢/🔴 |

---

### Métricas de Diversidade

| Métrica | Fórmula | Valor | Meta | Status |
|---------|---------|-------|------|--------|
| **Gender Diversity** | % mulheres no pipeline | **{%}%** | 40% | 🟢/🔴 |
| **PcD Inclusion** | % PcD no pipeline | **{%}%** | 5% | 🟢/🔴 |
| **Diversity Conversion** | % diverso contratado vs. pipeline | **{%}%** | ≥100% | 🟢/🔴 |

---

### Cálculos Detalhados

**Cost per Hire:**
```
Custos Internos: R${valor}
- Salários recrutadores (proporcional): R${valor}
- Ferramentas (ATS, job boards): R${valor}
- Treinamentos: R${valor}

Custos Externos: R${valor}
- Job boards e anúncios: R${valor}
- Agências (se houver): R${valor}
- Eventos e employer branding: R${valor}

Total: R${valor}
Contratações: {n}
Cost per Hire: R${total} / {n} = R${resultado}
```

---

### Tendências (Últimos 6 Meses)

| Métrica | {mes-5} | {mes-4} | {mes-3} | {mes-2} | {mes-1} | {mes} | Trend |
|---------|---------|---------|---------|---------|---------|-------|-------|
| Time to Fill | {n}d | {n}d | {n}d | {n}d | {n}d | {n}d | 📈/📉 |
| Conversão | {%}% | {%}% | {%}% | {%}% | {%}% | {%}% | 📈/📉 |
| Cost/Hire | R${n} | R${n} | R${n} | R${n} | R${n} | R${n} | 📈/📉 |

---

**Ações Sugeridas:**
[Exportar dashboard] [Ver detalhes por vaga] [Configurar alertas de KPI]
```

---

## Templates de Ações Rápidas

Esta seção contém templates para as ações rápidas disponíveis no painel de sugestões da LIA.

---

### 23. Criar Nova Vaga

**Trigger**: "Criar uma nova vaga", "Nova vaga", "Abrir vaga"

```markdown
## ➕ Criar Nova Vaga

Vou te ajudar a criar uma nova vaga. Para configurar corretamente, preciso de algumas informações:

### Dados Básicos Coletados

| Campo | Status | Valor |
|-------|--------|-------|
| Título da vaga | ✅ Informado | {titulo} |
| Departamento | ✅ Informado | {departamento} |
| Nível de senioridade | ⏳ Pendente | - |
| Tipo de contratação | ⏳ Pendente | - |
| Modelo de trabalho | ⏳ Pendente | - |

### Formulário de Criação

**Título:** {titulo}
**Departamento:** {departamento}
**Gestor responsável:** {gestor}

**Requisitos identificados:**
- {requisito_1}
- {requisito_2}
- {requisito_3}

### Análise de Mercado

| Métrica | Valor Sugerido |
|---------|----------------|
| Faixa salarial de mercado | R${min} - R${max} |
| Tempo médio para fechamento | {dias} dias |
| Candidatos disponíveis estimados | {n} |
| Concorrência por talento | {nivel} |

### Recomendações LIA

**Para aumentar atratividade:**
1. ✅ {recomendacao_1}
2. ✅ {recomendacao_2}
3. ✅ {recomendacao_3}

### Próximos Passos

1. Completar informações básicas
2. Revisar descrição da vaga
3. Definir requisitos obrigatórios vs. desejáveis
4. Configurar pipeline de seleção
5. Publicar ou enviar para aprovação

---

**Ações Sugeridas:**
[Preencher formulário completo] [Usar template similar] [Enviar para aprovação]
```

---

### 24. Solicitar Aprovação de Vaga

**Trigger**: "Solicite aprovação de nova vaga", "Aprovar vaga", "Enviar vaga para aprovação"

```markdown
## 📋 Solicitação de Aprovação de Vaga

### Resumo da Solicitação

**Vaga:** {titulo_vaga}
**Solicitante:** {nome_solicitante}
**Data da solicitação:** {data}
**Status:** 🟡 Aguardando aprovação

### Dados da Vaga

| Campo | Valor |
|-------|-------|
| Título | {titulo} |
| Departamento | {departamento} |
| Gestor requisitante | {gestor} |
| Nível | {senioridade} |
| Tipo de contratação | {tipo} |
| Modelo de trabalho | {modelo} |
| Faixa salarial | R${min} - R${max} |
| Headcount aprovado | {sim/não} |

### Justificativa

**Motivo da abertura:**
{justificativa}

**Impacto no negócio:**
- {impacto_1}
- {impacto_2}

### Análise de Orçamento

| Item | Valor | Status |
|------|-------|--------|
| Orçamento departamento | R${valor} | 🟢 Disponível |
| Custo estimado anual | R${valor} | - |
| % do orçamento | {%}% | {status} |

### Fluxo de Aprovação

| Etapa | Aprovador | Status | Data |
|-------|-----------|--------|------|
| 1. Gestor Direto | {nome} | ✅ Aprovado | {data} |
| 2. RH Business Partner | {nome} | 🟡 Pendente | - |
| 3. Diretor de Área | {nome} | ⏳ Aguardando | - |

### Documentação Anexa

- [ ] Descrição da vaga
- [ ] Justificativa de headcount
- [ ] Orçamento aprovado
- [ ] Perfil ideal (competências)

### Parecer LIA

**Análise preliminar:**
- {analise_1}
- {analise_2}

**Recomendação:** {recomendacao}

---

**Ações Sugeridas:**
[Enviar para aprovadores] [Editar justificativa] [Anexar documentos] [Cancelar solicitação]
```

---

### 25. Compartilhar Candidatos com Gestor

**Trigger**: "Compartilhe candidatos com gestor", "Enviar candidatos para gestor", "Shortlist para gestor"

```markdown
## 📤 Compartilhar Candidatos com Gestor

### Resumo do Compartilhamento

**Vaga:** {titulo_vaga}
**Gestor destinatário:** {nome_gestor}
**Candidatos selecionados:** {n} perfis

### Lista de Candidatos

| # | Candidato | Score LIA | Experiência | Status | Destaque |
|---|-----------|-----------|-------------|--------|----------|
| 1 | **{nome_1}** | ⭐ {score}/100 | {anos}a | Disponível | Top pick |
| 2 | {nome_2} | {score}/100 | {anos}a | Disponível | - |
| 3 | {nome_3} | {score}/100 | {anos}a | Em processo | - |
| 4 | {nome_4} | {score}/100 | {anos}a | Disponível | - |
| 5 | {nome_5} | {score}/100 | {anos}a | Disponível | - |

### Análise Comparativa

| Critério | {nome_1} | {nome_2} | {nome_3} | Peso |
|----------|----------|----------|----------|------|
| Experiência técnica | {score}/5 | {score}/5 | {score}/5 | Alto |
| Fit cultural | {score}/5 | {score}/5 | {score}/5 | Alto |
| Disponibilidade | {score}/5 | {score}/5 | {score}/5 | Médio |
| Pretensão salarial | {score}/5 | {score}/5 | {score}/5 | Médio |
| **Score Total** | **{total}** | **{total}** | **{total}** | - |

### Recomendação LIA

**Candidato recomendado:** {nome_1}

**Justificativa:**
- {justificativa_1}
- {justificativa_2}
- {justificativa_3}

**Pontos de atenção:**
- ⚠️ {ponto_atencao_1}
- ⚠️ {ponto_atencao_2}

### Configuração do Compartilhamento

| Opção | Configuração |
|-------|--------------|
| Incluir currículos | ✅ Sim |
| Incluir análise LIA | ✅ Sim |
| Incluir pretensão salarial | ⬜ Não |
| Incluir contatos | ⬜ Não |
| Prazo para feedback | 3 dias úteis |

### Mensagem para o Gestor

```
Olá {nome_gestor},

Segue a shortlist de {n} candidatos pré-selecionados para a vaga de {titulo_vaga}.

Destaco {nome_1} como principal recomendação, com score LIA de {score}/100 e {anos} anos de experiência relevante.

Aguardo seu feedback em até 3 dias úteis para darmos continuidade ao processo.
```

---

**Ações Sugeridas:**
[Enviar agora] [Editar mensagem] [Adicionar mais candidatos] [Agendar envio]
```

---

### 26. Consultar Informações de Candidato

**Trigger**: "Consulte informações sobre candidato", "Ver perfil do candidato", "Detalhes do candidato"

```markdown
## 👤 Informações do Candidato

### {nome_candidato}

**Score LIA:** ⭐ {score}/100 | **Status:** {status_atual}

---

### Resumo Executivo

{resumo_profissional}

### Dados Pessoais

| Campo | Valor |
|-------|-------|
| Nome completo | {nome} |
| Email | {email} |
| Telefone | {telefone} |
| LinkedIn | {linkedin} |
| Localização | {cidade}, {estado} |
| Disponibilidade | {disponibilidade} |

### Experiência Profissional

| Empresa | Cargo | Período | Duração |
|---------|-------|---------|---------|
| {empresa_1} | {cargo_1} | {periodo_1} | {duracao_1} |
| {empresa_2} | {cargo_2} | {periodo_2} | {duracao_2} |
| {empresa_3} | {cargo_3} | {periodo_3} | {duracao_3} |

**Tempo total de experiência:** {anos_total} anos
**Média de permanência:** {anos_media} anos por empresa

### Formação Acadêmica

| Instituição | Curso | Conclusão |
|-------------|-------|-----------|
| {instituicao_1} | {curso_1} | {ano_1} |
| {instituicao_2} | {curso_2} | {ano_2} |

### Competências Técnicas

| Skill | Nível | Anos de Experiência |
|-------|-------|---------------------|
| {skill_1} | Avançado | {anos}a |
| {skill_2} | Avançado | {anos}a |
| {skill_3} | Intermediário | {anos}a |
| {skill_4} | Intermediário | {anos}a |

### Histórico no Processo

| Data | Etapa | Responsável | Resultado |
|------|-------|-------------|-----------|
| {data_1} | Aplicação | Sistema | Recebido |
| {data_2} | Triagem LIA | LIA | Score {score}/100 |
| {data_3} | Entrevista RH | {nome} | ✅ Aprovado |
| {data_4} | Entrevista Técnica | {nome} | 🟡 Pendente |

### Análise LIA

**Pontos Fortes:**
- ✅ {ponto_forte_1}
- ✅ {ponto_forte_2}
- ✅ {ponto_forte_3}

**Pontos de Atenção:**
- ⚠️ {ponto_atencao_1}
- ⚠️ {ponto_atencao_2}

**Fit com a vaga ({titulo_vaga}):**
- Match de competências: {%}%
- Match cultural: {%}%
- Adequação salarial: {status}

### Pretensão e Disponibilidade

| Item | Valor |
|------|-------|
| Pretensão salarial | R${valor} |
| Modelo preferido | {modelo} |
| Disponibilidade para início | {prazo} |
| Disposição para realocação | {sim/não} |

---

**Ações Sugeridas:**
[Agendar entrevista] [Enviar feedback] [Mover para próxima etapa] [Ver currículo completo]
```

---

### 27. Adicionar Novo Candidato

**Trigger**: "Adicione novo candidato", "Cadastrar candidato", "Novo candidato"

```markdown
## ➕ Adicionar Novo Candidato

### Formulário de Cadastro

Vou te ajudar a cadastrar um novo candidato no sistema.

### Dados Coletados

| Campo | Status | Valor |
|-------|--------|-------|
| Nome completo | ✅ | {nome} |
| Email | ✅ | {email} |
| Telefone | ⏳ Pendente | - |
| Currículo | ⏳ Pendente | - |
| Vaga de interesse | ✅ | {vaga} |

### Informações Básicas

**Nome:** {nome}
**Email:** {email}
**Telefone:** {telefone}
**LinkedIn:** {linkedin}
**Localização:** {cidade}, {estado}

### Experiência Identificada

| Empresa | Cargo | Período |
|---------|-------|---------|
| {empresa_1} | {cargo_1} | {periodo_1} |
| {empresa_2} | {cargo_2} | {periodo_2} |

### Skills Identificadas

- {skill_1}
- {skill_2}
- {skill_3}
- {skill_4}

### Análise Preliminar LIA

**Score estimado:** {score}/100

**Match com vagas abertas:**

| Vaga | Match | Status |
|------|-------|--------|
| {vaga_1} | {%}% | 🟢 Alto |
| {vaga_2} | {%}% | 🟡 Médio |
| {vaga_3} | {%}% | 🟡 Médio |

### Fonte do Candidato

| Campo | Valor |
|-------|-------|
| Origem | {origem} |
| Indicado por | {nome_indicador} (se aplicável) |
| Data de cadastro | {data} |
| Cadastrado por | {recrutador} |

### Próximos Passos

1. ⬜ Completar dados de contato
2. ⬜ Anexar currículo
3. ⬜ Associar a vaga
4. ⬜ Iniciar triagem automática
5. ⬜ Enviar email de confirmação

### Consentimento LGPD

| Item | Status |
|------|--------|
| Consentimento para tratamento de dados | ⏳ Pendente |
| Consentimento para comunicações | ⏳ Pendente |
| Prazo de retenção informado | ⏳ Pendente |

---

**Ações Sugeridas:**
[Completar cadastro] [Anexar currículo] [Associar a vaga] [Enviar para triagem]
```

---

### 28. Reagendar Entrevista

**Trigger**: "Reagende uma entrevista", "Remarcar entrevista", "Alterar horário de entrevista"

```markdown
## 📅 Reagendar Entrevista

### Dados da Entrevista Atual

| Campo | Valor |
|-------|-------|
| Candidato | {nome_candidato} |
| Vaga | {titulo_vaga} |
| Tipo de entrevista | {tipo} |
| Data/hora atual | {data_hora_atual} |
| Entrevistadores | {entrevistadores} |
| Local/Link | {local_ou_link} |

### Motivo do Reagendamento

**Solicitante:** {nome_solicitante}
**Motivo:** {motivo}

| Solicitante | Motivo Comum |
|-------------|--------------|
| 🧑‍💼 Candidato | Conflito de agenda / Imprevisto pessoal |
| 👤 Entrevistador | Reunião urgente / Viagem |
| 🏢 Empresa | Reestruturação do processo |

### Disponibilidade do Candidato

| Data | Horário | Status |
|------|---------|--------|
| {data_1} | {horario_1} | 🟢 Disponível |
| {data_2} | {horario_2} | 🟢 Disponível |
| {data_3} | {horario_3} | 🟡 Verificar |

### Disponibilidade dos Entrevistadores

**{entrevistador_1}:**
| Data | Horário | Status |
|------|---------|--------|
| {data_1} | {horario_1} | 🟢 Livre |
| {data_2} | {horario_2} | 🔴 Ocupado |

**{entrevistador_2}:**
| Data | Horário | Status |
|------|---------|--------|
| {data_1} | {horario_1} | 🟢 Livre |
| {data_2} | {horario_2} | 🟢 Livre |

### Melhor Horário Sugerido

**Recomendação LIA:** {data_sugerida} às {horario_sugerido}

**Justificativa:**
- ✅ Todos os participantes disponíveis
- ✅ Dentro do prazo ideal do processo
- ✅ Horário preferencial do candidato

### Novo Agendamento

| Campo | Valor |
|-------|-------|
| Nova data/hora | {nova_data_hora} |
| Formato | {presencial/remoto} |
| Link/Local | {novo_link_local} |
| Duração | {duracao} minutos |

### Notificações a Enviar

| Destinatário | Tipo | Status |
|--------------|------|--------|
| {candidato} | Email + WhatsApp | ⏳ Pendente |
| {entrevistador_1} | Email + Calendário | ⏳ Pendente |
| {entrevistador_2} | Email + Calendário | ⏳ Pendente |

### Template de Mensagem

**Para o candidato:**
```
Olá {nome_candidato},

Precisamos reagendar sua entrevista para a vaga de {titulo_vaga}.

📅 Nova data: {nova_data}
⏰ Novo horário: {novo_horario}
📍 Local/Link: {local_link}

Confirme sua disponibilidade respondendo esta mensagem.

Atenciosamente,
{nome_recrutador}
```

---

**Ações Sugeridas:**
[Confirmar reagendamento] [Buscar outros horários] [Notificar participantes] [Cancelar entrevista]
```

---

### 29. Atualizar Status de Candidato

**Trigger**: "Atualize status do candidato", "Mover candidato", "Alterar etapa do candidato"

```markdown
## 🔄 Atualizar Status de Candidato

### Candidato Selecionado

**Nome:** {nome_candidato}
**Vaga:** {titulo_vaga}
**Status atual:** {status_atual}
**Tempo na etapa atual:** {dias} dias

### Movimentação

| De | Para |
|----|------|
| {etapa_origem} | {etapa_destino} |

### Etapas Disponíveis

| Etapa | Status | Ação |
|-------|--------|------|
| ✅ Aplicação | Concluída | - |
| ✅ Triagem | Concluída | - |
| ➡️ **Entrevista RH** | Atual | - |
| ⬜ Entrevista Técnica | Próxima | Mover |
| ⬜ Entrevista Gestor | Pendente | Mover |
| ⬜ Proposta | Pendente | Mover |
| ⬜ Contratado | Final | Mover |
| ❌ Rejeitado | Encerramento | Mover |
| ⏸️ Em Espera | Pausar | Mover |

### Histórico de Movimentações

| Data | De | Para | Responsável | Observação |
|------|----|----|-------------|------------|
| {data_1} | Aplicação | Triagem | Sistema | Automático |
| {data_2} | Triagem | Entrevista RH | {nome} | Score: {score}/100 |
| {data_3} | Entrevista RH | {destino} | {nome} | {observacao} |

### Análise da Movimentação

**Validações:**
- ✅ Candidato elegível para a etapa
- ✅ Todas as etapas anteriores concluídas
- ✅ Feedback registrado na etapa atual
- ⚠️ Tempo na etapa atual: {dias} dias (média: {media} dias)

### Feedback da Etapa Atual

**Avaliador:** {nome_avaliador}
**Data:** {data_avaliacao}
**Resultado:** {resultado}

**Parecer:**
{parecer_texto}

**Pontos avaliados:**

| Critério | Nota | Observação |
|----------|------|------------|
| {criterio_1} | {nota}/5 | {obs_1} |
| {criterio_2} | {nota}/5 | {obs_2} |
| {criterio_3} | {nota}/5 | {obs_3} |

### Notificações Automáticas

| Ação | Destinatário | Tipo |
|------|--------------|------|
| Atualização de status | {candidato} | Email |
| Novo candidato na etapa | {proximo_avaliador} | Notificação |
| Log de auditoria | Sistema | Automático |

### Template de Comunicação

**Se aprovado para próxima etapa:**
```
Olá {nome_candidato},

Temos o prazer de informar que você avançou para a próxima etapa do processo seletivo para {titulo_vaga}!

Próxima etapa: {etapa_destino}
Em breve entraremos em contato para agendar.
```

**Se rejeitado:**
```
Olá {nome_candidato},

Agradecemos seu interesse na vaga de {titulo_vaga} e o tempo dedicado ao nosso processo seletivo.

Após cuidadosa avaliação, decidimos seguir com outros candidatos neste momento. Seu perfil ficará em nosso banco de talentos para futuras oportunidades.
```

---

**Ações Sugeridas:**
[Confirmar movimentação] [Adicionar feedback] [Enviar notificação] [Cancelar]
```

---

### 30. Buscar Candidatos

**Trigger**: "Buscar candidatos", "Pesquisar candidatos", "Encontrar perfis"

```markdown
## 🔍 Buscar Candidatos

### Critérios de Busca

**Vaga/Perfil:** {titulo_vaga_ou_descricao}

### Filtros Aplicados

| Filtro | Valor |
|--------|-------|
| Cargo/Título | {titulo} |
| Experiência mínima | {anos} anos |
| Localização | {localizacao} |
| Modelo de trabalho | {modelo} |
| Faixa salarial | R${min} - R${max} |
| Disponibilidade | {disponibilidade} |

### Skills Buscadas

| Skill | Prioridade | Nível Mínimo |
|-------|------------|--------------|
| {skill_1} | Obrigatória | Avançado |
| {skill_2} | Obrigatória | Intermediário |
| {skill_3} | Desejável | Qualquer |
| {skill_4} | Desejável | Qualquer |

### Resultados da Busca

**Total encontrado:** {n} candidatos
**Altamente compatíveis (>80%):** {n}
**Compatíveis (60-80%):** {n}
**Parcialmente compatíveis (<60%):** {n}

### Top 10 Candidatos

| # | Candidato | Score | Experiência | Localização | Disponibilidade | Status |
|---|-----------|-------|-------------|-------------|-----------------|--------|
| 1 | **{nome_1}** | ⭐ {score}/100 | {anos}a | {cidade} | Imediata | 🟢 Novo |
| 2 | {nome_2} | {score}/100 | {anos}a | {cidade} | 30 dias | 🟢 Novo |
| 3 | {nome_3} | {score}/100 | {anos}a | {cidade} | Imediata | 🟡 Em processo |
| 4 | {nome_4} | {score}/100 | {anos}a | {cidade} | A combinar | 🟢 Novo |
| 5 | {nome_5} | {score}/100 | {anos}a | {cidade} | Imediata | 🟢 Novo |
| 6 | {nome_6} | {score}/100 | {anos}a | {cidade} | 15 dias | 🟢 Novo |
| 7 | {nome_7} | {score}/100 | {anos}a | {cidade} | Imediata | 🔵 No banco |
| 8 | {nome_8} | {score}/100 | {anos}a | {cidade} | 30 dias | 🔵 No banco |
| 9 | {nome_9} | {score}/100 | {anos}a | {cidade} | Imediata | 🟢 Novo |
| 10 | {nome_10} | {score}/100 | {anos}a | {cidade} | A combinar | 🟢 Novo |

### Análise do Candidato #1 - {nome_1}

**Score:** ⭐ {score}/100

**Match de Competências:**
| Skill Requerida | Candidato | Match |
|-----------------|-----------|-------|
| {skill_1} | {nivel} - {anos}a | ✅ |
| {skill_2} | {nivel} - {anos}a | ✅ |
| {skill_3} | {nivel} - {anos}a | 🟡 |

**Experiência Relevante:**
- {empresa_1} - {cargo_1} ({periodo_1})
- {empresa_2} - {cargo_2} ({periodo_2})

**Por que este candidato?**
- {razao_1}
- {razao_2}

### Fontes dos Candidatos

| Fonte | Quantidade | % |
|-------|------------|---|
| Banco interno | {n} | {%}% |
| LinkedIn | {n} | {%}% |
| Indicações | {n} | {%}% |
| Job boards | {n} | {%}% |

### Refinar Busca

**Sugestões para ampliar resultados:**
- Flexibilizar experiência para {anos-1} anos (+{n} candidatos)
- Incluir localidades próximas (+{n} candidatos)
- Aceitar nível {nivel_abaixo} para {skill_3} (+{n} candidatos)

**Sugestões para refinar resultados:**
- Adicionar certificação {certificacao}
- Filtrar por empresa anterior específica
- Exigir inglês avançado

---

**Ações Sugeridas:**
[Salvar busca] [Adicionar à vaga] [Contatar candidatos] [Exportar lista] [Refinar filtros]
```

---

## Referências de Mercado

### Benchmarks Utilizados

| Métrica | Fonte | Valor | Ano |
|---------|-------|-------|-----|
| Time to Fill | SHRM | 42 dias | 2024 |
| Cost per Hire | SHRM | US$4,700 (~R$23.500) | 2024 |
| Offer Acceptance Rate | LinkedIn | 85% | 2024 |
| Interview to Offer | Greenhouse | 33% | 2024 |
| First-Year Retention | Work Institute | 80% | 2024 |
| Quality of Hire | Korn Ferry | 3.5/5 | 2024 |

### Fontes de Referência

1. **SHRM (Society for Human Resource Management)**
   - Human Capital Benchmarking Report
   - Talent Acquisition Benchmarking Report

2. **LinkedIn Talent Solutions**
   - Global Talent Trends Report
   - Recruiting Benchmarks

3. **Greenhouse/Lever/SmartRecruiters**
   - Industry Benchmark Reports
   - Best Practices Guides

4. **AIHR (Academy to Innovate HR)**
   - Recruitment Dashboard Templates
   - HR Analytics Frameworks

5. **iCIMS/Workday**
   - Workforce Report
   - Talent Acquisition KPIs

---

## Diretrizes de Implementação

### Para o Time de Desenvolvimento

1. **Cada template deve ser dinâmico:** Substituir placeholders por dados reais
2. **Manter formatação Markdown:** Para renderização correta no chat
3. **Quick Actions:** Implementar como botões clicáveis
4. **Dados em tempo real:** Buscar do banco de dados/API
5. **Cache:** Considerar cache para métricas pesadas (atualizar a cada 5 min)

### Para o Time de Produto

1. **Teste A/B:** Testar variações de formato com recrutadores
2. **Feedback:** Coletar NPS após cada resposta
3. **Personalização:** Permitir que usuários customizem templates favoritos
4. **Exportação:** Habilitar exportação em PDF/Excel para relatórios

---

**Documento criado em:** 2026-01-20
**Última atualização:** 2026-01-20
**Responsável:** Equipe de Produto LIA
