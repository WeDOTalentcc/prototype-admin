# Formato de Relatório

> Parte da skill `feature-audit`. Carregue quando precisar deste topico especifico.

Ao final da auditoria, produzir relatório no formato:

```
# Relatório de Auditoria — [Nome da Feature]

### Resumo
- Total itens verificados: X
- ✅ Aprovados: X
- ⚠️ Parciais: X
- ❌ Faltando: X
- N/A: X

### Dimensão 1: Integração (Wiring)
- ✅ Hook useX conectado ao ComponenteY
- ❌ Hook useInterpretContext criado mas NÃO conectado ao UniversalTransitionModal
- ✅ Endpoint /interpret-context tem proxy e hook

### Dimensão 2: Fluxo de Dados
- ✅ Dados fluem do backend ao componente
- ⚠️ Sub-status salvo localmente mas não persistido via API

[... continua para todas as 14 dimensões ...]

### Ações Necessárias (ordenadas por prioridade)
1. 🔴 CRÍTICO: Conectar useInterpretContext ao modal
2. 🟡 IMPORTANTE: Adicionar persistência de sub-status
3. 🟢 MENOR: Adicionar aria-labels nos botões de ícone
```

---
