# Git Hooks — WeDOTalent

Hooks via `pre-commit` framework para enforcement automático das regras de
governança definidas em `CLAUDE.md` e `docs/BRANCH_MAP.md`.

## Instalação (1x por dev/máquina)

```bash
pip install pre-commit
pre-commit install --hook-type commit-msg
```

Após esse setup, todo `git commit` dispara as validações automaticamente.

## Hooks ativos

### branch-map-theme-check

**O que faz:** bloqueia commits em branches genéricas (sprint accumulators
como `feat/orch-migration-sprint-I`, `main`, `develop`) que tocam temas
**não mapeados** em `docs/BRANCH_MAP.md`.

**Regra que enforça:** Guide 1 (Branch por tema) + Guide 2 (BRANCH_MAP é
canônico) do `CLAUDE.md`.

**Como contornar legitimamente:**
- Trabalho dentro de tema já mapeado: nada a fazer, passa
- Trabalho em tema novo: criar branch própria OU adicionar tema ao BRANCH_MAP primeiro
- Urgência justificada: `git commit --no-verify` (bypass explícito)

**Script:** `scripts/check_branch_map.py`

## Comportamento esperado

```bash
# Em branch específica de tema → passa
$ git checkout feat/teams-integration
$ git commit -m "feat(teams): nova rota webhook"
✅ commit aceito

# Em branch genérica, tema mapeado → passa
$ git checkout feat/orch-migration-sprint-I
$ git commit -m "feat(teams): correção urgente no webhook"
✅ commit aceito (theme 'teams' está em BRANCH_MAP §1)

# Em branch genérica, tema novo não mapeado → bloqueia
$ git checkout feat/orch-migration-sprint-I
$ git commit -m "feat(billing): nova feature de faturamento"
❌ Commit bloqueado pelo Branch Map Theme Check
   [...mensagem instrutiva com 4 opções...]
```

## Manutenção

Quando adicionar tema novo ao BRANCH_MAP, o sensor passa a permitir commits
desse tema automaticamente (a checagem é por substring contra o conteúdo do
mapa). Sem mudança no script.

Para adicionar nova branch ao set de "branches genéricas", editar
`scripts/check_branch_map.py:GENERIC_BRANCH_PATTERNS`.

## Troubleshooting

**Hook não dispara após `git commit`:**
```bash
ls -la .git/hooks/commit-msg  # deve existir e apontar para pre-commit
pre-commit install --hook-type commit-msg --overwrite
```

**Hook dispara mas Python não acha:**
```bash
which python3  # confirmar que está no PATH
# se necessário, ajustar `entry:` em .pre-commit-config.yaml
```

**Falso positivo (tema legítimo mas não detectado):**
- Verificar que o tema aparece em `docs/BRANCH_MAP.md` (case-insensitive)
- Se tema correto está lá mas hook bloqueia, abrir issue para ajuste de detecção
