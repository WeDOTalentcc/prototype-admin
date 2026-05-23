<!-- /autoplan restore point: /Users/paulomoraes/.gstack/projects/Python/main-autoplan-restore-20260523-123038.md -->
# Plano canonical — Candidato 2 surfaces (Drawer + Page dual-mode)

**Owner:** Paulo
**Versão:** V3 (reescrito 2026-05-23 após decisão de eliminar Surface 3 / Caminho B / absorção)
**Escopo:** Replit (lia-agent-system FastAPI + plataforma-lia Next.js). NÃO toca GitHub canonical. NÃO considera migração `recruiter_agent_v5`.
**Status:** Awaiting approval to execute

---

## 1. Decisão central (Paulo, 2026-05-23)

**Surface 3 (rota standalone `/funil-de-talentos/candidato/[id]/` como entidade separada) sai.** É legado.

**Mas a URL `/funil-de-talentos/candidato/[id]` continua existindo** porque Paulo acessa via deep-link (compartilhamento de candidato).

**Caminho B (absorção)** vence: o código limpo de Surface 3 migra pra Surface 2. Não desperdiça trabalho bom.

**Resultado:** 2 surfaces propositalmente distintas + 1 eixo de dados comum.

---

## 2. Arquitetura alvo

```
                 EIXO DE DADOS COMUM
                 (hooks + endpoints canonical + building blocks)
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
           ┌──────▼──────┐                 ┌──────▼──────┐
           │  Surface 1  │                 │  Surface 2  │
           │   DRAWER    │                 │    PAGE     │
           │  (kanban)   │                 │   dual-mode │
           │             │                 │             │
           │ Read-only + │                 │ MODAL mode: │
           │   pipeline  │                 │  do kanban  │
           │   decision  │                 │             │
           │             │                 │ PAGE  mode: │
           │             │                 │ rota /funil/│
           │             │                 │ candidato/  │
           │             │                 │ [id] (URL)  │
           │             │                 │             │
           │             │                 │ Read + EDIT │
           │             │                 │ (lápis D7)  │
           └─────────────┘                 └─────────────┘
                ✅                                ✅
```

---

## 3. Estado real (auditado 2026-05-23)

### Surface 1 — Drawer (`<CandidatePreview>`)
- Wrapper: `src/components/candidate-preview.tsx`
- Pasta: `src/components/candidate-preview/` (22 arquivos)
- Status: ~95% canonical, **1 bug P0** (proxy Files inexistente)

### Surface 2 — Page (`<CandidatePage>`) — atualmente só modal
- Wrapper: `src/components/candidate-page.tsx`
- Pasta: `src/components/candidate-page/` (6 arquivos)
- Status: mock pesado, ZERO edit
- **Vai virar dual-mode após F4**

### Surface 3 — Rota standalone (a ser absorvida)
- Pasta: `src/app/[locale]/(dashboard)/funil-de-talentos/candidato/[id]/`
- Status: ~95% wired, building blocks corretos, **será absorvida pela Surface 2 em F3**
- A rota Next sobrevive (em F4) mas com novo conteúdo: renderiza `<CandidatePage mode="page" />`

### Building blocks atômicos
- `src/components/candidate-profile/` (6 arquivos) — Avatar, ScoreBadge canonical 0-10, SkillsList, ContactActions, ProfileExperienceSection, ProfileEducationSection
- Status: canonical, ambas as surfaces vão usar após F1

---

## 4. Matriz cross-surface (estado atual vs alvo)

### Estado ATUAL

| Tab/Recurso | Surface 1 (Drawer) | Surface 2 (Page Modal) | Surface 3 (Rota — será absorvida) |
|---|---|---|---|
| Profile | ✅ wired (sub-cards próprios) | ⚠️ wired, sem building blocks | ✅ wired + building blocks |
| Activities | ✅ wired (3 fontes Rails) | 🔴 mock 7 itens | ✅ wired `/candidates/[id]/activities` |
| Files | 🔴 proxy `/data_files` **inexistente** | 🔴 7 cards JSX hardcoded | ✅ wired `/candidates/[id]/files` |
| Opinions | ✅ wired | ⚠️ endpoint divergente | ✅ wired |
| WSI Score | ✅ 0-10 canonical | 🔴 0-100 legacy (3 locais) | ⚠️ 0-100 em 1 local |
| ActionBar | ✅ presente | — propositalmente ausente | — propositalmente ausente |
| PipelineDecisionBar | ✅ presente | — propositalmente ausente | — propositalmente ausente |
| Modal vídeo | ✅ ScreeningMediaModal | 🔴 placeholder estático | ✅ via outros modais |
| Modal LIA Chat | ✅ wired | 🔴 stub teatral | ✅ via UnifiedCommunicationModal |
| Edit (lápis) | N/A (drawer = read-only) | ❌ inexistente | ⚠️ parcial (notas) |

### Estado ALVO (após plano)

| Tab/Recurso | Surface 1 (Drawer) | Surface 2 (Page dual-mode) |
|---|---|---|
| Profile | ✅ wired + building blocks canonical (boy scout) | ✅ wired + building blocks |
| Activities | ✅ wired | ✅ wired (absorvido de S3) |
| Files | ✅ wired (proxy corrigido) | ✅ wired (absorvido de S3) |
| Opinions | ✅ wired endpoint canonical | ✅ wired (absorvido de S3) |
| WSI Score | ✅ 0-10 (já está) | ✅ 0-10 |
| ActionBar | ✅ presente | — (propositalmente ausente) |
| PipelineDecisionBar | ✅ presente | — (propositalmente ausente) |
| Modal vídeo | ✅ ScreeningMediaModal | ✅ ScreeningMediaModal (reusado) |
| Modal LIA Chat | ✅ canonical | ✅ canonical (reusado de S1 ou via lia-float-context) |
| Edit (lápis) | N/A (read-only por design) | ✅ inline em campos de Profile |

---

## 5. Eixo de dados canonical

### Hooks compartilhados (criar/consolidar)
```
useCandidate(id)                — dados gerais
useCandidateFiles(id)           — files
useCandidateOpinions(id)        — opinions
useCandidateActivities(id)      — activities
useCandidateAnalysis(id)        — CV analysis
useCandidateFieldUpdate(id)     — edit canonical
useCandidateBigFive(id)         — Big Five 0-10
```

### Endpoints canonical decididos
| Recurso | Endpoint canonical |
|---|---|
| Files | `/api/backend-proxy/candidates/[id]/files?company_id=` |
| Files upload | `POST /api/backend-proxy/candidates/[id]/files` |
| Files delete | `DELETE /api/backend-proxy/candidates/[id]/files/[attachmentId]` |
| Activities | `/api/backend-proxy/candidates/[id]/activities?company_id=` |
| Opinions history | `/api/backend-proxy/opinions/candidate/[id]/history?company_id=` |
| Opinions summary | `/api/backend-proxy/opinions/candidate/[id]/summary?company_id=` |
| CV Analysis | `/api/backend-proxy/lia/profile-analysis/candidate/[id]?company_id=` |
| CV Analysis create | `POST /api/backend-proxy/lia/profile-analysis` |
| Update (full) | `PUT /api/backend-proxy/candidates/[id]` |
| Update (via LIA) | `POST /api/backend-proxy/chat/actions/candidate-field-update` |
| Favorite | `POST/DELETE /api/backend-proxy/candidates/[id]/favorite` |
| Hide | `PUT /api/backend-proxy/candidates/[id]/hide` |
| Stage | `PATCH /api/backend-proxy/candidates/[id]/stage` |

### Building blocks canonical (em `src/components/candidate-profile/`)
- `<CandidateAvatar>` — foto + iniciais fallback
- `<CandidateScoreBadge>` — WSI 0-10 com cores canonical
- `<CandidateSkillsList>` — chips + overflow
- `<CandidateContactActions>` — email/phone/linkedin
- `<ProfileExperienceSection>` — experiências profissionais
- `<ProfileEducationSection>` — formação
- `<EditableField>` (criar em F5) — wrapper de edit inline para qualquer campo

---

## 6. Decisões fechadas (audit trail consolidado)

| # | Decisão | Resposta |
|---|---|---|
| D2 | Grid fake | **Eliminar** |
| D3 | Migração `recruiter_agent_v5` | **Ignorar — Replit é foco** |
| D4 | Tab order | **Default inteligente** |
| D5 | File card sem triagem | **Metadata + chip "sem análise"** |
| D6 | Surface 3 destino | **Auditar → eliminar (legado)** |
| D7 | Edit pattern | **Inline lápis por campo** |
| D9 | Endpoint Files canonical | **`/candidates/[id]/files`** |
| D10 | Surface canonical referência | **Surface 3 (código limpo) absorvido em Surface 2** |
| D14 | Framing 3 surfaces / 2 surfaces | **2 surfaces (Drawer + Page dual-mode)** |
| D15 | Surface 2 vs Surface 3 | **"São a mesma coisa" — consolidar** |
| D17 | Rota `/funil-de-talentos/candidato/[id]` | **Preservar** (Paulo acessa via URL/link) |
| D18 | Caminho A vs B | **B — Absorção** |

---

## 7. Princípios não-negociáveis

1. **2 surfaces propositalmente diferentes**, mesmo eixo de dados.
2. **Não inventar métrica que o backend não devolve.**
3. **Análise/parecer vive na triagem, não no arquivo.**
4. **Building blocks atômicos** em `candidate-profile/` são canonical.
5. **Multi-tenancy via JWT**, nunca payload.
6. **WSI score = 0-10** canonical via `CandidateScoreBadge` (Task #512).
7. **LGPD/ADR-001:** sem PII fictícia, sem campos sensíveis editáveis (race/gender/marital/religion/health), sem SQL inline.
8. **Design tokens v4.2.2** zero `bg-blue-*`, zero hex hardcoded.
9. **Edit pattern = lápis inline por campo** (Surface 2 dual-mode — não Surface 1 drawer).
10. **Surface 1 drawer permanece read-only** (decisão de pipeline acontece lá, não edit).
11. **Replit é foco** — não tocar GitHub canonical, não considerar v5 migration.

---

## 8. Fases (6 fases, 28-37h total)

### F0 — Mapa de Verdade (4-5h) — audit + contracts

**Objetivo:** congelar contratos canonical antes de mexer em código.

**Entregáveis:**
- Snapshots JSON de cada endpoint canonical (executar com candidato de teste no Replit)
- Zod schemas em `src/schemas/candidate-canonical.zod.ts`:
  - `CandidateFile`, `Opinion`, `Activity`, `AiFeedback`, `CvAnalysis`
- SWR cache key matrix por hook:
  - `["candidate", id]`, `["candidate-files", id]`, `["candidate-opinions", id]`, etc.
  - `dedupingInterval: 30000`, `revalidateOnFocus: false`
- LGPD erasure cascade probe (candidato deletado → data_files/opinions/profile-analysis cascateiam?)
- Edit infra audit:
  - O que `PUT /candidates/[id]` aceita como partial update?
  - `POST /chat/actions/candidate-field-update` schema?
  - RBAC: quem pode editar o quê?
  - Audit trail de field changes existe?
- LGPD field policy: lista de campos que NÃO podem ser editáveis (race, gender, marital, religion, health, age below 18)
- Surface 1 Files bug: rodar Replit dev, confirmar se [useCandidateFiles.tsx:83](plataforma-lia/src/components/candidate-preview/useCandidateFiles.tsx:83) retorna 404 ou dado vazio

**Sensor permanente:** `tests/contract/test_candidate_canonical_contracts.ts` — snapshot do shape de cada endpoint.

**Gate:** Paulo confirma endpoint update preferred (PUT direto vs candidate-field-update) e LGPD field policy.

---

### F1 — Building blocks `candidate-profile/` canonical (3-4h)

**Objetivo:** consolidar 6 building blocks como única fonte para Surface 2 (e opcionalmente Surface 1).

**Red (testes que falham):**
- `CandidateScoreBadge.test.tsx` — escala 0-10, tiers (≥7.5 verde / ≥6 amarelo / <6 vermelho)
- `ProfileExperienceSection.test.tsx` — renderiza N experiences
- `ProfileEducationSection.test.tsx` — idem
- `CandidateAvatar.test.tsx` — fallback iniciais
- `CandidateSkillsList.test.tsx` — maxVisible + overflow
- `CandidateContactActions.test.tsx` — email/phone/linkedin disponibilidade

**Green:** garantir props mínimas + estados loading/empty/error + `aria-label`/`aria-hidden`.

**Refactor (boy scout):** se sub-cards de Surface 1 (`candidate-preview/Profile*`) podem usar building blocks também, fazer. Senão, documentar.

**Sensor:** `check_candidate_score_uses_canonical_badge.ts` — bloquear `/100` em `candidate-*` (exceto docstrings).

---

### F2 — P0 transversais (3-4h)

**Por que cedo:** bugs ativos em produção.

**Parte (a) — Fix Surface 1 Files broken:**
- Red: test valida `useCandidateFiles` chama proxy existente + retorna lista.
- Green: trocar [useCandidateFiles.tsx:83](plataforma-lia/src/components/candidate-preview/useCandidateFiles.tsx:83) de `/data_files?reference_type=` para `/candidates/[id]/files`.
- Adapter de response shape se necessário.

**Parte (b) — WSI 0-100 → 0-10 cross-surface (4 locais):**
1. [candidate-page.tsx:149](plataforma-lia/src/components/candidate-page.tsx:149) `liaScore || 92` → remover fallback
2. [useCandidatePageCore.tsx:402](plataforma-lia/src/components/candidate-page/useCandidatePageCore.tsx:402) `getScoreColor` thresholds → usar `getWsiScoreColor` canonical
3. [useCandidatePageCore.tsx:330](plataforma-lia/src/components/candidate-page/useCandidatePageCore.tsx:330) `Nota: .../100` → `Nota: .../10`
4. [CandidatoOpinionsTab.tsx:188](plataforma-lia/src/app/[locale]/(dashboard)/funil-de-talentos/candidato/[id]/components/CandidatoOpinionsTab.tsx:188) `Score: .../100` → `Score: .../10`

Adapter para legacy: se opinion antigo no DB tiver score 0-100, dividir por 10 com confidence flag.

**Sensor:** `check_no_orphan_proxies.ts` + `check_candidate_score_uses_canonical_badge.ts` (já criados em F1).

---

### F3 — Absorção Surface 3 → Surface 2 (6-8h) ⭐ pivot

**Objetivo:** mover código limpo de `/funil-de-talentos/candidato/[id]/` para `src/components/candidate-page/`. Surface 2 herda qualidade.

**Estratégia:**
1. **Copiar** (não mover ainda):
   - `funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx` → `candidate-page/CandidatePageProfileTab.tsx` (substituindo o atual mock)
   - `funil-de-talentos/candidato/[id]/components/CandidatoActivitiesTab.tsx` → `candidate-page/CandidatePageActivitiesTab.tsx`
   - `funil-de-talentos/candidato/[id]/components/CandidatoFilesTab.tsx` → `candidate-page/CandidatePageFilesTab.tsx`
   - `funil-de-talentos/candidato/[id]/components/CandidatoOpinionsTab.tsx` → `candidate-page/CandidatePageOpinionsTab.tsx`
   - `funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx` → `candidate-page/useCandidatePageCore.tsx` (substituindo o atual com mocks)
2. **Adaptar imports** dos componentes copiados:
   - Building blocks `candidate-profile/*` permanecem
   - Imports relativos viram absolutos
3. **Atualizar `src/components/candidate-page.tsx`** (wrapper) para consumir os novos componentes
4. **Remover mocks antigos:**
   - `activities = [...]` array do hook
   - `aiPredictions = [...]`
   - 7 cards JSX do FilesTab
   - Fallback `liaScore || 92`
   - Modal vídeo placeholder
   - Modal LIA chat stub
5. **Testes:** preservar testes de Surface 3 (renomear) + adicionar testes faltantes
6. **Snapshot test** garante render correto antes e depois

**Sensors:**
- `check_no_hardcoded_candidate_mocks.ts` (nomes Maria Oliveira/Carlos Mendes/Ana Silva/Roberto Silva + arquivos Apresentacao_Pessoal/Triagem_Voz)
- `check_no_fake_ai_analysis.ts` (objeto literal `{confidence, communication, clarity, enthusiasm}`)
- `check_no_hardcoded_arrays.ts` (array literal `[{user, timestamp, ...}]` ou `[{name, type, size}]`)

---

### F4 — Surface 2 dual-mode + rota preservada (3-4h)

**Objetivo:** Surface 2 funciona como modal (do kanban) E como página (da rota standalone).

**Mudanças no `CandidatePage` wrapper:**
```tsx
interface CandidatePageProps {
  candidate: Record<string, unknown>
  mode?: 'modal' | 'page'  // default 'modal'
  isOpen?: boolean         // só relevante em modo modal
  onClose?: () => void     // só relevante em modo modal
  onBackToKanban?: () => void  // só modal
  // ... callbacks de ação
}
```

**Comportamentos por modo:**
- `mode="modal"`: render como overlay (z-30 atual), exige `isOpen`, header tem [X] + [< Voltar]
- `mode="page"`: render como página normal (sem `fixed inset-0`), header tem só [< Voltar pro Funil]

**Rota `/funil-de-talentos/candidato/[id]/page.tsx`:**
```tsx
export default function CandidateProfilePage({ params }: { params: { id: string } }) {
  const { id } = params
  const { candidate, loading, error } = useCandidate(id)
  if (loading) return <Loader />
  if (error || !candidate) return <NotFound />
  return <CandidatePage candidate={candidate} mode="page" />
}
```

**Cleanup:**
- Deletar pasta `src/app/[locale]/(dashboard)/funil-de-talentos/candidato/[id]/components/`
- Deletar `CandidatoDetailClient.tsx`, `useCandidatePageCore.tsx` da pasta da rota (absorvidos em F3)
- Manter só `page.tsx` + `layout.tsx` na rota

**Sensor:** `check_no_orphan_routes.ts` — rotas que importam de `/funil/.../components/` ou usam `useCandidatePageCore` da rota velha falham.

---

### F5 — Edit pattern inline lápis (D7) (6-8h) — feature nova

**Objetivo:** lápis em campos de Surface 2 (ambos modos) com `<EditableField>` reusável.

**Componente novo:** `src/components/candidate-profile/EditableField.tsx`
```tsx
interface EditableFieldProps<T> {
  value: T
  onSave: (newValue: T) => Promise<void>
  validate?: (value: T) => string | null
  type?: 'text' | 'email' | 'phone' | 'textarea' | 'select' | 'date'
  options?: { label: string; value: T }[]  // para type='select'
  label?: string
  placeholder?: string
  disabled?: boolean
  hideEditIcon?: boolean  // sempre editável
}
```

**Comportamento:**
- Render: valor + ícone lápis ao hover
- Click no lápis: vira input inline
- `Enter`: chama `onSave` (optimistic update + rollback em erro)
- `Esc`: cancela
- Erro de validação: mensagem inline em vermelho
- Loading: spinner + bloqueia outras edits no mesmo card

**Hook canonical:** `src/hooks/candidates/useCandidateFieldUpdate.ts`
- Wrapper sobre `PUT /candidates/[id]` ou `POST /chat/actions/candidate-field-update` (escolha em F0)
- Multi-tenant (company_id JWT)
- Optimistic update via SWR mutate

**Campos editáveis em Surface 2:**
- Header: phone, email, linkedin URL, github URL
- Perfil → ContactActions: idem
- Perfil → Skills: adicionar/remover skill
- Perfil → ProfileExperienceSection: title/company/dates/description (por experiência)
- Perfil → ProfileEducationSection: degree/institution/field/dates
- Perfil → Info pessoal: location, headline, summary
- Salary expectation, currency

**Campos NÃO editáveis (LGPD policy):**
- ❌ race
- ❌ gender
- ❌ marital_status
- ❌ religion
- ❌ health_data
- ❌ idade direta (date_of_birth editável só se >18, calculate_age read-only)

**Sensor:** `check_editable_fields_not_lgpd_sensitive.ts` — bloquear `<EditableField name="race|gender|marital|religion|health">`.

**Feature flag:** `ff_candidate_edit` (default off em prod, on em dev). Permite rollout gradual.

---

### F6 — Sensors permanentes + cleanup + ADR (3-4h)

**Sensors finais (8 blocking):**

| Sensor | Detecta |
|---|---|
| `check_no_hardcoded_candidate_mocks.ts` | Nomes/arquivos mock literais em `candidate-*` |
| `check_no_fake_ai_analysis.ts` | Objeto `{confidence, communication, clarity, enthusiasm}` |
| `check_no_hardcoded_arrays.ts` | Array literal de dados em `candidate-*` |
| `check_candidate_score_uses_canonical_badge.ts` | `/100` em `candidate-*` |
| `check_no_orphan_proxies.ts` | `fetch('/api/backend-proxy/X')` sem pasta `X/` |
| `check_no_orphan_routes.ts` | Imports de rotas/components deletados |
| `check_editable_fields_not_lgpd_sensitive.ts` | `<EditableField name="race|gender|...">` |
| `check_company_id_from_jwt.ts` | `company_id` em body/header (deve ser JWT) |

**ADRs:**
- `ADR-001-CANONICAL-AXIS.md` — registra "2 surfaces, mesmo eixo, building blocks compartilhados"
- `ADR-002-EDIT-PATTERN.md` — registra D7 inline lápis + LGPD field policy
- `ADR-003-CANDIDATE-ROUTE-ABSORPTION.md` — registra absorção Surface 3 → Surface 2 dual-mode

**Cleanup:**
- `CLAUDE.md` Replit: seção nova "Candidato 2-surface canonical"
- Boy scout: remover OPT-043 (`style={{}}` dinâmicos) em arquivos tocados
- `git grep -r 'from.*candidate-preview\|from.*candidate-page\|from.*candidate-profile'` — mapa final de consumers documentado

**Feature flag rollout (F5):**
- Dev: `ff_candidate_edit=true` default
- Staging: ativar manualmente
- Prod: ativar gradualmente quando smoke test passar

---

## 9. Gates de aceite

Cada fase só fecha quando:
- ✅ **TDD verde**: red→green→refactor commitados na ordem
- ✅ **P0/P1/P2 limpo**
- ✅ **Multi-tenant**: `company_id` do JWT (cookie)
- ✅ **LGPD**: sem PII fictícia, sem campos sensitive editáveis
- ✅ **Design tokens v4.2.2**: zero `bg-blue-*`, zero hex
- ✅ **Sensors blocking**: lint + contract test
- ✅ **i18n**: 0 violations no `lint:i18n:blocking`
- ✅ **Boy scout**: 0 P2 novo no arquivo tocado
- ✅ **WSI score**: 0-10 canonical

---

## 10. Time estimate

| Fase | Tempo |
|---|---|
| F0 Mapa de Verdade | 4-5h |
| F1 Building blocks | 3-4h |
| F2 P0 transversais (Files broken + WSI 0-10) | 3-4h |
| F3 **Absorção Surface 3 → Surface 2** | 6-8h |
| F4 Surface 2 dual-mode + rota preservada | 3-4h |
| F5 Edit pattern inline lápis | 6-8h |
| F6 Sensors + cleanup + ADRs | 3-4h |
| **Total** | **28-37h** |

5-6 sessões focadas. ~4 dias úteis se sessões de 7-8h.

---

## 11. Anti-objetivos

- **NÃO** unificar Surface 1 com Surface 2 (drawer e page têm propósitos distintos)
- **NÃO** mexer em Surface 1 (drawer) além de fix Files broken + opcional boy scout building blocks
- **NÃO** preservar `candidate-page/` mock (será substituído via absorção em F3)
- **NÃO** deletar a rota `/funil-de-talentos/candidato/[id]/` (preservar URL — Paulo acessa via deep-link)
- **NÃO** considerar migração `recruiter_agent_v5`
- **NÃO** reescrever backend
- **NÃO** inventar métrica que o backend não devolve
- **NÃO** tocar GitHub canonical
- **NÃO** sugerir/executar `git push`
- **NÃO** mencionar/sugerir Anderson ou outros do time
- **NÃO** permitir edit de campos LGPD-sensitive

---

## 12. Riscos / mitigação

| Risco | Mitigação |
|---|---|
| Endpoint canonical não devolve campo esperado | F0 valida shape via Zod + snapshot |
| Surface 1 Files broken já em produção | F2 cedo (3ª fase) |
| Edit pattern (D7) escopo grande | F5 isolado, feature flag `ff_candidate_edit` |
| Cascade delete LGPD não verificado | F0 inclui probe explícito |
| Absorção Surface 3 quebra a rota durante a transição | F3 → F4 sequenciais, snapshot test antes/depois |
| WSI legacy 0-100 em opinion antigo do DB | F2 adapter divide por 10 com confidence flag |
| `aiPredictions[]` mock removido sem endpoint real | F3 esconde seção até backend existir |
| Edit em campo LGPD-sensitive escapa | F5 sensor `check_editable_fields_not_lgpd_sensitive` |
| Rollback após edit falha | F5 optimistic update + SWR mutate rollback |
| Building blocks editáveis quebram Surface 1 que não quer edit | F5 prop `editable={false}` default + opt-in |

---

## 13. Próximos passos

1. Paulo aprova este PLAN.md V3
2. F0 inicia (audit endpoints + contracts + edit infra + LGPD policy)
3. F0 retorna ao Paulo com 2 confirmações:
   - Endpoint update preferred (`PUT /candidates/[id]` vs `POST candidate-field-update` vs ambos)
   - LGPD field policy (lista exata de campos não-editáveis)
4. Após confirmação, F1 → F6 sequenciais com commits atômicos no Replit (`feat/benefits-prv-canonical` branch atual)
5. Opcional final: rodar `/autoplan` V2 retrospectivo pra audit pós-execução
