# Mapa Completo: Fluxo de Onboarding de Cliente WeDo Talent

> **Documento de Análise e Plano de Melhorias**  
> Última atualização: Janeiro 2026

---

## Resumo Executivo

### O que JÁ EXISTE (Funcional)

| Componente | Localização | Status |
|------------|-------------|--------|
| Lista de clientes | `/admin/clientes` | ✅ |
| Criar cliente | `CreateClientDialog` | ✅ |
| Detalhes do cliente | `/admin/clientes/[id]` | ✅ |
| Dashboard de onboarding | Checklist visual | ✅ |
| Gestão de usuários | `/admin/clientes/[id]/usuarios` | ✅ |
| Convidar usuários | Botão funcional | ✅ |
| Detecção SCIM | Banner automático | ✅ |
| Sistema de email | Resend/SendGrid | ✅ |
| WorkOS SSO | Fluxo completo | ✅ |
| Setup inicial | Wizard 6 passos | ✅ |

### O que FALTA (Gaps Identificados)

| Gap | Impacto | Prioridade |
|-----|---------|------------|
| Integração HubSpot ↔ WeDo | Alto | 🔴 Alta |
| Criar WorkOS Organization automaticamente | Alto | 🔴 Alta |
| Email automático de boas-vindas | Médio | 🟡 Média |
| Convite automático do primeiro Admin | Médio | 🟡 Média |
| Dashboard de status de onboarding consolidado | Baixo | 🟢 Baixa |

---

## Visão Geral das 6 Fases

```
┌─────────────────────────────────────────────────────────────┐
│                    MAPA DE MATURIDADE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FASE 1: COMERCIAL (HubSpot)     [███░░░░░░░] 30%          │
│  FASE 2: PROVISIONAMENTO (WeDo)  [███████░░░] 70%          │
│  FASE 3: CONFIG SSO (WorkOS)     [████████░░] 80%          │
│  FASE 4: CONVITES                [███████░░░] 70%          │
│  FASE 5: PRIMEIRO LOGIN          [█████████░] 90%          │
│  FASE 6: SETUP INICIAL           [█████████░] 90%          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## FASE 1: COMERCIAL (HubSpot)

### Fluxo Atual

```
HubSpot CRM
    ↓
Lead qualificado → Demo → Proposta → Contrato
    ↓
[MANUAL] Time WeDo recria dados no Admin
```

### O que JÁ EXISTE

- ✅ HubSpot como CRM comercial
- ✅ Pipeline de vendas configurado

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🔴 **Sync HubSpot → WeDo** | Quando deal fecha, criar cliente automaticamente |
| 🔴 **Sync WeDo → HubSpot** | Atualizar deal com status de onboarding |
| 🟡 Webhook HubSpot | Receber eventos de deal closed |

### Solução Proposta

```
HubSpot (Deal Closed Won)
    ↓ [Webhook]
WeDo Backend
    ↓ [Automático]
├── Criar ClientAccount
├── Criar CompanyWorkOSConfig
├── Criar Organization no WorkOS
├── Enviar email de boas-vindas
└── Atualizar HubSpot com link de acesso
```

---

## FASE 2: PROVISIONAMENTO (WeDo Admin)

### Fluxo Atual

```
Time WeDo acessa /admin/clientes
    ↓
Clica "Novo Cliente" → Preenche formulário → Salva
    ↓
Cliente criado no banco [ClientAccount]
    ↓
[MANUAL] Ir ao WorkOS Dashboard criar Organization
[MANUAL] Copiar org_id e salvar no WeDo
[MANUAL] Enviar email ao cliente
```

### O que JÁ EXISTE

- ✅ **CreateClientDialog** - Formulário completo
- ✅ **Backend /clients POST** - CRUD funcional
- ✅ **CompanyWorkOSConfig model** - Tabela existe

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🔴 **Criar WorkOS Organization automaticamente** | Chamar API WorkOS ao criar cliente |
| 🔴 **Salvar organization_id** | Preencher CompanyWorkOSConfig |
| 🟡 **Enviar email de boas-vindas** | Usar email_service existente |

### Solução Proposta

```python
# Ao criar cliente, adicionar:
1. Criar Organization no WorkOS via API
2. Salvar organization_id em CompanyWorkOSConfig
3. Gerar link do Admin Portal
4. Enviar email de boas-vindas com instruções
```

---

## FASE 3: CONFIGURAÇÃO SSO (WorkOS)

### Fluxo Atual

```
Cliente recebe email com link Admin Portal
    ↓
Acessa WorkOS Admin Portal
    ↓
Configura IdP (Okta/Azure AD/Google)
    ↓
Testa conexão SSO
    ↓
[Opcional] Ativa SCIM Directory Sync
```

### O que JÁ EXISTE

- ✅ **workos-links.ts** - URLs tenant-specific
- ✅ **WorkOS Admin Portal embedado** - Modal funcional
- ✅ **Documentação SSO** - Guia completo em português
- ✅ **SCIM Webhooks** - 8 eventos processados
- ✅ **Group-to-Role mapping** - Funcional

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🟡 **Notificação quando SSO ativo** | Webhook do WorkOS ou polling |
| 🟢 **Vídeo tutorial** | Gravação mostrando configuração |

---

## FASE 4: CONVITES

### Fluxo Atual

```
Time WeDo acessa /admin/clientes/[id]/usuarios
    ↓
Clica "Convidar Usuário" → Preenche nome/email/role
    ↓
[PARCIAL] Usuário criado com status "pending"
    ↓
[NÃO IMPLEMENTADO] Email de convite enviado
```

### O que JÁ EXISTE

- ✅ **UI de convite** - Modal funcional
- ✅ **Endpoint POST /clients/:id/users** - Backend existe
- ✅ **ClientUser model** - status pending/active/inactive
- ✅ **Email service** - Resend/SendGrid configurados

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🔴 **Enviar email de convite** | Conectar email_service ao convite |
| 🟡 **Template de convite** | Email bonito com branding |
| 🟡 **Link de aceite** | Página para aceitar convite |
| 🟡 **Expiração de convite** | Links expiram em 7 dias |

### Solução Proposta

```python
# Ao convidar usuário:
1. Criar ClientUser com status="pending"
2. Gerar token de convite (JWT 7 dias)
3. Enviar email usando email_service
4. Usuário clica link → aceita → status="active"
```

---

## FASE 5: PRIMEIRO LOGIN

### Fluxo Atual

```
Usuário acessa plataforma
    ↓
Clica "Entrar com SSO"
    ↓
WorkOS AuthKit → IdP → Callback
    ↓
Backend sync-user → JWT → Onboarding 6 slides
```

### O que JÁ EXISTE

- ✅ **Fluxo SSO completo** - Funcional
- ✅ **sync-user endpoint** - Cria/atualiza usuário
- ✅ **Onboarding visual** - 6 slides impactantes
- ✅ **MFA via AuthKit** - Suportado

### O que FALTA

| Gap | Descrição |
|-----|-----------|
| 🟢 **Fallback email/senha** | Para clientes sem SSO |
| 🟢 **Detecção de domínio** | Auto-redirect por email |

---

## FASE 6: SETUP INICIAL

### Fluxo Atual

```
Cliente completa onboarding visual
    ↓
Wizard de 3 passos:
├── Configurar empresa (5 min)
├── Criar primeira vaga (3 min)
└── Ativar recrutamento (2 min)
    ↓
Dashboard operacional
```

### O que JÁ EXISTE

- ✅ **Setup wizard** - Completo
- ✅ **Análise de cultura por IA** - Funcional
- ✅ **Benefícios sugeridos** - Automático
- ✅ **Criação de vaga assistida** - LIA ajuda

### Status: ✅ COMPLETO

---

## PLANO DE IMPLEMENTAÇÃO

### Sprint 1: Integração HubSpot (1-2 semanas)

#### 1.1 Webhook HubSpot → WeDo

```
Objetivo: Quando deal fechar no HubSpot, criar cliente automaticamente

Tarefas:
□ Criar endpoint POST /webhooks/hubspot
□ Validar assinatura HMAC do HubSpot
□ Mapear campos HubSpot → ClientAccount
□ Criar cliente no banco
□ Criar Organization no WorkOS
□ Atualizar deal no HubSpot com link de acesso

Arquivos:
- lia-agent-system/app/api/v1/hubspot_webhooks.py (novo)
- lia-agent-system/app/services/hubspot_service.py (novo)
```

#### 1.2 Sync WeDo → HubSpot

```
Objetivo: Atualizar HubSpot quando status do cliente mudar

Tarefas:
□ Salvar hubspot_deal_id no ClientAccount
□ Ao mudar status, chamar API HubSpot
□ Atualizar propriedade "onboarding_status" no deal
□ Registrar atividade de timeline

Eventos a sincronizar:
- Cliente criado
- SSO configurado
- Primeiro login
- Onboarding completo
- Primeira vaga criada
```

### Sprint 2: Automação WorkOS (1 semana)

#### 2.1 Criar Organization Automaticamente

```
Objetivo: Ao criar cliente, criar Organization no WorkOS

Tarefas:
□ Adicionar workos SDK ao backend
□ No POST /clients, chamar workos.organizations.create()
□ Salvar organization_id em CompanyWorkOSConfig
□ Gerar Admin Portal link
□ Retornar link no response

Código:
# lia-agent-system/app/services/workos_provisioning_service.py
async def provision_workos_organization(client: ClientAccount):
    org = workos.organizations.create(
        name=client.name,
        domains=[client.email_domain]
    )
    await save_workos_config(client.id, org.id)
    return org
```

#### 2.2 Email de Boas-Vindas

```
Objetivo: Enviar email automático quando cliente é criado

Tarefas:
□ Criar template "welcome_client" no email_service
□ Incluir: link Admin Portal, guia SSO PDF, contato suporte
□ Chamar send_email no fluxo de criação
□ Registrar envio no histórico

Template:
- Assunto: "Bem-vindo à WeDo Talent - Próximos Passos"
- Corpo: Instruções para configurar SSO
- Anexo: PDF guia de configuração
```

### Sprint 3: Sistema de Convites (1 semana)

#### 3.1 Envio de Email de Convite

```
Objetivo: Quando convidar usuário, enviar email automaticamente

Tarefas:
□ Criar template "invite_user"
□ Gerar token JWT (7 dias validade)
□ Enviar email com link de aceite
□ Criar página /aceitar-convite
□ Ao aceitar, mudar status para "active"

Fluxo:
1. Admin convida usuário
2. Backend cria ClientUser (status=pending)
3. Backend envia email com token
4. Usuário clica link
5. Frontend valida token
6. Backend atualiza status para active
7. Usuário pode fazer login
```

#### 3.2 Gerenciamento de Convites

```
Objetivo: UI para ver e gerenciar convites pendentes

Tarefas:
□ Mostrar data de envio e expiração
□ Botão "Reenviar convite"
□ Botão "Cancelar convite"
□ Badge de expirado após 7 dias
```

### Sprint 4: Dashboard de Onboarding (3-5 dias)

#### 4.1 Status Consolidado

```
Objetivo: Mostrar progresso de onboarding de todos os clientes

Tarefas:
□ Criar /admin/onboarding-clientes
□ Lista de clientes com status de cada etapa
□ Filtrar por: pendentes, em progresso, completos
□ Alertas para clientes parados há X dias

Etapas rastreadas:
1. ☑ Cliente criado
2. ☐ Email de boas-vindas enviado
3. ☐ SSO configurado
4. ☐ Admin convidado
5. ☐ Admin fez primeiro login
6. ☐ Setup inicial completo
7. ☐ Primeira vaga criada
```

---

## Variáveis de Ambiente Necessárias

```bash
# HubSpot
HUBSPOT_API_KEY=pat-xxx
HUBSPOT_WEBHOOK_SECRET=xxx

# WorkOS (já existem)
WORKOS_API_KEY=sk_xxx
WORKOS_CLIENT_ID=client_xxx

# Email (já existem)
RESEND_API_KEY=re_xxx
# ou
SENDGRID_API_KEY=SG.xxx
```

---

## Arquitetura de Integrações

```
┌─────────────────────────────────────────────────────────────┐
│                      HubSpot CRM                            │
│  (Comercial: Leads, Deals, Pipeline)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ Webhook: Deal Closed Won
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   WeDo Talent Backend                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ ClientAccount│  │CompanyWorkOS│  │ ClientUser │         │
│  │   (Dados)   │  │  Config    │  │ (Usuários) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
            ▼                                 ▼
┌─────────────────────┐           ┌─────────────────────────┐
│      WorkOS         │           │    Email Service        │
│  - Organizations    │           │  - Resend/SendGrid      │
│  - SSO/SCIM        │           │  - Templates            │
│  - Admin Portal    │           │  - Boas-vindas/Convite  │
└─────────────────────┘           └─────────────────────────┘
```

---

## Cronograma Sugerido

| Sprint | Escopo | Duração | Prioridade |
|--------|--------|---------|------------|
| **1** | Integração HubSpot (webhook + sync) | 1-2 semanas | 🔴 Alta |
| **2** | Automação WorkOS (org + email) | 1 semana | 🔴 Alta |
| **3** | Sistema de Convites (email + aceite) | 1 semana | 🟡 Média |
| **4** | Dashboard Onboarding | 3-5 dias | 🟢 Baixa |

**Tempo total estimado: 4-5 semanas**

---

## Métricas de Sucesso

| Métrica | Antes | Depois |
|---------|-------|--------|
| Tempo para criar cliente | 30-60 min | 5 min |
| Etapas manuais | 6+ | 1 (criar no HubSpot) |
| Taxa de erro | Alta | Próxima de zero |
| Visibilidade de status | Nenhuma | Dashboard completo |

---

## Histórico

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | Jan 2026 | Análise inicial |
| 2.0 | Jan 2026 | Correção: identificado sistema existente, plano atualizado com HubSpot |

