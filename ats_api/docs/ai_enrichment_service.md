# AI Enrichment Service

## 📝 Overview

O **AI Enrichment Service** enriquece automaticamente o perfil de candidatos (SourcedProfile) com informações estruturadas extraídas da análise de IA, criando:

- **Skills** (competências técnicas)
- **SkillRelationships** (associações de skills com níveis)
- **Expertise** (highlights técnicos e de carreira)
- **Enrichment Metadata** (metadados sobre o enriquecimento)

## 🚀 Como Funciona

### Fluxo Automático

1. **AI Analysis Job** analisa o currículo do candidato via Gemini
2. Salva a análise no `SourcedProfileSourcing`
3. **AI Enrichment Service** é chamado automaticamente
4. Extrai skills, expertise e metadata da análise
5. Salva tudo estruturado no `SourcedProfile`

### Exemplo de Análise AI

```json
{
  "skills_assessment": {
    "strong": ["Ruby", "Rails", "PostgreSQL", "Redis"],
    "mentioned": ["Docker", "AWS", "React"]
  },
  "highlights": [
    {
      "type": "technical_depth",
      "description": "Solid experience with Ruby on Rails ecosystem"
    }
  ]
}
```

### Resultado no SourcedProfile

**Skills Created:**
- Ruby (level_skill: 3 - Advanced)
- Rails (level_skill: 3 - Advanced)
- Docker (level_skill: 2 - Experienced)

**Expertise Added:**
```json
[
  {
    "type": "technical_depth",
    "description": "Solid experience with Ruby on Rails ecosystem",
    "source": "ai_analysis",
    "confidence": "high",
    "added_at": "2026-02-17T14:30:00Z"
  }
]
```

**Profile Data Metadata:**
```json
{
  "enrichment": {
    "enriched_at": "2026-02-17T14:30:00Z",
    "enrichment_source": "ai_analysis",
    "sourcing_id": 658,
    "ai_score": 85,
    "ai_confidence": "high",
    "skills_extracted": 7,
    "highlights_added": 2
  }
}
```

## 🔧 Uso Manual

```ruby
# Via SourcedProfileSourcing (recomendado)
sps = SourcedProfileSourcing.find(123)
enrichment = SourcedProfiles::AiEnrichmentService.new(sps)
enrichment.enrich!

# Verifica resultados
sps.sourced_profile.skills.pluck(:name)
# => ["Ruby", "Rails", "PostgreSQL", "Redis", "Docker", "AWS", "React"]

sps.sourced_profile.expertise
# => [{"type"=>"technical_depth", "description"=>"..."}]
```

## ✨ Benefícios

### Para Conversão Candidate
Quando o `SourcedProfile` for convertido em `Candidate`:
- **Skills já criadas** → transferência automática
- **Expertise estruturada** → currículo enriquecido
- **Metadata de qualidade** → confiança na análise

### Para Busca e Matching
- **Skills indexadas** → busca por competência
- **Níveis de proficiência** → filtragem por senioridade
- **Highlights** → resumo executivo automático

### Para Recrutadores
- **Perfil completo** → visão 360° do candidato
- **Skills validadas pela IA** → reduz viés
- **Expertise destacada** → foco no que importa

## 📊 Dados Extraídos

### Skills Assessment
- **strong**: Level 3 (Advanced) - habilidades dominantes
- **mentioned**: Level 2 (Experienced) - habilidades mencionadas

### Highlights
- `career_progression` - Progressão de carreira
- `technical_depth` - Profundidade técnica
- `international_exposure` - Experiência internacional
- `industry_match` - Match com indústria
- `leadership` - Liderança
- `education` - Formação acadêmica

## 🧪 Testes

```bash
docker compose exec web bundle exec rspec spec/services/sourced_profiles/ai_enrichment_service_spec.rb
```

**13 examples, 0 failures** ✅

### Casos Cobertos
- Criação de skills e relationships
- Níveis de proficiência corretos
- Prevenção de duplicatas
- Reuso de skills existentes
- Handling de análise vazia
- Metadata estruturada

## 🔄 Integração

### Job que Chama o Enrichment
`app/jobs/sourced_profiles/ai_analysis_job.rb`

```ruby
def handle_success(sourced_profile_sourcing, profile, result)
  # Salva análise
  sourced_profile_sourcing.update!(
    score: result[:score],
    analysis: insights,
    ai_metadata: metadata
  )

  # Enriquece profile (AUTOMÁTICO)
  enrich_profile_with_ai_data(sourced_profile_sourcing)
end
```

## 📈 Métricas

### Por Enrichment
- Skills extraídas
- Highlights adicionados
- Timestamp de enriquecimento
- Score e confiança da IA

### Exemplo Real
```ruby
profile.profile_data["enrichment"]
# => {
#   "enriched_at" => "2026-02-17T14:30:00Z",
#   "skills_extracted" => 7,
#   "highlights_added" => 2,
#   "ai_score" => 85,
#   "ai_confidence" => "high"
# }
```

## 🎯 Próximos Passos

1. **Auto-categorização de Skills** - Associar `skill_category_id`
2. **Extração de Experiências** - Criar `Experience` records
3. **Extração de Educação** - Criar `Education` records
4. **Certificações** - Popular `certifications_data`
5. **Idiomas** - Popular `languages_data` com níveis

## 🚨 Importante

- Enrichment é **idempotente** - rodar múltiplas vezes não duplica
- Skills são **case-insensitive** - "Ruby" = "ruby" = "RUBY"
- Expertise **não duplica** - check por `description`
- **Transaction-safe** - tudo ou nada

## 📝 Logs

```
[AiEnrichment] Extracting 7 skills
[AiEnrichment] Created skill relationship: Ruby (level: 3)
[AiEnrichment] Created skill relationship: Docker (level: 2)
[AiEnrichment] Added 2 expertise items
[AiEnrichment] Added enrichment metadata
[AiEnrichment] Enriched SourcedProfile #123
```

---

**Status**: ✅ Production Ready  
**Tests**: 13/13 passing  
**Coverage**: Core functionality
