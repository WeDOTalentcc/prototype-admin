# Roadmap: Otimização da Integração Pearch AI

**Data de Análise:** Dezembro 2025  
**Versão:** 1.0  
**Status:** Proposta para Avaliação

---

## 1. Resumo Executivo

Este documento apresenta uma análise completa dos campos disponíveis na API da Pearch AI, comparando com o que já utilizamos na plataforma LIA, incluindo custos de créditos, estimativas de valor e recomendações de implementação.

### Principais Descobertas

1. **Muitos campos de alto valor são GRATUITOS** (incluídos no custo base)
2. **LIA (Claude) é 3-5x mais barata** que Pearch Insights para análises de IA
3. **Abordagem híbrida** oferece melhor custo-benefício
4. **Campos como `is_opentowork` e `outreach_message`** são gratuitos e não estamos usando

---

## 2. Estratégia 100% Opt-in (Implementado - Dezembro 2025)

### 2.1 Princípio Fundamental

**Pearch = SEMPRE escolha explícita do recrutador, NUNCA automático**

Zero créditos gastos sem consentimento explícito do usuário.

### 2.2 Modelo de Custo Simplificado

| Tipo de Busca | Custo | Características |
|---------------|-------|-----------------|
| **Local (Base Interna)** | **Gratuito** | Sempre o padrão |
| **Global (Pearch FAST)** | 1 crédito/candidato | Requer confirmação explícita |

> **Nota:** A opção PRO (5 créditos/candidato) foi removida para simplificar e reduzir custos.

### 2.3 Fluxo de Busca Opt-in

```
┌─────────────────────────────────────────────────────────────┐
│                    1. BUSCA PADRÃO                          │
│  Sempre LOCAL (gratuito)                                    │
│  Mostra: Candidatos da base interna + "Fonte: Local"        │
│  Custo: ZERO                                                │
└─────────────────────────────────────────────────────────────┘
                              │
                (poucos resultados ou usuário deseja mais)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 2. SUGESTÃO DE EXPANSÃO                     │
│  Card: "Poucos resultados. Expandir para busca global?"     │
│  Texto genérico: "+800M perfis disponíveis"                 │
│  NÃO mostra contagem específica de candidatos globais       │
└─────────────────────────────────────────────────────────────┘
                              │
                     (usuário clica "Expandir")
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              3. CONFIRMAÇÃO DE CRÉDITOS                     │
│  Dialog: "Buscar até X candidatos"                          │
│  Custo estimado: X créditos (1 crédito/candidato)           │
│  Botões: [Cancelar] [Confirmar Busca]                       │
└─────────────────────────────────────────────────────────────┘
                              │
                     (usuário confirma)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                4. BUSCA GLOBAL EXECUTADA                    │
│  Mostra: Resultados + badge "Fonte: Global"                 │
│  Contagem global aparece SÓ AGORA                           │
│  Créditos debitados                                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Componentes UI Implementados

| Componente | Localização | Função |
|------------|-------------|--------|
| `CreditConfirmationDialog` | `search/credit-confirmation-dialog.tsx` | Confirmação de créditos antes de busca global |
| `SearchSourcePill` | `candidates-page.tsx` | Indicador visual "Fonte: Local" / "Fonte: Global" |
| `LowResultsCard` | `candidates-page.tsx` | Card sugerindo expansão quando < 5 resultados |
| Modal de Filtros | `advanced-filters-modal.tsx` | Seção "Origem da Busca" com 3 opções |

### 2.5 Opções de Origem da Busca

No modal de filtros avançados:

| Opção | Descrição | Custo |
|-------|-----------|-------|
| 🏠 **Base Local (Gratuito)** | Busca apenas na base interna | Gratuito |
| 🌐 **Busca Global Pearch** | Busca em 800M+ perfis | 1 crédito/candidato |
| 🔄 **Híbrido** | Local primeiro, depois Global | Créditos só para global |

### 2.6 Regras de Exibição

| Situação | O que mostrar |
|----------|--------------|
| Antes de buscar Pearch | Nada sobre Pearch (zero custo) |
| Sugestão de expansão | Texto genérico "+800M perfis" (sem contagem) |
| Usuário clica "Expandir" | Diálogo de confirmação de créditos |
| Após busca Pearch | Resultados + badge "Fonte: Global" + contagem |

### 2.7 Integração com Wizard de Criação de Vagas

Após criar uma vaga:
1. **Busca automática LOCAL** (gratuito) para encontrar candidatos
2. **Análise de aderência:**
   - BAIXO (<40%): Sugestão forte de expandir global
   - MÉDIO (40-70%): Sugestão moderada
   - ALTO (>70%): Resultados locais suficientes
3. **GlobalSuggestionModal** com opções:
   - "Calibração" (refinar critérios)
   - "Triagem" (iniciar processo)
4. **Confirmação de créditos** se usuário optar por global

### 2.8 Calibração com Indicador de Origem

Na calibração de candidatos:
- 🏠 **Badge "Base Local"** (verde): Candidato já na base
- 🌐 **Badge "Busca Global"** (âmbar): Candidato do Pearch

**Ações automáticas:**
- Candidatos GLOBAIS aprovados → Adicionados à base local + vaga
- Candidatos LOCAIS aprovados → Opcional adicionar à vaga (toggle)

### 2.9 Benefícios da Estratégia

| Benefício | Impacto |
|-----------|---------|
| Custo controlado | Zero gastos inesperados |
| Transparência | Usuário sempre sabe o custo antes |
| Priorização local | Maximiza uso da base existente |
| Flexibilidade | Expansão global quando necessário |
| Confiança | Usuário no controle total |

---

## 3. Estrutura de Créditos da Pearch AI

### 3.1 Custo Base por Tipo de Busca

| Tipo | Custo/Candidato | Características |
|------|-----------------|-----------------|
| `fast` | 1 crédito | Mais rápido, menor recall |
| `pro` | 5 créditos | Melhor qualidade e recall |

### 3.2 Opções Adicionais (Custo Extra)

| Opção | Custo Adicional | Descrição |
|-------|-----------------|-----------|
| `insights: true` | +1 crédito | Análises de IA detalhadas |
| `profile_scoring: true` | +1 crédito | Score 0-4 com reranking |
| `high_freshness: true` | +2 créditos | Dados em tempo real do LinkedIn |
| `require_emails: true` | +1 crédito | Filtrar só perfis com email |
| `show_emails: true` | +2 créditos | Exibir emails (só cobra se tiver) |
| `require_phone_numbers: true` | +1 crédito | Filtrar só perfis com telefone |
| `show_phone_numbers: true` | +14 créditos | Exibir telefones (só cobra se tiver) |

### 3.3 Estimativa de Custo por Crédito

- **Plano básico:** ~$0.03 - $0.05 por crédito
- **Plano volume:** ~$0.02 - $0.03 por crédito

---

## 4. Tabela Completa de Campos Disponíveis

### 4.1 Dados Básicos do Perfil

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Recomendação |
|-------|-----------|------------|--------------|-----------|--------------|
| `name`, `first_name`, `last_name` | Nome completo | ✅ Usando | Gratuito | N/A | Manter |
| `picture_url` | Foto do perfil | ✅ Usando | Gratuito | N/A | Manter |
| `title`, `headline` | Cargo atual | ✅ Usando | Gratuito | N/A | Manter |
| `current_company` | Empresa atual | ✅ Usando | Gratuito | N/A | Manter |
| `summary` | Resumo do perfil | ✅ Usando | Gratuito | N/A | Manter |
| `location` | Localização | ✅ Usando | Gratuito | N/A | Manter |
| `linkedin_url`, `linkedin_slug` | Perfil LinkedIn | ✅ Usando | Gratuito | N/A | Manter |
| `total_experience_years` | Anos de experiência | ✅ Usando | Gratuito | N/A | Manter |

### 3.2 Indicadores Profissionais Diferenciados

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `is_opentowork` | Aberto a oportunidades | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐⭐⭐ | **IMPLEMENTAR - Alta prioridade** |
| `is_decision_maker` | É decisor/líder (0-1) | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐⭐ | Implementar |
| `is_hiring` | Está contratando | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐ | Implementar |
| `is_top_universities` | Universidades de ponta | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐ | Implementar |
| `estimated_age` | Idade estimada | ❌ Não usando | **Gratuito** | N/A | ⭐⭐ | Avaliar (LGPD) |
| `gender` | Gênero | ❌ Não usando | **Gratuito** | N/A | ⭐⭐ | Para relatórios D&I |

### 3.3 Rede e Influência

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `followers_count` | Seguidores LinkedIn | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐ | Implementar - Indicador de influência |
| `connections_count` | Conexões LinkedIn | ❌ Não usando | **Gratuito** | N/A | ⭐⭐ | Implementar |

### 3.4 Skills e Expertise

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `skills[]` | Habilidades listadas | ✅ Usando | Gratuito | N/A | ⭐⭐⭐⭐⭐ | Manter |
| `expertise[]` | Áreas de expertise | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐⭐ | Implementar - Complementa skills |

### 3.5 Idiomas

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `languages[]` | Idiomas declarados | ⚠️ Parcial | **Gratuito** | N/A | ⭐⭐⭐⭐ | Melhorar - Mostrar proficiência (A1-C2) |
| `inferred_languages[]` | Idiomas inferidos pela IA | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐ | Implementar |

### 3.6 Experiência Profissional

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `experiences[]` | Lista de experiências | ✅ Usando | Gratuito | N/A | ⭐⭐⭐⭐⭐ | Manter |
| `company_info.industries` | Indústrias da empresa | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐⭐ | Implementar - Contexto de mercado |
| `company_info.num_employees` | Tamanho da empresa | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐ | Implementar - Porte |
| `company_info.technologies` | Stack da empresa | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐⭐ | Implementar - Tech stack |
| `company_info.is_startup` | Se é startup | ❌ Não usando | **Gratuito** | N/A | ⭐⭐⭐ | Implementar - Cultura |
| `company_info.funding_total_usd` | Funding levantado | ❌ Não usando | **Gratuito** | N/A | ⭐⭐ | Para vagas em startups |
| `company_info.annual_revenue` | Faturamento anual | ❌ Não usando | **Gratuito** | N/A | ⭐⭐ | Porte financeiro |

### 3.7 Educação

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `education[]` | Formação acadêmica | ✅ Usando | Gratuito | N/A | ⭐⭐⭐⭐ | Manter |

### 3.8 Contatos

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `has_emails` | Tem email (boolean) | ⚠️ Parcial | **Gratuito** | N/A | ⭐⭐⭐ | Mostrar indicador |
| `has_phone_numbers` | Tem telefone (boolean) | ⚠️ Parcial | **Gratuito** | N/A | ⭐⭐⭐ | Mostrar indicador |
| `emails[]` | Lista de emails | ✅ Usando | +2 créditos | N/A | ⭐⭐⭐⭐⭐ | Sob demanda |
| `best_personal_email` | Melhor email pessoal | ❌ Não usando | +2 créditos | N/A | ⭐⭐⭐⭐ | Implementar |
| `best_business_email` | Melhor email corporativo | ❌ Não usando | +2 créditos | N/A | ⭐⭐⭐⭐ | Implementar |
| `phone_numbers[]` | Lista de telefones | ✅ Usando | +14 créditos | N/A | ⭐⭐⭐⭐ | Sob demanda |
| `phone_types[]` | Tipo do telefone | ❌ Não usando | +14 créditos | N/A | ⭐⭐⭐ | Implementar quando puxar telefone |

### 3.9 Análises de IA e Insights

| Campo | Descrição | Status LIA | Custo Pearch | Custo LIA | Valor | Recomendação |
|-------|-----------|------------|--------------|-----------|-------|--------------|
| `insights.overall_summary` | Resumo IA do candidato | ❌ Não usando | +1 crédito (~$0.03) | **~$0.007** | ⭐⭐⭐⭐⭐ | **USAR LIA** - 4x mais barato |
| `insights.query_insights[]` | Match por requisito | ❌ Não usando | +1 crédito (~$0.03) | **~$0.007** | ⭐⭐⭐⭐⭐ | **USAR LIA** - Mais customizável |
| `match_level` | Nível de match | ❌ Não usando | +1 crédito | **~$0.007** | ⭐⭐⭐⭐ | **USAR LIA** |
| `short_rationale` | Justificativa do match | ❌ Não usando | +1 crédito | **~$0.007** | ⭐⭐⭐⭐ | **USAR LIA** |
| `short_quotes` | Citações comprobatórias | ❌ Não usando | +1 crédito | **~$0.007** | ⭐⭐⭐⭐ | **USAR LIA** |
| `score` (0-4) | Score de relevância | ✅ Usando | +1 crédito | N/A | ⭐⭐⭐⭐⭐ | Manter da Pearch |
| `outreach_message` | Mensagem de abordagem | ❌ Não usando | **Gratuito** | ~$0.01 | ⭐⭐⭐⭐⭐ | **IMPLEMENTAR** - Gratuito! |

---

## 5. Comparação de Custos: LIA vs Pearch para Análises de IA

### 5.1 Custo por Candidato

| Solução | Custo/Candidato | Cálculo |
|---------|-----------------|---------|
| **Pearch Insights** | ~$0.02 - $0.05 | +1 crédito por candidato |
| **LIA (Claude Sonnet)** | ~$0.007 - $0.01 | ~1000 tokens input + ~300 tokens output |

**Resultado: LIA é 3-5x mais barata**

### 4.2 Comparação Detalhada

| Fator | Pearch Insights | LIA (Claude) | Vencedor |
|-------|-----------------|--------------|----------|
| **Custo** | ~$0.03/candidato | ~$0.007/candidato | ✅ LIA |
| **Latência** | Vem junto na busca | +1-3 seg/candidato | ✅ Pearch |
| **Chamadas API** | Nenhuma adicional | +1 por candidato | ✅ Pearch |
| **Qualidade Match** | Focado na query | Análise profunda | ✅ LIA |
| **Personalização** | Padrão da Pearch | 100% customizável | ✅ LIA |
| **Contexto da Vaga** | Só usa a query | Usa toda a JD | ✅ LIA |
| **Big Five/WSI** | Não disponível | Disponível | ✅ LIA |

### 4.3 Cenário de Economia

| Cenário | Pearch Insights | Abordagem Híbrida | Economia |
|---------|-----------------|-------------------|----------|
| 20 candidatos buscados, 5 analisados | $0.60 (20 × $0.03) | $0.035 (5 × $0.007) | **94%** |
| 50 candidatos buscados, 10 analisados | $1.50 (50 × $0.03) | $0.07 (10 × $0.007) | **95%** |

---

## 6. Recomendações de Implementação

### 6.1 Prioridade ALTA (Implementar Imediatamente)

#### 5.1.1 `is_opentowork` - Badge "Aberto a Oportunidades"

**Valor:** Candidatos receptivos a propostas - taxa de resposta muito maior  
**Custo:** Gratuito  
**Implementação:**
- Adicionar badge verde no card do candidato
- Filtro rápido "Apenas abertos a oportunidades"
- Ordenação priorizando candidatos open to work

```jsx
{candidate.is_opentowork && (
  <Badge className="bg-green-100 text-green-700">
    <Briefcase className="w-3 h-3 mr-1" />
    Aberto a oportunidades
  </Badge>
)}
```

#### 5.1.2 `outreach_message` - Mensagem de Abordagem Pronta

**Valor:** Mensagem personalizada gerada pela IA da Pearch  
**Custo:** Gratuito  
**Implementação:**
- Botão "Copiar Mensagem de Abordagem"
- Modal com preview da mensagem
- Integração com sistema de comunicação

#### 5.1.3 Análises de IA via LIA (não Pearch)

**Valor:** Análise profunda e customizada  
**Custo:** ~$0.007/candidato (vs $0.03 Pearch)  
**Benefícios:**
- Considera toda a descrição da vaga
- Gera Nota LIA com critérios específicos
- Análise Big Five e comportamental
- WSI (Work Sample Interview) scoring

### 5.2 Prioridade MÉDIA (Próximo Sprint)

#### 5.2.1 Indicadores de Perfil

| Campo | UI Sugerida |
|-------|-------------|
| `is_decision_maker` | Badge "Líder" ou "Decisor" |
| `is_top_universities` | Badge "Top Universidade" |
| `is_hiring` | Badge "Gerente Contratando" |
| `followers_count` > 1000 | Badge "Influenciador" |

#### 5.2.2 Dados de Empresa

| Campo | UI Sugerida |
|-------|-------------|
| `company_info.is_startup` | Tag "Ex-Startup" ou "Ex-Corporação" |
| `company_info.industries` | Filtro por indústria anterior |
| `company_info.technologies` | Match com stack da vaga |

#### 5.2.3 Idiomas com Proficiência

- Mostrar nível real: "Inglês C1", "Espanhol B2"
- Filtro por nível mínimo de idioma

### 5.3 Prioridade BAIXA (Backlog)

- `estimated_age` - Avaliar implicações LGPD
- `gender` - Para relatórios de D&I apenas
- `annual_revenue` - Para vagas específicas
- `funding_total_usd` - Para vagas em startups

---

## 7. Arquitetura Proposta

### 7.1 Fluxo de Busca Otimizado

```
┌─────────────────────────────────────────────────────────────┐
│                     BUSCA INICIAL                           │
│  Pearch com: insights=false, profile_scoring=true           │
│  Retorna: dados básicos + score + campos gratuitos          │
│  Custo: 6 créditos/candidato (PRO + scoring)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   LISTAGEM DE CANDIDATOS                    │
│  Mostra: nome, cargo, empresa, score, is_opentowork,        │
│          followers, is_decision_maker, has_email/phone      │
└─────────────────────────────────────────────────────────────┘
                              │
                    (usuário clica em candidato)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              ANÁLISE DETALHADA (sob demanda)                │
│  LIA (Claude) analisa: match com vaga, Big Five,            │
│  competências, nota LIA, recomendações                      │
│  Custo: ~$0.007/candidato                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                    (usuário decide contatar)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                DADOS DE CONTATO (sob demanda)               │
│  Pearch com: show_emails=true ou show_phone_numbers=true    │
│  Custo: +2 créditos (email) ou +14 créditos (telefone)      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Comparação de Cenários de Custo

| Cenário | Abordagem Atual | Abordagem Otimizada | Economia |
|---------|-----------------|---------------------|----------|
| 20 buscas, 5 análises, 2 contatos | ~$2.00 | ~$0.80 | 60% |
| 50 buscas, 10 análises, 5 contatos | ~$5.00 | ~$1.70 | 66% |

---

## 8. Checklist de Implementação

### Fase 1: Campos Gratuitos (1-2 sprints)

- [ ] Adicionar `is_opentowork` no card do candidato
- [ ] Implementar `outreach_message` com botão de copiar
- [ ] Adicionar `is_decision_maker` como badge
- [ ] Mostrar `followers_count` como indicador
- [ ] Exibir `is_top_universities` como badge
- [ ] Melhorar exibição de `languages` com proficiência
- [ ] Adicionar `expertise` junto com skills
- [ ] Mostrar `has_emails` e `has_phone_numbers` como indicadores

### Fase 2: Dados de Empresa (1 sprint)

- [ ] Exibir `company_info.industries` no histórico
- [ ] Mostrar `company_info.num_employees` (porte)
- [ ] Adicionar `company_info.technologies` para match de stack
- [ ] Implementar `company_info.is_startup` como filtro

### Fase 3: Análises LIA (já parcialmente implementado)

- [ ] Verificar se análise LIA já cobre todos os campos
- [ ] Garantir que análise considera toda a JD
- [ ] Adicionar análise Big Five no preview
- [ ] Implementar WSI scoring para candidatos

### Fase 4: Otimizações de Backend

- [ ] Configurar busca padrão sem `insights` (economiza crédito)
- [ ] Implementar cache de perfis já buscados
- [ ] Criar endpoint de enriquecimento sob demanda (email/telefone)

---

## 9. Métricas de Sucesso

| Métrica | Atual | Meta |
|---------|-------|------|
| Custo médio por candidato avaliado | ~$0.10 | ~$0.04 |
| Taxa de resposta a abordagens | - | +30% (com is_opentowork) |
| Tempo para primeira abordagem | - | -50% (com outreach_message) |
| Créditos Pearch economizados | - | 40-60% |

---

## 10. Próximos Passos

1. **Aprovar prioridades** - Validar ordem de implementação
2. **Sprint 1** - Implementar campos gratuitos de alto valor
3. **Sprint 2** - Dados de empresa e filtros avançados
4. **Sprint 3** - Otimizações de backend e cache
5. **Monitorar métricas** - Acompanhar economia e conversão

---

## 12. Sistema de Ações em Candidatos - Página de Resultados

**Data de Análise:** Dezembro 2025  
**Status:** Proposta para Avaliação  
**Referências de Mercado:** SeekOut, HireEZ, Gem, Juicebox, LinkedIn Recruiter

### 12.1 Padrões de Mercado Identificados

| Plataforma | Padrão Principal | Destaque |
|------------|------------------|----------|
| **SeekOut** | Multi-select + Floating Action Bar + Projects | Power Filters (40+), Bias Reducer |
| **HireEZ** | Bulk Actions + Drip Campaigns + Temperature Scoring | EZ Agent (IA agêntica), Sourcing Hub 1B+ perfis |
| **Juicebox** | Shortlist → Projects → Export to ATS | Agents 24/7, 41 integrações ATS |
| **LinkedIn Recruiter** | Bulk até 25 candidatos + Templates compartilhados | 13% response rate threshold |
| **Gem** | CRM-style com sequências automatizadas | Foco em relacionamento contínuo |

### 12.2 Arquitetura de Ações Proposta

#### 12.2.1 Floating Action Bar (Ações em Lote)

Quando candidatos são selecionados, aparece uma barra flutuante no rodapé:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ☑ 12 candidatos selecionados                                          │
│                                                                          │
│  [📧 Enviar E-mail]  [📱 Triagem WhatsApp]  [📋 Adicionar à Vaga]      │
│  [⭐ Favoritos]  [🙈 Ocultar]  [🔄 Atualizar Pearch]  [📤 Exportar]    │
│                                                              [✕ Limpar] │
└─────────────────────────────────────────────────────────────────────────┘
```

**Comportamento:**
- Aparece quando 1+ candidatos são selecionados
- Mostra contagem de selecionados
- Ações contextuais baseadas na seleção
- Botão "Limpar" para deselecionar todos

#### 12.2.2 Ações no Preview/Card do Candidato

Menu de 3 pontos (⋮) com ações contextuais:

```
┌─────────────────────────────┐
│  👁 Ver perfil completo     │
│  ─────────────────────────  │
│  📋 Adicionar à vaga...     │
│  📱 Triagem rápida (WhatsApp)│
│  📧 Enviar e-mail...        │
│  📅 Agendar entrevista      │
│  ─────────────────────────  │
│  ⭐ Adicionar aos favoritos │
│  🔄 Atualizar dados (Pearch)│
│  🙈 Ocultar da busca        │
│  ─────────────────────────  │
│  📤 Exportar candidato      │
└─────────────────────────────┘
```

### 12.3 Ações de Triagem Vinculadas a Vagas

| Ação | Comportamento | Custo |
|------|---------------|-------|
| **Triagem sem adicionar** | Dispara screening → Quando responder, adiciona à vaga automaticamente | Gratuito |
| **Triagem + Adicionar** | Adiciona à vaga + Dispara screening imediatamente | Gratuito |
| **Apenas adicionar** | Adiciona à vaga sem disparar comunicação | Gratuito |

**Fluxo de Triagem:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  SELECIONAR VAGA PARA TRIAGEM                                           │
│                                                                          │
│  ▼ Vaga destino                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Desenvolvedor Backend Sênior                                     │    │
│  │ Analista de Dados Pleno                                          │    │
│  │ + Criar nova vaga                                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ○ Disparar triagem agora (adiciona à vaga quando responder)            │
│  ○ Adicionar à vaga + disparar triagem                                   │
│  ○ Apenas adicionar à vaga (sem comunicação)                            │
│                                                                          │
│  [Cancelar]                                      [Confirmar - 12 cand.]  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.4 Ações de Organização

#### 12.4.1 Salvar Busca

| Campo | Descrição |
|-------|-----------|
| **Nome** | Identificador da busca (ex: "Devs Python SP Remoto") |
| **Filtros** | Todos os filtros aplicados salvos |
| **Alertas** | Opção de receber notificação de novos candidatos |
| **Frequência** | Diário, Semanal, ou Manual |

#### 12.4.2 Sistema de Listas de Candidatos

**Conceito:** Coleções personalizadas de candidatos para organização, nurturing e sourcing.

##### Nova Aba no Funil de Talentos

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Busca  │  Favoritos  │  📂 Listas  │  Buscas Salvas  │  Histórico     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↑
                         NOVA ABA
```

##### Visualização da Aba Listas

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📂 MINHAS LISTAS                                        [+ Nova Lista] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 📁 Finalistas Backend Q1                           12 candidatos  │   │
│  │    Criada em 01/12/2025 • Última atualização: há 2 dias          │   │
│  │    [Ver Candidatos]  [📋 Adicionar a Vagas]  [⋮]                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 📁 Pool Tech São Paulo                             45 candidatos  │   │
│  │    Criada em 15/11/2025 • Última atualização: há 1 semana        │   │
│  │    [Ver Candidatos]  [📋 Adicionar a Vagas]  [⋮]                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

##### Pontos de Integração - Adicionar à Lista

| Local | Tipo | Descrição |
|-------|------|-----------|
| **Preview do Candidato** | Individual | Botão/menu "Adicionar à Lista" no card/drawer |
| **Tabela de Candidatos** | Individual | Menu de 3 pontos → "Adicionar à Lista" |
| **Floating Action Bar** | Bulk | Selecionar múltiplos → "Adicionar à Lista" |
| **Resultados de Busca** | Bulk | Após busca, adicionar resultados à lista |

##### Menu no Preview do Candidato

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PREVIEW DO CANDIDATO                                               [×] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Avatar]  João Silva                                                   │
│            Desenvolvedor Backend Sênior                                 │
│            São Paulo, SP • Remoto                                       │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  [📋 Adicionar à Vaga]  [📂 Adicionar à Lista]  [⭐]  [⋮]       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    ↑                                    │
│                          BOTÃO DEDICADO                                 │
│  ...                                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

##### Floating Action Bar - Ação em Lote

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ☑ 12 candidatos selecionados                                          │
│                                                                          │
│  [📂 Add à Lista]  [📋 Add à Vaga]  [📧 E-mail]  [⭐ Favoritos]  [🙈]  │
│         ↑                                                    [✕ Limpar] │
│   AÇÃO EM LOTE                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

##### Modal: Adicionar à Lista

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ADICIONAR À LISTA                                                      │
│                                                                          │
│  3 candidatos selecionados                                              │
│                                                                          │
│  Selecione uma ou mais listas:                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Finalistas Backend Q1                          (12 candidatos) │   │
│  │ ☐ Pool Tech São Paulo                            (45 candidatos) │   │
│  │ ☐ Leads Passivos Remoto                           (8 candidatos) │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ─────── ou ───────                                                     │
│                                                                          │
│  Nome da nova lista: [________________________________]                 │
│                                                                          │
│  [Cancelar]                                      [Adicionar à Lista]    │
└─────────────────────────────────────────────────────────────────────────┘
```

##### Adicionar Lista/Candidatos a Vagas

Da aba Listas, o recrutador pode adicionar:
- **Candidatos individuais** de uma lista a uma ou mais vagas
- **Lista inteira** a uma ou mais vagas (bulk)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ADICIONAR A VAGAS                                                      │
│                                                                          │
│  📂 Lista: Finalistas Backend Q1 (12 candidatos)                        │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  ○ Adicionar TODOS os 12 candidatos                                     │
│  ○ Adicionar apenas selecionados (3 candidatos)                         │
│                                                                          │
│  Selecione uma ou mais vagas:                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ ☐ Desenvolvedor Backend Sênior          (São Paulo • 5 cand.)   │   │
│  │ ☐ Desenvolvedor Backend Pleno           (Remoto • 12 cand.)     │   │
│  │ ☐ Tech Lead Backend                     (São Paulo • 3 cand.)   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Opções de triagem:                                                     │
│  ○ Apenas adicionar (sem comunicação)                                   │
│  ○ Adicionar + disparar triagem WhatsApp                                │
│  ○ Adicionar + disparar e-mail de abordagem                             │
│                                                                          │
│  [Cancelar]                                [Adicionar a 2 Vagas]        │
└─────────────────────────────────────────────────────────────────────────┘
```

##### Visualização de Candidatos na Lista

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Voltar                                                               │
│                                                                          │
│  📁 Finalistas Backend Q1                               12 candidatos   │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  [Buscar na lista...]        [📋 Add a Vagas]  [📤 Exportar]  [⋮]      │
│                                      ↑                                   │
│                          LISTA INTEIRA P/ VAGAS                         │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ ☐ │ João Silva           │ Dev Backend Sr  │ 92 │ 🏠 Local  │ ⋮ │    │
│  │ ☐ │ Maria Santos         │ Dev Backend Pl  │ 88 │ 🌐 Global │ ⋮ │    │
│  │ ☐ │ Pedro Costa          │ Dev Backend Sr  │ 85 │ 🏠 Local  │ ⋮ │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ☑ 3 selecionados                                                       │
│  [📋 Add a Vagas]  [📧 E-mail]  [🔄 Mover p/ Lista]  [🗑 Remover]       │
│         ↑                                                                │
│  SELECIONADOS P/ VAGAS                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

##### Modelo de Dados (Backend)

```python
# Tabela: candidate_lists
class CandidateList(Base):
    __tablename__ = "candidate_lists"
    
    id: str                    # UUID
    company_id: str            # Multi-tenancy
    name: str                  # Nome da lista
    description: Optional[str] # Descrição opcional
    color: Optional[str]       # Cor para identificação visual
    created_by: str            # User ID
    created_at: datetime
    updated_at: datetime
    
# Tabela: candidate_list_members
class CandidateListMember(Base):
    __tablename__ = "candidate_list_members"
    
    id: str
    list_id: str               # FK → candidate_lists
    candidate_id: str          # FK → candidates
    added_by: str              # User ID
    added_at: datetime
    notes: Optional[str]       # Nota sobre o candidato nesta lista
    source: str                # "search", "manual", "import"
```

##### Endpoints API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/lists` | Listar listas do usuário/empresa |
| POST | `/api/v1/lists` | Criar nova lista |
| GET | `/api/v1/lists/{id}` | Detalhes da lista |
| PUT | `/api/v1/lists/{id}` | Atualizar lista |
| DELETE | `/api/v1/lists/{id}` | Excluir lista |
| GET | `/api/v1/lists/{id}/candidates` | Candidatos da lista |
| POST | `/api/v1/lists/{id}/candidates` | Adicionar candidatos (bulk) |
| DELETE | `/api/v1/lists/{id}/candidates` | Remover candidatos (bulk) |
| POST | `/api/v1/lists/{id}/add-to-vacancies` | Adicionar lista a vagas |

##### MVP - Escopo Mínimo

| # | Funcionalidade | Prioridade | Esforço |
|---|----------------|------------|---------|
| 1 | Nova aba "Listas" no Funil de Talentos | P0 | Médio |
| 2 | CRUD de listas (criar, renomear, excluir) | P0 | Baixo |
| 3 | Botão "Add à Lista" no preview do candidato | P0 | Baixo |
| 4 | Ação bulk "Add à Lista" na Floating Action Bar | P0 | Médio |
| 5 | Visualizar candidatos de uma lista | P0 | Médio |
| 6 | Remover candidatos de uma lista | P0 | Baixo |
| 7 | Adicionar candidatos da lista a vagas (individual) | P0 | Médio |
| 8 | Adicionar lista inteira a vagas (bulk) | P0 | Médio |
| 9 | Mover candidatos entre listas | P1 | Baixo |
| 10 | Duplicar lista | P1 | Baixo |

##### Futuro - Automações com LIA

| Evolução | Descrição |
|----------|-----------|
| **Pipeline ativo** | Lista → Pipeline com etapas (Lead → Contato → Triagem → Entrevista) |
| **Triagem automática** | LIA dispara screening para candidatos da lista |
| **Atualização Pearch** | Atualizar dados de todos os candidatos da lista |
| **Alertas inteligentes** | Notificar quando candidatos mudam status (`is_opentowork`) |
| **Scoring contínuo** | Re-avaliar candidatos quando novas vagas são criadas |
| **Nutrição automática** | Sequências de e-mail para manter relacionamento |

##### Componentes Frontend

| Componente | Arquivo Sugerido | Função |
|------------|------------------|--------|
| `ListsTab` | `talent-funnel-tabs/lists-tab.tsx` | Nova aba de listas |
| `ListCard` | `ui/list-card.tsx` | Card de lista na aba |
| `ListDetailView` | `lists/list-detail-view.tsx` | Visualização de candidatos |
| `AddToListModal` | `modals/add-to-list-modal.tsx` | Modal para adicionar à lista |
| `AddListToVacanciesModal` | `modals/add-list-to-vacancies-modal.tsx` | Modal para adicionar a vagas |
| `CreateListModal` | `modals/create-list-modal.tsx` | Modal de criação de lista |

#### 12.4.3 Ocultar Candidatos

- Remove da visualização atual
- Acessível em "Candidatos Ocultos" para reverter
- Útil para limpar resultados já avaliados
- Não afeta outros recrutadores (pessoal)

### 12.5 Integração Pearch - Ações

#### 12.5.1 Atualizar Dados

| Ação | Custo | Descrição |
|------|-------|-----------|
| **Atualizar perfil único** | 1 crédito | Re-sincroniza com dados mais recentes do Pearch |
| **Atualizar em lote** | 1 crédito/candidato | Atualiza múltiplos perfis selecionados |

**Dados atualizados:**
- Cargo atual e empresa
- Skills e experiências
- Contatos (se `show_emails`/`show_phone_numbers` ativos)
- `is_opentowork` status

#### 12.5.2 Enriquecimento em Lote

Para candidatos LOCAIS sem dados Pearch:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ENRIQUECER COM PEARCH                                                  │
│                                                                          │
│  8 candidatos selecionados da base local                                │
│                                                                          │
│  Custo estimado: 8 créditos (1/candidato)                               │
│  Saldo atual: 450 créditos                                              │
│                                                                          │
│  Dados que serão buscados:                                              │
│  ☑ Cargo atual e empresa                                                │
│  ☑ Skills e experiências                                                │
│  ☑ is_opentowork status                                                 │
│  ☐ E-mails (+2 créditos cada) ← toggle                                  │
│  ☐ Telefones (+14 créditos cada) ← toggle                               │
│                                                                          │
│  [Cancelar]                                      [Confirmar Enriquecimento]│
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.6 Sistema de Comunicação

#### 12.6.1 E-mail

| Funcionalidade | Descrição |
|----------------|-----------|
| **Templates** | Biblioteca de templates pré-definidos (editáveis) |
| **Variáveis** | `{{nome}}`, `{{vaga}}`, `{{empresa}}`, `{{recrutador}}` |
| **Agendamento** | Escolher data/hora de envio |
| **Sequências** | Follow-up automático (3, 7, 14 dias) |
| **Tracking** | Abertura, cliques, respostas |

#### 12.6.2 Triagem WhatsApp (OpenMic.ai)

| Funcionalidade | Descrição |
|----------------|-----------|
| **Perguntas por vaga** | Configuráveis no wizard de criação |
| **Score automático** | LIA analisa respostas |
| **Gravação de áudio** | Opcional para perguntas específicas |
| **Transcrição** | Gemini converte áudio → texto |

### 12.7 Agendamento

#### 12.7.1 Agendar Entrevista

Integração com calendários:

| Integração | Status | Funcionalidade |
|------------|--------|----------------|
| **Google Calendar** | Planejado | Sincronização de disponibilidade |
| **Microsoft Outlook** | Planejado | Slots do gestor |
| **Calendly** | Planejado | Link de agendamento |

**Fluxo:**
1. Recrutador seleciona candidato(s)
2. Escolhe gestor/entrevistador
3. Sistema mostra slots disponíveis
4. Candidato recebe link para escolher horário
5. Confirmação automática para ambos

### 12.8 UX - Padrão ElevenLabs

#### 12.8.1 Hierarquia Visual de Ações

| Tipo | Estilo | Uso | Exemplo |
|------|--------|-----|---------|
| **Primária** | Botão sólido cyan (#60BED1) | Ação principal | "Adicionar à Vaga" |
| **Secundária** | Botão outline | Ações frequentes | "Enviar E-mail" |
| **Terciária** | Dropdown/Menu | Ações menos frequentes | Menu de 3 pontos |
| **Destrutiva** | Texto vermelho | Ações irreversíveis | "Ocultar", "Remover" |

#### 12.8.2 Feedback Visual

| Tipo | Implementação |
|------|---------------|
| **Toast** | Confirmação: "12 candidatos adicionados à vaga X" |
| **Loading** | Spinner durante ações em lote |
| **Undo** | "Desfazer" por 5 segundos para ações reversíveis |
| **Progress** | Barra de progresso para ações longas |

### 12.9 Priorização de Implementação

#### Fase 1 - Essencial (MVP)

| # | Funcionalidade | Esforço | Impacto |
|---|----------------|---------|---------|
| 1 | Floating Action Bar (seleção múltipla) | Médio | Alto |
| 2 | Adicionar à vaga (com/sem triagem) | Médio | Alto |
| 3 | Favoritos | Baixo | Médio |
| 4 | Ocultar candidato | Baixo | Médio |

#### Fase 2 - Comunicação

| # | Funcionalidade | Esforço | Impacto |
|---|----------------|---------|---------|
| 5 | Disparar e-mail (individual/lote) | Alto | Alto |
| 6 | Triagem WhatsApp vinculada à vaga | Alto | Alto |
| 7 | Templates de e-mail | Médio | Médio |

#### Fase 3 - Organização

| # | Funcionalidade | Esforço | Impacto |
|---|----------------|---------|---------|
| 8 | Salvar busca | Baixo | Médio |
| 9 | Criar projetos/listas | Médio | Médio |
| 10 | Atualizar dados Pearch | Baixo | Médio |

#### Fase 4 - Avançado

| # | Funcionalidade | Esforço | Impacto |
|---|----------------|---------|---------|
| 11 | Agendar entrevista | Alto | Alto |
| 12 | Sequências de e-mail (drip) | Alto | Médio |
| 13 | Exportar candidatos | Baixo | Baixo |

### 12.10 Componentes a Criar

| Componente | Localização Sugerida | Função |
|------------|---------------------|--------|
| `FloatingActionBar` | `components/ui/floating-action-bar.tsx` | Barra de ações em lote |
| `CandidateActionsMenu` | `components/candidate-actions-menu.tsx` | Menu dropdown de ações |
| `AddToVacancyModal` | `components/modals/add-to-vacancy-modal.tsx` | Modal de seleção de vaga |
| `ScreeningOptionsModal` | `components/modals/screening-options-modal.tsx` | Opções de triagem |
| `SaveSearchModal` | `components/modals/save-search-modal.tsx` | Salvar busca |
| `ProjectsManager` | `components/projects-manager.tsx` | Gerenciar projetos/listas |
| `BulkEmailModal` | `components/modals/bulk-email-modal.tsx` | Envio de e-mail em lote |
| `PearchUpdateModal` | `components/modals/pearch-update-modal.tsx` | Atualizar/enriquecer dados |

---

## 13. Referências

- [Pearch AI API Documentation](https://apidocs.pearch.ai/reference/post_v2-search)
- [Pearch AI Pricing](https://pearch.ai/pricing)
- [Anthropic Claude Pricing](https://www.anthropic.com/claude/sonnet)
- [SeekOut Platform](https://www.seekout.com/)
- [HireEZ Platform](https://hireez.com/)
- [Juicebox Documentation](https://docs.juicebox.work/)
- [LinkedIn Recruiter Bulk Actions](https://www.linkedin.com/help/recruiter/answer/a417213)
- Modelo de dados: `lia-agent-system/app/models/pearch.py`
- Serviço Pearch: `lia-agent-system/app/services/pearch_service.py`
