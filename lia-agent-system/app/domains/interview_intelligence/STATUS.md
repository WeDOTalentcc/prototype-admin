# STATUS — `app/domains/interview_intelligence`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Produto — Squad de Inteligência de Entrevista.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~1.865 (Python) em 6 services.
- **Conteúdo:** `bias_detector_service.py`, `comparative_analysis_service.py`,
  `feedback_generator_service.py`, `strategic_opinion_service.py`,
  `interview_wsi_service.py`, `transcription_service.py`.
- **Importadores externos:** `app/domains/talent_intelligence/tools/interview_intelligence_tools.py`
  (≥13 referências), `app/api/v1/interviews.py`, `app/api/v1/interview_notes.py`,
  `app/api/v1/interview_analysis.py`.
- **Endpoints REST ativos:** sim — `interviews.py` (15 endpoints),
  `interview_notes.py` (7 endpoints), `interview_analysis.py` (5 endpoints).
- **Testes existentes:** ❌ nenhum dedicado.
- **`@register_domain`:** ❌ não registrado como chat domain.

## Classificação
**Categoria 4 — Feature REST candidata a chat domain.** Hoje serve apenas
como backend REST. Tem services maduros (bias detection, comparative
analysis, opinião estratégica) que poderiam virar `interview_intelligence`
domain no chat unificado, ao estilo `agent_studio`.

## Plano de evolução
1. Cobrir services existentes com testes unitários (bias_detector e
   comparative_analysis primeiro — são os mais usados pelo frontend).
2. Definir 5–8 actions iniciais (`compare_interviews`, `detect_bias`,
   `generate_feedback`, `summarize_panel`, etc.).
3. Criar `domain.py` com `@register_domain`, `_ACTION_TOOL_MAP` e tools.
4. Adicionar agent-types ao `AGENT_TYPE_TO_DOMAIN`.
5. Atualizar relatório Fase 2C movendo para a tabela dos registrados.

## Regra anti-deleção
🛑 **NÃO DELETAR.** Endpoints REST em `app/api/v1/interview*` dependem
diretamente destes services. Deletar quebra a tela de entrevistas no
frontend.

## Cobertura mínima de testes exigida
- Cada service novo deve ter teste unitário cobrindo input válido + um modo
  de falha.
- Antes de promover a chat domain: 1 teste de `execute_action` por action
  prevista.
