# STATUS — `app/domains/workforce`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Produto — Squad de Workforce Planning.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~338 (Python) — `dependencies.py` +
  `repositories/workforce_repository.py`.
- **Conteúdo:** repositório de planejamento de força de trabalho.
- **Importadores externos:** `app/api/v1/workforce.py` (22 endpoints),
  `app/api/v1/workforce_planning.py` (7 endpoints).
- **Endpoints REST ativos:** sim — 29 endpoints somando os dois routers.
- **Testes existentes:** ❌ nenhum dedicado.
- **`@register_domain`:** ❌ não registrado.

## Classificação
**Categoria 4 — Feature REST candidata a chat domain.** Tem 29 endpoints
ativos servindo o frontend, mas nenhum service nem agente. É praticamente
só camada de dados. Promoção a chat domain exige construir services e
agente primeiro.

## Plano de evolução
1. Cobrir o repositório com testes de integração.
2. Adicionar services de análise (gap de headcount, projeção de
   contratação) antes de chat domain.
3. Decidir com produto se vira `workforce_planning` chat domain ou se
   permanece como feature REST + agregada em `analytics`.

## Regra anti-deleção
🛑 **NÃO DELETAR.** 29 endpoints REST dependem deste repositório. Deleção
quebra a tela de planejamento de força de trabalho.

## Cobertura mínima de testes exigida
- Cada novo método de repositório exige teste de integração com banco
  fake.
