# Guia de Desenvolvimento - Plataforma LIA

## Setup Inicial

### Pré-requisitos
- Node.js 20+
- npm ou yarn
- Editor com TypeScript support (VS Code recomendado)

### Instalação

```bash
cd plataforma-lia
npm install
```

### Executar em Desenvolvimento

```bash
npm run dev
```

Servidor rodará em: `http://localhost:5000`

### Build para Produção

```bash
npm run build
```

Saída estática em: `out/`

## Estrutura de Arquivos

### Adicionar Nova Página

1. **Criar componente em `src/components/pages/`**

```typescript
// src/components/pages/nova-feature-page.tsx
'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function NovaFeaturePage() {
  const [data, setData] = useState([])
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Nova Feature</h1>
      {/* Conteúdo */}
    </div>
  )
}
```

2. **Adicionar rota no sidebar**

```typescript
// src/components/sidebar.tsx
const menuItems = [
  // ... itens existentes
  {
    icon: IconName,
    label: 'Nova Feature',
    count: 0,
    action: () => setCurrentPage('nova-feature')
  }
]
```

3. **Adicionar switch case na página principal**

```typescript
// src/app/page.tsx
{currentPage === 'nova-feature' && <NovaFeaturePage />}
```

### Adicionar Novo Dashboard

1. **Criar componente do dashboard**

```typescript
// src/components/pages/dashboards/novo-dashboard.tsx
export default function NovoDashboard() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar collapsible */}
      <DashboardSidebar />
      
      {/* Main content */}
      <main className="flex-1 overflow-auto px-3 pt-3 pb-6 bg-gray-50 dark:bg-gray-900">
        <div className="grid grid-cols-2 gap-2.5">
          {/* Cards ultra-compactos */}
        </div>
      </main>
    </div>
  )
}
```

2. **Adicionar ao dashboards-page.tsx**

```typescript
const dashboardCategories = [
  // ... categorias existentes
  {
    id: 'novo-dashboard',
    name: 'Novo Dashboard',
    icon: IconName,
    color: 'wedo-cyan',
    description: 'Descrição breve'
  }
]
```

## Padrões de UI

### Cards Ultra-Compactos

```tsx
<Card className="bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800">
  <CardHeader className="p-3">
    <CardTitle className="text-[12px] font-medium flex items-center gap-2">
      <Icon className="w-4 h-4 text-wedo-cyan" />
      Título do Card
    </CardTitle>
  </CardHeader>
  <CardContent className="p-3 space-y-2">
    {/* Conteúdo compacto */}
  </CardContent>
</Card>
```

### KPI Display

```tsx
<div className="space-y-1">
  <div className="text-[9px] text-gray-500 dark:text-gray-400 tracking-tight">
    Label da Métrica
  </div>
  <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
    1.234
  </div>
  <div className="text-[9px] text-green-600 dark:text-green-400">
    ↑ 12% vs mês anterior
  </div>
</div>
```

### Badges Numéricos

```tsx
<Badge className="text-[9px] tracking-tight bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
  24 vagas
</Badge>
```

### Ícones LIA

```tsx
import { Brain } from 'lucide-react'

<Button variant="outline" className="gap-2">
  <Brain className="w-4 h-4 text-wedo-cyan" />
  Analisar com LIA
</Button>
```

### Sidebar Collapsible (Dashboard)

```tsx
const [isCollapsed, setIsCollapsed] = useState(true)
const [isLocked, setIsLocked] = useState(false)

<aside 
  className={`
    ${isCollapsed && !isLocked ? 'w-16' : 'w-64'}
    transition-all duration-200
    bg-white dark:bg-gray-950
    border-r border-gray-200 dark:border-gray-800
  `}
  onMouseEnter={() => !isLocked && setIsCollapsed(false)}
  onMouseLeave={() => !isLocked && setIsCollapsed(true)}
>
  {/* Menu items */}
</aside>
```

## Helpers e Utilities

### Função de Cores de Status

```typescript
const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    'Ativa': '#A8D5B7',
    'Aprovada': '#B8E6B8',
    // ... outros status
  }
  return colors[status] || '#E5E7EB'
}

// Uso
<div 
  className="px-2 py-1 rounded text-xs"
  style={{ backgroundColor: getStatusColor(job.status) }}
>
  {job.status}
</div>
```

### Formatação de Dados

```typescript
// Datas
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('pt-BR')
}

// Números
const formatNumber = (num: number): string => {
  return num.toLocaleString('pt-BR')
}

// Moeda
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}
```

### Cálculo de Dias

```typescript
const getDaysOpen = (openDate: string): number => {
  const now = new Date().getTime()
  const open = new Date(openDate).getTime()
  return Math.floor((now - open) / (1000 * 60 * 60 * 24))
}
```

## Boas Práticas

### Performance

1. **Use React.memo para componentes pesados**
```typescript
const HeavyComponent = React.memo(({ data }) => {
  // Renderização pesada
})
```

2. **Evite re-renders desnecessários**
```typescript
// ❌ Ruim - cria nova função a cada render
<button onClick={() => handleClick(id)}>Click</button>

// ✅ Bom - função estável
const handleButtonClick = useCallback(() => {
  handleClick(id)
}, [id])

<button onClick={handleButtonClick}>Click</button>
```

3. **Lazy load componentes grandes**
```typescript
const BigComponent = lazy(() => import('./BigComponent'))
```

### Acessibilidade

1. **Use semantic HTML**
```tsx
<nav aria-label="Menu principal">
  <ul role="list">
    <li><a href="#home">Home</a></li>
  </ul>
</nav>
```

2. **Labels em ícones**
```tsx
<button aria-label="Fechar modal">
  <X className="w-4 h-4" />
</button>
```

3. **Focus management**
```tsx
<input 
  className="focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
  aria-describedby="input-help"
/>
```

### TypeScript

1. **Defina interfaces para props**
```typescript
interface ButtonProps {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary'
  disabled?: boolean
}

export function Button({ label, onClick, variant = 'primary', disabled }: ButtonProps) {
  // ...
}
```

2. **Use enums para constantes**
```typescript
enum JobStatus {
  Active = 'Ativa',
  Paused = 'Paralisada',
  Closed = 'Concluída'
}
```

3. **Evite `any`**
```typescript
// ❌ Ruim
const handleData = (data: any) => {}

// ✅ Bom
const handleData = (data: unknown) => {
  if (isValidData(data)) {
    // Type guard
  }
}
```

## Debugging

### Console Logs

```typescript
// Development only
if (process.env.NODE_ENV === 'development') {
  console.log('Debug info:', data)
}
```

### React DevTools
- Instalar extensão do navegador
- Inspecionar componentes e state
- Profiling de performance

### TypeScript Errors
```bash
# Check de tipos sem build
npx tsc --noEmit
```

## Testes

### Estrutura de Teste (Futura Implementação)

```typescript
import { render, screen } from '@testing-library/react'
import { JobCard } from './job-card'

describe('JobCard', () => {
  it('renders job title', () => {
    const job = { title: 'Dev Frontend' }
    render(<JobCard job={job} />)
    expect(screen.getByText('Dev Frontend')).toBeInTheDocument()
  })
})
```

## Git Workflow

### Commits
```bash
# Mensagens em português, descritivas
git commit -m "Adiciona filtro de status em vagas"
git commit -m "Corrige bug na paginação de candidatos"
git commit -m "Otimiza performance do dashboard Big Five"
```

### Branches (Sugestão)
```bash
main          # Produção
develop       # Desenvolvimento
feature/xyz   # Novas features
fix/xyz       # Bug fixes
```

## Troubleshooting

### Build Errors

**Erro**: `Module not found: Can't resolve '@/components/...'`
**Solução**: Verificar `tsconfig.json` paths configuration

**Erro**: `Image optimization not available in static export`
**Solução**: Usar `unoptimized: true` em next.config.js

### Runtime Errors

**Erro**: `Hydration failed`
**Solução**: Garantir que SSR e Client render sejam idênticos, usar `suppressHydrationWarning` se necessário

**Erro**: `Maximum update depth exceeded`
**Solução**: Verificar useEffect dependencies e evitar setState em render
