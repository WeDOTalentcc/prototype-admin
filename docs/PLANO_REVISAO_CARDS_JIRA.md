# Plano Estruturado de Revisão - Cards JIRA MVP

> **Data:** Fevereiro 2026  
> **Objetivo:** Garantir consistência total entre documentação e plataforma  
> **Documento Alvo:** `docs/lia-mvp-cards-jira.md` (17.964 linhas)

---

## DIAGNÓSTICO INICIAL

### Estrutura Atual do Documento

| Seção | Linhas | Descrição |
|-------|--------|-----------|
| Header/Resumo | 1-360 | Visão geral, cronograma, índice |
| ÉPICO 1-8 | 361-8200 | Cards detalhados (Auth a Templates) |
| ÉPICO 9-11 | 8200-13100 | Agendamento, Notificações, Kanban |
| Integrações | 13100-16000 | Twilio, Microsoft, LLM, WorkOS |
| Arquitetura | 16000-16800 | Documentação técnica |
| ÉPICO 12-15 | 16164-17130 | JD Avançado, Config, Agentes |
| Cenários | 17130-17965 | Análise de cenários A/B |

### Contagem Declarada vs Encontrada (Cards Únicos)

| Épico | Declarado | Únicos | Detalhados | Status |
|-------|-----------|--------|------------|--------|
| ÉPICO 1: Auth | 4 | 4 | ✅ | ✅ OK |
| ÉPICO 2: Wizard | 13 | 13 | ✅ | ✅ OK |
| ÉPICO 3: Mapeamento | 6 | 6 | ✅ | ✅ OK |
| ÉPICO 4: Perguntas WSI | 5 | 5 | ✅ | ✅ OK |
| ÉPICO 5: Triagem | 11 | 12 | ⚠️ | ❌ TRI-012 extra |
| ÉPICO 6: Score | 8 | 8 | ✅ | ✅ OK |
| ÉPICO 7: Gates | 7 | 7 | ✅ | ✅ OK |
| ÉPICO 8: Templates | 7 | 7 | ✅ | ✅ OK |
| ÉPICO 9: Agendamento | 8 | 8 (AGE-*) | ✅ | ⚠️ Usa prefixo AGE |
| ÉPICO 10: Notificações | 6 | 6 | ✅ | ✅ OK |
| ÉPICO 11: Kanban | 27 | 27 | 27 | ⚠️ Multi-prefixo |
| ÉPICO 12: JD Avançado | 5 | 2 | ❌ | ❌ Faltam JD-003,004,005 |
| ÉPICO 13: Config | 6 | 5 | ❌ | ❌ Falta CFG-006 |
| ÉPICO 14: Integrações | 33 | 33 | ✅ | ✅ OK |
| ÉPICO 15: Agentes | 8 | 8 | ✅ | ✅ OK |
| **TOTAL** | **154** | **~151** | - | ❌ 3 faltantes |

### Discrepâncias Críticas Identificadas

1. **ÉPICO 5 (Triagem):** TRI-012 existe mas declarado 11 cards
2. **ÉPICO 9 (Agendamento):** Prefixo AGE-* conflita com ÉPICO 15
3. **ÉPICO 11 (Kanban):** 4 prefixos (KAN, TAB, PRV, VAG) - confuso
4. **ÉPICO 12 (JD):** Faltam cards JD-003, JD-004, JD-005
5. **ÉPICO 13 (Config):** Falta card CFG-006
6. **KAN-005:** Marcado como ⚠️ Obsoleto (não Pendente)
7. **KAN-009:** Ausente do índice e sem detalhamento

### Prefixos por Épico (ÉPICO 11)

| Prefixo | Cards | Descrição |
|---------|-------|-----------|
| KAN-* | 9 detalhados | Kanban estrutura |
| TAB-* | 5 | Tabela de candidatos |
| PRV-* | 5 | Preview lateral |
| VAG-* | 8 | Tabela de vagas |
| **Total** | **27** | ✅ Correto |

---

## PLANO DE 6 FASES

### Fase 1: Inventário ✅ (Concluída)
- [x] Mapear estrutura do documento
- [x] Identificar todas as seções
- [x] Contagem inicial de referências

### Fase 2: Validação de Contagem
- [ ] Listar cards únicos por épico
- [ ] Comparar com contagem declarada no resumo executivo
- [ ] Identificar cards faltantes ou duplicados
- [ ] Verificar se 154 cards estão realmente documentados

**Checklist Fase 2:**
```
□ ÉPICO 1: 4 cards únicos (AUTH-001 a AUTH-004)
□ ÉPICO 2: 13 cards únicos (WIZ-001 a WIZ-013)
□ ÉPICO 3: 6 cards únicos (MAP-001 a MAP-006)
□ ÉPICO 4: 5 cards únicos (WSI-001 a WSI-005)
□ ÉPICO 5: 11 cards únicos (TRI-001 a TRI-011)
□ ÉPICO 6: 8 cards únicos (SCO-001 a SCO-008)
□ ÉPICO 7: 7 cards únicos (GAT-001 a GAT-007)
□ ÉPICO 8: 7 cards únicos (TPL-001 a TPL-007)
□ ÉPICO 9: 8 cards únicos (AGD-001 a AGD-008)
□ ÉPICO 10: 6 cards únicos (NOT-001 a NOT-006)
□ ÉPICO 11: 27 cards únicos (KAN-001 a KAN-027)
□ ÉPICO 12: 5 cards únicos (JD-001 a JD-005)
□ ÉPICO 13: 6 cards únicos (CFG-001 a CFG-006)
□ ÉPICO 14: 33 cards únicos (INT-xxx-xxx)
□ ÉPICO 15: 8 cards únicos (AGE-001 a AGE-008)
```

### Fase 3: Consistência de Status
- [ ] Verificar TODOS os cards têm "📋 Pendente"
- [ ] Remover qualquer "✅ Pronto", "🔧 Em progresso"
- [ ] Garantir 0 cards marcados como implementados
- [ ] Verificar tabelas de resumo mostram 0%

**Padrões a buscar e corrigir:**
- `| ✅ Pronto |` → `| 📋 Pendente |`
- `Status: Pronto` → `Status: 📋 Pendente`
- `Implementado` → `A implementar`
- `Configurado` → `A configurar`

### Fase 4: Validação de Sprints
- [ ] Todas referências usam Sprint 1-4
- [ ] Remover Sprint 0, 5, 6, 7, 8
- [ ] Labels corretas: `sprint-1` a `sprint-4`
- [ ] Cronograma consistente em todas seções

**Mapeamento de Sprints:**
```
Sprint 0 → Sprint 1 (Auth + Setup)
Sprint 1-2 → Sprint 1 (Wizard)
Sprint 3 → Sprint 2 (Triagem)
Sprint 4-5 → Sprint 3 (Score)
Sprint 6-8 → Sprint 4 (Finalização)
```

### Fase 5: Cross-Reference com Código
Comparar documentação com arquivos reais:

| Área | Arquivo | Verificar |
|------|---------|-----------|
| Agentes | `lia-agent-system/app/agents/` | 10 agentes ativos |
| Prompts | `app/agents/prompts/agent_prompts.py` | 10 prompts |
| Intelligence Layer | `app/services/intelligence_layer_service.py` | 8 métodos |
| ATS Clients | `app/services/ats_clients/` | 5 clients |
| Templates | `app/data/curated_templates_*.py` | 326 templates |

### Fase 6: Relatório Final
- [ ] Gerar lista de todas alterações feitas
- [ ] Atualizar contagens finais
- [ ] Criar changelog de revisão
- [ ] Validação final automatizada

---

## CRITÉRIOS DE ACEITAÇÃO

### Documento Válido se:
1. ✅ 154 cards únicos documentados
2. ✅ 0 cards com status "Pronto" ou "Implementado"
3. ✅ Todas referências usam Sprint 1-4
4. ✅ Contagens no resumo = contagens reais
5. ✅ Cross-reference com código validado
6. ✅ Nenhuma referência a Sprint 0 ou 5-8

### Validação Automática
```bash
# Executar após cada fase:
grep -c "Sprint 0\|Sprint 5\|Sprint 6\|Sprint 7\|Sprint 8" docs/lia-mvp-cards-jira.md
# Esperado: 0

grep -c "✅ Pronto\|| Pronto" docs/lia-mvp-cards-jira.md
# Esperado: 0

grep -c "📋 Pendente" docs/lia-mvp-cards-jira.md
# Esperado: ~154+ (índice + detalhamento)
```

---

## PRÓXIMOS PASSOS

1. **Aprovar este plano** - Confirmar abordagem
2. **Executar Fase 2** - Validar contagem exata de cards únicos
3. **Executar Fases 3-4** - Corrigir status e sprints
4. **Executar Fase 5** - Cross-reference com código
5. **Gerar relatório final** - Fase 6

---

*Plano gerado em Fevereiro 2026*
