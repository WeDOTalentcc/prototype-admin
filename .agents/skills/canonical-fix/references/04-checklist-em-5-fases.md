# Checklist em 5 fases

> Parte da skill `canonical-fix`. Carregue quando precisar deste topico especifico.

Execute na ordem. Nao pule fases.

### Fase 1 — Mapear o canonico

Descobrir qual arquivo e a fonte da verdade do conceito que voce vai mexer.

- [ ] Listar TODOS os arquivos com nome similar ao alvo:
  ```bash
  # Frontend (TS/TSX)
  find plataforma-lia/src -type f \( -name "*foo*.ts" -o -name "*foo*.tsx" \) | grep -v node_modules | grep -v ".next"

  # Backend (Python)
  find lia-agent-system/app -type f -name "*foo*.py" | grep -v __pycache__
  ```
- [ ] Para cada arquivo encontrado, verificar:
  - Quando foi modificado por ultimo? (`ls -lt`)
  - Quantas linhas tem? (arquivo de 50 linhas vs 600 linhas — qual parece o "real"?)
  - Esta importado em algum lugar? Se nao, e candidato a dead code.
- [ ] Procurar duplicatas por **export** (mesmo nome de funcao/classe em arquivos diferentes):
  ```bash
  grep -rn "export function useFoo\|export const useFoo\|export class FooService" \
    plataforma-lia/src lia-agent-system/app --include="*.ts" --include="*.tsx" --include="*.py"
  ```
- [ ] Procurar duplicatas de **rota** (Next.js / FastAPI):
  ```bash
  # Next.js: route.ts em paths similares
  find plataforma-lia/src/app -name "route.ts" | xargs grep -l "foo"

  # FastAPI: handlers de rota similares
  grep -rn "@router\.\(get\|post\|put\|delete\).*foo" lia-agent-system/app --include="*.py"
  ```
- [ ] **Decisao explicita**: anote qual arquivo e o canonico e por que. Os outros sao dead code (Fase 5 vai deletar) ou variantes legitimas (raro — precisa justificar).

### Fase 2 — Listar consumidores

Saber quem importa/chama o canonico antes de mexer.

- [ ] Listar todos os imports do simbolo canonico:
  ```bash
  grep -rn "from.*canonical-file\|import.*useFoo\|import.*FooService" \
    plataforma-lia/src lia-agent-system/app --include="*.ts" --include="*.tsx" --include="*.py"
  ```
- [ ] Para cada consumidor, classificar:
  - **Quebra se eu mudar a assinatura?** (mudanca de tipo de retorno, parametro novo)
  - **Continua funcionando se eu so corrigir o bug interno?** (mais comum)
- [ ] Se >5 consumidores quebrariam com mudanca de assinatura, considere abrir task de refactor separada (Fase 3).
- [ ] Anotar a contagem: "N consumidores, X quebram, Y nao quebram".

### Fase 3 — Decidir o tipo de fix

Arvore de decisao:

```
A mudanca quebra a assinatura publica do canonico?
|
+-- NAO -> Fix interno no canonico (caminho rapido).
|          Vai para Fase 4.
|
+-- SIM -> Quantos consumidores quebram?
            |
            +-- 1 a 3 -> Fix no canonico + atualizar consumidores na mesma task.
            |             Vai para Fase 4.
            |
            +-- 4+    -> PARAR. Abrir task separada de refactor.
                          Nao aplicar workaround para "destravar". Discutir com usuario.
```

Sinais de que voce esta prestes a fazer **workaround** (proibido):

- "Vou colocar um `if` no consumidor pra contornar."
- "Vou duplicar o hook e mudar so essa parte."
- "Vou criar uma flag de env pra ativar so aqui."
- "Vou catchar a excecao e retornar `[]` pra UI nao quebrar."
- "Vou criar uma rota nova `/v2/foo` ao inves de corrigir `/foo`."

Se reconheceu algum, **volte para Fase 1** — voce nao identificou o canonico ou esta fugindo da fonte real.

### Fase 4 — Executar o fix

Regras explicitas durante a edicao:

- [ ] Editar APENAS o canonico (e os consumidores se Fase 3 mandou).
- [ ] **Nada de `try/except: pass`** ou `try { } catch {}` engolindo erro. Se precisa capturar, logar com contexto e re-raise ou retornar erro estruturado.
- [ ] **Nada de fallback silencioso** (`?? []`, `or {}`, `default=None` sem semantica clara). Se a operacao falha, falhar de forma visivel (excecao, toast de erro, status 500 com mensagem).
- [ ] **Nada de copy-paste** de logica que ja existe. Se precisa do mesmo comportamento em outro lugar, importar.
- [ ] **Nada de flag/env improvisada** ("`USE_NEW_FOO=true`") sem plano de remocao. Se for flag legitima, documentar prazo de remocao no codigo.
- [ ] **Nada de migration inline / fallback de "criar tabela se nao existir"** dentro de endpoint de runtime. Migrations sao Alembic. Se a tabela nao existe, a migration nao rodou — esse e o bug.
- [ ] Se identificar duplicata morta na Fase 1, deletar agora (mesmo commit).
- [ ] Atualizar/adicionar teste que reproduz o bug — se nao tem teste, o bug volta.

### Fase 5 — Validar

- [ ] Re-rodar os greps da Fase 1 — duplicata foi deletada?
  ```bash
  find plataforma-lia/src -type f -name "*foo*.ts*" | grep -v node_modules
  # Esperado: apenas o canonico
  ```
- [ ] Re-rodar os greps da Fase 2 — todos os consumidores ainda compilam?
  ```bash
  # LSP / typecheck
  npx tsc --noEmit  # frontend
  python -m mypy app  # backend (se configurado)
  ```
- [ ] Rodar teste de regressao do bug original.
- [ ] Rodar teste e2e do fluxo afetado (`runTest()` da skill `lia-testing`).
- [ ] Procurar por `TODO`, `FIXME`, `HACK`, `XXX` que voce introduziu — nenhum deve sobrar sem task associada.
  ```bash
  grep -n "TODO\|FIXME\|HACK\|XXX" arquivo-modificado
  ```
- [ ] Confirmar que nenhum `print()`, `console.log()` ou debug code ficou no commit.

---
