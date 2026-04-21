# Spec-Driven: 4 Fases Adaptativas

> Parte da skill `lia-planning`. Carregue quando precisar deste topico especifico.

Para features grandes ou complexas, usar profundidade proporcional:

```
SPECIFY -> DESIGN -> TASKS -> EXECUTE
(obrigatorio)  (opcional)  (opcional)  (obrigatorio)
```

| Escopo | Specify | Design | Tasks | Execute |
|--------|---------|--------|-------|---------|
| **Small** (<=3 arquivos) | Quick mode | - | - | Implementar direto |
| **Medium** (<10 tasks) | Spec breve | Inline | Implicitas | Implementar + verificar |
| **Large** (multi-componente) | Spec + IDs | Arquitetura + componentes | Breakdown + deps | Implementar + verificar por task |
| **Complex** (ambiguidade) | Spec + brainstorming | Research + arquitetura | Breakdown + paralelo | Implementar + UAT interativa |

**Safety valve:** Se ao listar steps no Execute surgirem >5 ou dependencias complexas, PARE e crie tasks formais.

---
