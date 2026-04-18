# Skills da Plataforma LIA — Guia de Uso por Momento

16 skills organizadas por QUANDO usar. Cada skill tem um gatilho claro.

---

## FASE 1: ANTES DE CODIFICAR

Usar quando vai iniciar trabalho novo (feature, refactor, bug fix).

| Skill | Gatilho | O que faz |
|-------|---------|-----------|
| **lia-planning** | "vamos comecar", "novo sprint", "bug fix", "especificar feature", "brainstorming" | 4 modos (Bug Fix / Feature / Refactor / Sprint) + spec-driven (4 fases) + brainstorming estruturado |
| **feature-impact** | "quero criar X", "vamos ajustar Y" | Analisa impacto em 13 dimensoes antes de escrever codigo |

**Fluxo recomendado:** `lia-planning` (define modo + spec) -> `feature-impact` (mapeia impacto) -> codificar

---

## FASE 2: DURANTE O DESIGN / UI

Usar quando vai criar ou modificar interface visual.

| Skill | Gatilho | O que faz |
|-------|---------|-----------|
| **frontend-design** | Criar tela nova, "quero algo bonito/marcante" | Direcao estetica, anti-patterns "AI slop", exemplos de codigo |
| **design-standardize** | Criar qualquer componente de interface | Tokens DS v4.2.1, regra 90/10, tipografia, dark mode |
| **design-patterns** | Componente complexo, muitas props, refatorar arquitetura | GoF patterns + React Composition Patterns (compound components, evitar boolean props) |

**Fluxo recomendado:** `frontend-design` (PASSO 0 intencao) -> `design-standardize` (aplica tokens) -> `design-patterns` (se complexo)

---

## FASE 3: DURANTE A IMPLEMENTACAO

Usar enquanto escreve codigo.

| Skill | Gatilho | O que faz |
|-------|---------|-----------|
| **lia-testing** | Criar feature, refatorar, criar agente IA, escrever testes | TDD (Red/Green/Refactor) + piramide 5 camadas + evals IA (golden dataset, LLM-as-judge) |
| **vue-migration-prep** | Criar/refatorar componente React | Garante que o codigo sera portavel para Vue/Nuxt no futuro |

**Fluxo recomendado:** `lia-testing` (teste primeiro) + `vue-migration-prep` (portabilidade) em paralelo

---

## FASE 4: VALIDACAO E QUALIDADE

Usar DEPOIS de implementar, antes de entregar.

| Skill | Gatilho | O que faz |
|-------|---------|-----------|
| **feature-audit** | Feature pronta, antes de marcar como concluida | Auditoria em 14 dimensoes: integracao, dados, UI, backend, tipos, fluxo |
| **browser-use** | Testar fluxo real no browser, preencher formularios, screenshots | Automacao de browser para validacao visual e funcional |

**Fluxo recomendado:** `feature-audit` (checklist) -> `browser-use` (validar no browser)

---

## FASE 5: COMPLIANCE E GOVERNANCA

Usar quando a feature toca dados pessoais, avaliacao de candidatos ou agentes IA.

| Skill | Gatilho | O que faz |
|-------|---------|-----------|
| **lia-compliance** | Feature nova, agente, screening, dados pessoais, deploy producao | Unifica: Governanca WeDO (13 Crencas, 18 Production Readiness), Screening/WSI, DEI/Fairness (FairnessGuard), LGPD (PII, DSR, EU AI Act) |

**Fluxo recomendado:** Carregar `lia-compliance` e navegar para a PARTE relevante (1-4)

---

## UTILITARIAS (sob demanda)

Usar quando precisa de uma funcionalidade especifica.

| Skill | Gatilho | O que faz |
|-------|---------|-----------|
| **humanizer** | "texto parece IA", "melhorar escrita" | Remove sinais de escrita generada por IA |
| **pdf** | Qualquer operacao com arquivos PDF | Ler, criar, combinar, dividir, OCR |
| **pptx** | Qualquer operacao com apresentacoes PowerPoint | Criar, ler, editar slides |
| **agent-tools** | "gerar imagem", "rodar modelo IA", "buscar na web" | 150+ apps IA via inference.sh |
| **find-skills** | "existe skill para X?", "como faco Y?" | Descobre skills disponiveis |
| **skill-creator** | "criar nova skill", "melhorar skill existente" | Meta-skill para criar/otimizar skills |

---

## COMO PEDIR PARA USAR UMA SKILL

Nao precisa lembrar os nomes. Basta descrever o que quer:

| Voce diz | Skill que ativa |
|----------|----------------|
| "vamos comecar uma feature nova" | lia-planning + feature-impact |
| "cria uma tela bonita de login" | frontend-design + design-standardize |
| "refatora este componente" | design-patterns + vue-migration-prep |
| "esta pronto, verifica" | feature-audit |
| "toca dados de candidatos" | lia-compliance (PARTEs 3 e 4) |
| "quero testar no browser" | browser-use |
| "o texto ficou com cara de IA" | humanizer |
| "preciso de um PDF" | pdf |
| "vou fazer deploy" | lia-compliance (Production Readiness Gate) |
| "escrever testes primeiro" | lia-testing (TDD) |
