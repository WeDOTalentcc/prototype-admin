# GitHub Actions — Temporariamente Desativados

Todos os workflows desta pasta estão **desativados** por enquanto. Os arquivos
`.yml` foram renomeados para `.yml.disabled` para impedir que o GitHub Actions
os carregue, sem perder o conteúdo.

## Política atual

Não fazer commit nem deploy automático no GitHub. Por ora, tudo fica salvo
apenas no Replit.

## Workflows desativados

- `ci.yml.disabled` — lint, testes, build (backend + frontend)
- `deploy.yml.disabled` — build/push de imagem Docker e deploy no GCP
- `docker-build.yml.disabled` — build/push de imagens no GHCR
- `e2e-tests.yml.disabled` — testes end-to-end com Playwright

## Como reativar

Renomeie os arquivos de volta removendo o sufixo `.disabled`:

```bash
cd .github/workflows
mv ci.yml.disabled ci.yml
mv deploy.yml.disabled deploy.yml
mv docker-build.yml.disabled docker-build.yml
mv e2e-tests.yml.disabled e2e-tests.yml
```

Depois faça commit e push. O GitHub Actions volta a carregar os workflows
automaticamente.
