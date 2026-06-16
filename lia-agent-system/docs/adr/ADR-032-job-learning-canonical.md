# ADR-032 — JobPatternService é o canônico para aprendizado de padrões de vaga

**Data:** 2026-06-12
**Status:** Aceito
**Decisores:** Paulo Moraes

## Contexto

O módulo de aprendizado de padrões de criação de vaga () tinha menção
a um possível  como alternativa ao . Auditoria de
2026-06-12 confirmou que  nunca foi implementado em nenhum arquivo do
projeto.

## Decisão

 (, 944 LOC)
**é e permanece** o único serviço canônico para:

- Sugestões de wizard baseadas em histórico de vagas similares
- Recomendações de salário, skills, competências comportamentais
- Predição de time-to-fill baseada em padrões históricos
- Geração de success profile
- Registro de outcomes de vagas (hired, closed, expired)

O router  expõe este serviço via .

## Alternativas consideradas

- **Criar JdSimilarService**: Descartado — nunca foi implementado, JobPatternService
  cobre o mesmo domínio com 944 LOC em produção ativa.

## Consequências

- Não criar  — seria redundante com 
- Não criar nova implementação de "job learning" sem deprecar a existente
- Estender  para novas funcionalidades de aprendizado de padrões
-  router permanece o único ponto de acesso externo ao aprendizado
- Qualquer referência a "JdSimilarService" em código ou comentários é dead reference — remover
