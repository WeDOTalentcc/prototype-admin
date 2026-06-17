---
name: canonical-fix
description: "Identifica o arquivo canonico (fonte da verdade) antes de qualquer fix, refactor ou edicao com risco de duplicata. Use OBRIGATORIAMENTE quando: (a) for corrigir um bug, (b) for editar codigo onde podem existir duplicatas (rotas paralelas, hooks clonados .ts/.tsx, services com nomes similares), (c) for refatorar, (d) o usuario pedir 'corrige na raiz', 'sem gambiarra', 'sem workaround', 'corrige na origem', 'arruma direito'. Garante que o fix seja aplicado na fonte (nao no consumidor), sem fallback silencioso, sem try/except mascarando, sem flag improvisada e sem copy-paste de logica."
---

# Canonical-Fix — Corrigir na Origem, Sem Workaround

Procedimento obrigatorio antes de editar codigo para corrigir um bug ou refatorar. Garante que voce identifique o **arquivo canonico** (fonte da verdade), entenda quem o consome, e aplique o fix no lugar certo — nunca no consumidor, nunca atras de um fallback, nunca com copy-paste.

## Quando ativar

- Antes de corrigir qualquer bug (runtime, logico, visual, performance) — sempre rodar este checklist primeiro
- Antes de editar arquivo com nome/export/rota suspeito de duplicata (`use-foo.ts` + `use-foo.tsx`, `route.ts` em dois lugares, services com nome parecido)
- Antes de iniciar refactor que toca multiplos consumidores ou multiplas telas
- Quando o usuario disser "corrige na raiz", "sem gambiarra", "sem workaround", "arruma direito", "vai na fonte" ou "corrige na origem"
- Quando o sintoma aparece em N lugares ao mesmo tempo (sinal forte de fonte unica quebrada)
- Quando voce esta prestes a colocar `try/except: pass`, `?? []` ou `if (data) { ... }` para esconder ausencia de dado
- Quando voce esta prestes a copiar logica de um lugar para outro porque "e mais facil"
- Como pre-requisito do Modo Bug Fix em `lia-planning` (rodar antes de propor o fix)

## Quando NAO ativar

- Typo trivial em string literal de UI (sem logica)
- Adicao de feature totalmente nova em arquivo novo, sem tocar codigo existente
- Mudanca de copy/texto em arquivo de traducao ou i18n
- Quando o usuario pediu explicitamente workaround temporario com prazo (ex: "poe um patch ate sexta, vou abrir task")
- Configuracao de ambiente (.env, dotfiles, secrets) sem mudanca de codigo

## Filosofia

> **Corrigir na fonte e mais lento de comecar e mais rapido de terminar.**
>
> Workaround no consumidor parece rapido: 5 minutos. Mas multiplica o problema, esconde a causa, e na proxima vez que alguem mexer ali o bug volta — agora com mais um camuflado por cima. O fix canonico custa 30 minutos hoje e zera a divida tecnica daquele ponto.

Tres regras que NUNCA se quebram:

1. **Falhar alto, nao silenciosamente.** Se o codigo nao consegue cumprir o contrato, levanta excecao com mensagem clara. `try/except: pass` e `?? []` em retorno de API sao proibidos.
2. **Uma fonte da verdade por conceito.** Se existem duas implementacoes do mesmo hook/rota/service, uma delas e dead code e precisa ser deletada — nao mantida "por seguranca".
3. **Fix no produtor, nao no consumidor.** Se 5 telas exibem dado errado por causa de 1 hook, o fix e no hook (1 lugar). Nunca corrigir nas 5 telas.

---

## Checklist em 5 fases

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

## Anti-padroes catalogados

Casos reais que ja ocorreram na plataforma LIA. Se voce reconhecer um padrao parecido no que esta prestes a fazer, **pare e volte para Fase 1**.

### 1. Rota paralela (route duplication)

**Sintoma**: bug em `/api/backend-proxy/candidates`. Em vez de corrigir, criou-se `/api/backend-proxy/candidates-v2` com a logica certa, e os componentes novos apontam para v2 enquanto os velhos continuam quebrados.

**Por que e ruim**: dois endpoints fazem quase a mesma coisa, divergem com o tempo, ninguem sabe qual usar, bug original nunca foi resolvido.

**Fix correto**: corrigir `/candidates` e deletar `/candidates-v2` (ou nao cria-lo).

### 2. Hook duplicado `.ts` + `.tsx`

**Sintoma**: existe `useCandidatesExecuteSearch.ts` E `useCandidatesExecuteSearch.tsx`. Bug aparece em uma versao. Recriaram a logica na outra "porque era mais facil".

**Por que e ruim**: 647 linhas de dead code (caso real, ver tasks abertas), consumidores divididos entre as duas versoes, fix em um nao reflete no outro.

**Fix correto**: identificar qual e o canonico (geralmente o que tem mais imports recentes), portar qualquer logica unica do morto, deletar o morto.

### 3. Fallback escondendo 500

**Sintoma**:
```ts
const { data } = useSWR('/api/foo', fetcher);
const items = data?.items ?? [];  // <-- esconde que API caiu
```
ou
```python
try:
    return await foo_service.get_items(...)
except Exception:
    return []  # <-- 500 vira "lista vazia" silenciosa
```

**Por que e ruim**: usuario ve UI vazia sem entender por que. Equipe descobre o bug semanas depois quando alguem reclama. Logs nao mostram erro porque foi engolido.

**Fix correto**: deixar excecao subir. UI mostra estado de erro explicito (toast, empty state com mensagem "Falha ao carregar, tente novamente"). Backend retorna 500 com detail. Logar com `logger.exception`.

### 4. Try/except engolindo erro

**Sintoma**:
```python
try:
    result = complex_call()
except Exception as e:
    pass  # ou: logger.debug(e); return None
```

**Por que e ruim**: identico ao #3. Bug fica invisivel. Quando aparece, ja propagou para 3 lugares.

**Fix correto**: capturar excecoes especificas (`except IntegrityError`), tratar com semantica clara, re-raise quando nao souber tratar. Se precisa retornar default, comentar o porque e logar com `warning`.

### 5. Feature flag virou workaround permanente

**Sintoma**: env var `USE_NEW_PIPELINE=true` criada "temporariamente" ha 8 meses, ninguem sabe se pode remover, codigo tem `if os.getenv('USE_NEW_PIPELINE'):` em 14 lugares.

**Por que e ruim**: dobra o codigo para sempre. Refactor futuro precisa entender os dois caminhos.

**Fix correto**: flags so existem com prazo escrito no codigo (`# REMOVE: 2026-06-01 apos task #XXX`). Se nao tem prazo, escolher um caminho e remover o outro.

### 6. Fix no componente quando o bug e no hook

**Sintoma**: `useCandidates()` retorna data com campo errado. Em vez de corrigir o hook, cada componente que usa faz `data.map(c => ({ ...c, name: c.first_name + ' ' + c.last_name }))`.

**Por que e ruim**: 12 componentes duplicam a mesma transformacao. Quando o backend mudar, 12 lugares quebram.

**Fix correto**: corrigir o hook (ou o adapter de API) para retornar o formato certo. Componentes consomem direto.

### 7. Migration inline em endpoint de runtime

**Sintoma**:
```python
@router.post("/questions/save")
async def save_question(...):
    await db.execute("CREATE TABLE IF NOT EXISTS questions (...)")
    # ... resto do handler
```

**Por que e ruim**: schema do banco vira responsabilidade do request handler. Race condition, performance, inconsistencia entre tenants. Esconde que a migration Alembic nao rodou.

**Fix correto**: criar migration Alembic. Endpoint assume que tabela existe. Se nao existe, falhar com 500 explicito (e investigar por que `alembic upgrade head` nao rodou — caso real do post-merge.sh, ver replit.md).

### 8. Copy-paste de logica de validacao

**Sintoma**: regras de negocio (ex: "vaga so pode ir para triagem se tem >=3 candidatos") replicadas em frontend, em 2 endpoints e no agente IA.

**Por que e ruim**: mudanca da regra exige alteracao em 4 lugares, sempre esquece um.

**Fix correto**: regra mora em UM service backend (`PolicyService.can_move_to_screening(...)`). Frontend chama endpoint que usa o service. Agente chama o mesmo service.

---

## Comandos prontos

### Detectar duplicatas — frontend

```bash
# Hooks duplicados (mesmo nome em .ts e .tsx)
find plataforma-lia/src -type f \( -name "use-*.ts" -o -name "use-*.tsx" \) \
  | grep -v node_modules | grep -v ".next" \
  | xargs -n1 basename | sed 's/\.tsx\?$//' | sort | uniq -d

# Componentes com nome similar
find plataforma-lia/src -type f -name "*.tsx" | grep -v node_modules \
  | xargs -n1 basename | sort | uniq -d

# Mesmo export em multiplos arquivos
grep -rn "^export function useFoo\|^export const useFoo" plataforma-lia/src \
  --include="*.ts" --include="*.tsx" | grep -v node_modules

# Rotas Next.js duplicadas (mesmo path-segment final)
find plataforma-lia/src/app/api -name "route.ts" | sed 's|.*/api/||;s|/route.ts||' | sort | uniq -d
```

### Detectar duplicatas — backend

```bash
# Services com nome similar
find lia-agent-system/app -name "*service*.py" | grep -v __pycache__ \
  | xargs -n1 basename | sort | uniq -d

# Mesmo handler de rota
grep -rn "@router\.\(get\|post\|put\|delete\|patch\)" lia-agent-system/app \
  --include="*.py" | awk -F'"' '{print $2}' | sort | uniq -d

# Funcoes com mesmo nome em modulos diferentes
grep -rn "^def [a-z_]*\|^async def [a-z_]*" lia-agent-system/app --include="*.py" \
  | awk -F: '{print $3}' | sed 's/.*def \([a-z_][a-z_0-9]*\).*/\1/' | sort | uniq -c | sort -rn | head -20
```

### Mapear consumidores

```bash
# Quem importa o hook canonico
grep -rn "import.*useCandidatesExecuteSearch\|from.*useCandidatesExecuteSearch" \
  plataforma-lia/src --include="*.ts" --include="*.tsx" | grep -v node_modules

# Quem importa o service backend
grep -rn "from app\.services\.foo_service import\|FooService(" \
  lia-agent-system/app --include="*.py" | grep -v __pycache__

# Quem chama o endpoint
grep -rn "/api/backend-proxy/candidates\b\|/api/v1/candidates\b" \
  plataforma-lia/src lia-agent-system --include="*.ts" --include="*.tsx" --include="*.py"
```

### Detectar anti-padroes

```bash
# try/except engolindo erro
grep -rn -A1 "except.*:" lia-agent-system/app --include="*.py" \
  | grep -B1 "pass\|return \[\]\|return {}\|return None" | head -40

# Fallback silencioso no frontend
grep -rn "?? \[\]\|?? {}\||| \[\]\|catch.*=>.*\[\]" plataforma-lia/src \
  --include="*.ts" --include="*.tsx" | grep -v node_modules | head -40

# print() em codigo de producao
grep -rn "print(" lia-agent-system/app --include="*.py" | grep -v "test_\|^#"

# console.log de debug
grep -rn "console\.log" plataforma-lia/src --include="*.ts" --include="*.tsx" \
  | grep -v node_modules | grep -v ".next"

# Feature flags sem prazo de remocao
grep -rn "os\.getenv\|process\.env\." lia-agent-system/app plataforma-lia/src \
  --include="*.py" --include="*.ts" --include="*.tsx" | grep -i "use_new\|enable_new\|feature_"
```

---

## Integracao com outras skills

| Skill | Quando combinar |
|-------|-----------------|
| **lia-planning** | No modo Bug Fix, rodar `canonical-fix` na fase **Diagnosticar** (antes de "Isolar/Corrigir"). No modo Refactor, rodar antes de "Planejar". |
| **feature-audit** | Apos aplicar o fix canonico, rodar `feature-audit` Dimensoes 1 (Integracao) e 7 (Consistencia) para confirmar que nenhum consumidor quebrou e nenhum padrao duplicado sobrou. |
| **vue-migration-prep** | Ao decidir o canonico, garanta que ele segue Princípios 1 e 2 (separacao de concerns, props tipadas) — assim a migracao futura nao precisa reescolher canonico. |
| **design-standardize** | Se a duplicata e de componente UI, aplicar tokens canonicos no consolidado (regra 90/10, tipografia) durante Fase 4. |
| **lia-testing** | Fase 5 obriga teste de regressao. Usar TDD (Red/Green/Refactor) — escrever teste que falha primeiro, depois aplicar fix. |

---

## Saida esperada

Ao terminar, voce deve poder responder:

1. **Qual era o canonico?** (caminho exato do arquivo)
2. **Quais duplicatas/dead code foram deletados?** (lista)
3. **Quantos consumidores foram tocados?** (numero + caminhos)
4. **Qual teste cobre a regressao?** (caminho do teste)
5. **Algum workaround foi necessario?** (deve ser "nao" — se "sim", justificar)

Se nao consegue responder essas 5, a skill nao foi aplicada — volte para a Fase 1.

---

## Addendum v2 — duplicatas de rotas paralelas e link com o orchestrator

### Sintoma especifico: rotas paralelas no Next.js + FastAPI

Padrao recorrente da plataforma LIA: a mesma operacao tem TRES caminhos:
1. `plataforma-lia/src/app/api/<dominio>/route.ts` (rota Next "direta")
2. `plataforma-lia/src/app/api/backend-proxy/<dominio>/route.ts` (proxy Next -> FastAPI)
3. `lia-agent-system/app/api/v1/<dominio>.py` (FastAPI canonico)

Quando isso acontece, o canonico e SEMPRE o FastAPI (3). Os caminhos (1) e (2) sao consumidores. Aplicar Fase 2-5 da skill: deletar (1) se existir, manter (2) APENAS como passthrough fino, garantir que toda logica viva em (3).

Comando para detectar duplicatas de rota:
```bash
# Mesma operacao em mais de um lugar
grep -rln "POST.*candidates\|/screening\|/jobs" \
  plataforma-lia/src/app/api lia-agent-system/app/api \
  --include="*.ts" --include="*.py"
```

### Sintoma especifico: hooks duplicados `.ts` vs `.tsx`

Tambem comum: `useFoo.ts` e `useFoo.tsx` coexistindo. O canonico e `.ts` se nao retorna JSX; `.tsx` se retorna. Nunca os dois. Verificar:
```bash
ls plataforma-lia/src/hooks/use-*.{ts,tsx} 2>/dev/null | sort
```

### Cross-reference com `lia-orchestrator`

Esta skill e disparada AUTOMATICAMENTE pela orchestrator em qualquer modo BUG FIX, REFACTOR e em BUILD que toca arquivo existente. Se voce esta lendo esta skill por conta propria, confira a Tabela 4 da `lia-orchestrator` para ver se ha outras skills que devem ser carregadas em conjunto.

