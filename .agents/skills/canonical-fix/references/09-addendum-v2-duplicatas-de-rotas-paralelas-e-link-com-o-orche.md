# Addendum v2 — duplicatas de rotas paralelas e link com o orchestrator

> Parte da skill `canonical-fix`. Carregue quando precisar deste topico especifico.

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
