# Plano de Ajustes UX - Concentração da Interação com LIA

**Data**: Dezembro 2025  
**Versão**: 1.0  
**Objetivo**: Simplificar a arquitetura de interação recrutador-LIA, removendo redundâncias e concentrando a experiência nos prompts expandidos das telas de gestão

---

## 📋 RESUMO EXECUTIVO

### Problema Atual
- Menu possui item "Chat com a LIA" separado (redundante)
- Indicadores e Biblioteca ficam na área operacional (deveria ser Admin)
- Múltiplos pontos de entrada para conversar com LIA (confuso)
- Jornada de criação de vaga não aproveita dados do setup da empresa

### Solução Proposta
1. **Remover "Chat com a LIA"** do menu lateral
2. **Mover "Indicadores" e "Biblioteca"** para área Admin
3. **Concentrar interação com LIA** nos prompts expandidos das telas:
   - Gestão de Vagas (jobs-page)
   - Página da Vaga (job-detail)
   - Funil de Talentos (candidates-page)
4. **Nova jornada de criação de vaga** com painéis laterais interativos

---

## 🎯 MUDANÇAS NO MENU/SIDEBAR

### Estado Atual
```
📊 Dashboard
👥 Funil de Talentos
💼 Gestão de Vagas
🧠 Chat com a LIA        ← REMOVER
📈 Indicadores           ← MOVER PARA ADMIN
📚 Biblioteca            ← MOVER PARA ADMIN
⚙️ Configurações
```

### Estado Futuro
```
📊 Dashboard
👥 Funil de Talentos
💼 Gestão de Vagas
⚙️ Configurações
   └─ Admin
      ├─ Empresa & Equipe
      ├─ Recrutamento
      ├─ Comunicação
      ├─ Metas & Planejamento
      ├─ 📈 Indicadores      ← MOVIDO
      └─ 📚 Biblioteca       ← MOVIDO
```

### Tarefas
- [ ] **1.1** Remover item "Chat com a LIA" do sidebar.tsx
- [ ] **1.2** Mover "Indicadores" para dentro de Admin/Configurações
- [ ] **1.3** Mover "Biblioteca" para dentro de Admin/Configurações
- [ ] **1.4** Ajustar navegação e rotas correspondentes

---

## 🧠 CONCENTRAÇÃO DA INTERAÇÃO COM LIA

### Filosofia
O recrutador interage com a LIA **exclusivamente** através dos **prompts expandidos** presentes nas telas de trabalho:

| Tela | Prompt Expandido | Função Principal |
|------|------------------|------------------|
| **Gestão de Vagas** | ✅ Já implementado | Criar vagas, buscar vagas, análises |
| **Página da Vaga** | ⏳ Implementar | Editar vaga, buscar candidatos, análises da vaga |
| **Funil de Talentos** | ✅ Já implementado | Buscar candidatos, análises, triagem |

### Tarefas
- [ ] **2.1** Garantir que o prompt expandido de Gestão de Vagas cubra todos os casos de uso do antigo "Chat com a LIA"
- [ ] **2.2** Implementar prompt expandido na Página da Vaga (job-detail)
- [ ] **2.3** Revisar prompt expandido do Funil de Talentos para completude
- [ ] **2.4** Remover página/componente separado de chat com LIA

---

## 🚀 NOVA JORNADA DE CRIAÇÃO DE VAGA

### Conceito
Jornada conversacional que usa **painéis laterais interativos** para coletar informações estruturadas, aproveitando ao máximo os dados já configurados no setup da empresa.

### Fluxo Visual

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JORNADA DE CRIAÇÃO DE VAGA                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ETAPA 1: Descrição Inicial + Extração                              │
│  ┌─────────────────────┬───────────────────────────────────────┐   │
│  │     CHAT (50%)      │      CRITÉRIOS DETECTADOS (50%)       │   │
│  │                     │                                       │   │
│  │ "Detalhe o máximo   │  🔍 Detectando critérios...           │   │
│  │  que puder sobre a  │  ○ Cargo                              │   │
│  │  vaga para otimizar │  ○ Gestor/Área                        │   │
│  │  o processo de      │  ○ Competências técnicas              │   │
│  │  construção.        │  ○ Competências comportamentais       │   │
│  │                     │  ○ Senioridade/Idiomas                │   │
│  │  Vou aproveitar ao  │  ○ Modelo de trabalho                 │   │
│  │  máximo as          │                                       │   │
│  │  informações que já │                                       │   │
│  │  tenho da sua       │                                       │   │
│  │  empresa!"          │                                       │   │
│  │                     │                                       │   │
│  │ [📎 Anexar JD]      │                                       │   │
│  │ [📋 Usar anterior]  │                                       │   │
│  │ [_______________]   │                                       │   │
│  └─────────────────────┴───────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ETAPA 2: Informações Básicas + Gestores                            │
│  ┌─────────────────────┬───────────────────────────────────────┐   │
│  │     CHAT (50%)      │      PAINEL COM CAMPOS (50%)          │   │
│  │                     │                                       │   │
│  │ "Preenchi com base  │  📋 INFORMAÇÕES BÁSICAS               │   │
│  │  na sua descrição   │  ┌─────────────────────────────────┐ │   │
│  │  e no setup da      │  │ Título: [Desenvolvedor Backend] │ │   │
│  │  empresa. Confirme  │  │ Área: [Engenharia ▼]            │ │   │
│  │  ou ajuste!"        │  │ Gestor: [João Silva ▼]          │ │   │
│  │                     │  │ Vagas: [1]                      │ │   │
│  │                     │  │ Modelo: [● Remoto ○ Híbrido]    │ │   │
│  │                     │  │ Localização: [São Paulo]        │ │   │
│  │                     │  └─────────────────────────────────┘ │   │
│  │                     │                                       │   │
│  │                     │  [✓ Confirmar e Continuar]            │   │
│  └─────────────────────┴───────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ETAPA 3: Remuneração e Benefícios                                  │
│  ┌─────────────────────┬───────────────────────────────────────┐   │
│  │     CHAT (50%)      │      PAINEL REMUNERAÇÃO (50%)         │   │
│  │                     │                                       │   │
│  │ "Agora vamos para   │  💰 REMUNERAÇÃO E BENEFÍCIOS          │   │
│  │  a remuneração.     │  ┌─────────────────────────────────┐ │   │
│  │  Preenchi os        │  │ Faixa Salarial *                │ │   │
│  │  benefícios padrão  │  │ R$ De: [12.000] Até: [18.000]   │ │   │
│  │  da empresa!"       │  │                                 │ │   │
│  │                     │  │ Bônus Anual                     │ │   │
│  │                     │  │ R$ De: [10.000] Até: [20.000]   │ │   │
│  │                     │  │                                 │ │   │
│  │                     │  │ Benefícios *                    │ │   │
│  │                     │  │ ☑ Vale Refeição (R$ 30/dia)    │ │   │
│  │                     │  │ ☑ Plano de Saúde               │ │   │
│  │                     │  │ ☑ Auxílio Home Office          │ │   │
│  │                     │  └─────────────────────────────────┘ │   │
│  │                     │                                       │   │
│  │                     │  [✓ Concluído]                        │   │
│  └─────────────────────┴───────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ETAPA 4: Competências Técnicas                                     │
│  ETAPA 5: Competências Comportamentais                              │
│  ETAPA 6: Requisitos Adicionais (Idiomas, Formação)                 │
│  ETAPA 7: Scorecard e Critérios de Avaliação                        │
│  ETAPA 8: Revisão Final e Publicação                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Princípios dos Painéis Laterais
1. **Chat à esquerda (50%)** - LIA orienta e contextualiza
2. **Painel à direita (50%)** - Formulário estruturado para preenchimento rápido
3. **Pré-preenchimento** - LIA usa dados do setup da empresa para pré-preencher campos
4. **Botão "Concluído"** - Fecha o painel e volta ao chat
5. **Extração automática** - LIA detecta critérios do texto/JD em tempo real

### Tarefas
- [ ] **3.1** Criar componente `JobCreationWizard` com layout 50/50
- [ ] **3.2** Implementar ETAPA 1: Descrição Inicial + Extração de Critérios
- [ ] **3.3** Implementar ETAPA 2: Informações Básicas (com pré-preenchimento)
- [ ] **3.4** Implementar ETAPA 3: Remuneração e Benefícios
- [ ] **3.5** Implementar ETAPA 4: Competências Técnicas
- [ ] **3.6** Implementar ETAPA 5: Competências Comportamentais
- [ ] **3.7** Implementar ETAPA 6: Requisitos Adicionais
- [ ] **3.8** Implementar ETAPA 7: Scorecard
- [ ] **3.9** Implementar ETAPA 8: Revisão Final
- [ ] **3.10** Integrar wizard ao botão "Nova Vaga" da Gestão de Vagas

---

## 📊 AJUSTES NA TELA DE FUNIL DE TALENTOS

### Melhorias Planejadas
1. **Prompt Expandido Completo** - Garantir todas as funcionalidades de busca e análise
2. **Integração com Vagas** - Facilitar associação de candidatos a vagas
3. **Quick Actions Contextuais** - Ações rápidas baseadas no contexto

### Tarefas
- [ ] **4.1** Revisar e completar funcionalidades do prompt expandido
- [ ] **4.2** Adicionar quick actions para associar candidato a vaga
- [ ] **4.3** Melhorar feedback visual de ações da LIA

---

## 📄 APROVEITANDO O QUE JÁ CONSTRUÍMOS

### Componentes Existentes a Reutilizar

| Componente | Localização | Uso na Nova Jornada |
|------------|-------------|---------------------|
| `LiaQueriesGuide` | `ui/lia-queries-guide.tsx` | Sugestões de queries |
| `PromptSuggestionsPopover` | `ui/prompt-suggestions-popover.tsx` | Sugestões contextuais |
| `ExpandableAIPrompt` | `ui/expandable-ai-prompt.tsx` | Base do chat lateral |
| `ContextPill` | `jobs-page.tsx` | Contexto visual |
| `QuickActionChips` | `jobs-page.tsx` | Ações rápidas |

### Tabs Já Implementadas no Drawer da LIA

| Tab | Status | Aproveitamento |
|-----|--------|----------------|
| **IA Natural** | ✅ Funcional | Manter como entrada conversacional |
| **Job Description** | ✅ Reformulado | Usar para criar vaga a partir de JD |
| **Templates** | ✅ Reformulado | 3 seções: templates, vagas existentes, salvar |

---

## 📅 CRONOGRAMA SUGERIDO

### Fase 1: Limpeza do Menu (1-2 dias)
- Remover "Chat com a LIA"
- Mover Indicadores e Biblioteca para Admin

### Fase 2: Prompt Expandido da Página da Vaga (2-3 dias)
- Implementar drawer da LIA na página de detalhe da vaga
- Ações: editar vaga, buscar candidatos, análises

### Fase 3: Nova Jornada de Criação de Vaga (5-7 dias)
- Componente wizard com layout 50/50
- Painéis laterais interativos
- Integração com dados do setup da empresa
- 8 etapas completas

### Fase 4: Refinamentos do Funil de Talentos (2-3 dias)
- Quick actions contextuais
- Melhorias de UX

---

## ✅ CHECKLIST GERAL

### Menu/Navegação
- [ ] Remover "Chat com a LIA" do menu
- [ ] Mover "Indicadores" para Admin
- [ ] Mover "Biblioteca" para Admin

### Prompts Expandidos
- [ ] Gestão de Vagas - Revisar completude
- [ ] Página da Vaga - Implementar drawer LIA
- [ ] Funil de Talentos - Revisar completude

### Nova Jornada de Criação
- [ ] Wizard 50/50 (chat + painéis)
- [ ] 8 etapas implementadas
- [ ] Pré-preenchimento com dados da empresa
- [ ] Extração automática de critérios

### Documentação
- [ ] Atualizar replit.md com novas decisões
- [ ] Documentar componentes criados

---

*Documento criado em Dezembro 2025 - Plano de Ajustes UX LIA*
