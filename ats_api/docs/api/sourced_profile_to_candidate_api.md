# API de Conversão SourcedProfile para Candidate/Apply

## Autenticação

Todas as requisições requerem autenticação via token Bearer no header:
```
Authorization: Bearer <token>
```

## Endpoints

### Importar SourcedProfile para Candidate

Converte um sourced_profile em candidate. Se o candidate já existir (mesmo external_id e provider), atualiza os dados.

```
POST /v1/users/sourced_profiles/:id/import
```

Resposta:
```json
{
  "data": {
    "message": "Candidato importado",
    "candidate": { ... },
    "created": true
  }
}
```

### Converter Múltiplos SourcedProfiles em Candidates

Converte múltiplos sourced_profiles em candidates em background.

```
POST /v1/users/sourced_profiles/convert_to_candidates
```

Body:
```json
{
  "sourced_profile_ids": [1, 2, 3]
}
```

Resposta:
```json
{
  "data": {
    "message": "Conversão iniciada em background",
    "sourced_profile_ids": [1, 2, 3],
    "total": 3
  }
}
```

### Criar Apply a partir de SourcedProfileSourcing

Cria um apply (candidatura) em uma vaga a partir de um sourced_profile_sourcing. Se o sourced_profile ainda não tiver um candidate associado, ele é convertido automaticamente.

```
POST /v1/users/applies/create_collection
```

Body (opção 1 - usando collections):
```json
{
  "collections": [
    {
      "reference_type": "SourcedProfileSourcing",
      "reference_id": 1
    }
  ],
  "apply": {
    "job_id": 1,
    "selective_process_id": 1,
    "selective_process_status": "active"
  }
}
```

Body (opção 2 - usando select_all_params para múltiplos):
```json
{
  "select_all_params": {
    "reference_type": "SourcedProfileSourcing",
    "where": { ... }
  },
  "apply": {
    "job_id": 1,
    "selective_process_id": 1,
    "selective_process_status": "active"
  }
}
```

Resposta:
```json
{
  "data": {
    "message": "1 aplicações criadas com sucesso."
  }
}
```

### Criar Apply a partir de SourcedProfile

Também é possível criar apply diretamente a partir de um sourced_profile:

```json
{
  "collections": [
    {
      "reference_type": "SourcedProfile",
      "reference_id": 1
    }
  ],
  "apply": {
    "job_id": 1,
    "selective_process_id": 1
  }
}
```

## Fluxo de Conversão

1. O sistema verifica se o sourced_profile já tem um `candidate_id`
2. Se não tiver, executa a conversão automaticamente usando `SourcedProfiles::ConvertToCandidateJob`
3. Cria o candidate com dados do sourced_profile (nome, email, telefone, skills, experiências, etc.)
4. Associa o candidate ao sourced_profile através do `candidate_id`
5. Cria o apply vinculando o candidate à vaga

## Observações

- A conversão de sourced_profile para candidate é automática quando necessário
- O candidate criado terá `source: 'sourcing'`
- Skills, experiências, educações e idiomas do sourced_profile são transferidos para o candidate
- Pin e confidential settings do sourced_profile são preservados no candidate

