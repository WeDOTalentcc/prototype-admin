# Guia Canonical · `few_shot_examples` no lia-agent-system

```
═══════════════════════════════════════════════════════════════════════════════════════
  Criado em.....: 2026-05-23 (W4-038 · Sprint X.D)
  Repo..........: Replit lia-agent-system · feat/benefits-prv-canonical
  Arquivos-chave:
    Schema doc......: app/prompts/shared/few_shot_template.yaml
    Sensor CI.......: scripts/check_few_shot_yaml_schema.py
    CLI management..: scripts/manage_few_shots.py
    Domínios YAML...: app/prompts/domains/*.yaml (29 arquivos)
    Serviço auto...: app/services/fewshot_evolution_service.py
═══════════════════════════════════════════════════════════════════════════════════════
```

---

## O que são `few_shot_examples`?

Few-shot examples são exemplos reais de conversas que são injetados no system prompt do
agente antes de ele responder. Eles "mostram" ao LLM o padrão de resposta esperado para
cada domain, melhorando qualidade e consistência.

Cada domain da LIA tem seu próprio arquivo YAML em `app/prompts/domains/<domain>.yaml`
com uma seção `few_shot_examples:`. Esses exemplos são carregados pelo
`FewShotEvolutionService` e injetados no `SystemPromptBuilder`.

**Cap por agent:** máximo 15 exemplos por arquivo (FIFO rotation em auto-evolved).

---

## Schema canonical (obrigatório)

Cada entrada em `few_shot_examples` segue este schema:

```yaml
few_shot_examples:
  - id: "automation-ex-01"
    # Formato: <domain>-ex-NN (manual) ou auto-<audit_log_id[:8]> (auto-evolved)
    # DEVE ser único dentro do arquivo (case-insensitive). Sensor enforça.

    category: "happy_path"
    # Categorias são DOMAIN-SPECIFIC (40+ em uso ativo).
    # Pattern obrigatório: ^[a-z][a-z0-9_]*$ (lowercase + underscore + digits)
    # Exemplos comuns: happy_path, pausa, conflito_horario, candidato_perfeito,
    #                  bias_check, reagendamento, confirmacao, cancelamento,
    #                  erro_input, fallback, etc.
    # RESERVADO: "auto_evolved" — usado pelo FewShotAutoInserter (não usar manual).

    scenario: "Candidato confirma entrevista sem problemas"
    # Descritivo curto (1 linha, < 80 chars). Label human-readable do cenário.

    user_input: "Sim, confirmo presença na entrevista de amanhã às 14h"
    # O que o usuário disse — verbatim ou anonimizado.
    # ATENÇÃO: PII deve ser removida antes de gravar (AnonymizationPipeline no
    # caminho auto-evolved; revisão humana no caminho manual).

    expected_response: |
      Ótimo! Confirmação registrada. ✅
      Entrevista: amanhã às 14h com Carla (RH).
      Lembre de levar documento com foto. Boa sorte! 🍀
    # Resposta ideal do agente. Multilinha via `|` YAML.
    # Inclui formatação, emojis e tom canonical do domain.

    demonstrates:
      - "confirmacao_positiva"
      - "empatia_tone"
    # Tags semânticas (opcional, mas recomendado).
    # Útil para o evolution service deduplicar por similaridade.
```

---

## Domínios disponíveis (29 arquivos)

```
agent_calibration     agent_studio          analysis
analytics             ats_integration       automation
autonomous            candidate_self_service communication
company_settings      culture_analysis      cv_screening
digital_twin          hiring_policy         intent_classification
interview_scheduling  job_creation          job_management
offer                 orchestrator          pipeline
pipeline_transition   recruiter_assistant   recruitment_campaign
sourcing              talent_pool           wsi_evaluation
wsi_interview         wsi_layer2_extraction
```

---

## Como adicionar um exemplo (CLI)

### Via CLI (recomendado para uso manual)

```bash
# SSH no Replit
ssh replit-wedo-0405

cd /home/runner/workspace/lia-agent-system

# Listar exemplos existentes de um domain
python scripts/manage_few_shots.py list --domain automation

# Adicionar exemplo manual
python scripts/manage_few_shots.py add \
  --domain communication \
  --id communication-ex-07 \
  --category confirmacao_entrevista \
  --scenario "Candidato confirma disponibilidade de horário" \
  --user-input "Posso na sexta às 15h" \
  --expected-response "Perfeito! Agendado para sexta às 15h. Enviei confirmação no seu email. 📅" \
  --demonstrates confirmacao,disponibilidade

# Validar todos os YAMLs contra o schema
python scripts/manage_few_shots.py validate

# Validar domain específico
python scripts/manage_few_shots.py validate --domain communication

# Remover auto_evolved antigos (FIFO — mantém os N mais recentes)
python scripts/manage_few_shots.py prune --domain automation --keep-recent 10
```

### Adicionando direto no YAML

Abrir `app/prompts/domains/<domain>.yaml` e adicionar na seção `few_shot_examples:`.
Seguir o schema acima. Depois validar:

```bash
python scripts/check_few_shot_yaml_schema.py
```

---

## Auto-evolution (como funciona)

O `FewShotEvolutionService` em `app/services/fewshot_evolution_service.py` roda
automaticamente via cron job (`app/jobs/tasks/ml.py`) e:

1. Lê `audit_logs` de interações recentes com qualidade alta (score > 0.85)
2. Anonimiza PII via `AnonymizationPipeline`
3. Avalia se o exemplo é diverso o suficiente dos existentes
4. Insere com `category: "auto_evolved"` e `id: "auto-<audit_log_id[:8]>"`
5. Se o cap (15) é atingido, remove o `auto_evolved` mais antigo (FIFO)

**O serviço persiste sinais de learning via `LearningSignalRepository`** (tabela
`learning_signals`, `company_id NOT NULL`, multi-tenant fail-closed). Quando um
exemplo é consumido, `consumed_for_fewshot` flag é marcado.

---

## Sensor anti-regressão (CI)

`scripts/check_few_shot_yaml_schema.py` roda em CI e valida:

| Regra | Descrição |
|-------|-----------|
| `id` único | Dentro do arquivo, case-insensitive |
| `category` pattern | `^[a-z][a-z0-9_]*$` |
| Campos required | `scenario`, `user_input`, `expected_response` non-empty string |
| `demonstrates` | Se presente, deve ser `list[str]` |
| Cap | Máximo 15 exemplos por arquivo (avisa em 12+) |

**Modo atual:** warn-only (baseline tem 7 violations em `wsi_interview.yaml` que
usa schema legado `input/output/competency` em vez de `user_input/expected_response`).
Promover para `--blocking` quando esse arquivo for corrigido.

### Rodar o sensor manualmente

```bash
ssh replit-wedo-0405
cd /home/runner/workspace/lia-agent-system

# Warn-only (default)
python scripts/check_few_shot_yaml_schema.py

# Blocking (exit 1 se violations)
python scripts/check_few_shot_yaml_schema.py --blocking

# Output JSON (para CI tooling)
python scripts/check_few_shot_yaml_schema.py --json
```

---

## Regras de qualidade (resumo)

1. **Sem PII** — nomes reais, CPF, email, telefone devem ser anonimizados antes de gravar
2. **Tom canonical** — `expected_response` deve seguir o tom do domain (profissional para
   RH/admin, conversacional e empático para candidatos)
3. **Cenário diverso** — não duplicar cenários que já existem (o sensor não detecta
   semântica, mas o evolution service tem deduplicação por `demonstrates` similarity)
4. **ID único e descritivo** — `<domain>-ex-NN` para manual; nunca inventar `auto-*`
5. **Cap 15** — se já tem 15, fazer `prune` antes de adicionar (ou deixar o serviço
   fazer FIFO automaticamente)
6. **Commits atômicos** — ao adicionar exemplos manualmente, commitar 1 domain por vez
   com mensagem `feat(few_shot): add <domain> examples for <category>`

---

## Arquivos relacionados

| Arquivo | Função |
|---------|--------|
| `app/prompts/shared/few_shot_template.yaml` | Schema canonical (documentação de contrato) |
| `scripts/check_few_shot_yaml_schema.py` | Sensor CI anti-regressão |
| `scripts/manage_few_shots.py` | CLI para add/list/validate/prune |
| `app/services/fewshot_evolution_service.py` | Auto-evolution service |
| `app/domains/analytics/repositories/learning_signal_repository.py` | Persistência dos sinais |
| `alembic/versions/184_learning_signals.py` | Migration da tabela learning_signals |
| `app/prompts/domains/*.yaml` | 29 arquivos de domain com few_shot_examples |

---

## Baseline de violations (2026-05-23)

```
Total violations: 7
Arquivo: app/prompts/domains/wsi_interview.yaml
Motivo: usa schema legado (input/output/competency) em vez do canonical
        (user_input/expected_response/demonstrates)
Ação: corrigir wsi_interview.yaml e promover sensor para --blocking
```

---

```
═══════════════════════════════════════════════════════════════════════════════════════
  Harness: sensor check_few_shot_yaml_schema.py (warn-only → blocking quando 0 violations)
  Auto-evolution: FewShotEvolutionService + LearningSignalRepository (W3-021 + W4-038)
  Próximo passo: corrigir wsi_interview.yaml schema drift → promover blocking
═══════════════════════════════════════════════════════════════════════════════════════
```
