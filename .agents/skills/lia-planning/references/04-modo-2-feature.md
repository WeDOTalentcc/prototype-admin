# Modo 2: Feature

> Parte da skill `lia-planning`. Carregue quando precisar deste topico especifico.

Para funcionalidades novas ou melhorias significativas.

```
SPEC -> IMPACTO -> IMPLEMENTAR -> TESTAR -> AUDITAR
```

1. **Spec** (o que, nao como)
   - Definir comportamento esperado em linguagem simples
   - Listar criterios de aceite
   - Identificar dependencias (APIs, componentes, dados)
   - Perguntar ao usuario se o design/layout muda

2. **Impacto** (usar skill `feature-impact` para features grandes)
   - Mapear arquivos afetados
   - Verificar impacto no Design System v4.2.1
   - Checar se afeta preparacao para migracao Vue

3. **Implementar**
   - Seguir convencoes existentes do codebase
   - `"use client"` sempre na primeira linha de client components
   - Hooks em `.tsx` quando contiverem JSX
   - Sem `any` — usar tipos especificos
   - Sem inline styles — usar Tailwind

4. **Testar**
   - `runTest()` com plano detalhado
   - Testar happy path E edge cases
   - Testar responsividade quando UI

5. **Auditar** (usar skill `feature-audit` para features medias/grandes)
   - Code review com `architect()`
   - Atualizar `PLANO_IMPLEMENTACAO_v2.md` com novas metricas

### Brainstorming para Features Complexas

Quando a feature tem ambiguidade ou multiplas abordagens possiveis, ANTES do Modo 2:

1. **Explorar contexto** — verificar arquivos, docs, commits recentes
2. **Perguntar** — uma pergunta por vez, preferir multipla escolha
3. **Propor 2-3 abordagens** — com trade-offs e recomendacao
4. **Apresentar design** — secoes proporcionais a complexidade, aprovar cada uma
5. **Aprovar** — so implementar apos aprovacao do usuario

**HARD-GATE:** NAO implementar ate ter design aprovado. Todo projeto passa por este processo. "Simples" eh onde suposicoes nao examinadas causam mais retrabalho.

---
