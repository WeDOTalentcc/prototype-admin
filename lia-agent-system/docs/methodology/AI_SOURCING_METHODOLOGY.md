# Metodologia de Busca de Candidatos - LIA Platform

## Visão Geral

A plataforma LIA utiliza uma metodologia multi-camadas para busca e match de candidatos, combinando técnicas tradicionais de recrutamento com inteligência artificial avançada.

---

## Arquitetura do Sistema de Sourcing

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCING AGENT (Ag.2)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Boolean    │  │   Semantic   │  │   Pearch AI  │          │
│  │   Builder    │  │   Search     │  │   External   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              CANDIDATE MATCHER                       │       │
│  │  (Skills + Experience + Location + Culture Fit)     │       │
│  └─────────────────────────────────────────────────────┘       │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              WSI SCORING (0-100)                     │       │
│  │  (WeDoTalent Skill Index + Bloom + Dreyfus)         │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Boolean Query Builder

### Descrição
Sistema que gera queries de busca avançadas compatíveis com múltiplas plataformas (LinkedIn, banco de dados interno, Pearch AI).

### Funcionamento

```python
# Exemplo de geração de query
query = BooleanQueryBuilder.build_query(
    title="Desenvolvedor Backend",
    skills=["Python", "Django", "PostgreSQL", "Docker"],
    companies=["Nubank", "iFood", "Stone"],
    location="São Paulo",
    seniority="senior",
    years_experience=5,
    exclude_terms=["Estagiário", "Trainee"]
)

# Resultado:
{
    "linkedin": '("Desenvolvedor Backend") AND "Python" AND "Django" AND "PostgreSQL" AND "São Paulo"',
    "database": '("Desenvolvedor Backend" OR "Backend Developer") AND ("Python" AND "Django" AND "PostgreSQL" AND "Docker") AND ("Senior" OR "Sênior" OR "Sr." OR "Lead") NOT "Estagiário" NOT "Trainee"',
    "pearch": '"Desenvolvedor Backend" "Python" "Django" "PostgreSQL" "Docker" "Senior" "São Paulo"'
}
```

### Recursos
- **Expansão de sinônimos**: "developer" → ["desenvolvedor", "programador", "engineer"]
- **Mapeamento de senioridade**: junior, pleno, senior, specialist, manager, director
- **Suporte multi-idioma**: PT-BR e EN
- **Termos de exclusão**: Filtra perfis indesejados

---

## 2. Semantic Search Service

### Descrição
Serviço de busca semântica que usa IA (Gemini) para expandir termos de busca com sinônimos, tecnologias relacionadas e variações.

### Domínios Suportados

| Domínio | Exemplos de Expansão |
|---------|---------------------|
| **Skills** | React → ReactJS, Next.js, Redux, TypeScript |
| **Job Titles** | Backend Developer → Desenvolvedor Backend, Server-side Engineer |
| **Industries** | Fintech → Serviços Financeiros, Pagamentos, Banking |
| **Companies** | Competidores do mercado |
| **Fields of Study** | Ciência da Computação → Engenharia de Software, Sistemas |

### Performance
- **P95 target**: < 300ms
- **Cache Redis**: TTL de 5-10 minutos
- **Debounce frontend**: 400-500ms

### Exemplo de Resposta

```json
{
    "original_query": "Python",
    "domain": "skills",
    "suggestions": [
        {"term": "Python3", "confidence": 0.95, "is_synonym": true},
        {"term": "Django", "confidence": 0.85, "is_related": true},
        {"term": "FastAPI", "confidence": 0.80, "is_related": true},
        {"term": "Flask", "confidence": 0.80, "is_related": true},
        {"term": "Programming Languages", "confidence": 0.70, "is_broader": true}
    ],
    "cached": false,
    "processing_time_ms": 180
}
```

---

## 3. Pearch AI Integration

### Descrição
Integração com API externa Pearch AI para busca de candidatos em base de dados global com 800M+ perfis.

### Tipos de Busca

| Tipo | Créditos | Descrição |
|------|----------|-----------|
| **Fast** | 1/candidato | Busca básica, resultados rápidos |
| **Pro** | 5/candidato | Busca avançada com mais dados |

### Recursos Adicionais

| Feature | Créditos Extra | Descrição |
|---------|----------------|-----------|
| Insights | +1 | Análise de perfil |
| Profile Scoring | +1 | Score de match |
| High Freshness | +2 | Dados mais recentes |
| Require Emails | +1 | Filtrar só com email |
| Show Emails | +2 | Revelar emails |
| Show Phone | +14 | Revelar telefones |

### Fluxo de Busca

```
1. Usuário define critérios
2. Sistema estima créditos
3. Usuário confirma busca
4. Pearch retorna candidatos
5. Sistema enriquece com dados locais
6. Candidatos são rankeados
```

---

## 4. Candidate Matcher (Scoring)

### Fórmula de Match

```
OVERALL_SCORE = (Skills × 0.50) + (Experience × 0.30) + (Location × 0.20)
```

### 4.1 Skills Match

```python
# Lógica de match de skills
required_match_pct = matched_required / total_required × 100
nice_match_pct = matched_nice_to_have / total_nice × 100
final_pct = required_match_pct × 0.80 + nice_match_pct × 0.20
```

**Exemplo:**
- Required: Python, Django, PostgreSQL (3/3 matched = 100%)
- Nice-to-have: Docker, Kubernetes (1/2 matched = 50%)
- **Skills Score: 100 × 0.8 + 50 × 0.2 = 90%**

### 4.2 Experience Match

| Situação | Score | Status |
|----------|-------|--------|
| Atende requisito | 100 | meets_requirement |
| Ligeiramente abaixo (1 ano) | 80 | slightly_under |
| Abaixo (2 anos) | 60 | under_qualified |
| Muito abaixo (3+ anos) | 30 | significantly_under |
| Superqualificado | 70-100 | overqualified |

### 4.3 Location Match

| Situação | Score |
|----------|-------|
| Vaga remota | 100 |
| Mesma cidade | 100 |
| Mesmo estado | 80 |
| Mesmo país | 60 |
| Híbrido + candidato remoto | 70 |
| Mismatch total | 0 |

### 4.4 Tiers de Classificação

| Tier | Score | Recomendação |
|------|-------|--------------|
| **A** | >= 85 | Strong Match |
| **B** | >= 70 | Good Match |
| **C** | >= 55 | Potential Match |
| **D** | < 55 | Weak Match |

---

## 5. WSI (WeDoTalent Skill Index)

### Metodologia de Avaliação

O WSI combina três frameworks:

#### 5.1 Taxonomia de Bloom (Conhecimento)
| Nível | Descrição | Score |
|-------|-----------|-------|
| Lembrar | Reconhece termos | 1 |
| Entender | Explica conceitos | 2 |
| Aplicar | Usa na prática | 3 |
| Analisar | Decompõe problemas | 4 |
| Avaliar | Julga qualidade | 5 |
| Criar | Desenvolve soluções | 6 |

#### 5.2 Escala Dreyfus (Proficiência)
| Nível | Descrição | Score |
|-------|-----------|-------|
| Novato | Segue regras | 1 |
| Iniciante Avançado | Reconhece padrões | 2 |
| Competente | Planeja ações | 3 |
| Proficiente | Vê contexto amplo | 4 |
| Expert | Intuição refinada | 5 |

#### 5.3 Big Five (Personalidade)
- Abertura a Experiências
- Conscienciosidade
- Extroversão
- Amabilidade
- Estabilidade Emocional

### Score Final WSI

```
WSI_SCORE = (Bloom × 0.35) + (Dreyfus × 0.35) + (BigFive × 0.30)
```

Normalizado para escala 0-100.

---

## 6. Fluxo Completo de Sourcing

```
┌─────────────────────────────────────────────────────────────┐
│  1. DEFINIÇÃO DE CRITÉRIOS                                  │
│     └─ Título, Skills, Localização, Experiência            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. GERAÇÃO DE QUERIES                                      │
│     ├─ Boolean Query Builder                                │
│     └─ Semantic Expansion (Gemini + Cache)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. BUSCA PARALELA                                          │
│     ├─ Banco de Dados Local (candidatos existentes)        │
│     └─ Pearch AI (candidatos externos)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. MERGE & DEDUP                                           │
│     └─ Unifica resultados, remove duplicatas               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. SCORING (Candidate Matcher)                             │
│     ├─ Skills Match (50%)                                  │
│     ├─ Experience Match (30%)                              │
│     └─ Location Match (20%)                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. RANKING & TIERS                                         │
│     ├─ Tier A: >= 85 (Strong Match)                        │
│     ├─ Tier B: >= 70 (Good Match)                          │
│     ├─ Tier C: >= 55 (Potential Match)                     │
│     └─ Tier D: < 55 (Weak Match)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  7. WSI SCORING (opcional)                                  │
│     └─ Avaliação profunda: Bloom + Dreyfus + Big Five      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  8. APRESENTAÇÃO                                            │
│     └─ Lista rankeada com scores e justificativas          │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Métricas de Performance

| Métrica | Target | Atual |
|---------|--------|-------|
| Tempo de busca local | < 200ms | ~150ms |
| Tempo de busca Pearch | < 2s | ~1.5s |
| Precisão de match | > 80% | ~75% |
| Recall de candidatos | > 70% | ~65% |
| Custo por busca externa | < 50 créditos | ~30 créditos |

---

## 8. Integrações

- **Pearch AI**: Busca externa de candidatos
- **Redis**: Cache de queries e embeddings
- **Gemini**: Expansão semântica
- **PostgreSQL**: Banco de candidatos local
- **Learning Hub**: Patterns de sucesso para ranking

---

*Documentação técnica - LIA Platform v2.2*
