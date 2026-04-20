# STATUS — `app/domains/journey_mapping`

> Fonte de verdade do estado deste dir. Alterar este arquivo exige PR explícito.
> Vinculado ao relatório `docs/fase2c_domain_verification_report.md` (seção
> "Diagnóstico dos Domínios em Desenvolvimento Estratégico").

## Dono
Produto — Squad de Recruitment Journey.

## Estado atual (auditoria 20/abr/2026)
- **Linhas de código:** ~245 (Python) — `dependencies.py` +
  `repositories/journey_mapping_repository.py`.
- **Conteúdo:** repositório CRUD para mapeamento de jornada do candidato.
- **Importadores externos:** `app/api/v1/journey_mapping.py` (13 endpoints),
  `app/api/v1/journey_intelligence.py`.
- **Endpoints REST ativos:** sim — 13 endpoints em `journey_mapping.py`.
- **Testes existentes:** ❌ nenhum dedicado.
- **`@register_domain`:** ❌ não registrado.

## Classificação
**Categoria 4 — Feature REST candidata a chat domain.** Atualmente é só
camada de dados + endpoints. Não tem agentes nem services de domínio.
Promoção a chat domain exige construir camada de service + agente primeiro.

## Plano de evolução
1. Adicionar services de leitura/análise (resumo de jornada, gargalos por
   etapa) antes de pensar em chat domain.
2. Cobrir `journey_mapping_repository.py` com pelo menos 1 teste de
   integração.
3. Decidir (com produto) se faz sentido virar chat domain ou se permanece
   como feature REST consumida pelo `analytics` domain.

## Regra anti-deleção
🛑 **NÃO DELETAR.** `app/api/v1/journey_mapping.py` e
`journey_intelligence.py` dependem deste repositório.

## Cobertura mínima de testes exigida
- Ao adicionar qualquer novo método no repositório, exigir teste de
  integração com banco fake (não inline-CREATE-TABLE — proibido por
  ARCHITECTURE.md).
