# Modo 3: Refactor

> Parte da skill `lia-planning`. Carregue quando precisar deste topico especifico.

Para melhorias de qualidade sem mudanca de comportamento.

```
MEDIR -> PLANEJAR -> EXECUTAR -> MEDIR DE NOVO
```

1. **Medir** (antes) — contar metricas: `:any`, `as any`, inline styles, linhas
2. **Planejar** — definir meta, listar arquivos alvo, estimar esforco
3. **Executar** — um arquivo por vez, compilar e testar apos cada um
4. **Medir de novo** — recontar, atualizar PLANO com delta

### Comandos de Medicao

```bash
# Contar :any
grep -r ": any" plataforma-lia/src --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v ".next/" | wc -l

# Contar as any
grep -r "as any" plataforma-lia/src --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v ".next/" | wc -l

# Contar inline styles
grep -rn "style={{" plataforma-lia/src --include="*.tsx" | grep -v node_modules | wc -l

# Listar monolitos >1500 linhas
find plataforma-lia/src -name "*.tsx" -o -name "*.ts" | grep -v node_modules | grep -v ".next" | xargs wc -l | sort -rn | head -20

# Score de qualidade
# Score = 10 - (any/100 * 1.5) - (as_any/50 * 1.0) - (inline/500 * 1.0) - (monolitos/5 * 0.5)
```

---
