# DIAGNÓSTICO JIRA - PLATAFORMA LIA MVP

**Data:** 02 de Fevereiro de 2026  
**Projeto:** WT (wedotalent tasks 2026)  
**Documento de Referência:** `docs/lia-mvp-cards-jira.md`

---

## RESUMO EXECUTIVO

| Métrica | Quantidade |
|---------|------------|
| **Total de cards no documento** | 154 |
| **Total de cards no Jira** | 258 |
| **Cards sincronizados (OK)** | 100 |
| **Cards a CRIAR** | 51 |
| **Cards a AVALIAR exclusão** | 130 |
| **Avisos (obsoletos/pós-MVP)** | 4 |

---

## 1. CARDS A CRIAR (51 cards)

Estes cards estão no documento `lia-mvp-cards-jira.md` mas **não existem** no Jira:

### Wizard Avançado (5 cards novos)
| Código | Título | Tipo |
|--------|--------|------|
| WIZ-009 | Skip Calibração Conversacional | Full-Stack |
| WIZ-010 | Estágio de Salário Interativo | Frontend |
| WIZ-011 | Estágio de Competências | Frontend |
| WIZ-012 | Estágio de Perguntas WSI | Frontend |
| WIZ-013 | Quality Gates WSI | Backend |

### Triagem e Kanban (3 cards novos)
| Código | Título | Tipo |
|--------|--------|------|
| TRI-012 | Serviço de Pré-Qualificação | Backend |
| KAN-009 | Componentes Kanban Modulares | Frontend |
| KAN-010 | Feedback Implícito em Transições | Backend |

### Integrações Twilio (3 cards novos)
| Código | Título | Tipo |
|--------|--------|------|
| INT-TWI-005 | Templates Aprovados Meta | Integração |
| INT-TWI-006 | Status Delivery Reports | Backend |
| INT-TWI-007 | Rate Limiting e Filas | Backend |

### Integrações Microsoft Graph (4 cards novos)
| Código | Título | Tipo |
|--------|--------|------|
| INT-MSG-002 | OAuth Flow Microsoft | Backend |
| INT-MSG-003 | Calendar API | Backend |
| INT-MSG-004 | Teams Meeting API | Backend |
| INT-MSG-006 | Token Refresh | Backend |

### Integrações LLM (9 cards novos)
| Código | Título | Tipo |
|--------|--------|------|
| INT-LLM-001 | Cliente Anthropic Claude | Backend |
| INT-LLM-002 | Cliente Google Gemini | Backend |
| INT-LLM-003 | Router de Modelos | Backend |
| INT-LLM-004 | Fallback entre Modelos | Backend |
| INT-LLM-005 | Gestão de Prompts | Backend |
| INT-LLM-006 | Cache de Respostas | Backend |
| INT-LLM-007 | Monitoramento de Custos | Backend |
| INT-LLM-008 | Rate Limiting LLM | Backend |
| INT-LLM-009 | Logging de Conversas | Backend |

### Integrações WorkOS (7 cards novos)
| Código | Título | Tipo |
|--------|--------|------|
| INT-WOS-001 | Configurar WorkOS Account | Integração |
| INT-WOS-002 | SSO SAML/OIDC | Backend |
| INT-WOS-003 | Directory Sync SCIM | Backend |
| INT-WOS-004 | MFA Enforcement | Backend |
| INT-WOS-005 | User Management SDK | Backend |
| INT-WOS-006 | Webhook de Eventos | Backend |
| INT-WOS-007 | Admin Portal | Frontend |

### Integrações Apify (3 cards novos)
| Código | Título | Tipo |
|--------|--------|------|
| INT-APY-001 | Configurar Apify Account | Integração |
| INT-APY-002 | LinkedIn Scraper Actor | Backend |
| INT-APY-003 | Integração com Sourcing Agent | AI |

### JD e Wizard Avançado (5 cards novos) - Épico 12
| Código | Título | Tipo |
|--------|--------|------|
| JD-001 | Preview de JD com Sugestões LIA | Frontend |
| JD-002 | JD Completo para Publicação | Frontend |
| JDW-001 | Interação com Sugestões LIA | Backend |
| JDW-002 | Análise de Compensação de Mercado | Backend |
| JDW-003 | Insights de Mercado para Vagas | Backend |

### Configurações Avançadas (6 cards novos) - Épico 13
| Código | Título | Tipo |
|--------|--------|------|
| CFG-001 | LIA Field Toggles | Frontend |
| CFG-002 | Verificação de Completude | Backend |
| CFG-003 | Configuração de Jornada | Frontend |
| CFG-004 | Hub de Comunicação | Frontend |
| CFG-005 | Dados da Empresa para LIA | Frontend |
| IMP-001 | Importação Inteligente | Frontend |

### Agentes IA Especializados (6 cards novos) - Épico 15
| Código | Título | Tipo |
|--------|--------|------|
| AGT-001 | Agente Avaliador WSI | AI |
| AGT-002 | Agente de Triagem Curricular | AI |
| AGT-003 | Agente de Agendamento | AI |
| AGT-004 | Orquestrador de Pipeline Chat | AI |
| DAT-001 | Sistema de Solicitação de Dados | Frontend |
| ENT-001 | Análise de Transcrição | Backend |

---

## 2. CARDS A AVALIAR EXCLUSÃO (130 cards)

Estes cards existem no Jira mas **não estão** no documento `lia-mvp-cards-jira.md` atualizado.

### Categorias Identificadas:

#### Cards DEV antigos (tarefas de desenvolvimento genéricas)
- WT-47 a WT-66: Cards de sprints DEV antigas (DEV-S1-xxx, DEV-S2-xxx, etc.)

#### Cards VAG antigos (funcionalidades de vagas excedentes)
- WT-291 a WT-357: Cards VAG-009 a VAG-078 (funcionalidades de vagas que foram consolidadas ou removidas do MVP)

#### Cards CONFIG antigos (configurações admin antigas)
- WT-1037 a WT-1094: Cards SET-xxx, EMP-xxx, MET-xxx, BGL-xxx, INT-xxx, VOZ-xxx (funcionalidades de configuração que foram reestruturadas)

> **AÇÃO RECOMENDADA:** Revisar cada grupo antes de excluir. Alguns podem ter sido renomeados/consolidados em novos cards.

---

## 3. CARDS OBSOLETOS/PÓS-MVP (não criar)

Estes cards estão marcados como obsoletos ou pós-MVP no documento:

| Código | Motivo |
|--------|--------|
| KAN-005 | ⚠️ Obsoleto |
| INT-MSG-001 | 🔄 Consolidado em AGE-001 |
| INT-MSG-005 | 🔄 Pós-MVP |
| INT-MSG-007 | 🔄 Pós-MVP |

---

## 4. CARDS SINCRONIZADOS (100 cards OK)

Os seguintes cards já existem no Jira e correspondem ao documento. Nenhuma ação necessária:

- AUTH-001 a AUTH-004 (4 cards)
- WIZ-001 a WIZ-008 (8 cards)
- MAP-001 a MAP-006 (6 cards)
- WSI-001 a WSI-005 (5 cards)
- TRI-001 a TRI-011 (11 cards)
- SCO-001 a SCO-008 (8 cards)
- GAT-001 a GAT-007 (7 cards)
- TPL-001 a TPL-007 (7 cards)
- AGE-001 a AGE-008 (8 cards)
- NOT-001 a NOT-006 (6 cards)
- KAN-001 a KAN-008 (8 cards, exceto KAN-005)
- TAB-001 a TAB-005 (5 cards)
- PRV-001 a PRV-005 (5 cards)
- VAG-001 a VAG-008 (8 cards)
- INT-TWI-001 a INT-TWI-004 (4 cards)

---

## 5. RECOMENDAÇÕES DE AÇÃO

### Prioridade Alta
1. **Criar os 51 novos cards** identificados na seção 1
2. **Revisar os 130 cards** da seção 2 antes de excluir

### Prioridade Média
3. Verificar se cards antigos têm informações úteis para migrar
4. Arquivar cards que não serão mais utilizados

### Observações
- O documento `lia-mvp-cards-jira.md` define 154 cards MVP + 58 cards Config = 212 cards total
- O Jira atual tem 258 cards, indicando que há cards legados de versões anteriores
- A diferença de 104 cards extras no Jira são principalmente de funcionalidades antigas/expandidas

---

## ARQUIVOS RELACIONADOS

| Arquivo | Descrição |
|---------|-----------|
| `scripts/jira-diagnostic-result.json` | Resultado completo do diagnóstico em JSON |
| `docs/lia-mvp-cards-jira.md` | Documento de referência com 154 cards MVP |
| `docs/configuracoes-admin-cards-jira.md` | Documento com 58 cards de configuração |

---

**Gerado automaticamente pelo script de diagnóstico Jira**  
**Data/Hora:** 02/02/2026 15:32 UTC
