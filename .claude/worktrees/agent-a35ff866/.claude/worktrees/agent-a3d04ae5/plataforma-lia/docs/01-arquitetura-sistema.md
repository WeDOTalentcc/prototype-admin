# Arquitetura do Sistema - Plataforma LIA

## Visão Geral Técnica

### Stack Principal
- **Framework**: Next.js 15.5.6 (App Router)
- **Runtime**: Node.js 20
- **Linguagem**: TypeScript
- **UI Framework**: React 18+
- **Estilização**: Tailwind CSS v3
- **Componentes Base**: Radix UI + shadcn/ui

### Bibliotecas de Visualização
- **Gráficos**: Chart.js, Recharts
- **Animações**: Framer Motion
- **Ícones**: Lucide React

## Estrutura de Diretórios

```
plataforma-lia/
├── src/
│   ├── app/                    # App Router (Next.js 15)
│   │   ├── globals.css        # Estilos globais + CSS variables
│   │   └── page.tsx           # Página principal
│   ├── components/
│   │   ├── pages/             # Páginas completas
│   │   │   ├── jobs-page.tsx
│   │   │   ├── candidates-page.tsx
│   │   │   ├── dashboards-page.tsx
│   │   │   └── settings-page-enhanced.tsx
│   │   ├── sidebar.tsx        # Menu lateral principal
│   │   └── ui/                # Componentes shadcn/ui
│   └── lib/
├── docs/                       # Documentação do projeto
├── public/                     # Arquivos estáticos
└── tailwind.config.ts         # Configuração Tailwind
```

## Configuração de Build

### Modo de Exportação
- **Tipo**: Static Export (`output: 'export'`)
- **Otimizações**: 
  - Image optimization desabilitado para static export
  - Remote patterns configurados para Unsplash e same-assets

### Domínios Remotos Permitidos
```typescript
remotePatterns: [
  { protocol: 'https', hostname: 'images.unsplash.com' },
  { protocol: 'https', hostname: 'same-assets.com' }
]
```

## Padrões Arquiteturais

### Componentes
- **Atomic Design**: Componentes pequenos e reutilizáveis
- **Composition Pattern**: Uso extensivo de children e slots
- **State Management**: React hooks (useState, useEffect)
- **Props Drilling**: Minimizado com context quando necessário

### Convenções de Código
- **TypeScript Strict Mode**: Tipagem forte obrigatória
- **Interfaces sobre Types**: Para objetos e contratos
- **Naming**: camelCase para variáveis, PascalCase para componentes
- **Arquivos**: kebab-case para nomes de arquivo

## Performance

### Otimizações Implementadas
- **Code Splitting**: Automático via Next.js App Router
- **Lazy Loading**: Componentes carregados sob demanda
- **Memoization**: React.memo para componentes pesados
- **CSS-in-JS**: Evitado em favor de Tailwind CSS classes

### Métricas Alvo
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: > 90

## Segurança

### Práticas Implementadas
- **No Secrets in Code**: Variáveis de ambiente para dados sensíveis
- **HTTPS Only**: Configuração de remote patterns
- **Input Validation**: Sanitização de inputs do usuário
- **XSS Protection**: React escape automático

## Deployment

### Ambiente Replit
- **Workflow**: `npm run dev` (porta 5000)
- **Hot Reload**: Habilitado via Next.js
- **Build**: `npm run build` (static export)

### Considerações de Produção
- **Static Export**: Compatível com CDN
- **No Server Components**: Apenas Client Components
- **Cache Strategy**: Headers de cache configuráveis
