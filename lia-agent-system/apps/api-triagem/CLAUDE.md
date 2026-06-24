# CLAUDE.md — api-triagem

Micro-app de triagem de candidatos da LIA.
Domínio: Triagem, Screening, WSI (text + async + voz), Big Five, CV Parser,
         Calibração, Elegibilidade, Portal do Candidato, Ações Afirmativas.
Porta padrão: `8003`.

## Regra Auth — OBRIGATÓRIA em todos os novos endpoints

Todo endpoint **novo** neste sub-app DEVE usar `get_auth_context_dependency`:

```python
from app.shared.auth.auth_provider import AuthContext, get_auth_context_dependency

@router.get("/endpoint")
async def meu_endpoint(auth: AuthContext = Depends(get_auth_context_dependency())):
    company_id = auth.company_id
```

**PROIBIDO** em novos endpoints: `get_current_active_user`, `get_current_user`, `get_current_user_or_demo`

**Endpoints legados existentes são PERM-EXEMPT** — NÃO reescrever em massa.

## PII — ATENÇÃO ESPECIAL

Este sub-app concentra o maior fluxo de PII de candidatos (CV, Big Five, WSI, voz).
Todo endpoint que lê/escreve dados de candidato DEVE usar `require_company_id` do JWT.
Consulte ADR-LGPD-001 e ADR-LGPD-002 em CLAUDE.md raiz.

### Camadas de PII neste sub-app

| Módulo | PII presente | Camada relevante |
|---|---|---|
| `cv_parser` | nome, CPF, email, telefone, endereço | Strip antes de enviar ao LLM vendor |
| `big_five` | perfil psicológico derivado | Agregado destrutivo — ADR-LGPD-001 |
| `wsi/*` | respostas de triagem, scoring | Dados de candidato — requere company_id |
| `voice_screening` | áudio + transcrição | Consentimento LGPD obrigatório antes de iniciar |
| `candidate_portal` | visão externa do candidato | Auth via token de portal (não JWT interno) |

### Regra de consentimento (voice)

Endpoints de `voice_screening` devem verificar `ConsentCheckerService` antes de iniciar
qualquer sessão de coleta. Ver `DataCollectionVoicePlugin.CONSENT_QUESTION` — hardcoded literal,
NUNCA interpolado com nome de tenant (ADR voice plugins CLAUDE.md raiz).

## Domínio

Rotas deste sub-app:
- `triagem` — triagem principal
- `screening`, `screening_questions` — screening de empresa
- `wsi/*` — WSI (text screening completo: questions/evaluation/sessions/reports)
- `wsi_async`, `wsi_observability`, `wsi_question_adjust`, `wsi_questions`, `wsi_screening_pipeline_endpoint`
- `cv_parser` — parsing e extração de CV
- `big_five` — Big Five assessment
- `voice_screening` — triagem por voz (Twilio + Gemini Live)
- `calibration`, `calibration_dashboard_v2` — calibração de triagem
- `eligibility_question_templates` — templates de perguntas eliminatórias
- `candidate_portal`, `candidate_portal_explanation` — portal externo do candidato
- `applications` — candidaturas
- `affirmative` — ações afirmativas / DEI

## Destino de extração (roadmap)

Prereq para **G10** (ats-pii como lib): este sub-app será o consumidor primário
de `ats-pii` quando disponível — toda PII de candidato passará por essa lib.
Quando G10 for iniciado, os MONOLITH-IMPORT markers em `main.py` devem ser
migrados para imports de `lia-pii` (lib a ser criada).

## Sensor ativo

`scripts/check_auth_provider_adoption.py --subapp triagem` — detecta novos
endpoints que usam auth legada.
