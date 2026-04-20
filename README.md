# ats_ia_same_dev

## Política de CI/CD

Por ora, **não fazer commit nem deploy automático no GitHub** — tudo fica
salvo no Replit. Os workflows do GitHub Actions estão temporariamente
desativados. Para reativar, ver `.github/workflows/README.md`.

## Glossário e Terminologia

A terminologia oficial da plataforma LIA está em **[`docs/GLOSSARY.md`](./docs/GLOSSARY.md)**.

Use sempre os termos canônicos definidos nesse arquivo. Para manter o glossário sincronizado com o código:

```bash
python3 scripts/glossary_sync.py
```

Ver [`docs/GLOSSARY_MAINTENANCE.md`](./docs/GLOSSARY_MAINTENANCE.md) para detalhes do processo.
