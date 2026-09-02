# WeDOTalent — Admin Console Prototype

Protótipo de alta fidelidade do painel administrativo interno da WeDOTalent. Fonte de referência visual e de comportamento para o time de engenharia durante o desenvolvimento do `admin-ui`.

**URL pública:** https://wedotalentcc.github.io/prototype-admin

---

## Rodando localmente

Não há build step. Basta abrir o arquivo diretamente no browser:

```bash
open index.html
# ou
open -a "Google Chrome" index.html
```

Funciona em qualquer browser moderno. Nenhuma dependência ou servidor necessário.

---

## Estrutura

```
prototype-admin/
├── index.html          # Toda a UI — telas, modais e componentes
├── styles/
│   ├── tokens.css      # Design tokens (cores, espaçamentos, sombras)
│   └── components.css  # Estilos dos componentes
└── scripts/
    └── app.js          # Navegação entre telas, modais, estado da sidebar
```

---

## Deploy

O protótipo é publicado automaticamente via **GitHub Pages** a partir da branch `main`.

Para atualizar a URL pública: commite as mudanças e faça push para `main`. O deploy ocorre em ~1 minuto sem nenhuma ação manual.

```bash
git add -A
git commit -m "feat: descrição da mudança"
git push origin main
```

---

## Telas implementadas

| Tela | ID | Descrição |
|------|----|-----------|
| Dashboard | `screen-dashboard` | KPIs, atividade recente, alertas |
| SaaS Metrics | `screen-saas-metrics` | MRR, churn, NRR, cohort |
| Clientes | `screen-clients` | Lista com paginação (12/página) |
| Provisionamentos | `screen-onboarding` | Status por etapa, paginação 20/página |
| Detalhe do Cliente | `screen-client-detail` | Overview, alterar plano |
| Usuários do Cliente | `screen-client-users` | Gestão de usuários/tenant |
| Faturamento | `screen-billing` | Invoices e métricas do cliente |
| Configuração LLM | `screen-llm-config` | Limites e modelos por tenant |
| Feature Flags | `screen-feature-flags` | Flags por tenant |
| Planos & Preços | `screen-plans` | Catálogo global de planos |
| Feature Flags Globais | `screen-global-flags` | Flags de plataforma |
| Email Templates | `screen-email-templates` | Templates transacionais |
| Contratos | `screen-contracts` | Sync HubSpot |
| Configurações | `screen-settings` | Configurações da plataforma |
| Integrações Globais | `screen-global-integrations` | Teams, HubSpot, Zapier |
| LIA Global | `screen-lia-global` | Configuração global do agente IA |
| Notificações | `screen-notifications` | Alertas e RBAC |
| AI Monitoring | `screen-ai-monitoring` | Monitoramento de agentes IA |
| Audit Logs | `screen-audit-logs` | Logs de auditoria |
| Acessos Assistidos | `screen-assisted-access` | Histórico das sessões de suporte na conta do cliente |

---

## Acesso assistido

Sessão curta e auditada em que alguém da WeDO entra na plataforma do cliente como um usuário real dele. O protótipo cobre os dois pontos da jornada:

**Modal "Acessar como cliente"** (`#overlay-assisted-access`), aberto pelo botão na lista de clientes e no detalhe do cliente. Coleta usuário alvo, motivo e duração. Estados, cada um em um cliente da lista:

| Estado | Como ver |
|--------|----------|
| Normal | Botão no card de **iFood Talentos** (ou no detalhe do cliente) |
| Motivo inválido | No modal do iFood, digite menos de 10 caracteres no motivo: o botão de abrir fica desabilitado |
| Acesso desligado pelo cliente | Botão no card de **Vega Recruit** |
| Conta suspensa | Botão no card de **GlobalHire Co.** |
| Abrindo a sessão | Selecione usuário, escreva o motivo e clique em **Abrir sessão** |

**Tela "Acessos Assistidos"** (sidebar, grupo Monitoramento): sessões ativas no topo com tempo restante e revogação, histórico filtrável, detalhe da sessão em drawer com as ações executadas (as sensíveis em destaque) e exportação.

Os demais estados da tela são telas próprias, alcançáveis por deep link (como as de `screen-clients`). O protótipo aplica o `#hash` no carregamento da página, então **recarregue** ao trocar o endereço:

- `index.html#screen-assisted-access-empty`: nenhuma sessão registrada
- `index.html#screen-assisted-access-loading`: carregando
- `index.html#screen-assisted-access-error`: falha ao carregar o histórico

---

## Histórias Jira relacionadas

WEDO-640 · WEDO-641 · WEDO-642 · WEDO-643 · WEDO-644 · WEDO-645 · WEDO-646 · WEDO-647 · WEDO-648 · WEDO-702 · WEDO-703 · WEDO-704 · WEDO-705 · WEDO-706 · WEDO-707 · WEDO-708 · WEDO-709 · WEDO-3468 · WEDO-3473

---

> **Não é código de produção.** Este repositório contém apenas o protótipo estático. O produto real está em `WeDOTalentcc/admin-ui`.
