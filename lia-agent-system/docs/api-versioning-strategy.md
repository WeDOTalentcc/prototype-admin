# API Versioning Strategy — lia-agent-system

**Status:** Active  
**Created:** 2026-06-17  
**Gap:** GAP-08-004

## Princípio

Toda a API pública do lia-agent-system vive sob `/api/v1/`. Esta versão permanece estável enquanto pudermos adicionar funcionalidade de forma backwards-compatible (additive-only changes).

## Quando criar v2

Uma **breaking change** exige nova versão. São breaking changes:
- Remover campo obrigatório de request/response
- Mudar tipo de campo existente (ex: `string` → `object`)
- Mudar semântica de campo existente (ex: `status` enum → string livre)
- Remover endpoint inteiramente
- Mudar método HTTP de endpoint (ex: GET → POST)
- Mudar código de status HTTP de sucesso (ex: 200 → 201)

**Não são** breaking changes (não requerem v2):
- Adicionar campo **opcional** a response (consumers devem ignorar campos desconhecidos)
- Adicionar campo **opcional** a request com valor default razoável
- Adicionar novo endpoint
- Melhorar mensagens de erro (desde que o campo `error` continue existente)

## Processo para criar v2

1. Criar `app/api/v2/` com os endpoints que mudam
2. Manter `v1` funcionando — deprecação não é remoção imediata
3. Adicionar headers de deprecação em v1 (ver abaixo)
4. Anunciar sunset date com no mínimo 90 dias de antecedência
5. Remover v1 somente após sunset date

## Headers de deprecação (RFC 8594)

Quando um endpoint v1 for deprecado, adicionar:

```python
response.headers["Deprecation"] = "true"
response.headers["Sunset"] = "Sat, 01 Jan 2027 00:00:00 GMT"
response.headers["Link"] = '</api/v2/endpoint>; rel="successor-version"'
```

## Contrato de compatibilidade

Todos os consumers devem:
- Usar `response?.field ?? defaultValue` — nunca assumir que campo existe
- Ignorar campos desconhecidos no lado consumer
- Não depender da ordem de campos em objetos JSON

## Referência

- RFC 8594 — Sunset HTTP Header Field
- `app/shared/types.py` WeDoBaseModel garante `extra='forbid'` nos requests
