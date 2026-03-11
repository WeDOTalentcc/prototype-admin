---
name: lgpd-data-protection
description: "Compliance LGPD, EU AI Act e proteção de dados na Plataforma LIA conforme Guia v3.3. Use ao criar/modificar funcionalidades que coletam, processam, armazenam ou transmitem dados pessoais de candidatos. Cobre 6 pilares LGPD, PII Masking, consentimento granular, direitos do titular (DSR), EU AI Act high-risk, e compliance multi-framework (SOC-2/SOX/ISO-27001/BCB-498). Referência: attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md"
---

# Proteção de Dados LGPD e Compliance Regulatório

Skill de compliance obrigatória para proteção de dados pessoais na Plataforma LIA. Cobre LGPD, EU AI Act, e frameworks regulatórios.

> **Skills relacionadas:** wedo-governance, screening-compliance, dei-fairness

## 1. Quando Usar

Ao criar ou modificar funcionalidades que coletam, processam, armazenam ou transmitem dados pessoais de candidatos.

---

## 2. Os 6 Pilares LGPD

| Pilar | O que garante |
|-------|---------------|
| **Consentimento** | Granular, versionado, com prova SHA256, revogável a qualquer momento |
| **Minimização** | Apenas dados necessários para a finalidade declarada |
| **PII Masking** | `PIIMaskingFilter` global em todos os loggers antes de persistir |
| **Criptografia** | Fernet (at-rest) + TLS 1.3 (in-transit) |
| **Retenção** | Exclusão automatizada por tipo de dado conforme política |
| **Auditoria** | Trilha de auditoria imutável append-only para todo tratamento |

---

## 3. PII Masking — Regras Obrigatórias

`PIIMaskingFilter` (`app/shared/pii_masking.py`) instalado via `install_global_pii_masking()` no root logger.

Mascara automaticamente: CPF (`***CPF***`), email (`***EMAIL***`), telefone (`***PHONE***`), nomes (`***NAME***`).

**Regras absolutas:**
- NUNCA logar dados pessoais em texto claro
- NUNCA incluir PII em mensagens de erro
- SEMPRE usar `PIIMaskingFilter` em novos loggers
- Secrets em vault (HashiCorp Vault / AWS Secrets Manager) — nunca em `.env` commitado

---

## 4. Consentimento Granular com Prova SHA256

**7 tipos de consentimento por propósito:**

| Tipo | Label | Obrigatório |
|------|-------|-------------|
| `personal_data` | Dados Pessoais | Sim |
| `sensitive_data` | Dados Sensíveis | Sim (quando aplicável) |
| `data_sharing` | Compartilhamento com Clientes | Sim |
| `marketing` | Comunicações Marketing | Não |
| `cookies` | Cookies | Não |
| `analytics` | Analytics | Não |
| `third_party` | Terceiros | Não |

**Prova criptográfica:** cada evento de consentimento (grant, revoke, renew, expire) gera hash SHA256:
```python
combined = f"{consent_version_id}|{subject_email}|{subject_identifier}|{event_type}|{consent_given}|{timestamp.isoformat()}"
proof_hash = hashlib.sha256(combined.encode()).hexdigest()
```

Hash de conteúdo dos termos (`calculate_content_hash`) detecta alterações retroativas.

HTTP **451** quando consentimento obrigatório está ausente.

---

## 5. LgpdCleanupService — Retenção Automatizada

`app/services/lgpd_cleanup_service.py` — job diário de exclusão com dry-run obrigatório.

| Tipo de Dado | Retenção | Critério |
|--------------|----------|---------|
| Candidatos rejeitados/desistentes | **90 dias** | `scheduled_deletion_at` na tabela `candidates` |
| Notas de entrevista / CVs | **180 dias** | Data de upload/criação |
| Logs de screening | **365 dias** | Data de execução do screening |
| Logs de IA (`AiConsumption`) | **365 dias** | `scheduled_deletion_at = NOW() + 365 days` em `record_usage()` |
| Candidatos contratados — contrato/onboarding | **7 anos** | Exigência legal trabalhista |
| Candidatos contratados — CV | **1 ano** | Referência interna |

Fluxo do job: query `scheduled_deletion_at < NOW()` → dry-run → exclusão permanente → log de confirmação.

---

## 6. Direitos do Titular (DSR)

7 direitos LGPD Art. 18 — rota `/admin/compliance/lgpd/portal-titular`:

| # | Direito | SLA |
|---|---------|-----|
| 1 | Confirmação de Existência | 15 dias úteis |
| 2 | Acesso aos Dados | 15 dias úteis |
| 3 | Correção de Dados | 15 dias úteis |
| 4 | Anonimização ou Bloqueio | 15 dias úteis |
| 5 | Eliminação de Dados | 15 dias úteis |
| 6 | Portabilidade (export) | 15 dias úteis |
| 7 | Revogação de Consentimento | Imediato |

Tipos de requisição DSR: `access, rectification, deletion, portability, restriction, opposition, review_automated_decision`.

---

## 7. FRIA — Fundamental Rights Impact Assessment (EU AI Act)

IA em recrutamento = sistema de **alto risco** (Art. 6 + Anexo III EU AI Act). FRIA obrigatório antes do deploy.

Estrutura do RIPD (Relatório de Impacto à Proteção de Dados):

| Seção | Conteúdo |
|-------|----------|
| 1. Identificação | Controlador (WeDOTalent) + DPO nomeado |
| 2. Descrição do Tratamento | Natureza: screening IA \| Escopo: candidatos \| Finalidade: avaliação justa |
| 3. Necessidade e Proporcionalidade | Base legal: Consentimento + Contrato \| Minimização \| Retenção por política |
| 4. Riscos aos Titulares | Discriminação algorítmica, vazamento PII, decisões automatizadas injustas, perfilamento excessivo |
| 5. Medidas Mitigatórias | Bias audit (trimestral), PII masking, criptografia Fernet, TLS 1.3, human oversight, direito de recurso |
| 6. Parecer do DPO | Assinatura + data + próxima revisão |

---

## 8. DPO Management

Rota: `/admin/compliance/lgpd/dpo` — registro de Encarregados conforme LGPD Art. 37.

Campos: nome completo, email, telefone, empresa, status (ativo/inativo), designação DPO Principal, data de nomeação, histórico de alterações.

Canal ANPD: `ouvidoria@anpd.gov.br` | notificação de incidentes via formulário eletrônico ANPD.

---

## 9. EU AI Act Compliance — Alto Risco

`ConfidencePolicyService` implementa os 3 níveis de confiança exigidos para sistemas de alto risco:
- `APPLY_SILENT` (≥ 0.85): aplica sem notificar
- `APPLY_NOTIFY` (0.70–0.84): aplica e notifica o recrutador
- `ASK_USER` (< 0.70): apresenta como sugestão, pede confirmação

---

## 10. Compliance Multi-Framework

| Framework | Cobertura |
|-----------|-----------|
| **LGPD** | Consentimento granular, PII masking, DSR, retenção, DPO |
| **EU AI Act** | FRIA, ConfidencePolicyService, human oversight, auditabilidade |
| **SOC-2** | Controles de segurança, audit logs, acesso restrito |
| **SOX** | Trilha de auditoria imutável, segregação de funções |
| **ISO-27001** | Criptografia, gestão de incidentes, continuidade |
| **BCB-498** | Controles para instituições financeiras reguladas |

30+ páginas admin de compliance em `/admin/compliance/`.

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/lgpd-data-protection` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/lgpd-data-protection.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/lgpd-data-protection/SKILL.md` |

**Quando ativar:**
- Ao criar ou modificar funcionalidades que coletam, processam ou transmitem dados pessoais
- Ao adicionar novos campos de dados de candidatos
- Ao configurar integrações externas que recebem dados pessoais
- Ao implementar ou modificar DSR, consentimento ou políticas de retenção
