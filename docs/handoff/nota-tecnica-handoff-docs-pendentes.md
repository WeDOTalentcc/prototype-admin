# Nota Técnica — Criar 3 Documentos de Handoff

> **Propósito:** guiar a criação dos documentos `bulk-actions.md`, `candidate-preview.md` e
> `candidate-full-page.md` nos mesmos moldes do `funil-talentos-busca.md`.
>
> **Onde ficam os docs:** Replit `replit-wedo-0405` → `/home/runner/workspace/docs/handoff/`
> (branch `feat/benefits-prv-canonical`). A cópia local espelho fica em
> `/Users/paulomoraes/Documents/Python/.claude/worktrees/focused-pascal-bdeb44/`.
>
> **Referência canônica de estrutura:** `docs/handoff/funil-talentos-busca.md` — ler antes
> de escrever qualquer novo doc.

---

## Template de estrutura (baseado no funil-talentos-busca.md)

Todo handoff doc segue este esqueleto. Adaptar seções conforme o domínio.

```
# Handoff — <Componente>: <Subtítulo>

> **Objetivo deste documento:** [quem pode replicar do zero lendo este doc]
> **Fora de escopo:** [o que deliberadamente não está aqui]
> **Como ler:** Parte A = fluxos (espinha dorsal). Parte B = subcomponentes/abas.
>              Parte C = referência (API, schema, config, checklist).
> **Stack:** [só as partes relevantes ao componente]

## Índice
(Parte A / Parte B / Parte C com âncoras)

# PARTE A — [FLUXOS PRINCIPAIS]
## 1. Visão geral & arquitetura
   - Diagrama mermaid do fluxo principal
   - Princípios para replicação (3-5 bullet points)

## 2. Conceitos-chave
   - Tabelas/matrizes que desmistificam mal-entendidos comuns
   - Avisos ⚠️ "O erro mais comum é..."

## 3. Anatomia da UI
   - Componente raiz + arquivo canônico
   - Mapa de sub-componentes

## 4. Os N fluxos/casos principais
   - Para cada fluxo: O que é · Gatilho · Fluxo passo-a-passo · Regras específicas
   - Bloco 📋 Regras de negócio comuns (consolidadas, não repetidas)

# PARTE B — [SUBCOMPONENTES / ABAS]
## 5..N  Um por subcomponente relevante
   - Estrutura · Endpoints · Estado · Regras de negócio

# PARTE C — REFERÊNCIA
## N+1. Contratos de API
   - Tabela: Método | Rota | Body/Params | Response | Auth

## N+2. Schema (tabelas relevantes)
   - Colunas-chave, FKs, RLS, índices
   - Migrações relevantes

## N+3. Componentes & estado (frontend)
   - Árvore de componentes
   - Stores Zustand envolvidos
   - Hooks canônicos

## N+4. Config & variáveis de ambiente
   - Flags relevantes
   - Relações-chave entre tabelas

## N+5. 📋 Quadro-resumo de regras de negócio
   - Tabela: # | Regra | Onde se aplica | Comportamento | Evidência (arquivo:linha)

## N+6. Checklist de replicação em outro ambiente
   - Lista numerada do que precisa ser implementado para paridade funcional

## N+7. Glossário
   - Termos específicos do domínio

## N+8. Gaps & pontos de atenção
   - O que está incompleto, divergente ou merece atenção futura
```

### Princípios editoriais do funil-talentos-busca.md (manter nos novos docs)

1. **Regras de negócio têm evidência.** Todo item de `📋 Regras de negócio` aponta para
   `arquivo.py:linha` ou `componente.tsx:linha`. Sem evidência = não é regra documentada.
2. **Desmistificar mitos explicitamente.** Bloco `⚠️ "O erro mais comum..."` ou
   `⚠️ "Não confundir X com Y"` onde houver confusão frequente.
3. **Uma fonte da verdade por conceito.** Se algo vale para N fluxos, documentar uma vez
   em seção própria e referenciar (`ver §X`).
4. **Mecanismo, não só existência.** `§5.3.2 Filtros` não lista só "há filtros" —
   lista todos os campos de `TableFilters`, tipos de controle, e que é client-side.
5. **Stack stack stack.** Cada bloco técnico nomeia o arquivo canônico + linha quando relevante.
6. **Rails eliminado = `RAILS_ENABLED=False`.** Qualquer tabela de origem Rails deve ser
   anotada como `[tabela PostgreSQL — origem Rails/ats_api; lida pelo FastAPI]`.

---

## Doc 1 — `bulk-actions.md`

### Objetivo
Permitir replicar do zero a barra de bulk actions e todos os seus 8 modais com paridade
funcional e de regras de negócio.

### Escopo
Todas as ações disponíveis quando ≥1 candidato está selecionado na tabela de resultados do
Funil de Talentos (ou em qualquer listagem de candidatos que use o mesmo `BulkActionsBar`).

### Contexto de onde aparece
- Funil de Talentos (`CandidateSearchResultsView`) — principal superfície
- Listagem de Listas (`lists-tab.tsx`)
- Listagem de Favoritos (`favorites-tab.tsx`)

### Fontes principais para ler no Replit antes de escrever

```bash
# Componente raiz da barra
find /home/runner/workspace/plataforma-lia/src -name "BulkActions*" -o -name "bulk-actions*"

# Cada modal de ação
find /home/runner/workspace/plataforma-lia/src -name "*BulkEmail*" -o -name "*bulk-email*"
find /home/runner/workspace/plataforma-lia/src -name "*WSIScreening*" -o -name "*wsi-screening*"
find /home/runner/workspace/plataforma-lia/src -name "*AddToList*" -o -name "*add-to-list*"
find /home/runner/workspace/plataforma-lia/src -name "*ShareSearch*" -o -name "*share-search*"
find /home/runner/workspace/plataforma-lia/src -name "*AddToVacancy*" -o -name "*add-to-vacancy*"

# Endpoints de bulk no backend
grep -rn "bulk" /home/runner/workspace/lia-agent-system/app/api/v1/ --include="*.py" -l
cat /home/runner/workspace/lia-agent-system/app/api/v1/bulk_actions.py

# FairnessGuard em bulk
grep -n "FairnessGuard\|fairness" /home/runner/workspace/lia-agent-system/app/api/v1/bulk_actions.py

# HITL gate em bulk (7 tools gated)
grep -n "hitl\|HITL\|approval" /home/runner/workspace/lia-agent-system/app/api/v1/bulk_actions.py
```

### Seções que devem existir (além do template)

- **As 8 ações com modal próprio:** para cada uma: gatilho, componente do modal,
  guards/pré-condições ("só se candidato tem email revelado", "só elegíveis para WSI"),
  endpoint backend, estados (loading / sucesso / erro parcial).
- **Seleção parcial vs total:** o que acontece quando só parte dos selecionados atende
  à pré-condição (ex: bulk email com 3/10 sem email revelado).
- **HITL gate:** quais das 8 ações passam pelo gate de aprovação (`LIA_HITL_GATE`).
- **FairnessGuard em bulk:** verificação de notas de rejeição.
- **Regras de escopo:** todas as ações respeitam `company_id` do JWT.

---

## Doc 2 — `candidate-preview.md`

### Objetivo
Permitir replicar o painel lateral de preview de candidato — o componente que abre ao
clicar num candidato nos resultados de busca (e em outras listagens) — com todas as suas
abas, dados exibidos e ações inline.

### Contexto de onde aparece
- Funil de Talentos (painel lateral direito ao clicar na linha)
- Listagem de Listas
- Possivelmente Kanban de vaga (confirmar)

### Fontes principais para ler no Replit antes de escrever

```bash
# Componente raiz do preview
find /home/runner/workspace/plataforma-lia/src -name "*CandidatePreview*" -o -name "*candidate-preview*"
find /home/runner/workspace/plataforma-lia/src -name "*CandidateSidePanel*" -o -name "*candidate-side-panel*"

# Abas do preview
find /home/runner/workspace/plataforma-lia/src -path "*/candidate-preview/*" -o -path "*/candidate-panel/*"

# Hook de dados do preview
grep -rn "useLiaCandidate\|useCandidateDetail\|useCandidate" \
  /home/runner/workspace/plataforma-lia/src --include="*.ts" --include="*.tsx" -l

# Endpoint de detalhe do candidato
grep -rn "GET.*candidate.*{id}\|candidate_detail\|get_candidate_by_id" \
  /home/runner/workspace/lia-agent-system/app/api/v1/ --include="*.py" | head -20

# Score LIA no preview
grep -rn "lia_score\|LIAScore\|lia-score" \
  /home/runner/workspace/plataforma-lia/src --include="*.tsx" -l

# BigFive no preview
grep -rn "BigFive\|big_five\|big-five" \
  /home/runner/workspace/plataforma-lia/src --include="*.tsx" -l

# Screenshots de referência visual (já existem no projeto)
ls /home/runner/workspace/docs/screenshots/candidate-preview* 2>/dev/null || true
```

### Seções que devem existir (além do template)

- **As N abas do preview** (confirmar quais existem lendo o código):
  cada aba com dados exibidos, endpoint de hidratação, estado de loading.
- **Dados sempre visíveis** (header do painel: nome, score, fonte, contato).
- **Ações inline no preview:** ⭐ favoritar, 👍/✖ like-dislike, adicionar à lista,
  abrir página full, revelar contato — com suas regras individuais.
- **PII visibility:** quais campos respeitam `resolve_pii_field_visibility` por papel
  do usuário (campos mascarados vs visíveis por role).
- **Score LIA vs Match Score:** como os dois números coexistem no painel (§11 do funil doc
  explica a diferença — referenciar ou resumir).
- **Expand para página full:** botão/link que abre `/candidatos/[id]` — quando aparece,
  qual o contrato de navegação.

---

## Doc 3 — `candidate-full-page.md`

### Objetivo
Permitir replicar a página completa do candidato (`/candidatos/[id]` ou equivalente),
suas abas, formulários de edição, histórico de interações, seções LGPD e endpoints CRUD.

### Contexto
Esta é a superfície mais rica de dados de um candidato. Mais complexa que o preview:
tem formulários de edição, permissões por papel, e seções que existem só nesta página.

### Fontes principais para ler no Replit antes de escrever

```bash
# Componente raiz da página
find /home/runner/workspace/plataforma-lia/src/app -path "*candidatos*" -o -path "*candidates*" | grep -v node_modules
find /home/runner/workspace/plataforma-lia/src -name "*CandidatePage*" -o -name "*candidate-page*" | grep -v "candidates-page"

# Abas da página full (diferente das abas do preview)
find /home/runner/workspace/plataforma-lia/src -path "*candidate*" -name "*tab*"

# Endpoints CRUD de candidato
cat /home/runner/workspace/lia-agent-system/app/api/v1/candidates.py | head -200
grep -n "def.*candidate\|@router\." /home/runner/workspace/lia-agent-system/app/api/v1/candidates.py | head -40

# Modelo de candidato no banco
cat /home/runner/workspace/lia-agent-system/libs/models/lia_models/candidate.py

# Permissões (RBAC) na página
grep -rn "can_view\|can_edit\|require_role\|UserRole" \
  /home/runner/workspace/lia-agent-system/app/api/v1/candidates.py | head -20

# PII masking na página full
grep -rn "mask_pii\|pii_field_visibility\|resolve_pii" \
  /home/runner/workspace/lia-agent-system/app/api/v1/candidates.py | head -10

# LGPD: histórico de consentimento, erasure
grep -rn "consent\|erasure\|lgpd\|LGPD" \
  /home/runner/workspace/lia-agent-system/app/api/v1/candidates.py | head -20
grep -rn "consent\|erasure" \
  /home/runner/workspace/lia-agent-system/app/domains/candidates/ --include="*.py" -l

# Histórico de interações / linha do tempo
grep -rn "interaction\|activity\|timeline\|history" \
  /home/runner/workspace/lia-agent-system/app/api/v1/candidates.py | head -10
```

### Seções que devem existir (além do template)

- **As N abas da página** (confirmar lendo o código):
  cada aba com dados, formulários, endpoints de save, guards de permissão.
- **Edição inline vs formulário:** quais campos são editáveis, por qual papel (recrutador,
  admin, o próprio candidato via portal).
- **PII por campo:** quais campos são mascarados por papel (integra com
  `pii-field-visibility-por-papel` — referenciar `candidate-preview.md` ou criar seção aqui).
- **Histórico de interações / linha do tempo:** o que aparece, granularidade, endpoints.
- **Seção LGPD:** consentimento, histórico de consentimento, fluxo de erasure (Art. 18
  cascade), o que o candidato pode ver/editar vs o recrutador.
- **Vínculo com vagas:** como candidaturas aparecem nesta página, navegação para o kanban.
- **Score LIA na página full:** mesmas regras do preview ou tem dados adicionais?
- **Tags / Notas:** como funcionam, persistência, multi-usuário.

---

## Metodologia de produção (para cada doc)

1. **Ler o doc de referência** `funil-talentos-busca.md` no Replit para calibrar o nível
   de detalhe esperado.

2. **Rodar os comandos de discovery** listados acima via `ssh replit-wedo-0405` para
   mapear os arquivos canônicos antes de escrever qualquer linha.

3. **Ler os componentes principais** (raiz + sub-componentes mais relevantes) e os
   endpoints backend. Não resumir — capturar nomes exatos de campos, tipos, e lógica de
   guards.

4. **Escrever rascunho seguindo o template** com as seções adaptadas ao domínio.

5. **Verificar regras de negócio** contra o código: cada item do quadro-resumo deve ter
   evidência (`arquivo:linha`).

6. **Commitar nos dois lugares:**
   - Replit: `git commit -m "docs(<nome>): handoff inicial" -- docs/handoff/<nome>.md`
   - Local: cópia espelho em
     `/Users/paulomoraes/Documents/Python/.claude/worktrees/focused-pascal-bdeb44/<nome>.md`

7. **Nunca** `git push` sem autorização explícita do Paulo.

---

## Referências úteis para contexto nos novos docs

- **HITL gate (7 tools gated):** `lia-agent-system/app/domains/candidates/services/` —
  `send_email`, `send_whatsapp`, bulk actions com `LIA_HITL_GATE`.
- **FairnessGuard:** `lia-agent-system/app/shared/compliance/fairness_guard.py` —
  já wired em bulk notes (`bulk_actions.py:322`).
- **PII visibility (pii-field-visibility-por-papel):** implementação em
  `lia-agent-system/app/shared/pii_masking.py` + `candidates_crud.py` (campo a campo).
- **Score LIA vs Match Score:** §11 do `funil-talentos-busca.md` explica as duas escalas.
- **Rails eliminado:** `RAILS_ENABLED=False` no Replit — tabelas `accounts`/`embeddings`
  são PostgreSQL com origem Rails mas lidas/escritas pelo FastAPI.
- **Multi-tenancy:** `company_id` SEMPRE do JWT (`Depends(require_company_id)`), nunca
  do payload. Regra absoluta em todos os endpoints.
