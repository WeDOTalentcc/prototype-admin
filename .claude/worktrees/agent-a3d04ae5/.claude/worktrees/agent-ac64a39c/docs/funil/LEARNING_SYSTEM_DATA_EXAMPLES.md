# Learning System - Dados de Exemplo para Validação

Este documento contém exemplos de dados para validar o fluxo completo do sistema de aprendizado.

---

## 1. Skills Confirmation (Stage 1)

### Request: Confirmar Skill
```bash
curl -X POST http://localhost:8000/api/v1/lia/learning/confirm-skill \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "skill_name": "Python",
    "skill_type": "technical",
    "was_accepted": true,
    "source": "wizard",
    "role": "Backend Developer",
    "seniority": "senior"
  }'
```

### Response Esperada
```json
{
  "success": true,
  "skill_id": "uuid-do-skill",
  "times_confirmed": 1,
  "is_promoted": false,
  "message": "Skill confirmada (1/3 para promoção)"
}
```

---

## 2. Stage Feedback (Stages 2-7)

### Request: Registrar Feedback do Stage 3 (Competências)
```bash
curl -X POST http://localhost:8000/api/v1/lia/learning/stage-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "stage_number": 3,
    "stage_name": "Competências",
    "field_name": "skills",
    "suggested_value": ["Python", "SQL", "AWS"],
    "accepted_value": ["Python", "SQL", "AWS", "Docker"],
    "was_accepted": true,
    "was_modified": true,
    "role": "Backend Developer",
    "seniority": "senior",
    "confidence_before": 0.85
  }'
```

### Response Esperada
```json
{
  "success": true,
  "feedback_id": "uuid-do-feedback",
  "stage": 3,
  "was_accepted": true,
  "was_modified": true
}
```

---

## 3. Job Outcome (Fechamento de Vaga)

### Request: Registrar Contratação Bem-Sucedida
```bash
curl -X POST http://localhost:8000/api/v1/lia/learning/job-outcome \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "outcome": "filled",
    "time_to_fill_days": 25,
    "salary_initial": 15000,
    "salary_final": 18000,
    "total_candidates": 50,
    "screened_candidates": 20,
    "interviewed_candidates": 8,
    "offered_candidates": 2,
    "satisfaction_score": 4.5,
    "skills_used": ["Python", "SQL", "Docker", "AWS"],
    "role": "Backend Developer",
    "seniority": "senior"
  }'
```

### Response Esperada
```json
{
  "success": true,
  "outcome_id": "uuid-do-outcome",
  "patterns_updated": 3,
  "message": "Outcome registrado com sucesso"
}
```

---

## 4. Skills Deduplication (Stages 1-3)

### Request: Obter Skills Sem Duplicatas
```bash
curl -X POST http://localhost:8000/api/v1/lia/learning/skills-deduplicated \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "role": "Backend Developer",
    "exclude_already_selected": ["Python", "JavaScript"]
  }'
```

### Response Esperada
```json
{
  "skills": [
    {
      "id": "uuid-1",
      "name": "Docker",
      "type": "technical",
      "times_confirmed": 5,
      "is_promoted": true,
      "confidence": 0.95
    },
    {
      "id": "uuid-2",
      "name": "AWS",
      "type": "technical",
      "times_confirmed": 3,
      "is_promoted": true,
      "confidence": 0.88
    }
  ],
  "total": 2
}
```

---

## 5. Feature Flags

### Request: Configurar Flag com Rollout Gradual
```bash
curl -X POST http://localhost:8000/api/v1/lia/feature-flags/set \
  -H "Content-Type: application/json" \
  -d '{
    "flag_key": "ai_suggestions_enhanced",
    "is_enabled": true,
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "rollout_percentage": 50,
    "description": "Enhanced AI suggestions for this company"
  }'
```

### Response Esperada
```json
{
  "success": true,
  "flag_id": "uuid-da-flag",
  "flag_key": "ai_suggestions_enhanced",
  "is_enabled": true,
  "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "rollout_percentage": 50
}
```

### Request: Verificar Flag
```bash
curl -X GET "http://localhost:8000/api/v1/lia/feature-flags/check/ai_suggestions_enhanced?company_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Response Esperada
```json
{
  "flag_key": "ai_suggestions_enhanced",
  "is_enabled": true,
  "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 6. Learning Dashboard

### Request: Obter Dashboard Completo
```bash
curl -X POST http://localhost:8000/api/v1/lia/learning/dashboard \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

### Response Esperada (com dados)
```json
{
  "summary": {
    "total_skills_learned": 25,
    "promoted_skills": 8,
    "total_responsibilities": 15,
    "total_outcomes_recorded": 12,
    "total_patterns_detected": 20
  },
  "stage_analytics": {
    "has_data": true,
    "total_feedback": 150,
    "overall_acceptance_rate": 0.85,
    "overall_modification_rate": 0.25,
    "by_stage": {
      "2": {"total": 30, "accepted": 28, "modified": 5, "acceptance_rate": 0.93, "modification_rate": 0.17},
      "3": {"total": 35, "accepted": 28, "modified": 12, "acceptance_rate": 0.80, "modification_rate": 0.34},
      "4": {"total": 25, "accepted": 22, "modified": 8, "acceptance_rate": 0.88, "modification_rate": 0.32},
      "5": {"total": 20, "accepted": 19, "modified": 3, "acceptance_rate": 0.95, "modification_rate": 0.15},
      "6": {"total": 25, "accepted": 23, "modified": 6, "acceptance_rate": 0.92, "modification_rate": 0.24},
      "7": {"total": 15, "accepted": 14, "modified": 2, "acceptance_rate": 0.93, "modification_rate": 0.13}
    },
    "most_modified_fields": [
      {"field": "skills", "modification_rate": 0.40},
      {"field": "salary_range", "modification_rate": 0.35},
      {"field": "responsibilities", "modification_rate": 0.28}
    ]
  },
  "outcome_insights": {
    "has_data": true,
    "total_jobs": 12,
    "filled_jobs": 10,
    "fill_rate": 0.83,
    "avg_time_to_fill_days": 28.5,
    "salary_range": {"min": 8000, "max": 25000, "avg": 15000},
    "top_skills": [
      {"skill": "Python", "count": 8},
      {"skill": "SQL", "count": 7},
      {"skill": "Docker", "count": 5}
    ]
  },
  "success_rates": {
    "fill_rate": 0.83,
    "cancel_rate": 0.08
  },
  "learning_health": {
    "score": 75.5,
    "status": "healthy",
    "recommendations": [
      "Sistema de aprendizado saudável! Continue registrando feedback."
    ]
  }
}
```

---

## 7. Outcome Insights

### Request: Obter Insights por Cargo
```bash
curl -X POST http://localhost:8000/api/v1/lia/learning/outcome-insights \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "role": "Backend Developer",
    "seniority": "senior"
  }'
```

### Response Esperada
```json
{
  "has_data": true,
  "total_jobs": 5,
  "filled_jobs": 4,
  "fill_rate": 0.80,
  "avg_time_to_fill_days": 22.3,
  "salary_range": {"min": 15000, "max": 22000, "avg": 18500},
  "top_skills": [
    {"skill": "Python", "count": 4},
    {"skill": "Docker", "count": 3},
    {"skill": "AWS", "count": 3}
  ],
  "filters_applied": {
    "role": "Backend Developer",
    "seniority": "senior"
  }
}
```

---

## 8. Fluxo Completo de Validação

### Passo a Passo para Testar

1. **Criar uma empresa** (se não existir)
2. **Confirmar 3 skills** → Skill deve ser promovida
3. **Registrar feedback em cada stage** (2-7)
4. **Criar e fechar uma vaga** → Registrar outcome
5. **Verificar dashboard** → Deve mostrar métricas
6. **Testar deduplicação** → Skills já selecionadas não devem aparecer
7. **Configurar feature flag** → Verificar comportamento

### Script de Validação Automatizada

```bash
#!/bin/bash
BASE_URL="http://localhost:8000/api/v1/lia"
COMPANY_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

echo "=== 1. Confirmar Skills (3x para promoção) ==="
for i in 1 2 3; do
  curl -s -X POST "$BASE_URL/learning/confirm-skill" \
    -H "Content-Type: application/json" \
    -d "{\"company_id\": \"$COMPANY_ID\", \"skill_name\": \"TestSkill\", \"skill_type\": \"technical\", \"was_accepted\": true, \"source\": \"test\"}" | jq .
done

echo "=== 2. Registrar Stage Feedback ==="
curl -s -X POST "$BASE_URL/learning/stage-feedback" \
  -H "Content-Type: application/json" \
  -d "{\"company_id\": \"$COMPANY_ID\", \"stage_number\": 3, \"field_name\": \"skills\", \"suggested_value\": [\"A\"], \"accepted_value\": [\"A\", \"B\"], \"was_accepted\": true, \"was_modified\": true}" | jq .

echo "=== 3. Verificar Feature Flag ==="
curl -s -X GET "$BASE_URL/feature-flags/check/learning_hub_enabled" | jq .

echo "=== 4. Obter Dashboard ==="
curl -s -X POST "$BASE_URL/learning/dashboard" \
  -H "Content-Type: application/json" \
  -d "{\"company_id\": \"$COMPANY_ID\"}" | jq .

echo "=== VALIDAÇÃO COMPLETA ==="
```

---

## Notas Importantes

1. **Multi-tenant**: Todos os dados são isolados por `company_id`
2. **Promoção automática**: Skills são promovidas após 3 confirmações
3. **Deduplicação**: SHA256 hash para responsabilidades
4. **Health Score**: 0-100, com status `nascent` < 40 < `developing` < 70 < `healthy`
5. **Feature Flags**: Suportam rollout gradual (0-100%)

---

## Runbook de Deploy para Staging/Produção

### 1. Verificar Tabelas Existentes

```bash
# Conectar ao banco de dados
psql $DATABASE_URL -c "\dt *feature* *stage_feedback* *learning_analytics*"
```

### 2. Aplicar Migração Alembic

```bash
cd lia-agent-system

# Verificar migrações pendentes
alembic history
alembic current

# Aplicar migração 003
alembic upgrade 003_add_learning_system_tables

# Verificar se tabelas foram criadas
alembic current
```

### 3. Inicializar Feature Flags Padrão (Opcional)

```bash
# Os 8 flags padrão são criados automaticamente quando acessados
# Para criar explicitamente:
curl -X POST "$API_URL/api/v1/lia/feature-flags/set" \
  -H "Content-Type: application/json" \
  -d '{"flag_key": "learning_hub_enabled", "is_enabled": true}'
```

### 4. Smoke Test

```bash
# Verificar endpoint de health
curl "$API_URL/api/v1/lia/feature-flags"

# Verificar dashboard
curl -X POST "$API_URL/api/v1/lia/learning/dashboard" \
  -H "Content-Type: application/json" \
  -d '{"company_id": "test-company-id"}'
```

### 5. Rollback (se necessário)

```bash
# Reverter migração
alembic downgrade -1

# Ou reverter para versão específica
alembic downgrade 002
```

### Checklist de Deploy

- [ ] Backup do banco de dados realizado
- [ ] Migração aplicada (`alembic upgrade head`)
- [ ] Tabelas criadas: `feature_flags`, `stage_feedback`, `learning_analytics`
- [ ] Índices verificados (partial unique index em `feature_flags`)
- [ ] Smoke tests passando
- [ ] Logs de erro verificados
