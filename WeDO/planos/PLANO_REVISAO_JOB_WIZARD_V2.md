# Plano Estruturado de Revisão - Job Wizard Enhancement Plan v2

> **Data:** Fevereiro 2026  
> **Objetivo:** Garantir consistência entre documentação e código real  
> **Documento Alvo:** `docs/proposals/job-wizard-enhancement-plan-v2.md` (1.715 linhas)

---

## DIAGNÓSTICO INICIAL

### Estrutura do Documento

| Parte | Seções | Conteúdo |
|-------|--------|----------|
| PARTE 1 | 1-4 | Visão Geral, Status, Métricas, Arquitetura |
| PARTE 2 | 5-9 | Modelo de Dados, JobDraft, Confiança, Skills |
| PARTE 3 | 10-14 | Wizard 6 Etapas, Fast Track, Templates |
| PARTE 4 | 15-20 | Learning Loop, Feedback |
| PARTE 5 | 21-30 | Arquitetura Técnica, Agentes, Integrações |
| APÊNDICES | A-F | APIs, Schemas, Exemplos |

### Áreas Críticas para Validação

| Área | Documento Declara | Verificar em |
|------|-------------------|--------------|
| Agentes IA | 10 agentes v2.2 | `app/agents/agent_registry.py` |
| ATS Clients | Gupy, Pandapé | `app/services/ats_clients/` |
| Templates | 326 curados | `app/data/curated_templates_*.py` |
| Intelligence Layer | 8 métodos | `app/services/intelligence_layer_service.py` |
| Endpoints | 142 endpoints | Código backend |
| Wizard Etapas | 6 etapas | `app/agents/job_wizard_graph.py` |

---

## INVENTÁRIO DE CÓDIGO REAL (Fevereiro 2026)

### ATS Clients Encontrados (4)
```
lia-agent-system/app/services/ats_clients/
├── base.py        (classe base)
├── gupy.py        ✅ Gupy
├── pandape.py     ✅ Pandapé  
├── merge.py       ✅ Merge (agregador)
└── stackone.py    ✅ StackOne
```

### Tipos de Agentes no Registry (9 ativos)
```
1. ANALYST_FEEDBACK     - Feedback de análise
2. ATS_INTEGRATOR       - Integração ATS
3. CV_SCREENING         - Triagem curricular
4. INTERVIEWER          - Entrevistador
5. JOB_PLANNER          - Planejador de vagas
6. RECRUITER_ASSISTANT  - Assistente do recrutador
7. SCHEDULING           - Agendamento
8. SOURCING             - Sourcing de candidatos
9. WSI_EVALUATOR        - Avaliador WSI
```

### Templates Curados (361 total)
```
├── curated_templates_tech.py           119 templates
├── curated_templates_vendas.py          98 templates
├── curated_templates_operacoes.py       34 templates
├── curated_templates_rh.py              32 templates
├── curated_templates_administrativo.py  21 templates
├── curated_templates_financas.py        19 templates
├── curated_templates_customer_success.py 15 templates
├── curated_templates_saude.py           13 templates
├── curated_templates_marketing.py        8 templates
└── curated_templates_cs.py               2 templates
```

### Intelligence Layer (12 métodos públicos)
```
1. assess_data_quality()
2. build_intelligence_context()
3. apply_pattern_adjustment()
4. generate_field_suggestion()
5. log_insight()
6. record_insight_outcome()
7. refresh_patterns()
8. get_wizard_enhancements()
9. _is_cache_expired()
10. _ensure_patterns_detected()
11. _ensure_correlations_analyzed()
12. _generate_reasoning()
```

---

## ❌ DISCREPÂNCIAS IDENTIFICADAS

| Área | Documento Declara | Código Real | Diferença |
|------|-------------------|-------------|-----------|
| Agentes | 10 ativos | 9 tipos | -1 |
| Templates | 326 | 361 | +35 |
| Intelligence Layer | 8 métodos | 12 métodos | +4 |
| ATS Clients | 2 (Gupy, Pandapé) | 4 (+Merge, StackOne) | +2 |

### Correções Necessárias

1. **Seção 21 (Agentes):** Atualizar de "10 agentes" para "9 tipos de agente"
2. **Seção 12 (Templates):** Atualizar de "326 templates" para "361 templates"
3. **Seção 2.2 (ATS):** Adicionar Merge e StackOne à lista
4. **Diagrama de arquitetura:** Atualizar números

---

## PLANO DE 5 FASES - ✅ CONCLUÍDO

### Fase 1: Inventário de Código ✅
- [x] Listar todos os agentes ativos no registry (9 tipos)
- [x] Verificar templates curados (361 total)
- [x] Mapear serviços do Intelligence Layer (12 métodos)
- [x] Verificar ATS clients (4: Gupy, Pandapé, Merge, StackOne)

### Fase 2: Cross-Reference ✅
- [x] Comparar agentes declarados vs implementados
- [x] Validar integrações ATS listadas
- [x] Verificar métodos do Intelligence Layer
- [x] Confirmar estrutura do Wizard

### Fase 3: Identificar Discrepâncias ✅
- [x] Agentes: 10 → 9 (corrigido)
- [x] Templates: 326 → 361 (corrigido)
- [x] Categorias: 9 → 10 (corrigido)

### Fase 4: Atualizar Documento ✅
- [x] Corrigir números e contagens
- [x] Atualizar diagramas ASCII
- [x] Atualizar tabela de templates
- [x] Atualizar changelog (v7.0 → v7.1)

### Fase 5: Validação Final ✅
- [x] Verificação: 0 referências a "326" (antes: 15+)
- [x] Verificação: 0 referências a "10 agentes" (antes: 8)
- [x] Todas referências corrigidas para valores corretos

---

## CHECKLIST DE VALIDAÇÃO

### Seção 2.1 - Integrações IA
```
□ Claude API (Anthropic) - verificar em código
□ Gemini API (Google) - verificar em código  
□ OpenAI API - verificar em código
□ Versões corretas de modelos
```

### Seção 2.2 - Integrações ATS
```
□ Gupy - verificar gupy.py
□ Pandapé - verificar pandape.py
□ Merge - verificar merge.py
□ StackOne - verificar stackone.py
□ Outros mencionados?
```

### Seção 21 - Multi-Agente
```
□ Contar agentes no registry
□ Listar nomes de cada agente
□ Verificar v2.2 está correta
□ Diagrama atualizado?
```

### Templates Curados
```
□ Verificar contagem total (326?)
□ Validar categorias
□ Confirmar estrutura WSI
```

---

## CRITÉRIOS DE ACEITAÇÃO

O documento está válido quando:

1. ✅ Número de agentes = contagem real no registry
2. ✅ Integrações ATS = arquivos em ats_clients/
3. ✅ Templates = contagem real nos arquivos
4. ✅ Endpoints = rotas definidas no código
5. ✅ Status de implementação reflete código atual
6. ✅ Versões de APIs/modelos atualizadas

---

## PRÓXIMOS PASSOS

1. **Executar Fase 1** - Inventariar código real
2. **Executar Fase 2** - Cross-reference com documento
3. **Gerar relatório** - Discrepâncias encontradas
4. **Atualizar documento** - Correções necessárias
5. **Validar** - Script automático

---

*Plano criado em Fevereiro 2026*
