# Auditoria Admin — Documento de Decisão Final

> Data: 2026-04-02
> Responsável: Equipe Técnica LIA
> Objetivo: Reduzir de 61 para ~35 páginas, removendo redundâncias e funcionalidades prematuras

---

## Resumo Executivo

| Decisão | Qtd | % | Resultado |
|---------|-----|---|-----------|
| MANTER | 30 | 49% | Páginas essenciais que permanecem na navegação |
| REMOVER | 22 | 36% | Páginas removidas da navegação (marcadas como "futuro") |
| SIMPLIFICAR | 9 | 15% | Páginas consolidadas em outras (conteúdo absorvido) |

**Resultado final: 30 páginas acessíveis (redução de 51%)**

---

## ÁREA 1: VISÃO GLOBAL (4 páginas)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 1 | Dashboard Administrativo | `/admin` | **MANTER** | Página central, essencial. KPIs reais via API. |
| 2 | Métricas da Plataforma | `/admin/metricas-plataforma` | **MANTER** | Visão financeira/operacional com dados reais. |
| 3 | Jornada de Recrutamento (global) | `/admin/jornada-recrutamento` | **REMOVER** | Redundante com `/clientes/[id]/jornada`. Não há caso de uso claro para template global vs instância por cliente. Remover da navegação; manter arquivo para futura decisão sobre templates. |
| 4 | Setup Empresa (global) | `/admin/setup-empresa` | **REMOVER** | Confuso com `/clientes/[id]/setup`. Se for template para clientes, precisa de redesign. Remover da navegação agora. |

**Resultado Área 1: 2 mantidas, 2 removidas**

---

## ÁREA 2: GESTÃO DE CLIENTES (3 páginas base)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 5 | Lista de Clientes | `/admin/clientes` | **MANTER** | Central de controle essencial. Dados reais via API. |
| 6 | Onboarding de Clientes | `/admin/onboarding-clientes` | **MANTER** | Operacional importante. Calculado localmente com dados reais. |
| 7 | SSO / SCIM | `/admin/sso` | **MANTER** | Funcional, conectado ao WorkOS. Dados reais. |

**Resultado Área 2: 3 mantidas**

---

## ÁREA 3: DETALHES POR CLIENTE (18 sub-páginas)

| # | Página | Sub-caminho | Decisão | Justificativa |
|---|--------|-------------|---------|---------------|
| 8 | Visão Geral do Cliente | `/` | **MANTER** | Dashboard central do cliente. Perfil=API, métricas=mock (a finalizar). |
| 9 | Usuários | `/usuarios` | **MANTER** | Essencial. Dados reais via API. |
| 10 | Setup Empresa | `/setup` | **MANTER** | Setup por cliente, essencial. Dados reais. |
| 11 | Jornada Recrutamento | `/jornada` | **MANTER** | Configuração operacional por cliente. Dados reais. |
| 12 | Workforce (Headcount) | `/workforce` | **REMOVER** | Funcionalidade avançada. Marcar como "futuro". Não há demanda imediata. |
| 13 | Integrações | `/integracoes` | **MANTER** | Mostra conexões ATS do cliente. Operacional. |
| 14 | Automações | `/automacoes` | **REMOVER** | Pode ser agrupado com Jornada futuramente. Funcionalidade prematura. |
| 15 | Big Five | `/big-five` | **REMOVER** | Funcionalidade diferenciada mas nichada. Marcar como "futuro". |
| 16 | Testes Técnicos | `/testes` | **REMOVER** | Pode ser seção dentro de Setup. Simplificar futuramente. |
| 17 | Comunicações | `/comunicacoes` | **MANTER** | Templates de comunicação operacionais. |
| 18 | Faturamento | `/faturamento` | **MANTER** | Financeiro essencial. |
| 19 | Consumo de IA | `/consumo-ia` | **MANTER** | Controle de custos IA essencial. |
| 20 | Métricas SaaS | `/metricas` | **MANTER** | Health score, engagement, churn risk. |
| 21 | Observabilidade | `/observabilidade` | **REMOVER** | Conteúdo pode ser aba dentro de Consumo de IA. Redundante. |
| 22 | Conformidade (hub) | `/conformidade` | **MANTER** | Dashboard compliance por cliente. |
| 23 | Conformidade/LGPD | `/conformidade/lgpd` | **SIMPLIFICAR** | Absorvido como seção do hub de conformidade do cliente (#22). |
| 24 | Conformidade/Controles | `/conformidade/controles` | **SIMPLIFICAR** | Absorvido como seção do hub de conformidade do cliente (#22). |
| 25 | Conformidade/Incidentes | `/conformidade/incidentes` | **SIMPLIFICAR** | Absorvido como seção do hub de conformidade do cliente (#22). |

**Resultado Área 3: 10 mantidas, 5 removidas, 3 simplificadas**

---

## ÁREA 4: COMPLIANCE GLOBAL (21 páginas → 8 páginas)

### Trust Center (3 páginas → 0 na navegação, conteúdo acessível via Dashboard)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 26 | Trust Center - Certificações | `/compliance/trust-center/certificacoes` | **SIMPLIFICAR** | Informação estática. Acessível via botão no Dashboard Compliance. Remover do menu lateral. |
| 27 | Trust Center - Subprocessadores | `/compliance/trust-center/subprocessadores` | **SIMPLIFICAR** | Juntar com Trust Center único acessível via Dashboard. |
| 28 | Trust Center - Recursos | `/compliance/trust-center/recursos` | **SIMPLIFICAR** | Juntar com Trust Center único acessível via Dashboard. |

### Controles de Segurança (5 páginas → 1 página)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 29 | Controles Hub | `/compliance/controles` | **MANTER** | Hub principal com filtros por framework. |
| 30 | Cobertura | `/compliance/controles/cobertura` | **SIMPLIFICAR** | Absorvido como aba/filtro no hub de controles (#29). |
| 31 | ISO 27001 | `/compliance/controles/iso-27001` | **SIMPLIFICAR** | Vira filtro no hub de controles. |
| 32 | SOC 2 | `/compliance/controles/soc-2` | **SIMPLIFICAR** | Vira filtro no hub de controles. |
| 33 | SOX | `/compliance/controles/sox` | **SIMPLIFICAR** | Vira filtro no hub de controles. |

### LGPD (5 páginas → 3 páginas)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 34 | LGPD Hub | `/compliance/lgpd` | **MANTER** | Hub principal LGPD. |
| 35 | DPO | `/compliance/lgpd/dpo` | **REMOVER** | Pode ser seção do hub LGPD. Funcionalidade simples. |
| 36 | Consentimentos | `/compliance/lgpd/consentimentos` | **MANTER** | Operacional LGPD essencial. |
| 37 | Transferências | `/compliance/lgpd/transferencias` | **REMOVER** | Relevância baixa no momento. Funcionalidade futura. |
| 38 | Portal do Titular | `/compliance/lgpd/portal-titular` | **MANTER** | Obrigatório LGPD (DSAR). |

### Monitoramento de Segurança (4 páginas → 0 na navegação principal)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 39 | Monitoramento Hub | `/compliance/monitoramento` | **REMOVER** | Redundante com Dashboard Compliance. Alertas/Incidentes acessíveis via links no dashboard. |
| 40 | Dashboard Segurança | `/compliance/monitoramento/dashboard-seguranca` | **REMOVER** | Redundante com hub de monitoramento e dashboard compliance. |
| 41 | Alertas | `/compliance/monitoramento/alertas` | **MANTER** | Operacional. Acessível via link no Dashboard Compliance. Não precisa de item próprio no menu lateral (redução de ruído). |
| 42 | Incidentes | `/compliance/monitoramento/incidentes` | **MANTER** | Obrigatório. Acessível via link no Dashboard Compliance. Não precisa de item próprio no menu lateral (redução de ruído). |

### Riscos (4 páginas → 0 na navegação)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 43 | Riscos Hub | `/compliance/riscos` | **REMOVER** | Funcionalidade avançada. Marcar como "futuro". |
| 44 | Registro de Riscos | `/compliance/riscos/registro` | **REMOVER** | Funcionalidade avançada. Futuro. |
| 45 | Continuidade | `/compliance/riscos/continuidade` | **REMOVER** | BCP é funcionalidade avançada. Futuro. |
| 46 | Fornecedores | `/compliance/riscos/fornecedores` | **REMOVER** | Gestão de risco de fornecedores. Futuro. |
| 47 | Seguro Cyber | `/compliance/riscos/seguro` | **REMOVER** | Funcionalidade muito nichada. Futuro. |

### Auditoria (5 páginas → 3 páginas)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 48 | Sala de Auditoria | `/compliance/auditoria` | **MANTER** | Hub principal de auditoria. |
| 49 | Logs | `/compliance/auditoria/logs` | **MANTER** | Essencial para rastreabilidade. |
| 50 | Bias/Fairness | `/compliance/auditoria/bias` | **MANTER** | Diferencial do produto. FairnessGuard. |
| 51 | Treinamentos | `/compliance/auditoria/treinamentos` | **REMOVER** | Funcionalidade avançada. Futuro. |
| 52 | SoD (Segregação) | `/compliance/auditoria/sod` | **REMOVER** | Funcionalidade avançada. Futuro. |
| 53 | Exportar | `/compliance/auditoria/exportar` | **MANTER** | Funcionalidade útil para relatórios. |

### Outros Compliance

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 54 | Dashboard Compliance | `/compliance` | **MANTER** | Página central de compliance. |
| 55 | Health Check | `/compliance/health-check` | **REMOVER** | Conteúdo pode ser seção do Dashboard Compliance. |
| 56 | Guardrails IA | `/compliance/guardrails` | **MANTER** | Essencial para governança IA. Diferencial. |

**Resultado Área 4: 8 mantidas (de 21), 13 removidas/simplificadas**

---

## ÁREA 5: CONFIGURAÇÕES GLOBAIS (4 páginas)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 57 | Hub Configurações | `/admin/configuracoes` | **MANTER** | Hub principal de configurações. |
| 58 | Políticas Globais | `/admin/configuracoes/politicas` | **MANTER** | Políticas de segurança, IA, retenção. |
| 59 | Comunicações | `/admin/configuracoes/comunicacoes` | **MANTER** | Matriz de comunicação, webhooks. |
| 60 | Auditoria & Logs | `/admin/configuracoes/auditoria` | **REMOVER** | Redundante com `/compliance/auditoria/logs`. Eliminar duplicidade. |

**Resultado Área 5: 3 mantidas, 1 removida**

---

## ÁREA 6: MONITORAMENTO (1 página)

| # | Página | Caminho | Decisão | Justificativa |
|---|--------|---------|---------|---------------|
| 61 | Saúde dos Agentes IA | `/admin/monitoring/agents` | **MANTER** | Diferencial do produto. Dados reais. |

**Resultado Área 6: 1 mantida**

---

## Páginas Extras (não listadas originalmente)

| Página | Caminho | Decisão | Justificativa |
|--------|---------|---------|---------------|
| Templates de Sistema | `/admin/templates` | **MANTER** | Templates reutilizáveis do sistema. |
| Guardrails IA | `/admin/compliance/guardrails` | **MANTER** | Configuração de guardrails da IA. |

---

## Redundâncias Resolvidas

### 1. Logs em 2 lugares → 1 lugar
- `/compliance/auditoria/logs` permanece (hub de compliance)
- `/configuracoes/auditoria` removido da navegação

### 2. Setup Empresa em 2 contextos → 1 contexto
- `/admin/setup-empresa` (global) → REMOVIDO da navegação
- `/admin/clientes/[id]/setup` (por cliente) → MANTIDO

### 3. Jornada de Recrutamento em 2 contextos → 1 contexto
- `/admin/jornada-recrutamento` (global) → REMOVIDO da navegação
- `/admin/clientes/[id]/jornada` (por cliente) → MANTIDO

### 4. Compliance (34% do admin) → reduzido de 21 para 8 páginas na navegação
- Trust Center: 3 páginas → acessível via botão no Dashboard (0 no menu)
- Controles: 5 páginas → 1 hub com filtros
- Monitoramento: 4 páginas → 2 (alertas + incidentes via links)
- Riscos: 5 páginas → 0 (todo "futuro")
- Auditoria: 5 → 3 (removidos treinamentos e SoD)

---

## Navegação Final (Menu Lateral)

### Sem cliente selecionado:
```
Overview
  - Dashboard Geral
  - Métricas da Plataforma

Gestão de Clientes
  - Lista de Clientes
  - Onboarding Clientes

--- separador ---

Compliance & Segurança
  - Dashboard Compliance
  - Controles
  - LGPD & Privacidade
  - Sala de Auditoria
  - Guardrails IA
  - Saúde dos Agentes

Configurações Globais
  - Políticas Globais
  - Comunicações
  - Templates de Sistema
  - Configurações do Sistema
  - SSO Empresarial
```

### Com cliente selecionado:
```
Operações do Cliente
  - Visão Geral
  - Usuários
  - Setup Empresa
  - Jornada de Recrutamento
  - Integrações
  - Comunicações

Faturamento & Métricas
  - Faturamento
  - Consumo de IA
  - Métricas SaaS

--- separador ---

(mesmos itens de Compliance e Configurações acima)
```

### Abas do cliente (header tabs):
```
Visão Geral | Usuários | Setup | Comunicações | Jornada | Integrações | Faturamento | Consumo IA | Métricas | Conformidade
```

---

## Próximos Passos

1. [x] Navegação atualizada (sidebar + tabs)
2. [x] Contrato de API documentado para time de dev do ats_api (ver `admin-api-contracts.md`)
3. [ ] Endpoints do lia-backend preparados com dados simulados realistas para páginas mantidas
4. [ ] Páginas removidas podem ser excluídas do filesystem em sprint futura
