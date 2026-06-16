# Como usar estes docs com Cursor / Claude Code

> Este arquivo contém **3 prompts prontos** para o time colar no assistente de IA.
> Os prompts cobrem todo o ciclo de implementação de um layer (Compliance, Infrastructure, Persona, Resilience, Agent Studio ou Operational).

---

## Visão geral

O kit do card Jira tem 3 tipos de arquivo:

| Tipo | Função |
|------|--------|
| Thematic docs (`themes/<layer>/<Cn>.md`) | Receitas operacionais — explicam **como** implementar |
| YAML bundles (`*_YAMLS_CANONICAL_BUNDLE.md`) | Conteúdo verbatim 100% dos YAMLs reais — fonte de **copy-paste** |
| `themes/README.md` | Índice master + ordem de execução recomendada |

O dev humano **não precisa** carregar arquivo por arquivo no chat — os 3 prompts abaixo instruem o assistente a ler tudo sozinho.

---

## Workflow do dev (10 passos)

1. **Jira:** baixa os anexos do card (docs do layer + bundles + README + este HOW_TO_USE)
2. **Repo v5:** salva tudo em `./docs/themes/` (mantendo subpastas: `compliance/`, `infrastructure/`, etc.)
3. **Cursor / Claude Code:** abre o repo v5
4. **Cola o Prompt 1 (Bootstrap)** trocando `<layer>` e respondendo SIM/NÃO sobre Replit
5. Assistente lê tudo sozinho e sugere o primeiro tema
6. **Cola o Prompt 2 (Implementar)** com o tema atual (ex: `C5`)
7. Implementa, revisa, commita
8. **Cola o Prompt 3 (Verificar)** com o mesmo tema
9. Corrige gaps reportados
10. Repete 6–9 para o próximo tema

---

## Ordem de execução recomendada (por card)

A ordem **não é** sequencial pelo número (C1→C2…). É a ordem de dependências.

| Card | Ordem |
|------|-------|
| Compliance | C5 → C1 → C7 → C2 → C3 → C4 → C6 → C8 |
| Infrastructure | I9 → I8 → I4 → I1 → I2 → I3 → I7 → I6 → I10 → I5 → I11 → I12 |
| Persona | P1 → P2 → P3 → P4 → P5 |
| Resilience | R1 → R3 → R4 → R2 |
| Agent Studio | AS1 (após I1+I2+I3+P1 prontos) |
| Operational | O1 + O2 desde o dia 1, O3 ao final |

O Prompt 1 (Bootstrap) instrui o assistente a confirmar essa ordem antes de começar.

---

## Cenário com vs sem SSH ao Replit

**Com SSH** (host alias `replit-wedo`):
- Validar implementação contra código vivo em `/home/runner/workspace/lia-agent-system/`
- Bundles servem como referência rápida; Replit é a fonte da verdade
- Recomendado para temas críticos (C1 Fairness, C5 Multi-tenancy, P1 System Prompt, I4 LLM Factory)

**Sem SSH:**
- Bundles são a única fonte verbatim
- Thematic docs + bundles são suficientes — todos os campos foram extraídos verbatim do código
- Risco: se YAML do Replit mudou após a data dos bundles, dev pode estar usando versão antiga (regerar bundle se houver dúvida)

---

# Prompt 1 — Bootstrap

> Cole **uma vez por card**, na primeira mensagem do chat com o assistente.

```
Vou implementar o layer <Compliance|Infrastructure|Persona|Resilience|Agent Studio|Operational>
do sistema LIA v4 no repo v5. Os arquivos de referência estão em ./docs/themes/.

Sua tarefa AGORA (NÃO implementar nada ainda):

1. Leia ./docs/themes/README.md — índice master.
2. Leia TODOS os arquivos em ./docs/themes/<layer>/ — receitas operacionais.
3. Leia os bundles YAML anexados — transcrições verbatim 100% dos YAMLs reais (copy-paste source).
4. Não invente. Se uma referência citar arquivo Python que ainda não existe no v5, é esperado — são os arquivos a CRIAR.
5. Acesso SSH ao Replit (host alias: replit-wedo) = <SIM|NÃO>. Se SIM, pode validar contra `/home/runner/workspace/lia-agent-system/` em caso de dúvida.

Quando terminar de ler, responda:
- Ordem recomendada dos temas (conforme README)?
- Qual tema começar primeiro?
- Pré-requisitos do v5 (DB, env vars, libs) que precisam estar prontos antes?
```

**Como usar:**
- Substitua `<Compliance|Infrastructure|Persona|Resilience|Agent Studio|Operational>` pelo nome do layer
- Substitua `<SIM|NÃO>` conforme você tem acesso SSH ao Replit
- O assistente lê tudo, valida coerência e propõe o tema inicial — **sem implementar**

---

# Prompt 2 — Implementar um tema

> Cole **uma vez por tema**, depois que o assistente sugerir o tema (ou você escolher).

```
Implementar tema <Cn|In|Pn|Rn|AS1|On> conforme ./docs/themes/<layer>/<doc>.md.

Protocolo:

1. Releia o doc do tema do começo ao fim.
2. Para cada arquivo Python listado:
   - Se já existe no v5, compare com o doc e proponha diff
   - Se não existe, crie seguindo o doc
3. Para cada YAML listado: copie verbatim do bundle — NÃO reescreva.
4. Respeite "NÃO pode adaptar" — regra legal/arquitetural imutável.
5. Use "Pode adaptar" para ajustar nomes/paths à estrutura do v5.
6. Ao final, rode mentalmente o checklist P0 do doc e me reporte gaps.

Constraints obrigatórios (CLAUDE.md):
- company_id sempre do JWT, nunca do payload
- Nunca usar raça/gênero/religião/saúde em decisão de IA
- LLM sempre via LLMFactory (não instanciar direto)
- Sem hardcoded secrets

Pode prosseguir.
```

**Como usar:**
- Substitua `<Cn|In|Pn|Rn|AS1|On>` pelo código do tema (ex: `C5`)
- Substitua `<layer>/<doc>.md` pelo path real (ex: `compliance/C5_MULTI_TENANCY_AND_ISOLATION.md`)
- Os 4 constraints obrigatórios são herdados de `CLAUDE.md` — não negociáveis

---

# Prompt 3 — Verificar (auditoria final do tema)

> Cole **ao final de cada tema**, depois de implementar e revisar.

```
Acabei de implementar o tema <Cn|In|...>.

Audite contra ./docs/themes/<layer>/<doc>.md:

1. Para cada item do checklist P0/P1/P2 do doc → ATENDIDO / NÃO ATENDIDO / N/A
2. Para cada arquivo Python que o doc lista → confirme que existe e cobre as responsabilidades
3. Para cada teste obrigatório → confirme que existe e roda
4. Liste gaps P0 (bloqueante) ou P1 (crítico)
5. Sugira testes adicionais para os gaps

Se SSH ao Replit disponível, valide comportamento contra `/home/runner/workspace/lia-agent-system/`.
```

**Como usar:**
- Substitua `<Cn|In|...>` pelo código do tema implementado
- O assistente faz uma auditoria item-a-item contra o checklist do doc
- **P0 bloqueante** = não merge antes de resolver
- **P1 crítico** = resolver no mesmo sprint

---

## Definition of Done por tema (Prompt 3 valida tudo)

- ✅ Todos os P0 do checklist atendidos
- ✅ Todos os arquivos Python documentados existem
- ✅ Todos os testes obrigatórios passam
- ✅ Code review por par com referência ao thematic doc
- ✅ Sem invenção: cada arquivo criado consta no doc

---

## FAQ rápido

**P: Preciso adicionar os arquivos manualmente no contexto do Cursor (`@file`)?**
R: Não. O Prompt 1 instrui o assistente a ler tudo sozinho a partir de `./docs/themes/`. Apenas garanta que a pasta está no repo aberto.

**P: O assistente vai pular temas?**
R: Não — o Prompt 1 pede a ordem antes de começar, e cada Prompt 2 é executado tema-a-tema sequencialmente.

**P: E se o doc disser "criar arquivo X" e ele já existir no v5?**
R: O Prompt 2 instrui o assistente a comparar e propor diff. Você decide se aceita.

**P: E se o YAML do Replit mudou depois que o bundle foi gerado?**
R: Se você tem SSH (Prompt 1 com SIM), o assistente valida contra o Replit. Sem SSH, regere o bundle puxando do Replit antes de começar o card.

**P: Posso pular o Prompt 3 (Verificar)?**
R: Não. O checklist P0/P1/P2 é a única forma de garantir que nada essencial ficou para trás. É 30s de copy-paste.

---

## Referências

- `themes/README.md` — índice master dos 33 docs
- `LIA_YAMLS_CANONICAL_BUNDLE.md` — verbatim de persona, compliance, guardrails, prompts, defensive
- `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md` — verbatim de compliance + fairness
- `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md` — 17 capabilities + agents_registry + tool_registry
