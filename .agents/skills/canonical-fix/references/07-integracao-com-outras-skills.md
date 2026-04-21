# Integracao com outras skills

> Parte da skill `canonical-fix`. Carregue quando precisar deste topico especifico.

| Skill | Quando combinar |
|-------|-----------------|
| **lia-planning** | No modo Bug Fix, rodar `canonical-fix` na fase **Diagnosticar** (antes de "Isolar/Corrigir"). No modo Refactor, rodar antes de "Planejar". |
| **feature-audit** | Apos aplicar o fix canonico, rodar `feature-audit` Dimensoes 1 (Integracao) e 7 (Consistencia) para confirmar que nenhum consumidor quebrou e nenhum padrao duplicado sobrou. |
| **vue-migration-prep** | Ao decidir o canonico, garanta que ele segue Princípios 1 e 2 (separacao de concerns, props tipadas) — assim a migracao futura nao precisa reescolher canonico. |
| **design-standardize** | Se a duplicata e de componente UI, aplicar tokens canonicos no consolidado (regra 90/10, tipografia) durante Fase 4. |
| **lia-testing** | Fase 5 obriga teste de regressao. Usar TDD (Red/Green/Refactor) — escrever teste que falha primeiro, depois aplicar fix. |

---
