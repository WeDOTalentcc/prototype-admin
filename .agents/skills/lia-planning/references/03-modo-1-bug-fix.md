# Modo 1: Bug Fix

> Parte da skill `lia-planning`. Carregue quando precisar deste topico especifico.

Para crashs, erros de runtime, funcionalidades quebradas.

```
DIAGNOSTICAR -> ISOLAR -> CORRIGIR -> VERIFICAR
```

1. **Diagnosticar** (maximo 10 min)
   - Reproduzir o erro (screenshot ou logs)
   - Identificar arquivo e linha exatos
   - Determinar causa raiz (nao o sintoma)
   - Classificar: crash vs visual vs logica vs performance
   - **Antes de propor o fix, rodar a skill `canonical-fix`** para confirmar qual arquivo e a fonte da verdade, mapear duplicatas/consumidores e evitar workaround no consumidor.

2. **Isolar**
   - Verificar se eh pre-existente (lista de erros a ignorar no scratchpad)
   - Identificar menor conjunto de arquivos afetados
   - Verificar se a correcao pode causar regressao

3. **Corrigir**
   - Correcao minima necessaria
   - Sem refactors oportunistas — fix apenas
   - Sem adicionar features — fix apenas

4. **Verificar**
   - Teste e2e com `runTest()` confirmando o fix
   - Screenshot antes/depois quando visual
   - Verificar que nao quebrou nada adjacente

**Checklist:**
- [ ] Causa raiz identificada (nao apenas sintoma)
- [ ] Correcao minima aplicada
- [ ] Nenhum debug log deixado no codigo
- [ ] Teste e2e passou
- [ ] Nenhuma regressao observada

---
