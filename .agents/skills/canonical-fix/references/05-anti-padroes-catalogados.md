# Anti-padroes catalogados

> Parte da skill `canonical-fix`. Carregue quando precisar deste topico especifico.

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
