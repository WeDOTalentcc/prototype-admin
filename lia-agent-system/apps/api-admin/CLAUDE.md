# CLAUDE.md — api-admin

## Regra Auth — OBRIGATÓRIA em todos os novos endpoints

```python
from app.shared.auth.auth_provider import AuthContext, get_auth_context_dependency

@router.get("/endpoint")
async def meu_endpoint(auth: AuthContext = Depends(get_auth_context_dependency())):
    company_id = auth.company_id
```

**PROIBIDO** em novos endpoints: `get_current_active_user`, `get_current_user`

## Controle de acesso — wedotalent_admin OBRIGATÓRIO

Todos os endpoints deste sub-app são para uso interno WeDOTalent.
Todo endpoint DEVE verificar `UserRole.wedotalent_admin` — nunca expor
funcionalidade admin para roles de tenant (recruiter, manager, etc).

Padrão canonical:
```python
if auth.user.role != UserRole.wedotalent_admin:
    raise HTTPException(status_code=403, detail="Acesso restrito a administradores WeDOTalent")
```

## Domínio

Rotas: admin platform, billing, saas_metrics, compliance, workos, global_policies,
       trust_center, incident_response, admin_lgpd, admin_prompts, admin_persona,
       admin_agents, admin_circuit_breakers, admin_dlq, admin_expurgo_audit,
       admin_bias_audit, admin_compliance_fairness, admin_consent, admin_external,
       admin_audit_decisions, admin_settings, admin_templates, admin_token_budget.

Acesso: APENAS `wedotalent_admin`. Jamais expor para tenant users.

## Frequência de deploy

Este sub-app tem frequência de deploy DIFERENTE dos sub-apps de tenant.
Mudanças de compliance e billing devem passar por revisão adicional antes de deploy.

## Multi-tenancy neste sub-app

Endpoints admin operam CROSS-TENANT por design (ex: listar todas as empresas,
ver métricas SaaS globais). Isso é INTENCIONAL e distinto dos sub-apps de tenant.
O gate `wedotalent_admin` é a barreira de segurança equivalente ao `company_id` JWT
nos sub-apps de tenant.

**NUNCA** misturar endpoints tenant-scoped com endpoints admin neste sub-app.
