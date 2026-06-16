# Manutenção do Glossário Central da LIA

> Este documento explica como o glossário funciona, como adicionar termos, como o sync automático opera e como o CI bloqueia PRs com termos indefinidos.

---

## 1. Onde o glossário vive

**Arquivo canônico:** `docs/GLOSSARY.md`

Não existe outro glossário oficial. Se você encontrar terminologia em outro documento (WeDO, audits, ADRs), a fonte de verdade para definição é o `GLOSSARY.md`. Os outros documentos são fontes de extração, não de verdade.

---

## 2. Como o sync automático funciona

O script `scripts/glossary_sync.py` realiza 4 operações:

### 2.1 Varredura de fontes

O sync opera em **dois níveis**:

#### Nível 1 — Termos obrigatórios (bloqueiam CI se sem definição)

| Fonte | O que detecta |
|---|---|
| `CANONICAL_REQUIRED_TERMS` no script | Todos os termos de metodologia da plataforma (WSI, BARS, Bloom, Dreyfus, etc.) |
| `CANONICAL_SIGLAS` no script | Siglas canônicas do domínio (WSI, CBI, STAR, OCEAN, LGPD, etc.) |
| `WeDO/**/*.md` + código | Siglas adicionais mencionadas em documentos e código |

#### Nível 2 — Componentes arquiteturais (stubs, não bloqueiam CI)

| Fonte | O que detecta |
|---|---|
| `lia-agent-system/app/**/*.py` | Classes com sufixo `*Guard`, `*Engine`, `*Orchestrator`, `*Graph`, `*Pipeline`, `*Scorer`, `*Generator`, `*Extractor` |
| `lia-agent-system/app/**/*.yaml` | Nomes de tools do `tool_registry_metadata.yaml` |

### 2.2 Comparação com o glossário atual

- **Novo obrigatório** = termo obrigatório ausente do glossário → **bloqueia CI**
- **Novo arquitetural** = componente detectado mas ausente → stub adicionado (não bloqueia)
- **Termo órfão** = no glossário mas sem referência detectada → warning apenas

### 2.3 Atualização in-place

Para cada termo novo, o script adiciona um stub na seção "Termos pendentes":

```markdown
### NomeDoTermo
| Campo | Valor |
|---|---|
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
...
```

### 2.4 Relatório

Gera `docs/glossary_sync_report.md` com:
- Lista de novos termos adicionados como stubs
- Lista de termos sem definição (bloqueiam CI)
- Lista de termos órfãos (geram warning, não bloqueiam)
- Contagens e metadados

---

## 3. Como rodar localmente

### Opção A — Makefile

```bash
make glossary-sync
```

### Opção B — Direto

```bash
# Atualiza GLOSSARY.md com novos stubs
python3 scripts/glossary_sync.py

# Simula sem modificar arquivos
python3 scripts/glossary_sync.py --dry-run

# Modo CI (falha se há termos sem definição)
python3 scripts/glossary_sync.py --check
```

---

## 4. Como adicionar um termo manualmente

1. Abra `docs/GLOSSARY.md`
2. Encontre a seção alfabética correta (ex.: "## B" para "Bloom")
3. Adicione a entrada seguindo o schema:

```markdown
### NomeOficial
| Campo | Valor |
|---|---|
| **Sigla** | SIGLA ou — |
| **Definição** | Descrição curta (≤ 3 frases). |
| **Categoria** | Scoring | Behavioral | Compliance | Sistema | Tool/Action |
| **Fontes** | `WeDO/documento.md` §seção |
| **Código relacionado** | `caminho/para/arquivo.py` → `NomeClasse` |
| **Owner** | Time responsável |
| **last_updated** | AAAA-MM-DD |
```

4. Commite junto com o código que introduz o termo.

### Regras para nomes de termos

- Use o nome **oficial** — nunca sinônimos
- Para siglas, inclua a expansão: `WSI — Work Suitability Index`
- Para dimensões OCEAN, use o padrão `Abertura (Openness)`
- Siga ordem alfabética dentro de cada seção

---

## 5. Como o CI bloqueia

O workflow `.github/workflows/glossary-sync.yml` roda em todo PR. Ele executa:

```bash
python3 scripts/glossary_sync.py --check
```

**Comportamento:**

| Situação | Resultado CI |
|---|---|
| Termo novo detectado e stub adicionado automaticamente | ⚠️ Warning — CI passa, mas próximo PR bloqueia se não preenchido |
| Termo com `TODO: needs definition` já existente | ❌ **BLOQUEIO** — PR não passa |
| Termos órfãos (no glossário, sem uso no código) | ⚠️ Warning — não bloqueia |
| Tudo ok | ✅ Green |

**Mensagem de bloqueio típica:**

```
❌ [glossary-sync] CI BLOQUEADO — termos sem definição encontrados:
   • NomeDaTermo
   • OutroTermo

Ação necessária: edite docs/GLOSSARY.md e preencha a definição
de cada termo acima (substitua 'TODO: needs definition').
```

---

## 6. Categorias de termos

| Categoria | Exemplos |
|---|---|
| **Scoring** | WSI, BARS, Bloom, Dreyfus, Gate, Rubric, Inflação |
| **Behavioral** | Big Five, OCEAN, Trait, CBI, STAR, Arquétipo |
| **Compliance** | LGPD, EU AI Act, SHA-256, FairnessGuard, PromptInjectionGuard |
| **Sistema** | Bloco A/B, Smart Saturation, Calibration Loop, SystemPromptBuilder |
| **Tool/Action** | Nomes de tools do `tool_registry_metadata.yaml` |

---

## 7. Contacts por categoria de termo

| Categoria | Owner primário | Contato |
|---|---|---|
| Scoring | Data Science + Produto | — |
| Behavioral | Produto + Data Science | — |
| Compliance | Jurídico + Engenharia | — |
| Sistema | Engenharia | — |
| Tool/Action | Engenharia | — |

---

## 8. Integração com system prompts

O `SystemPromptBuilder` (`lia-agent-system/app/shared/prompts/system_prompt_builder.py`) inclui uma seção de terminologia canônica extraída do glossário. Isso garante que o LLM use os termos oficiais e não invente sinônimos.

Os termos injetados no prompt são um subconjunto curado dos mais críticos (WSI, Bloom, Dreyfus, Big Five, Gates, Smart Saturation, etc.) — não o glossário completo, para não exceder o context window.

---

## 9. FAQ

**Q: Posso renomear um termo no glossário?**
A: Sim, mas você também deve atualizar todas as referências no código, docs e system prompts. Use `grep -r "NomeAntigo" .` para encontrar todas as ocorrências.

**Q: O script detecta termos em comentários Python?**
A: Sim, a varredura é por conteúdo de texto, não apenas por AST.

**Q: O que acontece com termos de bibliotecas externas (FastAPI, LangGraph)?**
A: Eles geralmente não têm os sufixos esperados e são ignorados. Se aparecerem como falso positivo, adicione-os a `IGNORE_TERMS` no script.

**Q: O sync modifica definições já preenchidas?**
A: Não. O script apenas adiciona stubs para termos novos. Definições existentes não são tocadas.

**Q: Como desativar o CI para um PR específico?**
A: Adicione o label `skip-glossary-check` ao PR. Use com parcimônia — apenas para PRs de infra que não introduzem novos termos.
