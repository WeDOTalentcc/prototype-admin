# Frontend — Handoff para o time de dev (2026-04-23)

> Execução dos 3 itens P2 arquiteturais deferidos na auditoria cross-cutting
> de 2026-04-22/23 (G3, G4, G5) + integração com o novo endpoint Art. 86 do
> backend IA + alinhamento com os fixes de compliance aplicados em produção.
>
> O manual operacional detalhado é o `FASE6_FE_TASK.md` (7.5K) —
> este documento resume contexto + integra com o ambiente real do time (FE
> próprio, BE `ats-api-copia`, IA em repo separada).

---

## O que este card cobre

3 itens P2 arquiteturais no repositório FE (branch `replit-sync` como referência do canônico):

| ID | Problema | Arquivos afetados |
|----|----------|-------------------|
| **G3** | `permissions.ts` com importação cíclica type-only entre `lib/` e `utils/` | `plataforma-lia/src/lib/permissions.ts` + `utils/permissions.ts` + `utils/permissions.test.ts` |
| **G4** | `config/pricing.ts` é alias morto de `lib/pricing.ts` | `plataforma-lia/src/config/pricing.ts` |
| **G5** | 6 hooks vivendo dentro de `components/` em vez de `hooks/` | `components/use{BatchApproval,LiaMetrics,LiaMetricsData,LiaScreeningDialogue,MetricsCalculations,RubricEvaluation}.ts` |

**Prioridade global:** P2 — sem impacto operacional, mas dívida arquitetural que dificulta manutenção.

---

## Por que essa tarefa existe (contexto)

Durante a auditoria cross-cutting de 2026-04-22/23, todos os P0/P1 foram resolvidos em produção (backend IA + compliance). Restaram 3 itens P2 no frontend que foram deferidos para janela FE dedicada por decisão de produto (não bloqueiam operação).

Agora existe espaço em roadmap. Este card resolve os 3 de uma vez + faz a integração com mudanças do backend IA que afetam FE (principalmente o novo endpoint Art. 86).

---

## O que muda para o dev (FE próprio do time)

### Novidades do backend IA que FE precisa consumir

**Novo endpoint candidate-facing (EU AI Act Art. 86):**

```
GET /api/v1/candidate/decisions/explain?candidate_token=<JWT>&vacancy_id=<opcional>
  Auth:     JWT do candidato (do portal do candidato)
  Response: {
    decisions: [{decision_type, timestamp, criteria_evaluated, criteria_ignored,
                 reasoning_summary, fairness_check, human_reviewed}],
    transparency_note: "...",
    art_86_notice: "De acordo com o EU AI Act (Art. 86) e a LGPD (Art. 20)...",
    total_decisions: N,
  }
  NUNCA retorna: wsi_score, lia_score, confidence, weights, red_flags
```

**FE precisa:**
1. Adicionar tela no portal do candidato que renderiza esta resposta
2. UI clara mostrando critérios objetivos avaliados + critérios ignorados (lista explícita) + prazo de 30 dias para contestação + botão "Solicitar revisão humana" que abre fluxo de contato com compliance
3. **NÃO exibir** nenhum campo sensível (seguir o scope_out do YAML do backend)

Exemplo de mockup conceitual:

```
┌─────────────────────────────────────────────────┐
│ Sua avaliação para a vaga [X]                   │
├─────────────────────────────────────────────────┤
│ Critérios considerados:                          │
│ ✓ Experiência em Python                          │
│ ✓ 5+ anos em backend                             │
│ ✓ Inglês intermediário                           │
│                                                  │
│ Critérios que NÃO foram considerados             │
│ (por proteção legal):                            │
│ × Idade × Gênero × Etnia × Estado civil          │
│ × Foto × Endereço × Religião × Deficiência       │
│                                                  │
│ De acordo com o EU AI Act (Art. 86) e a LGPD     │
│ (Art. 20), você tem direito de solicitar        │
│ revisão humana dentro de 30 dias.                │
│                                                  │
│ [ Solicitar revisão humana ]                    │
└─────────────────────────────────────────────────┘
```

### Fixes arquiteturais

Detalhes completos em `FASE6_FE_TASK.md`. Resumo:

**G3 — permissions.ts importação cíclica:**
- **Opção A (preferida):** Consolidar em `lib/permissions.ts`; transformar `utils/permissions.ts` em shim (`export * from '@/lib/permissions'`); mover teste
- **Opção B:** Quebrar ciclo com `import type` reorganizando tipos entre os dois

**G4 — config/pricing.ts alias morto:**
- Deletar `config/pricing.ts`
- Buscar imports: `grep -r "config/pricing" src/ --include="*.ts" --include="*.tsx"`
- Substituir por `@/lib/pricing`
- Confirmar zero referências

**G5 — 6 hooks misplaced:**
- Mover para subdiretório correto em `hooks/` (IA → `hooks/ai/`, UI → `hooks/ui/`)
- Renomear para kebab-case (padrão do projeto)
- Adicionar export no `index.ts` barrel
- Atualizar imports em todos os consumidores

### Ordem sugerida
```
1. G4 primeiro (mais simples — deletar arquivo + atualizar imports)
2. G3 depois (requer decisão Opção A vs B)
3. G5 por último (mais trabalhoso — 6 arquivos + consumidores)
4. Integração endpoint Art. 86 (trabalho de produto, não refactor)
```

---

## Invariantes obrigatórias

1. **NUNCA `git push`** — apenas commit local no Replit (se trabalhar no repo Replit) ou branch própria no FE repo do time. Push é exclusivo do Paulo via branch `replit-sync`.

2. **Design System v4.2.1** — não alterar lógica de UI durante o refactor. Só mover arquivos e atualizar imports.

3. **Build verde antes de commit** — `npm run build` deve passar sem erros nem warnings de ciclo.

4. **Um commit por tarefa** — G4 em commit separado de G3, G5 em commit separado. Mensagens sugeridas:
   ```
   G4: remove dead alias config/pricing.ts → canonical is lib/pricing.ts
   G3: resolve circular import in permissions.ts (type-only cycle)
   G5: move 6 misplaced hooks from components/ to hooks/ai/ and hooks/ui/
   ```

5. **Testes existentes não podem quebrar** — `npm test` passa.

6. **Candidate portal UI: nunca exibir campos sensíveis.** SSoT: `explain_candidate_decision.py` → `_FORBIDDEN_FIELDS` no backend IA. Se não vier no response, não renderizar.

7. **Art. 86 UI deve sempre incluir:**
   - Prazo de 30 dias claramente visível
   - Botão/link para solicitar revisão humana
   - Aviso legal completo do `art_86_notice` (não resumir)

---

## Validação

```bash
# G3: sem ciclo
npx madge --circular src/lib/permissions.ts src/utils/permissions.ts

# G4: zero referências ao arquivo deletado
grep -r "config/pricing" plataforma-lia/src/ --include="*.ts" --include="*.tsx"

# G5: zero hooks em components/
find plataforma-lia/src/components -name "use*.ts" | grep -v test

# Build + testes
cd plataforma-lia && npm run build && npm test -- --passWithNoTests
```

Smoke manual para integração Art. 86:
1. Gerar `candidate_token` JWT válido (via backend IA; comando de setup em `docs/responsible-ai/fact-sheets/README.md`)
2. Acessar `/candidate-portal/decisions/explain` no FE
3. Verificar que response renderiza corretamente
4. Verificar que resposta 401 (token inválido) mostra mensagem amigável
5. Verificar que resposta 429 (rate limit) explica o limite

---

## Diferenças do ambiente da sua empresa

| Dimensão | Referência Replit | Produto novo |
|----------|-------------------|--------------|
| Repo FE | `plataforma-lia/` dentro do monorepo Replit | **Repo próprio do time FE** (separado) |
| Tech stack | Next.js 14 | **Mesma tech** (manter paridade) |
| Design System | v4.2.1 (canônico) | **Mesma versão** — sem alterações de tokens |
| API base | endpoints em `lia-agent-system/app/api/v1/` | Agora chamando **IA repo separada** + `ats-api-copia` (Rails integrado) |
| Candidate portal auth | JWT com `CANDIDATE_PORTAL_JWT_SECRET` | **Mesmo padrão** — JWT emitido pelo backend IA |

**Ponto de integração crítico:** o endpoint Art. 86 fica na **IA repo**, não na ats-api-copia. Confirmar antes com time de backend IA qual é o host de produção desse endpoint.

---

## Referências

- **Manual operacional:** `FASE6_FE_TASK.md` (7.5K) — instruções passo-a-passo dos 3 itens com comandos e validações
- **Contexto maior:** `COMPLIANCE_DEV_HANDOFF_2026-04-23.md` (backend IA) — explica o endpoint Art. 86 e o scope_out que FE deve respeitar
- **Auditoria original:** `CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md` seções 0.8.8 (Duplicatas FE) + 0.8.9 (Hooks Organização)
- **Rastreamento:** `COMPLIANCE_CROSS_CUTTING_MATRIX.md` (G3/G4/G5)

---

## Não fazer

- `git push` — commits locais apenas
- Alterar tokens do Design System
- Alterar lógica de UI durante refactor (G3/G4/G5 são só movimentação + imports)
- Exibir score bruto, confidence numérica, red flags ou weights no portal do candidato
- Encurtar ou omitir o aviso Art. 86 mesmo a pedido do cliente
- Fazer chamada direta ao `fairness_audit_log` do FE — toda lógica de explicação passa pelo endpoint `/api/v1/candidate/decisions/explain`

---

*Handoff gerado em 2026-04-23 | Próxima revisão: após execução dos 3 itens + smoke da integração Art. 86*
