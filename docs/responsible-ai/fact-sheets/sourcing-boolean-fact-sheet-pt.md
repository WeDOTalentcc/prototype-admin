# AI Fact Sheet — Sourcing e Boolean Search

*Última atualização: 2026-04-23 | Idioma: PT-BR | [English version](./sourcing-boolean-fact-sheet-en.md)*

## 1. Propósito

O Sourcing é responsável por buscar ativamente candidatos — primeiro no banco interno (PostgreSQL), depois em fontes externas (Pearch AI com 190M+ perfis) — gerando strings booleanas otimizadas e rankeando por relevância à vaga. Também conduz outreach inicial via WhatsApp/LinkedIn quando configurado. Objetivo: **ampliar o pool de candidatos de forma imparcial**.

## 2. Inputs

- Requisitos da vaga (skills mandatórias, experiência mínima, localização, modelo de trabalho)
- Strings de busca do recrutador (livre ou estruturada)
- Fonte desejada (banco local / Pearch AI / ambos)
- Filtros adicionais (senioridade, idiomas, disponibilidade)

## 3. Outputs

- Boolean string otimizada (ex: `"React" AND "Sênior" AND ("TypeScript" OR "Next.js") NOT "Pleno"`)
- Lista de candidatos encontrados (ordenada por relevância)
- Longlist inicial (tipicamente 20-50 candidatos)
- Mensagens de outreach personalizadas (se ativado)
- Diagnóstico do resultado (pool saudável? precisa expandir critérios?)

## 4. Modelo e Arquitetura

- **Modelo LLM base:** `claude-sonnet-4-5` (Anthropic) para geração de boolean string e ranking semântico
- **Domain YAML canônico:** `app/prompts/domains/sourcing.yaml` (96 linhas, versão `2.0`, `updated_at: 2026-03-19`)
- **Agent:** `SourcingAgent` (em `app/domains/sourcing/`)
- **System prompt builder:** `SystemPromptBuilder.build(agent_type="sourcing")`
- **Integração externa:** Pearch AI API (banco externo de 190M+ perfis)

## 5. Atributos Protegidos — Cobertura

- 14 atributos protegidos via `protected_attributes.yaml` e FairnessGuard L1+L2+L3
- **Boolean string é validada antes da execução** — se contiver proxy discriminatório (ex: "bairro X" como proxy para classe social, "nome típico de" como proxy racial), FairnessGuard L1 bloqueia
- Regra canônica em `sourcing.yaml`: buscas são por competência e requisito objetivo, não por demografia
- **`orchestrator.yaml`** (atualizado 2026-04-23) tem regra explícita: *"Se o input contiver atributos protegidos como critério de filtro, classifique como intent='compliance_violation'"*

## 6. Métricas de Acurácia e Fairness

→ Ver seção 6 de `eu-ai-act-technical-documentation-pt.md` — métricas consolidadas. Sourcing monitora **queries com proxies** via `fairness_audit_log` — padrões sistemáticos detectados são escalados automaticamente. Próximo bias audit independente: Q3/2026.

## 7. Limitações Conhecidas

- **Dependência do banco:** candidatos precisam já ter consentido com LGPD no banco local ou estar em fontes externas com base legal adequada (Pearch AI é compliant).
- **Boolean string complexa:** strings com >10 operadores booleanos podem degradar performance da busca e ser rejeitadas pelo provider externo.
- **Idioma:** busca ativa funciona melhor em PT-BR e EN; idiomas menos comuns podem ter cobertura reduzida.
- **Outreach:** mensagens são templates personalizados, mas **não simulam conversa** com o candidato — recrutador deve validar cada outreach antes de envio.

## 8. Supervisão Humana (HITL)

- **Obrigatório:** recrutador aprova boolean string antes de execução em fontes externas (custo + LGPD)
- **Obrigatório:** outreach em massa exige confirmação explícita
- **Obrigatório:** se FairnessGuard bloquear query, recrutador recebe alerta educativo citando lei aplicável (Lei 9.029/95, LGPD Art. 20)
- **Opcional:** recrutador pode revisar e reordenar longlist antes de passar para CV Screening
- **Automatização mínima:** se `AUTONOMIA_LIA` configurada como alta, feature pode ativar buscas recorrentes — mas sempre com audit trail

## 9. Direitos do Candidato

- **Candidato encontrado via sourcing ativo:** é contactado via outreach com consentimento LGPD explícito (opt-in) antes de processar mais dados.
- **Direito de recusar:** se candidato recusa outreach, é marcado como "não-contatar" em `contact_preferences` — respeitado em buscas futuras.
- **Explicabilidade:** se candidato pedir explicação de por que foi contactado, recrutador acessa `audit_service` que registra a query + critérios técnicos usados. Endpoint `/api/v1/candidate/decisions/explain` retorna esse detalhe em linguagem simples.
- **Exclusão:** candidato pode solicitar remoção do banco local via `data_subject_request` (LGPD Art. 18).

## 10. Contatos

- **Compliance:** compliance@wedotalent.cc
- **Suporte:** support@wedotalent.cc
- **Privacidade (DPO):** dpo@wedotalent.cc

---

*Fonte canônica: `app/prompts/domains/sourcing.yaml` + `app/domains/sourcing/tools/` + `orchestrator.yaml` (atualizado 2026-04-23) + `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3. Zero invenção.*
