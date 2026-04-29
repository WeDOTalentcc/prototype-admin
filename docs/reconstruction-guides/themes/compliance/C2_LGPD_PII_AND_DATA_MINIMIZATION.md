# Theme C2 — LGPD PII & Data Minimization

**Layer:** Compliance  |  **Card Jira:** 2 (Compliance)
**Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/` no Replit

---

## O que é este tema

PII Masking é a camada que **remove dados pessoais identificáveis** de 2 fluxos críticos:
1. **Logs** — nenhum log registra CPF, email, telefone, nome em texto puro (ADR-006: "No PII in logs")
2. **Prompts LLM** — texto enviado ao Claude/OpenAI passa por PII strip em até 4 layers antes de sair da LIA (LGPD Art. 12 minimização + EU AI Act Art. 13 transparência)

É a implementação operacional de 2 artigos da LGPD: Art. 6 (minimização — usar só dado necessário) + Art. 11 (dados sensíveis — nunca coletar/processar sem base legal específica).

**Boundary com temas irmãos:**
- **C1 Fairness** — PII strip roda ANTES do FairnessGuard L3, não dentro dele (mas L3 chama PII strip antes de mandar ao Haiku)
- **C3 LGPD Consent** — consent é a base legal para processar; C2 é a operacionalização ("uma vez que processo, minimizo")
- **C7 Audit Trail** — audit log NÃO contém PII (só IDs); C2 garante isso
- **I9 Data Layer** — anonimização em exports / backfills

---

## Arquivos conectados (4 total)

### Camada Persona (LLM vê — 2 arquivos)

| Arquivo | Bundle | Como é injetado |
|---------|--------|-----------------|
| `compliance_block.yaml` (seções `decision.lgpd`, `communication.lgpd`, `operational.lgpd`) | LIA_YAMLS_CANONICAL_BUNDLE §shared | `ComplianceDomainPrompt` injeta a variante correta por agent_type |
| `guardrails_block.yaml` (seção `data_safety`) | LIA_YAMLS_CANONICAL_BUNDLE §shared | `GuardrailsDomainPrompt` injeta em todo agent |

**Conteúdo chave:**
- `decision.lgpd`: instrução ao agente sobre minimização + Art. 20 (direito revisão)
- `communication.lgpd`: opt-out do candidato + rate limits + horário permitido (08h-20h dias úteis)
- `operational.lgpd`: versão mínima para agentes sem decisão direta
- `data_safety` (guardrails): "NUNCA exponha CPF, email completo, telefone ou salário em respostas"

### Camada Código (Python — 2 arquivos)

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|------------------|
| `pii_masking.py` | `app/shared/pii_masking.py` | 235 | Masking em 2 contextos: logs (`mask_pii`, `PIIMaskingFilter`) + prompts LLM (`strip_pii_for_llm_prompt` com até 4 layers) |
| `fairness_guard.py` (função `_strip_pii`) | `app/shared/compliance/fairness_guard.py` | — | Chama `strip_pii_for_llm_prompt` antes de invocar Haiku no L3 |

### Integration points

- **Todos os logs** usam `get_masked_logger(__name__)` em vez de `logging.getLogger(__name__)` direto
- **`install_global_pii_masking()`** instala `PIIMaskingFilter` globalmente no startup (main.py)
- **LLM calls** via `LLMProviderFactory` podem invocar `strip_pii_for_llm_prompt` conforme política do provider
- **FairnessGuard L3** (C1) chama PII strip antes de cada request ao Haiku
- **Audit log** (C7) recebe apenas IDs, nunca PII (consequência de `data_safety` + masking global)

---

## Lógica IN → OUT

### Input

**Para logs:**
```python
log_message: str  # mensagem de log arbitrária (pode conter PII)
```

**Para LLM prompts:**
```python
text: str  # texto que vai ser enviado ao LLM (ex.: query + CV do candidato)
```

### Processing

**Fluxo para LOGS** (sempre ativo):

```
mensagem → PIIMaskingFilter (logging filter global) → mask_pii() →
  aplica PII_PATTERNS em ordem: [CPF, EMAIL, PHONE_BR, NAME_IN_LOG]
  → substitui por "***CPF***", "***EMAIL***", "***PHONE***", "***NAME***"
  → log persistido sem PII
```

**Patterns canônicos** (linhas 17-28 de `pii_masking.py`):
- `CPF_PATTERN`: `\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-/]?\d{2}\b`
- `EMAIL_PATTERN`: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
- `PHONE_BR_PATTERN`: `(?<!\d)(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\-\s]?\d{4}(?!\d)`
- `NAME_IN_LOG_PATTERN`: captura `name="..."` / `nome=...` / `candidato=...` / `recruiter=...` / `user=...`

**Fluxo para LLM PROMPTS** (`strip_pii_for_llm_prompt`, até 4 layers):

```
texto → [Flag check: LLM_PROMPT_PII_STRIPPING_ENABLED, default=true]
     ↓
L1 + L3 basic (regex): CPF, email, telefone, RG, CNPJ, ano formatura, idade explícita, endereço
     ↓
L4 opt-in (LLM_PROMPT_PRESIDIO_ENABLED=true):
   Presidio NER para: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, LOCATION, DATE_TIME, NRP
   (NRP = nationality/religion/political group — explicitamente removido)
     ↓
texto limpo → LLM
```

**Padrões canônicos para LLM** (`_LLM_PROMPT_PII_PATTERNS`, verificados via SSH 2026-04-24 em `pii_masking.py`):

| Padrão | Token de substituição |
|--------|----------------------|
| `CPF_PATTERN` | `[CPF REMOVIDO]` |
| `EMAIL_PATTERN` | `[EMAIL REMOVIDO]` |
| `PHONE_BR_PATTERN` | `[TELEFONE REMOVIDO]` |
| `_RG_PATTERN` | `[RG REMOVIDO]` |
| `_CNPJ_PATTERN` | `[CNPJ REMOVIDO]` |
| `_GRADUATION_YEAR_PATTERN` | `[ANO_FORMATURA REMOVIDO]` |
| `_AGE_EXPLICIT_PATTERN` | `[IDADE REMOVIDO]` |
| `_ADDRESS_BAIRRO_PATTERN` | `[ENDEREÇO REMOVIDO]` |

> **Atenção — formato diverge entre logs e LLM:** logs usam `***CPF***`, `***EMAIL***`, `***PHONE***`, `***NAME***` (asteriscos); prompts LLM usam `[TIPO REMOVIDO]` (colchetes + "REMOVIDO"). Nunca confundir os dois contextos ao validar masking.

**Fallback lenient**: se Presidio não instalado OU falha na inicialização, Layer 4 é skipped silenciosamente (texto segue com L1+L3 apenas). Linhas 174-192 de `pii_masking.py` implementam o singleton lazy + fail-safe.

### Output

**Logs:** string com tokens `***CPF***`, `***EMAIL***`, etc.

**LLM prompts:** string sem PII (best-effort; Presidio é opt-in)

### Side effects

- Audit log (C7) captura uso de `strip_pii_for_llm_prompt` com flag status (era pré-strip ou pós-strip?)
- Métricas em `observability.py` (I5): contador `pii_masked_total{layer=L1|L3|L4}`
- Se Presidio falhar carregando → 1 log info ("[PII-L4] presidio_analyzer não instalado — Layer 4 desabilitada")

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Flag `LLM_PROMPT_PII_STRIPPING_ENABLED=false` em prod (acidental) | Lint CI: `check_no_pii_in_logs.py` bloqueia merge se detectar |
| PII detectado em log histórico (pré-masking deployment) | Runbook: retenção + purge job + notificação DPO |
| False positive (regex bloqueia legítimo ex.: número de vaga) | Revisar pattern + adicionar exclusion — Presidio pode ajudar a reduzir |

---

## LGPD Art. 6 — Minimização de Dados Pessoais

**Base legal:** Lei 13.709/2018 Art. 6, II — "adequação: compatibilidade do tratamento com as finalidades informadas ao titular".

**Implementação operacional:**
1. Coletar só o necessário (responsabilidade do feature design, não do PII masking)
2. Uma vez coletado, **nunca expor** em outputs além do necessário:
   - Log não guarda PII (global filter)
   - LLM prompt é stripped (L1-L4)
   - Candidate portal (C4) tem `_FORBIDDEN_FIELDS` SSoT
   - Audit log (C7) tem só IDs

**Texto canônico em `compliance_block.yaml` decision.lgpd** (citar verbatim no dev handoff):
> "Não colete ou exponha dados pessoais desnecessariamente (Art. 6 LGPD — minimização)"

---

## LGPD Art. 11 — Dados Sensíveis

**Base legal:** Lei 13.709/2018 Art. 11 — lista fechada: origem racial/étnica, convicção religiosa, opinião política, filiação sindical, organização de caráter religioso/filosófico/político, saúde, vida sexual, genéticos, biométricos.

**Interseção com LIA:**
- 14 atributos protegidos de C1 incluem: raça/etnia, religião, orientação sexual, saúde, filiação sindical → **todos sensíveis**
- Tratamento: C1 bloqueia em filtros; C2 masca em logs/prompts; C3 exige consentimento específico
- Armazenamento: campos sensíveis no DB têm `is_sensitive=True` flag; audit de acesso em C7

**Texto canônico (`compliance_block.yaml`):**
> "Anonimize scores comportamentais brutos em outputs visíveis ao candidato"

---

## Presidio (Layer 4) — NER opt-in

**Por que opt-in:**
- Presidio adiciona dependência pesada (spaCy + modelos NER)
- Latência adicional (~100-300ms por call)
- Footprint de memória: ~500MB carregado
- Útil para textos longos (CVs, transcrições), menos crítico para queries curtas

**Entidades removidas** (`_PRESIDIO_ENTITIES` linha 196-199):
- `PERSON` — nomes
- `EMAIL_ADDRESS` — complementa regex
- `PHONE_NUMBER` — complementa regex
- `LOCATION` — endereços, cidades, bairros
- `DATE_TIME` — datas (útil para idade inferida)
- `NRP` — nationality/religion/political → complementa C1 (atributos protegidos)

**Como ativar:**
```bash
# .env
LLM_PROMPT_PRESIDIO_ENABLED=true
LLM_PROMPT_PII_STRIPPING_ENABLED=true  # (default)

# requirements
pip install presidio-analyzer spacy
python -m spacy download pt_core_news_sm  # modelo PT-BR
```

---

## Instruções para Claude Code / Cursor

### "Implementa PII masking no v5"

```
1. COPIE pii_masking.py (235L) ipsis litteris para <v5>/shared/pii_masking.py

2. INSTALE global filter no startup:
   # main.py (ou equivalente)
   from app.shared.pii_masking import install_global_pii_masking
   install_global_pii_masking()

3. SUBSTITUA TODOS os `logging.getLogger(__name__)` por `get_masked_logger(__name__)`:
   # scripts/check_no_pii_in_logs.py detecta violações

4. CONFIGURE .env:
   LLM_PROMPT_PII_STRIPPING_ENABLED=true     # obrigatório
   LLM_PROMPT_PRESIDIO_ENABLED=true          # opcional (recomendado para textos longos)

5. INSTALE Presidio (opcional, se Layer 4 ativo):
   pip install presidio-analyzer spacy
   python -m spacy download pt_core_news_sm

6. INTEGRE com LLM calls:
   from app.shared.pii_masking import strip_pii_for_llm_prompt
   prompt = strip_pii_for_llm_prompt(raw_prompt)
   response = await llm_provider.call(prompt)

7. GARANTA que FairnessGuard L3 (C1) chama strip antes de Haiku:
   # fairness_guard.py linha do check_semantic() deve ter:
   text = strip_pii_for_llm_prompt(text)

8. VERIFIQUE:
   - scripts/check_no_pii_in_logs.py passa (zero logs com getLogger direto)
   - Logs produzidos contêm "***CPF***" / "***EMAIL***" em texts com PII
   - Layer 4 Presidio carrega sem erros (ou fails gracefully)
```

### "Adiciona PII masking em uma feature nova"

```
Se feature produz logs:
  → Usar get_masked_logger, não logging.getLogger direto

Se feature envia texto ao LLM:
  → Wrap com strip_pii_for_llm_prompt antes do call
  → Exceção: chamadas internas de debug (já cobertas por filter global)

Se feature armazena em DB:
  → Campos sensíveis com column attribute is_sensitive=True
  → Audit trigger em ON SELECT para esses campos
  → Retenção conforme política LGPD (C3)

Se feature produz export:
  → Aplicar mask_pii em texto livre antes do write
  → Confirmar com DPO antes de release
```

### Setup em CLAUDE.md

```markdown
## Compliance: PII Masking (LGPD Art. 6, 11)

- **Logs:** SEMPRE `get_masked_logger(__name__)`. Nunca `logging.getLogger`.
- **LLM prompts:** `strip_pii_for_llm_prompt(text)` antes de cada call (exceto se já wrapped pelo provider factory)
- **DB:** campos sensíveis com `is_sensitive=True` + audit de acesso
- **Flag:** `LLM_PROMPT_PII_STRIPPING_ENABLED=true` em prod (default true)
- **Presidio:** opt-in via `LLM_PROMPT_PRESIDIO_ENABLED=true` para textos longos

Consultar `themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md` antes de mudar pii_masking.py ou adicionar log/LLM call novo.
```

### Setup em `.cursor/rules/pii-masking.mdc`

```
---
description: "C2 PII Masking — LGPD Art. 6 + Art. 11"
alwaysApply: false
---

Quando o usuário pedir para implementar logs, LLM calls, data exports, ou manipular dados de candidato:

1. Leia themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md
2. USE `get_masked_logger` em vez de `logging.getLogger`
3. WRAP LLM prompts com `strip_pii_for_llm_prompt`
4. NUNCA sugerir log direto com nome/email/CPF/telefone em string formatada
5. Presidio Layer 4 é opt-in — não forçar instalação se feature é leve
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Class names e namespaces
- Paths de arquivo
- Se v5 não usa Presidio, skipar Layer 4 (L1+L3 básico já cobre CPF/email/telefone)
- Modelo spaCy pode variar por idioma (pt_core_news_sm, en_core_web_sm)
- Token de substituição (`***CPF***` pode virar `[CPF]`, `<CPF>`, etc.)
- Adicionar patterns específicos do país (ex.: SSN para EUA, NIF para PT)

### NÃO pode adaptar (base legal ou arquitetural)

| Invariante | Por quê | Consequência se violar |
|-----------|---------|------------------------|
| PII NUNCA em logs de produção | ADR-006 + LGPD Art. 6 | Vazamento via log aggregator (Sentry, Datadog) |
| `strip_pii_for_llm_prompt` antes de LLM externo | LGPD Art. 12 (minimização em sistemas de IA) | PII sai para provider terceiro → breach |
| Flag `LLM_PROMPT_PII_STRIPPING_ENABLED` default `true` | Evita downgrade acidental de segurança | Regressão silenciosa |
| NRP Presidio habilitado (nationality/religion/political) | Complementa C1 (atributos protegidos) | Dados sensíveis LGPD Art. 11 expostos |
| Global filter instalado antes de qualquer log | Garantia de que NENHUM log escapa | Log de startup pode vazar |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `pii_masking.py` copiado/adaptado e presente
- [ ] **(P0)** `install_global_pii_masking()` chamado no startup
- [ ] **(P0)** Lint `check_no_pii_in_logs.py` passa (zero `logging.getLogger` direto)
- [ ] **(P0)** `LLM_PROMPT_PII_STRIPPING_ENABLED=true` em `.env` de produção
- [ ] **(P0)** `strip_pii_for_llm_prompt()` invocado antes de cada LLM call externo
- [ ] **(P0)** FairnessGuard L3 chama strip antes de invocar Haiku
- [ ] **(P1)** `LLM_PROMPT_PRESIDIO_ENABLED=true` em prod (se textos longos existirem)
- [ ] **(P1)** Presidio dependency instalada + modelo spaCy baixado
- [ ] **(P1)** Patterns customizados para country-specific IDs (além de CPF/Brasil)
- [ ] **(P1)** Campos sensíveis do DB marcados com `is_sensitive=True`
- [ ] **(P2)** Métricas `pii_masked_total` expostas no Prometheus
- [ ] **(P2)** Alertas quando Presidio falhar carregar 3× consecutivas

---

## Gotchas e erros comuns

| Sintoma | Causa raiz | Como evitar |
|---------|-----------|-------------|
| Log em prod mostra email | Dev usou `logging.getLogger` em vez de `get_masked_logger` | Lint bloqueia: `scripts/check_no_pii_in_logs.py` |
| Log em startup vaza PII | `install_global_pii_masking()` foi chamado DEPOIS dos primeiros logs | Mover para topo do `main.py` antes de qualquer import que logue |
| Presidio não carrega | Modelo spaCy não instalado | `python -m spacy download pt_core_news_sm` |
| Prompt LLM ainda tem PII | Provider factory não aplica strip | Confirmar que wrapper está antes do call, não depois |
| Regex consome regex-heavy request (ReDoS) | PHONE_BR_PATTERN é complexa | Limitar tamanho do input (max 100KB); timeout de 5s no strip |
| False positive em vaga (número virou "CPF") | CPF_PATTERN é genérico | Adicionar exclusion ou usar Presidio que entende contexto |
| Audit log tem PII (regressão) | Campo novo não passou por masking | Schema de audit limita a campos IDs-only; PR review catch |

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| Mask basic patterns | `tests/unit/test_pii_masking.py::test_mask_all_types` | CPF + email + phone + name → todos mascarados |
| Mask no log record | `tests/unit/test_pii_masking.py::test_filter_integration` | Log record via PIIMaskingFilter → output sem PII |
| Strip for LLM prompt L1 | `tests/unit/test_pii_strip_llm.py::test_l1_regex` | Regex capture — CPF/email/phone/RG/CNPJ |
| Strip for LLM prompt L3 | `tests/unit/test_pii_strip_llm.py::test_l3_quasi_id` | Ano formatura, idade explícita, endereço |
| Strip for LLM prompt L4 Presidio on | `tests/unit/test_pii_strip_llm.py::test_l4_presidio_enabled` | PERSON, LOCATION detectados |
| Strip for LLM prompt L4 Presidio off | `tests/unit/test_pii_strip_llm.py::test_l4_presidio_disabled` | Fail-safe: texto retorna intacto (só L1+L3 aplicado) |
| FairnessGuard L3 chama strip | `tests/integration/test_fairness_l3_pii_strip.py` | Haiku recebe texto sem PII |
| Global filter install | `tests/integration/test_global_pii_install.py` | Primeiro log após `install_global_pii_masking` sai mascarado |
| Lint check | `scripts/check_no_pii_in_logs.py` | CI bloqueia PR com `logging.getLogger` direto |

---

## Referências

### Bundles verbatim
- `LIA_YAMLS_CANONICAL_BUNDLE.md` §Parte 1 (compliance_block.yaml + guardrails_block.yaml)

### Reconstruction guides
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` **BLOCO E** — pii_masking.py verbatim (235 linhas)
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.2 C1 (integração com FairnessGuard L3)

### Handoff dev
- `COMPLIANCE_DEV_HANDOFF_2026-04-23.md` — invariante #4 (PII nunca em logs)

### Regulatório
- **LGPD Art. 6** — minimização de dados
- **LGPD Art. 11** — dados sensíveis (lista fechada)
- **LGPD Art. 12** — minimização em sistemas de IA
- **EU AI Act Art. 13** — transparência em high-risk AI systems
- **eu-ai-act-technical-documentation-pt.md** §4.2 (PII strip como mitigação de risco)

### Dependências externas
- `presidio-analyzer` (Microsoft) — NER-based PII detection
- `spacy` + `pt_core_news_sm` — modelo de língua PT-BR

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit em `lia-agent-system/`*
