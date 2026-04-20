# STATUS — `app/domains/technical_tests`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Produto — Squad de Avaliações Técnicas.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~276 (Python) — `dependencies.py` +
  `repositories/technical_tests_repository.py`.
- **Conteúdo:** repositório de provas técnicas e resultados.
- **Importadores externos:** `app/api/v1/technical_tests.py` (11
  endpoints).
- **Endpoints REST ativos:** sim — 11 endpoints.
- **Testes existentes:** ❌ nenhum dedicado.
- **`@register_domain`:** ❌ não registrado.

## Classificação
**Categoria 4 — Feature REST candidata a chat domain.** Estado idêntico ao
`workforce/`: só repositório + endpoints. Sem services nem agente.

## Plano de evolução
1. Cobrir repositório com testes de integração.
2. Adicionar services (geração de prova, correção automática, ranking).
3. Avaliar se deve ser chat domain próprio ou virar tools dentro de
   `cv_screening` (que já lida com avaliação técnica via WSI).

## Regra anti-deleção
🛑 **NÃO DELETAR.** 11 endpoints REST dependem deste repositório. Deleção
quebra a tela de provas técnicas.

## Cobertura mínima de testes exigida
- Cada novo método de repositório exige teste de integração.
- Se virar chat domain: pelo menos 1 teste de `execute_action` por action.
