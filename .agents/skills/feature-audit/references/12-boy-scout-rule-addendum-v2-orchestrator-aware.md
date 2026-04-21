# Boy Scout Rule (addendum v2 — orchestrator-aware)

> Parte da skill `feature-audit`. Carregue quando precisar deste topico especifico.

> **Sempre deixe o codigo um pouco melhor do que voce achou.** Encontrou um `print()` na area que esta editando? Remova. Encontrou um `except: pass`? Substitua. Encontrou um `bg-blue-500`? Padronize. Pequenas correcoes oportunas evitam que divida tecnica vire bola de neve.

Limites do Boy Scout em `feature-audit`:
- Aplicar **apenas** em arquivos que voce ja esta tocando para a tarefa principal.
- Limitar a 3-5 correcoes pequenas — se ha mais que isso, abrir task separada.
- Nunca refatorar arquitetura "de passagem" — isso vira refactor real (modo REFACTOR + `canonical-fix`).
