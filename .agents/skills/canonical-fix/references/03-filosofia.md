# Filosofia

> Parte da skill `canonical-fix`. Carregue quando precisar deste topico especifico.

> **Corrigir na fonte e mais lento de comecar e mais rapido de terminar.**
>
> Workaround no consumidor parece rapido: 5 minutos. Mas multiplica o problema, esconde a causa, e na proxima vez que alguem mexer ali o bug volta — agora com mais um camuflado por cima. O fix canonico custa 30 minutos hoje e zera a divida tecnica daquele ponto.

Tres regras que NUNCA se quebram:

1. **Falhar alto, nao silenciosamente.** Se o codigo nao consegue cumprir o contrato, levanta excecao com mensagem clara. `try/except: pass` e `?? []` em retorno de API sao proibidos.
2. **Uma fonte da verdade por conceito.** Se existem duas implementacoes do mesmo hook/rota/service, uma delas e dead code e precisa ser deletada — nao mantida "por seguranca".
3. **Fix no produtor, nao no consumidor.** Se 5 telas exibem dado errado por causa de 1 hook, o fix e no hook (1 lugar). Nunca corrigir nas 5 telas.

---
