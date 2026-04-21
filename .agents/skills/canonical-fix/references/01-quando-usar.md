# Quando usar

> Parte da skill `canonical-fix`. Carregue quando precisar deste topico especifico.

- Antes de corrigir qualquer bug (runtime, logico, visual, performance).
- Antes de editar arquivos com nomes/exports/rotas suspeitos de ter duplicata (`use-foo.ts` + `use-foo.tsx`, `route.ts` em dois lugares, dois services com nome parecido).
- Antes de iniciar um refactor que toca multiplos consumidores.
- Quando o usuario disser "corrige na raiz", "sem gambiarra", "sem workaround", "arruma direito", "vai na fonte".
- Quando o sintoma aparece em N lugares ao mesmo tempo (sinal forte de fonte unica quebrada).
