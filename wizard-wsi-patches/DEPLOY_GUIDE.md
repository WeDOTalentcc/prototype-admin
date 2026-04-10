# Deploy Guide — Wizard WSI Backend (Sprints 0 + 1A + 2B)

## Ordem de execução

1. **Sprint 0**: Deploy Phase 6 Hardening (migrations + models + APIs)
2. **Sprint 1A**: Supervisor routing + publish→Rails integration
3. **Sprint 2B**: Dedup + ActionCable + StageAutomation

---

## Sprint 0 — Phase 6 Hardening

**Usar**: `lia-hardening/UPLOAD_GUIDE_PHASE6.md` (guia completo existente)
**Script**: `sprint-0/DEPLOY_PHASE6.sh` (automatiza parte 1 — FastAPI)

### Checklist Sprint 0
- [ ] Migrations 055-058 aplicadas (`alembic upgrade head`)
- [ ] Models copiados (sourcing_agent, digital_twin)
- [ ] Services copiados (6 arquivos)
- [ ] API endpoints copiados (6 arquivos)
- [ ] Routers registrados em main.py
- [ ] `Depends(lambda: None)` substituído por deps reais
- [ ] Rails: migrations + models + controllers (per UPLOAD_GUIDE_PHASE6.md Parte 2)
- [ ] Frontend: proxy routes (per UPLOAD_GUIDE_PHASE6.md Parte 3)

---

## Sprint 1A — Supervisor + Publish

### 1A.1: Supervisor routing
**Arquivo**: `sprint-1a/01_supervisor_routing_patch.py`
**Aplicar em**: `app/hub/supervisor_graph.py`
- Adicionar job_creation ao DOMAIN_DESCRIPTIONS
- Adicionar keywords ao ROUTING_KEYWORDS
- Registrar domain no registry
- Adicionar feature flag ENABLE_UNIFIED_WIZARD

### 1A.2-1.7: Publish node Rails integration
**Arquivo**: `sprint-1a/02_publish_node_rails_integration.py`
**Aplicar em**: `app/domains/job_creation/nodes/publish_node.py`
- **SUBSTITUIR** o publish_node inteiro pelo novo
- Cria job no Rails via POST /v1/users/jobs
- Cria RecruitmentCampaign via POST /v1/users/recruitment_campaigns
- Chama WSIScreeningPipeline.build_pipeline()
- Envia progress WS messages em cada etapa
- Gera share_link
- Log no AuditService
- Propaga multi-tenancy (X-Company-ID header)

### 1A.8: Review node defaults
**Arquivo**: `sprint-1a/03_review_node_apply_defaults.py`
**Aplicar em**: `app/domains/job_creation/nodes/review_node.py`
- **SUBSTITUIR** o review_node inteiro pelo novo
- Aplica valores de company defaults nos campos do state

### 1A.6: Tool map
**Arquivo**: `sprint-1a/04_tool_map_publish_job.py`
**Aplicar em**: `app/domains/job_creation/domain.py`
- Adicionar publish_job ao _ACTION_TOOL_MAP

### 1A.9: Reutilizar services
**Arquivo**: `sprint-1a/05_reuse_cv_screening_services.py`
**Aplicar em**: `app/domains/job_creation/services/`
- Substituir imports locais por imports de cv_screening
- Remover arquivos duplicados

### Checklist Sprint 1A
- [ ] Supervisor roteia "criar vaga" para job_creation
- [ ] ENABLE_UNIFIED_WIZARD=true no .env
- [ ] publish_node cria job no Rails (verificar no banco)
- [ ] publish_node cria RecruitmentCampaign
- [ ] publish_node chama WSIScreeningPipeline
- [ ] review_node aplica company defaults
- [ ] publish_job no tool map
- [ ] Services importados de cv_screening (não duplicados)

---

## Sprint 2B — Backend Completions

### 2B.12: Deduplicação embedding
**Arquivo**: `sprint-2b/01_dedup_embedding_patch.py`
**Aplicar em**: `app/domains/cv_screening/services/jd_enrichment_service.py`
- Adicionar `deduplicate_skills_by_similarity()` após extrair skills
- Threshold: cosine > 0.85

### 2B.13-14: ActionCable + StageAutomation
**Arquivo**: `sprint-2b/02_actioncable_broadcast_patch.py`
**Aplicar em**: Importar no publish_node.py
- Após criar campaign: `await broadcast_campaign_update(...)`
- Após criar job: `await trigger_stage_automation(...)`

### Checklist Sprint 2B
- [ ] Skills duplicadas removidas do JD enrichment
- [ ] Campaign broadcast aparece no WorkflowRail
- [ ] StageAutomation triggers executam

---

## Env vars necessárias

```bash
# FastAPI
RAILS_BACKEND_URL=http://rails-api:3000
FRONTEND_URL=https://app.wedotalent.com
ENABLE_UNIFIED_WIZARD=true

# Rails
ENABLE_EVENT_PUBLISHING=true
JWT_SECRET_KEY=<shared-secret>

# Frontend
NEXT_PUBLIC_RAILS_WS_URL=ws://rails-api:3000
```

---

## Sprint 3 — Testes + Compliance

### Testes
- **Backend**: `sprint-3/test_job_creation_nodes.py` → copiar para `tests/domains/job_creation/`
- **Frontend**: `unified-chat-build/wizard/__tests__/useWizardFlow.test.ts` → já no lugar
- Rodar: `pytest tests/domains/job_creation/ -v` e `jest wizard/__tests__/`

### Compliance
- **Arquivo**: `sprint-3/compliance_patches.py`
- **PiiMasker**: copiar para `app/shared/compliance/pii_masker.py`
- **hash_response**: copiar para `app/shared/compliance/response_hasher.py`
- **EU_AI_ACT_DISCLAIMER**: adicionar ao template de report F11
- **audit_wizard_decision**: chamar em cada node do wizard

---

## Sprint 4 — Backend Integrations

### Arquivo: `sprint-4/backend_integrations.py`
- **Campaign orchestration**: `start_sourcing_campaign()` — chamar no publish_node
- **Calibration hard enforcement**: `calibration_node()` — substituir no job_creation
- **SLA tracking**: `create_recruitment_sla()` — chamar no publish_node
- **Email/WhatsApp**: `send_publish_notification()` — chamar no publish_node
- **OCR**: `extract_text_from_image()` — copiar para services/
- **Voice screening**: config toggle no wizard state

### Frontend (já aplicado localmente):
- Drag-and-drop no UnifiedChatInput
- Cancel button no DynamicContextPanel
- Wizard state persistence (localStorage)

---

## Verificação end-to-end

1. Chat LIA: digitar "Criar vaga de Product Manager Senior"
2. Supervisor roteia para job_creation ✓
3. Wizard stages aparecem (intake → ... → publish) ✓
4. Publish cria job no Rails: `SELECT * FROM jobs ORDER BY id DESC LIMIT 1` ✓
5. Campaign criada: `SELECT * FROM recruitment_campaigns ORDER BY id DESC LIMIT 1` ✓
6. WorkflowRail mostra campaign ✓
7. Handoff mostra link ✓
