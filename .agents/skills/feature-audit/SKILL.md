---
name: feature-audit
description: "Auditoria completa de features, ajustes e correções na Plataforma LIA, alinhada ao WeDO Talent Guide v3.3. Use OBRIGATORIAMENTE antes de marcar qualquer tarefa como concluída, após implementar features novas, fazer ajustes, ou quando o usuário pedir revisão/auditoria. Cobre 14 dimensões — integração, dados, UI/Design System v4.2.1, backend, tipos, fluxo do usuário, consistência, documentação, arquitetura de agentes, qualidade LLM, serviços IA, governança IA, segurança e performance. Para verificações mais profundas de governança, compliance e DEI, consultar as 4 skills complementares: wedo-governance, screening-compliance, dei-fairness e lgpd-data-protection."
---

# Feature Audit — Checklist Universal de Auditoria (14 Dimensões)

Esta skill é uma auditoria obrigatória de **14 dimensões** que deve ser executada antes de marcar qualquer feature, ajuste ou correção como concluído. Ela garante que nada fique desconectado, parcialmente implementado, invisível ao usuário, ou em violação ao Design System / arquitetura de IA.

## Quando ativar

- Quando o usuário disser "audita", "revisa", "valida", "checa", "passa o pente fino" ou "vê se tá tudo certo"
- **SEMPRE** antes de marcar tarefa como `completed` ou `completed_pending_review`
- Após implementar feature nova (componente, hook, endpoint, modal, agente, prompt, intent)
- Após corrigir bug ou aplicar refactor que toca múltiplas camadas
- Ao integrar mudanças entre frontend ↔ backend ↔ IA ↔ banco (qualquer cruzamento de camada)
- Ao criar ou modificar agentes IA, prompts, intents ou integrações externas (APIs de terceiros)
- Ao final de qualquer modo BUILD/REFACTOR/AUDIT do `lia-orchestrator`
- Antes de PR que adiciona/altera dimensão de governança, fairness, LGPD ou WSI

## Quando NÃO ativar

- Mudança puramente de copy/texto em arquivo de tradução ou i18n (sem lógica)
- Typo trivial em string literal (sem impacto funcional)
- Workaround temporário com prazo já documentado como dívida técnica
- Antes de implementar — auditoria é POST-implementação; para fase PRE use `feature-impact`
- Configuração de ambiente (`.env`, dotfiles) sem mudança de código

## Filosofia

> "Existir não é o mesmo que estar conectado. Compilar não é o mesmo que funcionar."

A falha mais comum NÃO é código quebrado — é código que existe mas não foi conectado ao fluxo real. Esta auditoria previne exatamente isso.

## Skills Complementares

Esta skill cobre as 14 dimensões de auditoria de feature. Para verificações mais profundas em governança, compliance, DEI e proteção de dados, usar as skills complementares:

| Skill | Escopo |
|-------|--------|
| **wedo-governance** | Verificação das 13 Crenças do Manifesto e Production Readiness (18 critérios) |
| **screening-compliance** | Compliance de screening, teste de viés, red teaming e model drift |
| **dei-fairness** | DEI, FairnessGuard 3 camadas, bias audit e acessibilidade |
| **lgpd-data-protection** | LGPD, EU AI Act, PII Masking e consentimento |

> **Guia canônico:** `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md`

## Mapa das 14 Dimensões

| # | Dimensão | Layer | Quando Obrigatória |
|---|----------|-------|--------------------|
| 1 | Integração (Wiring) | Full-stack | Sempre |
| 2 | Fluxo de Dados | Full-stack | Sempre |
| 3 | UI/UX + Design System v4.2.1 | Frontend | Features com UI |
| 4 | Backend e API | Backend | Features com API |
| 5 | Tipos e Contratos | Full-stack | Sempre |
| 6 | Fluxo do Usuário | Full-stack | Sempre |
| 7 | Consistência | Full-stack | Sempre |
| 8 | Documentação | Full-stack | Sempre |
| 9 | Arquitetura de Agentes | IA | Novos domínios/agentes |
| 10 | Qualidade LLM | IA | Prompts, intents, parsing |
| 11 | Serviços e Integrações IA | IA | WSI, scoring, APIs |
| 12 | Governança e Resiliência IA | IA | Compliance, flags, retry |
| 13 | Segurança e Proteção de Dados | Transversal | Sempre (check rápido) |
| 14 | Performance e Escalabilidade | Transversal | Features com dados/listas |

---

## As 14 Dimensões da Auditoria

Execute as dimensões relevantes para cada feature/ajuste (ver "Quando NÃO Pular Dimensões" ao final). Registre o resultado de cada item como ✅ (ok), ⚠️ (parcial), ❌ (faltando) ou N/A (não se aplica).

---

### DIMENSÃO 1: Integração de Componentes (Wiring)

Verifica se todos os componentes criados estão CONECTADOS entre si no fluxo real.

> **Skill complementar:** se ao verificar le o wiring você encontrar duplicatas (rota paralela, hook clonado `.ts`/`.tsx`, dois services com nome similar) ou suspeita de workaround (fix aplicado no consumidor em vez da fonte), pare e rode a skill **canonical-fix** antes de seguir.

**Checklist:**

1. **Hook → Componente**: Todo hook criado (`use-*.ts`) está sendo importado e chamado por pelo menos um componente?
   - Buscar: `grep -r "useNomeDoHook" --include="*.tsx" --include="*.ts"`
   - Se retornar 0 resultados em componentes, o hook NÃO está conectado

2. **Endpoint → Proxy → Hook**: Todo endpoint backend tem proxy frontend E hook que o chama?
   - Backend: `lia-agent-system/app/api/v1/` → endpoint existe?
   - Proxy: `plataforma-lia/src/app/api/backend-proxy/` → route.ts existe?
   - Hook: algum `use-*.ts` chama esse proxy?
   - Componente: algum `.tsx` usa esse hook?

3. **Props → Dados Reais**: Todo componente que recebe props via interface está recebendo dados REAIS (não só a tipagem)?
   - Verificar onde o componente é renderizado (`<NomeComponente prop={???} />`)
   - A prop está recebendo valor real ou está undefined/hardcoded?

4. **Modal → Trigger**: Todo modal criado tem pelo menos um botão/ação que o abre?
   - Buscar onde `isOpen`/`setIsOpen` é controlado
   - O trigger está acessível ao usuário no fluxo normal?

5. **Evento → Handler → Efeito**: Todo evento do usuário (click, drag, submit) chama um handler que produz efeito visível?
   - onClick → handleX → setState/fetch/toast
   - Se o handler existe mas não é chamado em nenhum onClick/onSubmit, está desconectado

**Como executar:**
```bash
# Para cada hook criado, verificar se é usado:
grep -r "useInterpretContext" plataforma-lia/src/ --include="*.tsx" --include="*.ts" -l

# Para cada endpoint, verificar cadeia completa:
grep -r "interpret-context" plataforma-lia/src/ --include="*.ts" --include="*.tsx" -l
grep -r "interpret-context" lia-agent-system/app/ --include="*.py" -l
```

---

### DIMENSÃO 2: Fluxo de Dados (Data Flow)

Verifica se os dados fluem corretamente do banco → backend → proxy → hook → componente → UI.

**Checklist:**

1. **Origem dos dados**: De onde vem o dado exibido no componente?
   - Banco (PostgreSQL) → Model (SQLAlchemy) → Endpoint (FastAPI) → Proxy (Next.js API) → Hook → Componente
   - Em qual ponto da cadeia o dado para de fluir?

2. **Estado local vs API**: O componente usa dados reais (da API) ou estado local/mock?
   - Buscar `useState` com valores hardcoded que deveriam vir de API
   - Buscar `// TODO`, `// mock`, `// placeholder`, `// temporary`

3. **Atualização pós-ação**: Quando o usuário faz uma ação (salvar, mover, editar), os dados na tela atualizam?
   - O `setCandidatesData` / `setXxx` é chamado após a resposta da API?
   - A tela reflete o novo estado sem precisar recarregar?

4. **Persistência**: O dado é salvo no banco ou só no estado local?
   - Se `setCandidatesData` muda localmente mas não há `fetch POST/PUT`, o dado se perde ao recarregar

5. **Fallback e loading**: Existe estado de loading enquanto busca dados? Existe fallback se a API falhar?

**Como executar:**
```bash
# Verificar se componente usa dados mock:
grep -n "useState\|mockData\|placeholder\|TODO\|FIXME" plataforma-lia/src/components/kanban/components/NomeComponente.tsx

# Verificar se há fetch real:
grep -n "fetch\|axios\|useSWR" plataforma-lia/src/components/kanban/hooks/use-nome.ts
```

---

### DIMENSÃO 3: Interface do Usuário (UI/UX) + Design System v4.2.1

Verifica se as mudanças são VISÍVEIS, ACESSÍVEIS e CONFORMES ao Design System LIA v4.2.1.

> **Referência canônica:** `plataforma-lia/docs/design-system/00-design-system-v4.md`

**Checklist:**

1. **Visibilidade**: O resultado da feature é visível na tela sem ação extra?
   - Se o sub-status é salvo mas não aparece em nenhum badge/label, é invisível
   - Se um dado existe no estado mas não é renderizado, é invisível

2. **Feedback visual**: Toda ação do usuário tem feedback visual imediato?
   - Loading spinner / Skeleton Loader (DS §2.25) durante operações assíncronas
   - Toast de sucesso/erro (DS §2.8) após ações
   - Mudança visual no componente (cor, texto, posição)

3. **Consistência entre visões**: A feature funciona igual em TODAS as visões?
   - Kanban (drag-drop) e Tabela (dropdown) devem ter o mesmo resultado
   - Mobile/responsive: a feature funciona em telas menores?
   - Breakpoints: xs(< 640px), sm(640px), md(768px), lg(1024px), xl(1280px), 2xl(1536px) — conforme `tailwind.config.ts`

4. **Regra 90/10 Monocromática** (DS §1.1, §1.2):
   - **90% grayscale** — usar tokens canônicos:
     - Backgrounds: `--lia-bg-primary` (#FFFFFF), `--lia-bg-secondary` (#F9FAFB/gray-50), `--lia-bg-tertiary` (#F3F4F6/gray-100)
     - Textos: `--lia-text-primary` (#111827/gray-900), `--lia-text-body` (#1F2937/gray-800), `--lia-text-secondary` (#4B5563/gray-600), `--lia-text-muted` (#6B7280/gray-500)
     - Bordas: `--lia-border-subtle` (#E5E7EB/gray-200), `--lia-border-default` (#D1D5DB/gray-300)
     - Botão primary: `bg-gray-900` (preto, NUNCA colorido)
   - **10% acento WeDo** — apenas para:
     - Brain icon LIA: `#60BED1` (cyan)
     - Badges contextuais: cyan, green, orange, purple, magenta (DS §1.2.2)
     - Status semântico: success (#22C55E), warning (#F59E0B), error (#EF4444), info (#60BED1) (DS §1.2.3)
     - NUNCA em botões primários ou ações principais

5. **Tipografia** (DS §1.3):
   - Famílias: Open Sans (UI geral) + Inter (dados/tabelas)
   - Hierarquia: usar classes `text-lia-*` ou equivalentes Tailwind (text-xs a text-xl)
   - Pesos: font-normal (400), font-medium (500), font-semibold (600), font-bold (700)
   - Nunca usar mais de 2 pesos na mesma região visual

6. **Espaçamento** (DS §1.4):
   - Escala base 4px: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64
   - Componentes: padding interno (12-16px), gap entre elementos (8-12px), margin entre seções (24-32px)

7. **Sombras e Elevação** (DS §1.7):
   - `shadow-sm` para cards sutis, `shadow-md` para cards elevados, `shadow-lg` para modais/dropdowns
   - Nunca shadow-2xl ou sombras dramáticas

8. **Bordas e Raios** (DS §1.8):
   - `rounded-md` (6px) para inputs/botões, `rounded-lg` (8px) para cards, `rounded-xl` (12px) para modais
   - Bordas quase invisíveis (`border-gray-200`), NUNCA grossas

9. **Motion e Animação** (DS §1.9):
   - Duração: micro (100ms), fast (150ms), normal (200ms), slow (300ms), emphasis (500ms)
   - Easing: `ease-out` para entradas, `ease-in` para saídas, `ease-in-out` para loops
   - Permitido: fade, slide, scale (sutil), skeleton shimmer
   - Proibido: bounce, elastic, rotação contínua

10. **Componentes do Design System** (DS Parte 2):
    - Usar variantes documentadas (DS v4.2.1, §2.1-§2.29): botões (4 variantes), inputs, cards, modais, tabelas, badges, tooltips, toasts, dropdowns, pagination, etc.
    - Verificar se o componente criado já existe no DS antes de criar um novo
    - Se criou componente novo, documenta no DS?

11. **Padrões de UI** (DS Parte 3):
    - Estados: default, hover, active, focus, disabled, loading, error (DS §3.1)
    - Empty states: ilustração + mensagem + CTA (DS §3.4)
    - Error pages: 404, 500, offline (DS §3.5)

12. **Brain Icon LIA** (DS §1.11):
    - Sempre cyan #60BED1
    - Tamanhos: sm (16px), md (20px), lg (24px), xl (32px)
    - Estados: idle (estático), thinking (pulse), success (bounce sutil), error (shake)
    - Usar em: avatar LIA no chat, badge de conteúdo gerado por IA, header de painel IA

13. **Design Tokens** (DS Parte 4):
    - CSS: usar variáveis `--lia-*` de `design-tokens.css` quando disponível
    - TypeScript: importar de `src/lib/design-tokens.ts` quando disponível
    - Nunca hardcodar hex direto se existe token equivalente

14. **Acessibilidade** (DS §3.6 + Crença #13 do Manifesto):
    - WCAG 2.1 AA como requisito obrigatório (Crença #13 — Acessível e Inclusiva)
    - Labels em elementos de formulário
    - Contraste WCAG AA mínimo (4.5:1 texto normal, 3:1 texto grande)
    - aria-labels em botões de ícone
    - Focus ring visível (ring-2 ring-offset-2 ring-gray-400)
    - Para verificações completas de acessibilidade e DEI, usar skill **dei-fairness**

15. **Qualidade Estética** (ver skill `frontend-design`):
    - A interface tem ponto de vista estético claro? Não é genérico "AI slop"?
    - Evita anti-patterns: gradiente roxo genérico, Inter/Arial em tudo, layouts previsíveis sem hierarquia
    - Para telas novas: verificar que PASSO 0 de `design-standardize` foi aplicado (intenção estética)
    - Para telas de entrada/branding: verificar que usa composição atmosférica e tipografia de impacto
    - Para interface interna: verificar que micro-interações, empty states e transições são cuidadosos

16. **Ambas as visões (Kanban + Tabela)**: Se a feature afeta candidatos, verificar que funciona tanto no card (CandidateCard.tsx) quanto na linha da tabela (CandidateTableRow.tsx / renderCustomCell em job-kanban-page.tsx)

**Como executar:**
```bash
# Verificar se usa tokens canônicos ou hex hardcoded:
grep -n "#[0-9A-Fa-f]\{6\}" plataforma-lia/src/components/novo-componente.tsx

# Verificar se usa design tokens:
grep -n "\-\-lia-\|design-tokens" plataforma-lia/src/components/novo-componente.tsx

# Buscar violações da regra 90/10 (cores de acento em botões primários):
grep -n "bg-cyan\|bg-blue\|bg-green\|bg-red" plataforma-lia/src/components/novo-componente.tsx

# Verificar acessibilidade básica:
grep -n "aria-label\|aria-describedby\|role=" plataforma-lia/src/components/novo-componente.tsx
```
- Usar a ferramenta de screenshot para verificar visualmente
- Comparar a feature no Kanban vs Tabela
- Comparar com o Design System v4.2.1 (`plataforma-lia/docs/design-system/00-design-system-v4.md`)

---

### DIMENSÃO 4: Backend e API

Verifica se o backend suporta corretamente a feature e segue os padrões de qualidade de código da plataforma.

**Checklist:**

1. **Endpoint existe e responde**: O endpoint retorna dados no formato esperado?
   - Testar com curl ou verificar no log do backend
   - Status 200? Formato JSON correto?

2. **Modelo de dados**: A tabela/coluna necessária existe no banco?
   - Se a feature salva `sub_status`, existe coluna `sub_status` na tabela?
   - O modelo SQLAlchemy reflete a coluna?

3. **Validação**: O endpoint valida os dados recebidos?
   - Pydantic schemas definidos? (obrigatório — sem `dict` cru em parâmetros de endpoint)
   - Erros retornam mensagens claras com HTTP status correto (400 validação, 404 não encontrado, 422 Pydantic, 500 servidor)?

4. **Proxy frontend**: O proxy Next.js (`/api/backend-proxy/...`) está configurado?
   - O path no proxy bate com o path do backend?
   - Headers (Content-Type, Authorization) são propagados?

5. **Resposta inclui dados necessários**: A resposta da API inclui TODOS os campos que o frontend precisa?
   - Se o frontend precisa de `sub_status` e a API não retorna, o dado nunca chega

6. **Boas práticas de código backend** (padrões arquiteturais obrigatórios da plataforma):

   - [ ] **Router fino (≤ 10 linhas por handler)**: O handler `@router.*` apenas valida schema de entrada, chama um método de service e retorna o resultado. Sem lógica de negócio, querysets SQL, decisões de negócio ou chamadas LLM dentro do router.
   - [ ] **Service stateless**: O service não guarda estado entre chamadas — recebe parâmetros, processa, retorna. Nenhum atributo de instância acumula dados entre requisições.
   - [ ] **Funções curtas (< 50 linhas)**: Funções e métodos com menos de 50 linhas de lógica real (excluindo docstrings/comentários). Funções com 50+ linhas devem ser divididas em subfunções nomeadas.
   - [ ] **Pydantic obrigatório em todos os contratos**: Todo input de endpoint (`RequestSchema`) e todo output de service (`ResponseSchema`) tem schema Pydantic explícito. Proibido `dict`, `Any` ou `**kwargs` sem tipagem em contratos de API.
   - [ ] **`company_id` em todos os models, queries e respostas**: Toda model SQLAlchemy tem coluna `company_id`. Toda query ao banco filtra `WHERE company_id = :cid` como condição obrigatória. Toda resposta de API exclui dados de outras empresas. `company_id` é extraído do JWT autenticado — nunca aceito como parâmetro de query/body sem validação de autorização.
   - [ ] **Structured logging (sem `print()`)**: Usar `logger.info/warning/error(msg, extra={...})` em todo código de produção. `print()` é proibido em qualquer arquivo fora de `test_*`. Todo log de decisão de negócio inclui `company_id`, `user_id` e contexto relevante no `extra`.
   - [ ] **Secrets fora do código**: Credenciais vêm de `settings.*` (Pydantic BaseSettings / env vars). Nenhum secret hardcoded no código. Nenhum `.env` commitado no git.

7. **Isolamento multi-tenant**: A feature NUNCA mistura dados entre empresas diferentes?
   - [ ] Toda query SQL/SQLAlchemy filtra `company_id` como condição obrigatória
   - [ ] Nenhum endpoint retorna dados além da empresa do usuário autenticado
   - [ ] `company_id` vem do JWT, não do corpo da requisição
   - [ ] Teste: autenticar como empresa A e tentar acessar dados da empresa B → deve retornar 403 ou lista vazia

**Como executar:**
```bash
# Verificar se endpoint existe:
grep -r "def.*nome_endpoint\|@router" lia-agent-system/app/api/ --include="*.py"

# Verificar se proxy existe:
ls plataforma-lia/src/app/api/backend-proxy/nome-endpoint/

# Verificar resposta:
curl -s http://localhost:8000/api/v1/nome-endpoint | python3 -m json.tool | head -20

# Verificar routers finos (contar linhas por handler — >10 é alerta):
grep -n "@router\." lia-agent-system/app/api/v1/nome_endpoint.py

# Verificar Pydantic em todos os endpoints (sem dict cru):
grep -n ": dict\|: Any\|\*\*kwargs" lia-agent-system/app/api/v1/nome_endpoint.py | grep -v "import\|#"

# Verificar company_id em queries (multi-tenant obrigatório):
grep -n "company_id" lia-agent-system/app/services/nome_service.py

# Verificar print statements proibidos:
grep -rn "print(" lia-agent-system/app/ --include="*.py" | grep -v "test_\|#"

# Verificar funções longas (≥ 50 linhas é alerta):
awk '/^    def /{start=NR} start && NR-start>=50{print FILENAME ":" NR " — função longa"; start=0}' \
  lia-agent-system/app/services/nome_service.py
```

---

### DIMENSÃO 5: Tipagem e Contratos (TypeScript/Python)

Verifica se os tipos estão corretos e consistentes entre frontend e backend.

**Checklist:**

1. **Interface/Type atualizado**: Se um componente precisa de novos campos, a interface foi atualizada?
   - `KanbanCandidate` tem o campo `subStatus`? `stageId`?
   - O tipo no frontend bate com o que a API retorna?

2. **Props obrigatórias vs opcionais**: Props marcadas como obrigatórias (`prop: string`) estão sendo passadas em TODOS os lugares onde o componente é usado?

3. **Enums/constantes alinhados**: Os códigos usados no frontend (ex: `'screening'`, `'scheduling'`) batem exatamente com os do backend?
   - Comparar `constants.ts` no frontend com `enums/constants` no backend

4. **Sem `any` desnecessário**: Verificar se há `as any` que mascara erros de tipo

5. **LSP limpo**: Executar verificação de diagnósticos LSP nos arquivos alterados
   - 0 erros é o objetivo
   - Warnings devem ser avaliados

**Como executar:**
```bash
# Verificar erros LSP:
# Usar get_latest_lsp_diagnostics nos arquivos alterados

# Buscar "any" suspeitos:
grep -n "as any\|: any" plataforma-lia/src/components/arquivo.tsx
```

---

### DIMENSÃO 6: Fluxo Completo do Usuário (User Journey)

Simula o caminho completo do usuário para verificar que funciona ponta a ponta.

**Checklist:**

Para cada feature, responder na sequência:

1. **Ponto de entrada**: Como o usuário INICIA a ação?
   - Clique em botão? Drag-drop? Digitação? Navegação?

2. **Caminho feliz**: O que acontece se tudo der certo?
   - Passo 1 → Passo 2 → ... → Resultado final
   - Cada passo está implementado E conectado ao próximo?

3. **Resultado visível**: O que o usuário VÊ como confirmação de sucesso?
   - Toast? Mudança na tela? Novo dado aparece?

4. **Caminhos alternativos**: O que acontece se o usuário...
   - Cancelar no meio?
   - Deixar campo obrigatório vazio?
   - Perder conexão durante a operação?

5. **Estado pós-ação**: Após completar a ação...
   - O dado persiste ao recarregar a página?
   - Outros componentes que dependem desse dado atualizaram?
   - O estado é consistente entre Kanban e Tabela?

**Como executar:**
Escrever o fluxo como texto sequencial e verificar CADA passo:
```
FLUXO: Mover candidato de Triagem → Entrevista
1. [Kanban] Usuário arrasta card → handleTransitionRequired é chamado? ✅/❌
2. [Modal] UniversalTransitionModal abre com dados corretos? ✅/❌
3. [Prompt] Usuário digita "agendar terça 14h" → useInterpretContext é chamado? ✅/❌
4. [SubStatus] Sub-status é sugerido automaticamente? ✅/❌
5. [Confirmar] Usuário clica Confirmar → API é chamada? ✅/❌
6. [Visual] Candidato aparece na nova coluna? ✅/❌
7. [Badge] Sub-status aparece como badge no card? ✅/❌
8. [Tabela] Na visão tabela, o candidato está na etapa correta? ✅/❌
9. [Persistência] Ao recarregar, o candidato ainda está na nova etapa? ✅/❌
```

---

### DIMENSÃO 7: Consistência com o Sistema Existente

Verifica se a feature é consistente com padrões já estabelecidos na plataforma.

> **Skill complementar:** quando esta dimensão revelar duplicação de lógica ou divergência entre constantes/códigos canônicos, use a skill **canonical-fix** para identificar a fonte da verdade e consolidar antes de seguir adiante (não copie a lógica para um novo lugar).

**Checklist:**

1. **Mesmo padrão de outros componentes similares**: A nova feature segue o mesmo padrão de features similares já existentes?
   - Se outros modais usam `Dialog` + `DialogContent`, o novo modal também usa?
   - Se outros hooks fazem `try/catch` com toast de erro, o novo hook também faz?

2. **Sem duplicação**: A feature não duplica lógica que já existe em outro lugar?
   - Buscar componentes/hooks similares que já fazem a mesma coisa
   - Se existe duplicação, consolidar em um lugar só

3. **Imports consistentes**: Usa as mesmas bibliotecas/utilitários que o resto do projeto?
   - `cn()` para classes condicionais
   - `textStyles` para tipografia
   - `toast()` para notificações
   - shadcn/ui components

4. **Nomenclatura**: Nomes de arquivos, componentes, hooks e variáveis seguem convenção do projeto?
   - Hooks: `use-nome-do-hook.ts` (kebab-case)
   - Componentes: `NomeComponente.tsx` (PascalCase)
   - Constantes: `NOME_CONSTANTE` (SCREAMING_SNAKE_CASE)
   - Backend: `nome_endpoint.py` (snake_case)

5. **Constantes canônicas**: Códigos de sub-status, action_behaviors, stage IDs usam os mesmos valores em TODOS os lugares?
   - Comparar `constants.ts`, `badge-utils.ts`, `use-universal-transition.ts`
   - Se `screening` no frontend é `screening` no backend (não `triagem` vs `screening`)

**Como executar:**
```bash
# Verificar se um código/constante é usado consistentemente:
grep -rn "screening\|triagem" plataforma-lia/src/components/kanban/ --include="*.ts" --include="*.tsx"

# Verificar duplicação de componentes:
grep -rn "Popover.*stage\|stage.*dropdown" plataforma-lia/src/components/ --include="*.tsx" -l
```

---

### DIMENSÃO 8: Documentação e Rastreabilidade

Verifica se a feature está documentada e rastreável.

**Checklist:**

1. **replit.md atualizado**: A seção "Recent Changes" reflete o que foi feito?
   - Arquivos criados/modificados
   - O que a feature faz
   - Dependências adicionadas

2. **Doc de requisitos atualizado**: O `docs/pipeline-transition-system.md` (ou doc equivalente) reflete o estado atual?

3. **Comentários inline**: Lógica complexa tem comentários explicando o "porquê"?
   - NÃO comentários óbvios como `// set state`
   - SIM comentários de decisão como `// Usa stageId em vez de stage slug para evitar mismatch`

4. **TODO/FIXME rastreados**: Se algo ficou como placeholder, está documentado?
   - Buscar `// TODO`, `// FIXME`, `// PLACEHOLDER`, `// HACK`
   - Cada um deve ter contexto: o que falta e quando será feito

---

### DIMENSÃO 9: Arquitetura de Agentes (IA)

Verifica se agentes IA seguem a arquitetura domain-driven documentada.

> **Referência:** `docs/lia-ai-architecture-cards-jira.md` (Seção 1: Visão Geral da Arquitetura)
> **Código:** `lia-agent-system/app/domains/`, `lia-agent-system/app/orchestrator/`

**Checklist:**

1. **DomainPrompt ABC** (base.py — 171L):
   - Todo novo domínio herda de `DomainPrompt`?
   - Implementa os 7 métodos obrigatórios: `get_system_prompt()`, `get_tools()`, `get_examples()`, `validate_input()`, `format_output()`, `get_domain_context()`, `get_constraints()`?
   - Prompt system usa template YAML com variáveis de contexto (tenant, user, role)?

2. **DomainWorkflow** (workflow.py — 463L):
   - Segue o pipeline LangGraph de 7 passos: classify → route → prepare → execute → validate → format → respond?
   - Cada nó tem handler próprio com tipagem de State?
   - Graph compila sem erros (`graph.compile()`)?

3. **CascadedRouter 3-tier** (orchestrator/cascaded_router.py):
   - Nível 1: Memory Router — busca em ConversationMemory antes de acionar LLM?
   - Nível 2: Fast Router — regex/keyword para intents comuns (< 5ms)?
   - Nível 3: LLM Router — só quando Fast falha, com fallback para domínio `recruiter_assistant`?
   - Métricas de routing logadas (tempo, nível usado, confiança)?

4. **DomainRegistry** (registry.py — 118L):
   - Novo domínio registrado com auto-discovery?
   - Metadata completa: `name`, `description`, `keywords`, `tools`, `priority`?
   - Sem domínios órfãos (registrados mas sem implementação)?

5. **Tool System** (shared/tools/):
   - Ferramentas declaradas com Pydantic schema (input/output tipados)?
   - Tenant scoping: toda tool recebe `tenant_id` e filtra dados por tenant?
   - Tools registradas no domínio correto (não em domínio genérico)?
   - Sem tools duplicadas entre domínios?

6. **ConversationMemory** (shared/memory/):
   - Contexto de conversa persistido entre sessões?
   - Resumo LLM gerado quando histórico > threshold?
   - Reference resolver funciona para pronomes ("ele", "essa vaga", "o candidato")?

**Como executar:**
```bash
# Verificar se domínio herda DomainPrompt:
grep -n "class.*DomainPrompt\|class.*domain" lia-agent-system/app/domains/*/domain.py

# Verificar registro no DomainRegistry:
grep -n "register\|domain_name" lia-agent-system/app/domains/registry.py

# Verificar cascade levels:
grep -n "memory_route\|fast_route\|llm_route" lia-agent-system/app/orchestrator/cascaded_router.py

# Verificar tools com tenant scoping:
grep -rn "tenant_id" lia-agent-system/app/shared/tools/ --include="*.py"
```

---

### DIMENSÃO 10: Qualidade LLM (Prompts, Intents, Parsing)

Verifica qualidade das interações com modelos de linguagem.

> **Código:** `lia-agent-system/app/shared/prompts/`, `lia-agent-system/app/shared/intelligence/`

**Checklist:**

1. **Prompts YAML estruturados**:
   - Prompts armazenados em YAML, não hardcoded em Python?
   - Template usa variáveis de contexto: `{tenant_name}`, `{user_role}`, `{language}`, `{domain_context}`?
   - Contém exemplos few-shot quando output é estruturado?
   - Versão do prompt rastreável (v1, v2...)?

2. **Classificação de intents**:
   - Intent classifier cobre os intents documentados para o domínio?
   - Fallback intent definido (não retorna `None` ou erro)?
   - Confiança mínima configurada (threshold para fallback)?
   - Intents mutuamente exclusivos (sem ambiguidade entre `CREATE_JOB` e `EDIT_JOB`)?

3. **Structured Output Parsing**:
   - Output do LLM parseado com Pydantic model (não regex manual)?
   - Parsing falha graciosamente (não estoura com output inesperado)?
   - Retry com prompt corrigido quando parsing falha na primeira tentativa?

4. **Fallback de provider**:
   - Se Claude falha, tenta Gemini ou OpenAI?
   - Ordem de fallback documentada e configurável por domínio?
   - Timeout por provider configurado (não esperar 60s em provider que caiu)?
   - Logs de fallback com razão (timeout, rate limit, 500)?

5. **Token Usage e Custo**:
   - Input/output tokens logados por chamada?
   - Prompt não excede janela de contexto (verificar contra max_tokens do modelo)?
   - Conversas longas têm truncation ou summarization?
   - Estimativa de custo por operação acessível para billing?

6. **Qualidade de respostas**:
   - LIA responde em português (não muda para inglês aleatoriamente)?
   - Tom conversacional consistente (não formal demais nem informal demais)?
   - Não alucina dados (ex: não inventa nome de candidato que não existe)?
   - Respostas têm tamanho adequado (não 3 parágrafos para "sim" nem 2 palavras para análise complexa)?

**Como executar:**
```bash
# Verificar prompts hardcoded:
grep -rn "system_prompt\|You are\|Você é" lia-agent-system/app/domains/ --include="*.py" | grep -v ".yaml\|.yml"

# Verificar output parsing com Pydantic:
grep -rn "BaseModel\|model_validate\|parse_obj" lia-agent-system/app/shared/ --include="*.py"

# Verificar fallback de provider:
grep -rn "fallback\|retry\|backup_provider" lia-agent-system/app/shared/providers/ --include="*.py"

# Verificar token logging:
grep -rn "token_usage\|total_tokens\|prompt_tokens" lia-agent-system/app/ --include="*.py"
```

---

### DIMENSÃO 11: Serviços e Integrações IA

Verifica se os serviços de IA (WSI, scoring, search, APIs externas) funcionam corretamente.

> **Código:** `lia-agent-system/app/services/`, `lia-agent-system/app/shared/intelligence/`

**Checklist:**

1. **WSI Pipeline** (7 blocos):
   - Bloco 1 (Fit Técnico): skills extraídas e comparadas com requisitos da vaga?
   - Bloco 2 (Experiência): anos e relevância calculados?
   - Bloco 3 (Formação): grau acadêmico mapeado corretamente?
   - Bloco 4 (Comportamental): competências soft avaliadas?
   - Bloco 5 (Cultural): valores organizacionais comparados?
   - Bloco 6 (Potencial): capacidade de crescimento estimada?
   - Bloco 7 (Score Consolidado): pesos configuráveis por tenant, soma = 100%?
   - Score final é numérico (0-100) E tem nível textual (Alto/Médio/Baixo)?

2. **Scoring Determinístico**:
   - Componentes determinísticos (anos de experiência, formação) não dependem de LLM?
   - Mesmo input sempre gera mesmo score determinístico?
   - Componentes LLM-assisted (fit cultural) têm cache para evitar re-avaliação?

3. **Embedding e Semantic Search**:
   - Modelo de embedding documentado (qual modelo, qual dimensão)?
   - Embeddings cacheados (não recalcula a cada busca)?
   - Similarity threshold configurável?
   - Resultados paginados (não retorna 10.000 matches de uma vez)?

4. **APIs Externas (saúde e resiliência)**:
   - Cada API externa tem health check?
   - Credenciais (Anthropic, OpenAI, Gemini, Deepgram, Merge, etc.) em secrets, não em código?
   - Rate limiting respeitado (não dispara 100 chamadas paralelas a API com limite de 10)?
   - Fallback ou fila quando API está indisponível?

5. **Batch Processing**:
   - Triagem em lote usa queue/worker, não loop síncrono?
   - Progresso reportado ao usuário (não "processando..." por 10 minutos)?
   - Erros individuais não falham o lote inteiro (continue-on-error)?

**Como executar:**
```bash
# Verificar WSI com 7 blocos:
grep -rn "bloco\|block\|wsi_score\|wsi_pipeline" lia-agent-system/app/ --include="*.py"

# Verificar health checks de APIs:
grep -rn "health_check\|ping\|is_available" lia-agent-system/app/shared/ --include="*.py"

# Verificar credenciais em secrets (não hardcoded):
grep -rn "api_key\|API_KEY\|secret" lia-agent-system/app/ --include="*.py" | grep -v "os.environ\|settings\|config"

# Verificar batch com queue:
grep -rn "queue\|worker\|celery\|background_task" lia-agent-system/app/ --include="*.py"
```

---

### DIMENSÃO 12: Governança e Resiliência IA

Verifica compliance, controle e recuperação de falhas no sistema de IA.

> **Código:** `lia-agent-system/app/shared/compliance/`, `lia-agent-system/app/shared/resilience/`

**Checklist:**

1. **LGPD / Privacidade**:
   - Dados pessoais de candidatos nunca enviados diretamente ao LLM sem anonimização?
   - Consentimento registrado antes de processar dados com IA?
   - Candidato pode solicitar exclusão de dados processados por IA?
   - Logs de IA não contêm PII (nome completo, CPF, email)?

2. **GovernanceRules**:
   - Regras de governança configuráveis por tenant?
   - Limites de score para decisão automática definidos (ex: auto-aprovar > 85, auto-rejeitar < 30)?
   - Decisões automáticas sempre têm justificativa textual (explainability)?
   - Human-in-the-loop obrigatório para decisões de rejeição?

3. **Feature Flags IA**:
   - Cada capability IA tem feature flag independente?
   - Flags documentadas: `ENABLE_LLM_SUBSTATUS_PREDICTION`, `ENABLE_WEBHOOK_*`, etc.
   - Desligar flag desabilita graciosamente (não estoura com erro)?
   - Flags configuráveis por tenant (tenant A pode ter WSI habilitado, tenant B não)?

4. **Retry e Circuit Breaker**:
   - Chamadas LLM têm retry com exponential backoff?
   - Circuit breaker: se provider falha N vezes consecutivas, para de tentar por X minutos?
   - Timeout configurável por tipo de operação (chat rápido: 10s, análise WSI: 60s)?
   - Estado de circuit breaker logado e monitorável?

5. **Monitoramento e Observabilidade**:
   - Latência de cada chamada LLM logada?
   - Taxa de erro por provider/domínio rastreável?
   - Alertas configurados para anomalias (custo diário > threshold, latência > 30s)?
   - Dashboard ou endpoint de métricas IA acessível?

6. **Auditoria de Decisões IA**:
   - Toda decisão IA (score, recomendação, rejeição) tem audit trail?
   - Audit trail inclui: timestamp, modelo usado, prompt (hash), input (hash), output, score, decisão?
   - Audit trail imutável (append-only, não pode ser editado ou deletado)?

7. **Circuit Breaker (3 estados — Crença #7 do Manifesto)**:
   - Serviços externos usam Circuit Breaker com 3 estados (CLOSED → OPEN → HALF_OPEN)?
   - Configs por serviço: `failure_threshold`, `recovery_timeout`?
   - Estado de circuit breaker logado e monitorável?

8. **TokenTrackingService (Crença #9)**:
   - Chamadas LLM rastreiam tokens via `TokenTrackingService`?
   - Registro inclui: `user_id`, `company_id`, `agent_type`, `model`, `input_tokens`, `output_tokens`, `latency_ms`?
   - Budget por empresa verificado antes de chamadas (`check_limits()`)?

9. **ConfidencePolicyService (Crença #10)**:
   - Decisões IA usam os 3 tiers de confiança do `ConfidencePolicyService`?
   - Tier adequado aplicado por tipo de decisão?

10. **Anti-sycophancy (Crença #11)**:
    - Benchmarks setoriais (8 benchmarks) são consultados antes de gerar avaliações?
    - Regras 145/147 aplicadas?

> Para verificação completa de governança e crenças, usar skill **wedo-governance**

**Como executar:**
```bash
# Verificar anonimização antes de LLM:
grep -rn "anonymize\|mask\|redact\|pii" lia-agent-system/app/ --include="*.py"

# Verificar feature flags IA:
grep -rn "feature_flag\|ENABLE_\|is_enabled" lia-agent-system/app/ --include="*.py"

# Verificar retry/circuit breaker:
grep -rn "retry\|backoff\|circuit_breaker\|max_retries" lia-agent-system/app/ --include="*.py"

# Verificar audit trail:
grep -rn "audit_log\|audit_trail\|decision_log" lia-agent-system/app/ --include="*.py"

# Verificar TokenTrackingService:
grep -rn "TokenTrackingService\|token_tracking\|track_tokens" lia-agent-system/app/ --include="*.py"

# Verificar ConfidencePolicyService:
grep -rn "ConfidencePolicyService\|confidence_policy" lia-agent-system/app/ --include="*.py"

# Verificar Circuit Breaker 3 estados:
grep -rn "CircuitBreaker\|HALF_OPEN\|circuit_breaker" lia-agent-system/app/ --include="*.py"
```

---

### DIMENSÃO 13: Segurança e Proteção de Dados

Verifica se o sistema é seguro contra ataques e vazamento de dados.

> **Transversal:** Aplica-se a frontend, backend e camada IA

**Checklist:**

1. **Secrets e API Keys**:
   - Nenhuma chave API hardcoded em código (usar `os.environ`, `process.env`, ou Replit secrets)?
   - Secrets nunca logados (nem em debug, nem em error handlers)?
   - Secrets nunca expostos em respostas de API ou frontend?
   - `.env` / `.env.local` no `.gitignore`?

2. **Sanitização de Input**:
   - Inputs de texto sanitizados contra XSS (HTML entities escapados)?
   - Queries SQL usam parameterized queries / ORM (nunca string concatenation)?
   - Uploads validados: tipo MIME, tamanho máximo, extensão permitida?

3. **Prompt Injection**:
   - Input do usuário NUNCA concatenado diretamente no system prompt?
   - Separação clara entre instruções do sistema e dados do usuário no prompt?
   - Detecção de tentativas de jailbreak (instruções como "ignore previous instructions")?
   - Output do LLM sanitizado antes de renderizar no frontend?

4. **Autenticação e Autorização**:
   - Endpoints protegidos por autenticação (JWT/session)?
   - Autorização por role (admin, recruiter, viewer) em endpoints sensíveis?
   - Tenant isolation: usuário do tenant A NUNCA acessa dados do tenant B?
   - Tokens com expiração adequada (não tokens eternos)?

5. **Rate Limiting**:
   - Endpoints de login com rate limiting (prevenir brute force)?
   - Endpoints de IA com rate limiting por tenant (prevenir abuso de tokens)?
   - Rate limit com resposta informativa (429 + Retry-After header)?

6. **Dados Sensíveis**:
   - CPF, email, telefone de candidatos nunca em logs plaintext?
   - Dados pessoais criptografados em repouso (at-rest encryption)?
   - Comunicação via HTTPS (nunca HTTP em produção)?
   - Sessão/cookies com flags `httpOnly`, `secure`, `sameSite`?

7. **PII Masking (Guia v3.3 — PIIMaskingFilter)**:
   - `PIIMaskingFilter` aplicado em todos os loggers que processam dados de candidatos?
   - Nenhum PII (nome, CPF, email, telefone) persiste em logs ou outputs de LLM?

8. **Consent Management (Guia v3.3 — consent_management.py)**:
   - Consentimento verificado antes de processar dados com IA (`consent_management.py`)?
   - Consentimento granular por tipo de processamento?
   - Portal do Titular acessível para revogação?

> Para verificação completa de LGPD, EU AI Act e proteção de dados, usar skill **lgpd-data-protection**

**Como executar:**
```bash
# Buscar API keys hardcoded:
grep -rn "sk-\|api_key.*=.*['\"]" lia-agent-system/ plataforma-lia/ --include="*.py" --include="*.ts" --include="*.tsx" | grep -v "os.environ\|process.env\|env\.\|config\."

# Buscar SQL injection:
grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*UPDATE\|f\".*DELETE" lia-agent-system/app/ --include="*.py"

# Buscar prompt injection risks:
grep -rn "user_input.*prompt\|message.*system_prompt\|f\".*{user" lia-agent-system/app/ --include="*.py"

# Verificar tenant isolation:
grep -rn "tenant_id" lia-agent-system/app/api/ --include="*.py" | head -20

# Verificar rate limiting:
grep -rn "rate_limit\|throttle\|RateLimiter" lia-agent-system/app/ --include="*.py"

# Verificar PIIMaskingFilter:
grep -rn "PIIMaskingFilter\|pii_mask\|pii_filter" lia-agent-system/app/ --include="*.py"

# Verificar consent management:
grep -rn "consent_management\|check_consent\|ConsentManager" lia-agent-system/app/ --include="*.py"
```

---

### DIMENSÃO 14: Performance e Escalabilidade

Verifica se o sistema performa adequadamente sob carga real.

> **Transversal:** Aplica-se a frontend, backend e camada IA

**Checklist:**

1. **Queries N+1**:
   - Listagens de candidatos usam JOIN/include, não queries em loop?
   - Pipeline view carrega dados em 1-2 queries, não N queries por candidato?
   - ORM com eager loading configurado para relações frequentes?

2. **Cache**:
   - Redis usado para: conversas ativas, embeddings, resultados de routing, WSI scores?
   - Cache invalidado corretamente quando dados mudam?
   - TTL adequado (conversas: 30min, embeddings: 24h, config: 1h)?
   - Cache miss não estoura em erro (fallback para DB/API)?

3. **Timeouts LLM**:
   - Timeout configurado por tipo de chamada (chat: 10-15s, análise: 30-60s, batch: 120s)?
   - Timeout não trava a UI (loading spinner + cancel option)?
   - Chamadas LLM longas em background job, não em request-response?

4. **Paginação Real**:
   - Listagens grandes usam cursor-based ou offset pagination?
   - Nunca `SELECT * FROM candidates` sem LIMIT?
   - Frontend usa infinite scroll ou pagination component (DS §2.16)?
   - API retorna `total_count`, `has_more`, `next_cursor`?

5. **Bundle Size Frontend**:
   - Code splitting por rota (lazy loading de páginas)?
   - Imports específicos (não `import * from 'library'`)?
   - Imagens otimizadas (WebP, lazy loading, srcset)?
   - Dependências pesadas (charts, editors) carregadas sob demanda?

6. **Operações em Lote (Bulk)**:
   - Triagem em massa usa queue + worker, não loop síncrono?
   - Envio de emails em lote usa fila com rate limiting?
   - Progresso reportado ao usuário (barra de progresso, não spinner eterno)?
   - Resultados parciais disponíveis antes do lote completar?

7. **Conexões e Recursos**:
   - Pool de conexões DB configurado (não abre/fecha conexão a cada request)?
   - Conexões WebSocket gerenciadas (cleanup, reconexão, heartbeat)?
   - Memory leaks: event listeners removidos em cleanup? Subscriptions canceladas?
   - Arquivos temporários removidos após processamento?

**Como executar:**
```bash
# Buscar queries N+1 (queries em loop):
grep -rn "for.*in.*:\n.*\.query\|for.*in.*:\n.*await.*find" lia-agent-system/app/ --include="*.py"

# Verificar paginação:
grep -rn "LIMIT\|offset\|cursor\|paginate" lia-agent-system/app/ --include="*.py"

# Verificar timeouts:
grep -rn "timeout\|TIMEOUT" lia-agent-system/app/ --include="*.py"

# Verificar bundle splitting no frontend:
grep -rn "lazy\|dynamic\|React.lazy\|next/dynamic" plataforma-lia/src/ --include="*.tsx" --include="*.ts"

# Verificar pool de conexões:
grep -rn "pool_size\|max_connections\|connection_pool" lia-agent-system/app/ --include="*.py"
```

---

## Formato de Relatório

Ao final da auditoria, produzir relatório no formato:

```
## Relatório de Auditoria — [Nome da Feature]

### Resumo
- Total itens verificados: X
- ✅ Aprovados: X
- ⚠️ Parciais: X
- ❌ Faltando: X
- N/A: X

### Dimensão 1: Integração (Wiring)
- ✅ Hook useX conectado ao ComponenteY
- ❌ Hook useInterpretContext criado mas NÃO conectado ao UniversalTransitionModal
- ✅ Endpoint /interpret-context tem proxy e hook

### Dimensão 2: Fluxo de Dados
- ✅ Dados fluem do backend ao componente
- ⚠️ Sub-status salvo localmente mas não persistido via API

[... continua para todas as 14 dimensões ...]

### Ações Necessárias (ordenadas por prioridade)
1. 🔴 CRÍTICO: Conectar useInterpretContext ao modal
2. 🟡 IMPORTANTE: Adicionar persistência de sub-status
3. 🟢 MENOR: Adicionar aria-labels nos botões de ícone
```

---

## Quando NÃO Pular Dimensões

### Para Features de Frontend/Produto:
- Features pequenas (1 arquivo): Dimensão 1 (wiring) + Dimensão 3 (UI/DS) + Dimensão 6 (fluxo)
- Ajustes de estilo: Dimensão 3 (UI/DS v4.2.1) + Dimensão 7 (consistência)
- Novas telas/páginas: Dimensões 1-8 obrigatórias + D13 (segurança) + D14 (performance)

### Para Features de IA/Backend:
- Novo domínio/agente: Dimensões 9, 10, 11, 12 obrigatórias + D4 (backend) + D13 (segurança)
- Novo prompt/intent: Dimensão 10 (qualidade LLM) + D12 (governança)
- Nova integração externa: Dimensão 11 (serviços) + D13 (segurança) + D14 (performance)
- Feature flag IA: Dimensão 12 (governança)

### Para Features Full-Stack:
- Pipeline/transição: TODAS as 14 dimensões obrigatórias
- Correções de bug: Dimensão 2 (dados) + Dimensão 6 (fluxo) + dimensão do layer afetado

## Atalho para Auditorias Rápidas (Ajustes Menores)

Para mudanças menores (< 3 arquivos, sem novos endpoints):
1. Dimensão 1 (Wiring) — tudo conectado?
2. Dimensão 3 (UI/DS v4.2.1) — visível e conforme ao design system?
3. Dimensão 6 (Fluxo) — funciona ponta a ponta?
4. Dimensão 13 (Segurança) — não expõe dados ou secrets?

---

## Arquivos-Chave da Plataforma para Referência

### Frontend (plataforma-lia/)
- Componentes Kanban: `src/components/kanban/components/`
- Hooks Kanban: `src/components/kanban/hooks/`
- Constantes/Tipos: `src/components/kanban/constants.ts`, `src/components/kanban/types.ts`
- Utils: `src/components/kanban/utils/`
- Páginas: `src/components/pages/`
- Hooks globais: `src/hooks/`
- API Proxies: `src/app/api/backend-proxy/`
- Design Tokens CSS: `src/styles/design-tokens.css`
- Design Tokens TS: `src/lib/design-tokens.ts`
- Design System Doc: `docs/design-system/00-design-system-v4.md`

### Backend (lia-agent-system/)
- Endpoints: `app/api/v1/`
- Models: `app/models/`
- Schemas: `app/schemas/`
- Services: `app/services/`
- Domains: `app/domains/`

### IA / Agentes (lia-agent-system/)
- Domínios IA: `app/domains/` (estrutura DDD com múltiplos domínios de código)
- **Agentes ReAct ativos (7):** Wizard, Pipeline (PipelineTransitionAgent), Sourcing, Talent, JobsManagement, Kanban, Policy
- Orchestrador: `app/orchestrator/` (cascaded_router.py, orchestrator.py, state_manager.py, policy_engine.py)
- Shared IA: `app/shared/` (providers, prompts, intelligence, tools, memory, compliance, resilience)
- Prompts: `app/shared/prompts/`
- Tools: `app/shared/tools/`

### Documentação
- WeDO Talent Guide v3.3: `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md`
- Design System v4.2.1: `plataforma-lia/docs/design-system/00-design-system-v4.md`
- Arquitetura IA: `docs/lia-ai-architecture-cards-jira.md`
- Pipeline: `docs/pipeline-transition-system.md`
- MVP Alpha Roadmap: `docs/mvp-alpha-scenarios.md`
- Memória: `replit.md`

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Digite `/feature-audit` no chat para ativar a skill completa |
| **Cursor IDE** | Mencione `@.cursor/rules/feature-audit.mdc` no contexto ou ative a regra para o projeto |
| **GitHub / Outros** | Referencie diretamente: `.agents/skills/feature-audit/SKILL.md` |

**Quando ativar:**
- DEPOIS de implementar qualquer feature, ajuste ou correção
- ANTES de marcar qualquer tarefa como concluída
- Para auditoria rápida de mudanças menores: D1 + D5 + D7 + D13

---

## Boy Scout Rule (addendum v2 — orchestrator-aware)

> **Sempre deixe o codigo um pouco melhor do que voce achou.** Encontrou um `print()` na area que esta editando? Remova. Encontrou um `except: pass`? Substitua. Encontrou um `bg-blue-500`? Padronize. Pequenas correcoes oportunas evitam que divida tecnica vire bola de neve.

Limites do Boy Scout em `feature-audit`:
- Aplicar **apenas** em arquivos que voce ja esta tocando para a tarefa principal.
- Limitar a 3-5 correcoes pequenas — se ha mais que isso, abrir task separada.
- Nunca refatorar arquitetura "de passagem" — isso vira refactor real (modo REFACTOR + `canonical-fix`).

## Cross-references com a cascata (orchestrator)

Esta skill e ATIVADA sempre ao final de modo BUILD/REFACTOR/AUDIT pela `lia-orchestrator`. Quando uma dimensao falha, dispare a skill correspondente:

| Dimensao falha | Skill a acionar |
|---|---|
| D1 Integracao, D7 Consistencia, D13 Seguranca/duplicatas | `canonical-fix` |
| D3 UI/DS | `design-standardize` (+ `frontend-design` se for tela nova de entrada) |
| D4 Backend | `backend-quality` |
| D7 Tipos / contratos | `backend-quality` (Pydantic) ou `vue-migration-prep` (props) |
| D9 Arquitetura de agentes, D10 Qualidade LLM, D12 Governanca IA | `ai-architecture` + `lia-compliance` PARTE 1 + PARTE 3 |
| D11 Servicos IA / integracoes | `integration-patterns` |
| D13 Seguranca/PII, D14 Performance | `lia-compliance` PARTE 4 + `backend-quality` PARTE 4 (N+1) |

