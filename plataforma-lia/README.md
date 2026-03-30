# Plataforma LIA — WeDo Talent

Plataforma de recrutamento inteligente com IA para o mercado brasileiro de RH.

## Stack

- **Framework:** Next.js 15 (App Router) + React 19
- **Linguagem:** TypeScript 5.8
- **Estilo:** Tailwind CSS 3.4 + shadcn/ui + Design System LIA
- **Backend:** FastAPI (via proxy `/api/backend-proxy`)
- **Auth:** WorkOS
- **Testes:** Vitest + Playwright
- **CI/CD:** GitHub Actions

## Setup local

```bash
npm install
cp .env.example .env.local  # configurar variáveis de ambiente
npm run dev                  # inicia na porta 3000
```

## Scripts

| Comando | Descrição |
|---|---|
| `npm run dev` | Desenvolvimento (hot reload) |
| `npm run build` | Build de produção |
| `npm test` | Testes unitários (Vitest) |
| `npm run test:e2e` | Testes E2E (Playwright) |
| `npm run lint` | ESLint |
| `npm run analyze` | Bundle analyzer |

## Documentação

- [Design System](docs/specs/frontend/DESIGN_SYSTEM.md)
- [UX Patterns](docs/specs/frontend/UX_PATTERNS.md)
- [Frontend Standards](docs/specs/frontend/FRONTEND_STANDARDS.md)
- [Auditoria Frontend](docs/audit/frontend-audit-consolidado-20-dimensoes.md)
