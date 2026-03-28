# Features Implementadas - Plataforma LIA

## Módulos Principais

### 1. Autenticação
- Login/Logout
- Gestão de sessão
- Perfis de usuário

### 2. Gestão de Vagas

#### Sistema de Status (12 estados)
1. **Ativa** - Vaga aberta para candidaturas
2. **Aprovada** - Aguardando publicação
3. **Aguardando aprovação** - Em revisão
4. **Reaberta** - Vaga reativada
5. **Paralisada** - Temporariamente pausada
6. **Interna** - Apenas funcionários
7. **Rascunho** - Em construção
8. **Fechada (preenchida)** - Posição preenchida
9. **Fechada (expirada)** - Prazo encerrado
10. **Cancelada** - Vaga cancelada
11. **Concluída** - Processo finalizado
12. **Arquivada** - Histórico

#### Funcionalidades
- **Filtros Avançados**: Status, dias abertos, departamento
- **Busca Global**: Multi-campo (ID, título, localização, etc.)
- **Ações em Lote**: Seleção múltipla de vagas
- **Pin de Vagas**: Fixar vagas prioritárias
- **Vagas Confidenciais**: Ícone de cadeado laranja (16px, stroke-2.5)
- **Preview de Vaga**: Modal com tabs (Overview, Script, Pipeline, LIA Metrics)
- **Pipeline Kanban**: Visualização de fluxo de candidatos

#### Dados da Vaga
```typescript
interface Job {
  id: number
  jobId: string
  title: string
  department: string
  location: string
  type: 'Tempo Integral' | 'Meio Período' | 'Contrato' | 'Freelance'
  status: JobStatus
  openDate: string
  salary: string
  applicants: number
  interviews: number
  offers: number
  isConfidential?: boolean
  isPinned?: boolean
  recruiterName: string
  recruiterEmail: string
  hiringManager: string
  nps: number
  // ... outros campos
}
```

### 3. Gestão de Candidatos

#### Status do Candidato
- Novo
- Triagem
- Entrevista
- Oferta
- Contratado
- Rejeitado

#### Funcionalidades
- **Perfil Completo**: Dados pessoais, experiência, educação
- **Testes**: English Test, Big Five Personality
- **Scoring LIA**: "Nota LIA Geral" com IA
- **Timeline**: Histórico de interações
- **Documentos**: Upload e gestão de arquivos
- **Comparação**: Side-by-side de candidatos

### 4. LIA Assistant (IA Integrada)

#### Sidebar Modal Customizável
- **Posição**: Lateral direita
- **Modos**: Colapsada / Expandida
- **Contexto**: Sugestões baseadas na página atual
- **Quick Actions**: Ações rápidas contextuais

#### Automação LIA (Brain Icon #60BED1)
- Screening automático
- Análise de compatibilidade
- Sugestões de perguntas
- Predições de sucesso
- Insights de pipeline

### 5. Testes e Avaliações

#### English Test
- Níveis: A1, A2, B1, B2, C1, C2
- Avaliação automatizada
- Scoring detalhado

#### Big Five Personality Test
- **Traços**: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- **Visualização**: Radar chart
- **Interpretação**: Insights LIA

### 6. Dashboards e Indicadores

#### Categorias Estratégicas (7 dashboards)

##### 1. Estratégicos
- Métricas C-level
- ROI de recrutamento
- Performance geral

##### 2. Previsões & IA
- Predições de contratação
- Análise preditiva
- Tendências futuras

##### 3. People Analytics
**Tabs integrados:**
- **Big Five Analytics**: Análise de personalidade da equipe
- **Diversidade & Inclusão**: Métricas de D&I
- **NPS (eNPS)**: Employee Net Promoter Score

##### 4. Modelos de Trabalho
- Remote vs Presencial vs Híbrido
- Distribuição geográfica
- Preferências de trabalho

##### 5. Funil & Performance
- Conversão por etapa
- Time to hire
- Taxa de aprovação

##### 6. War Room Operacional
- Métricas em tempo real
- Vagas críticas
- Alertas urgentes

##### 7. Análise de Competências
- Skills mais demandadas
- Gap analysis
- Treinamentos necessários

#### Layout Ultra-Compacto
- **Sidebar Menu**: w-64 expandida, w-16 colapsada (hover-activated)
- **Auto-expand**: On hover
- **Lock/Unlock**: Opcional
- **Typography**: 
  - Labels: `text-[11px]`
  - Descriptions: `text-[10px]`
  - Badges: `text-[9px] tracking-tight`

### 7. Configurações e Administração

#### Seções Principais
1. **Dados da Empresa**
   - Informações básicas
   - Endereços
   - Contatos

2. **Estrutura Organizacional**
   - Departamentos
   - Cargos
   - Hierarquias

3. **Pessoas**
   - Usuários
   - Permissões
   - Times

4. **Integrações**
   - APIs externas
   - Webhooks
   - SSO

5. **Configurações de Sistema**
   - Preferências gerais
   - Notificações
   - Segurança

#### Menu Administrativo
- **Typography**: Open Sans
  - Títulos: `text-[10px]`
  - Descrições: `text-[8px]`
  - Subsections: `text-[9px]`
- **Status Badges**: Configurado, Pendente, Não configurado

### 8. Sistema de Notificações

#### Tipos
- Novos candidatos
- Mudanças de status
- Entrevistas agendadas
- Ofertas pendentes
- Alertas de prazo

#### Canal
- In-app notifications
- Email (configurável)
- Badge counter no sidebar

### 9. Relatórios e Exports

#### Formatos Suportados
- PDF
- Excel/CSV
- JSON

#### Relatórios Disponíveis
- Performance por recrutador
- Análise de pipeline
- Métricas de diversidade
- Relatório de tempo de contratação

## Features Técnicas

### Cache Control
```tsx
<meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
```

### Image Optimization
- Remote patterns configurados
- Lazy loading habilitado
- Avatar fallbacks

### State Management
- React hooks (useState, useEffect)
- Local state por componente
- Context API para dados globais (quando necessário)

### Error Handling
- Try-catch em operações críticas
- Fallback UI para erros
- Loading states

## Convenções de Desenvolvimento

### Organização de Código
```typescript
// 1. Imports
import React from 'react'
import { Button } from '@/components/ui/button'

// 2. Interfaces/Types
interface Props {
  // ...
}

// 3. Component
export default function Component({ props }: Props) {
  // 4. State
  const [state, setState] = useState()
  
  // 5. Effects
  useEffect(() => {}, [])
  
  // 6. Handlers
  const handleClick = () => {}
  
  // 7. Render helpers
  const renderItem = () => {}
  
  // 8. Return
  return (
    // JSX
  )
}
```

### Naming Conventions
- **Componentes**: PascalCase (`CandidateCard`)
- **Funções**: camelCase (`handleSubmit`)
- **Constantes**: UPPER_SNAKE_CASE (`MAX_CANDIDATES`)
- **Interfaces**: PascalCase com I prefix opcional (`IUser` ou `User`)
- **Types**: PascalCase (`JobStatus`)

### Comentários
```typescript
// Comentários em português
// Explicar "por quê", não "o quê"
// Documentar edge cases e decisões técnicas
```
