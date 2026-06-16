# Análise Estratégica: NLP + Clustering para Plataforma LIA

**Data:** Janeiro 2026  
**Versão:** 1.0  
**Status:** Em Avaliação  
**Referência Acadêmica:** Kazlauskaitė et al. (2023) - "Job Advertisement Analysis Using NLP and Clustering"

---

## 1. Resumo Executivo

Este documento analisa a aplicação de técnicas de NLP (Natural Language Processing) e Clustering na Plataforma LIA para criar diferenciais competitivos em recrutamento e seleção. A metodologia é baseada em pesquisa acadêmica validada que analisou +500.000 anúncios de emprego.

### 1.1 Oportunidades Identificadas

| Área | Funcionalidade | Impacto Esperado |
|------|----------------|------------------|
| Criação de Vagas | Wizard inteligente com sugestões contextuais | Redução de 40% no tempo de criação |
| Sourcing | Match semântico por similaridade | +30% candidatos qualificados encontrados |
| Talent Mapping | Visualização de candidatos por cluster | Hunting passivo sem vaga aberta |
| Validação de JD | Detecção automática de inconsistências | Melhoria de 25% na qualidade das vagas |
| Analytics | Tendências de mercado em tempo real | Decisões baseadas em dados |

### 1.2 Stack Técnica Proposta

```
Sentence Transformers (all-MiniLM-L6-v2) → UMAP → HDBSCAN → Redis Cache
         ↓                                   ↓         ↓
    Vetores 384D                         50D      Clusters Dinâmicos
```

---

## 2. Fundamento Científico

### 2.1 Metodologia Validada

O artigo de referência (Applied Sciences 2023) demonstrou que:

1. **Sentence Transformers** capturam relações semânticas melhor que TF-IDF ou Word2Vec
2. **UMAP** preserva melhor a estrutura dos dados que PCA ou t-SNE (trustworthiness 0.986)
3. **HDBSCAN** produz clusters mais coerentes que K-Means ou DBSCAN
4. **Perfis gerados automaticamente** foram validados por especialistas como "aplicáveis na prática"

### 2.2 Pipeline de Processamento

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE CLUSTERIZAÇÃO                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ENTRADA                                                            │
│  ├── Texto de vaga (título, requisitos, descrição)                  │
│  └── Texto de currículo (experiências, skills, formação)            │
│                                                                     │
│  ETAPA 1: VETORIZAÇÃO                                               │
│  ├── Modelo: all-MiniLM-L6-v2 (Sentence Transformers)               │
│  ├── Saída: Vetor denso de 384 dimensões                            │
│  └── Captura: Significado semântico, não apenas keywords            │
│                                                                     │
│  ETAPA 2: REDUÇÃO DIMENSIONAL                                       │
│  ├── Método: UMAP (Uniform Manifold Approximation and Projection)   │
│  ├── Configuração: n_neighbors=30, min_dist=0.1, metric=cosine      │
│  ├── Saída: Vetor de 50 dimensões                                   │
│  └── Benefício: Preserva estrutura local e global dos dados         │
│                                                                     │
│  ETAPA 3: CLUSTERIZAÇÃO                                             │
│  ├── Método: HDBSCAN (Hierarchical Density-Based Clustering)        │
│  ├── Configuração: min_cluster_size=50, min_samples=10              │
│  ├── Saída: Cluster ID + probabilidade de pertencimento             │
│  └── Benefício: Detecta clusters de tamanhos variados               │
│                                                                     │
│  ETAPA 4: CACHE E PERSISTÊNCIA                                      │
│  ├── Embeddings: Redis com TTL de 24h                               │
│  ├── Clusters: Recalculados semanalmente ou sob demanda             │
│  └── Métricas: Armazenadas em PostgreSQL para analytics             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Métricas de Qualidade

| Métrica | Valor Obtido (Artigo) | Significado |
|---------|----------------------|-------------|
| Trustworthiness | 0.986 | Preservação de vizinhança após redução |
| Silhouette Score | 0.72 | Coesão e separação dos clusters |
| Davies-Bouldin Index | 0.45 | Qualidade da separação (menor = melhor) |

---

## 3. Aplicações na Plataforma LIA

### 3.1 Wizard Inteligente de Criação de Vagas

#### 3.1.1 Sugestão de Skills por Contexto

Quando o recrutador informa o título da vaga, o sistema:

1. Identifica o cluster de vagas similares
2. Analisa frequência de skills nesse cluster
3. Sugere skills categorizadas por frequência

**Interface Proposta:**

```
┌─────────────────────────────────────────────────────────────┐
│  Título: [Backend Developer Senior]                         │
│                                                             │
│  💡 LIA SUGERE (baseado em 2.847 vagas similares):          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Skills mais comuns neste perfil:                    │   │
│  │                                                       │   │
│  │  ✓ Frequente (>80%): Python, API REST, SQL, Git      │   │
│  │  ○ Comum (50-80%): Docker, AWS, PostgreSQL           │   │
│  │  ◦ Diferencial (20-50%): Kubernetes, Redis, GraphQL  │   │
│  │                                                       │   │
│  │  [+ Adicionar sugeridas]                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Lógica de Sugestão:**

```python
def suggest_skills_for_job(title: str) -> SkillSuggestions:
    # 1. Vetoriza o título
    title_embedding = model.encode(title)
    
    # 2. Encontra cluster mais próximo
    cluster_id = find_nearest_cluster(title_embedding)
    
    # 3. Analisa frequência de skills no cluster
    skill_frequencies = get_skill_frequencies(cluster_id)
    
    # 4. Categoriza por frequência
    return SkillSuggestions(
        frequent=[s for s in skill_frequencies if s.freq > 0.8],
        common=[s for s in skill_frequencies if 0.5 < s.freq <= 0.8],
        differential=[s for s in skill_frequencies if 0.2 < s.freq <= 0.5]
    )
```

#### 3.1.2 Detecção de Inconsistências

O sistema detecta automaticamente quando skills não fazem sentido juntas:

| Tipo de Inconsistência | Exemplo | Detecção | Sugestão LIA |
|------------------------|---------|----------|--------------|
| **Skills Conflitantes** | React + Angular + Vue | Frameworks concorrentes na mesma vaga | "Combinação rara (0.8%). Geralmente vagas pedem 1 framework. Deseja manter?" |
| **Perfil Misturado** | Backend + Figma + UI/UX | Skills de design em vaga técnica | "Skills de Design aparecem em apenas 3% das vagas Backend. Confirma?" |
| **Senioridade Inconsistente** | Junior + 5 anos + liderança | Requisitos de Senior para Junior | "Requisitos parecem de Senior/Lead, não Junior. Ajustar título?" |
| **Stack Obsoleta** | PHP 5, jQuery, MySQL 5.5 | Tecnologias em declínio | "Stack em declínio (-40%/ano). Considerar versões modernas?" |
| **Requisitos Excessivos** | 15 skills obrigatórias | Muitas skills obrigatórias | "Vagas com >8 skills obrigatórias têm 60% menos candidatos" |

**Interface de Alerta:**

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ LIA DETECTOU INCONSISTÊNCIA                             │
│                                                             │
│  Você adicionou "Figma" e "UI/UX Design" numa vaga de       │
│  Backend Developer.                                         │
│                                                             │
│  📊 Dados de mercado:                                       │
│  • Apenas 3% das vagas Backend pedem skills de design       │
│  • Isso pode reduzir seu pool de candidatos em 67%          │
│                                                             │
│  [Manter mesmo assim]  [Remover skills]  [Criar 2 vagas]   │
└─────────────────────────────────────────────────────────────┘
```

**Algoritmo de Detecção:**

```python
def detect_skill_conflicts(skills: List[str], cluster_id: int) -> List[Conflict]:
    conflicts = []
    
    # 1. Calcula co-ocorrência de skills no cluster
    cooccurrence_matrix = get_cooccurrence_matrix(cluster_id)
    
    # 2. Identifica skills com baixa co-ocorrência
    for i, skill1 in enumerate(skills):
        for skill2 in skills[i+1:]:
            if cooccurrence_matrix[skill1][skill2] < 0.05:  # <5% aparecem juntas
                conflicts.append(Conflict(
                    skills=[skill1, skill2],
                    cooccurrence=cooccurrence_matrix[skill1][skill2],
                    severity="high" if cooccurrence_matrix[skill1][skill2] < 0.01 else "medium"
                ))
    
    # 3. Detecta skills fora do cluster
    cluster_skills = get_cluster_skills(cluster_id)
    for skill in skills:
        if skill not in cluster_skills and get_skill_frequency(skill, cluster_id) < 0.1:
            conflicts.append(Conflict(
                skills=[skill],
                reason="out_of_cluster",
                frequency=get_skill_frequency(skill, cluster_id)
            ))
    
    return conflicts
```

#### 3.1.3 Predição de Match com Candidatos

Antes de publicar a vaga, o sistema prediz quantos candidatos do banco farão match:

```
┌─────────────────────────────────────────────────────────────┐
│  📈 ANÁLISE DE MATCH - LIA                                  │
│                                                             │
│  Com os requisitos atuais:                                  │
│  • 12 candidatos no banco fazem match (23%)                 │
│  • Média de mercado para esta vaga: 89 candidatos           │
│                                                             │
│  💡 Sugestões para melhorar match:                          │
│                                                             │
│  1. "AWS" → "Cloud (AWS/GCP/Azure)"                         │
│     +18 candidatos potenciais                               │
│                                                             │
│  2. Remover "Kubernetes" como obrigatório → desejável       │
│     +7 candidatos potenciais                                │
│                                                             │
│  3. Aceitar "3+ anos" em vez de "5+ anos"                   │
│     +22 candidatos potenciais                               │
│                                                             │
│  [Aplicar sugestão 1]  [Aplicar todas]  [Ignorar]          │
└─────────────────────────────────────────────────────────────┘
```

**Lógica de Predição:**

```python
def predict_candidate_match(job_draft: JobDraft) -> MatchPrediction:
    # 1. Vetoriza a vaga
    job_embedding = embed_job(job_draft)
    
    # 2. Busca candidatos por similaridade (não keywords)
    similar_candidates = vector_search(
        query=job_embedding,
        collection="candidates",
        threshold=0.7
    )
    
    # 3. Filtra por requisitos obrigatórios
    matching_candidates = [
        c for c in similar_candidates
        if meets_requirements(c, job_draft.requirements)
    ]
    
    # 4. Gera sugestões de melhoria
    suggestions = generate_improvement_suggestions(
        job_draft=job_draft,
        current_matches=len(matching_candidates),
        similar_candidates=similar_candidates
    )
    
    return MatchPrediction(
        matching_count=len(matching_candidates),
        total_similar=len(similar_candidates),
        suggestions=suggestions
    )
```

#### 3.1.4 Geração de Perguntas de Screening

Baseado no cluster identificado, gera perguntas WSI apropriadas:

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 PERGUNTAS SUGERIDAS - Cluster: Backend Senior           │
│                                                             │
│  Baseado no que diferencia candidatos neste cluster:        │
│                                                             │
│  TÉCNICAS (Bloom: Análise/Síntese)                          │
│  ├── "Descreva uma situação onde você otimizou uma API      │
│  │    que estava com problemas de performance"              │
│  ├── "Como você estruturaria um sistema de cache para       │
│  │    uma aplicação com 1M de usuários?"                    │
│  └── "Explique trade-offs entre SQL e NoSQL que você        │
│       já enfrentou em produção"                             │
│                                                             │
│  COMPORTAMENTAIS (Big Five: Conscientiousness)              │
│  ├── "Como você lida com débito técnico vs. entregas?"      │
│  └── "Descreva como você documenta decisões técnicas"       │
│                                                             │
│  [Usar estas perguntas]  [Personalizar]  [Gerar mais]       │
└─────────────────────────────────────────────────────────────┘
```

**Mapeamento Cluster → Perguntas:**

```python
CLUSTER_QUESTION_TEMPLATES = {
    "backend_senior": {
        "technical": [
            {
                "template": "Descreva uma situação onde você otimizou {skill} que estava com problemas de performance",
                "bloom_level": "analysis",
                "dreyfus_level": "proficient",
                "skills_placeholder": ["API", "banco de dados", "microserviço"]
            },
            {
                "template": "Como você estruturaria um sistema de {concept} para uma aplicação de alta escala?",
                "bloom_level": "synthesis",
                "dreyfus_level": "expert",
                "concepts": ["cache", "filas", "autenticação"]
            }
        ],
        "behavioral": [
            {
                "template": "Como você lida com {situation}?",
                "big_five": "conscientiousness",
                "situations": ["débito técnico", "prazos apertados", "requisitos incompletos"]
            }
        ]
    },
    "frontend_senior": {
        # ... templates específicos para frontend
    },
    "data_engineer": {
        # ... templates específicos para data engineering
    }
}
```

#### 3.1.5 Benchmark de Mercado

Compara a vaga com o mercado:

```
┌─────────────────────────────────────────────────────────────┐
│  📊 BENCHMARK DE MERCADO                                    │
│                                                             │
│  Sua vaga vs. 2.847 vagas similares:                        │
│                                                             │
│  Salário oferecido: R$ 15.000                               │
│  ├── Mercado: R$ 12.000 - R$ 18.000 (você está no P50)      │
│  └── 💡 Aumente para R$16.500 para top 30% de candidatos    │
│                                                             │
│  Skills obrigatórias: 8                                     │
│  ├── Mercado: média de 5 skills obrigatórias                │
│  └── ⚠️ Vagas com 8+ skills têm 40% menos aplicações        │
│                                                             │
│  Modelo de trabalho: Híbrido                                │
│  ├── 67% das vagas similares são remotas                    │
│  └── 💡 Considerar remoto para ampliar pool em 3x           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.2 Talent Map - Cluster de Similaridade de Candidatos

#### 3.2.1 Conceito

Mostrar com quem um candidato mais se parece dentro do banco de talentos, sem precisar de uma vaga aberta.

**Interface Proposta:**

```
┌─────────────────────────────────────────────────────────────┐
│  👤 Maria Santos - Engenheira de Dados                      │
│  📍 São Paulo | 💼 7 anos exp | 🎓 USP                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🧬 CLUSTER DE SIMILARIDADE                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Perfil semelhante a: Engenheiro de Dados Senior     │   │
│  │  Similaridade média: 87%                             │   │
│  │                                                       │   │
│  │  Candidatos similares no banco: 23                   │   │
│  │  ├── João Silva (91% similar) - Contratado ✓         │   │
│  │  ├── Ana Costa (89% similar) - Disponível            │   │
│  │  ├── Pedro Lima (86% similar) - Em processo          │   │
│  │  └── [Ver todos os 23...]                            │   │
│  │                                                       │   │
│  │  Skills definidoras deste cluster:                   │   │
│  │  Python • Spark • Airflow • AWS • SQL                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📊 POSIÇÃO NO TALENT MAP                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      [Visualização 2D do mapa de talentos]          │   │
│  │                                                       │   │
│  │   Backend    ○ ○       ○ Data Eng                    │   │
│  │     ○ ○         ○ ●←Maria                            │   │
│  │        ○ ○   ○ ○ ○                                   │   │
│  │   Frontend  ○ ○       ML/AI ○ ○                      │   │
│  │                                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Casos de Uso

| Cenário | Ação | Benefício |
|---------|------|-----------|
| **Recrutador sem vaga aberta** | "Quero ver meu pool de Data Engineers Seniors" | Visualiza pool de talentos por cluster |
| **Candidato novo entra no banco** | Sistema classifica automaticamente | "Este candidato é similar a 23 profissionais - 5 foram contratados" |
| **Hunting passivo** | "Busque candidatos similares ao João Silva" | Encontra talentos baseado em contratações bem-sucedidas |
| **Análise de diversidade** | Visualiza distribuição do cluster | "Este cluster tem 85% homens - oportunidade de diversificar" |
| **Comparação de candidatos** | Seleciona 2+ candidatos | Mostra posição relativa no cluster e diferenças |

#### 3.2.3 Algoritmo de Similaridade

```python
def find_similar_candidates(candidate_id: str, top_k: int = 20) -> SimilarityResult:
    # 1. Obtém embedding do candidato
    candidate = get_candidate(candidate_id)
    candidate_embedding = embed_candidate(candidate)
    
    # 2. Identifica cluster do candidato
    cluster_id = assign_to_cluster(candidate_embedding)
    cluster_info = get_cluster_info(cluster_id)
    
    # 3. Busca vizinhos mais próximos no espaço vetorial
    neighbors = vector_search(
        query=candidate_embedding,
        collection="candidates",
        top_k=top_k,
        exclude=[candidate_id]
    )
    
    # 4. Calcula similaridade detalhada
    similar_candidates = []
    for neighbor in neighbors:
        similarity = cosine_similarity(candidate_embedding, neighbor.embedding)
        similar_candidates.append(SimilarCandidate(
            id=neighbor.id,
            name=neighbor.name,
            similarity_score=similarity,
            status=neighbor.status,
            common_skills=find_common_skills(candidate, neighbor)
        ))
    
    # 5. Gera coordenadas 2D para visualização (UMAP projetado)
    map_position = project_to_2d(candidate_embedding)
    
    return SimilarityResult(
        cluster_name=cluster_info.name,
        cluster_id=cluster_id,
        similarity_score=calculate_avg_similarity(similar_candidates),
        similar_candidates=similar_candidates,
        defining_skills=cluster_info.top_skills,
        talent_map_position=map_position
    )
```

---

### 3.3 Sourcing Inteligente por Similaridade

#### 3.3.1 Match Semântico vs. Keywords

| Abordagem Tradicional | Abordagem com Clustering |
|----------------------|--------------------------|
| Busca por keywords exatas | Busca por similaridade vetorial |
| "Python" só encontra quem escreveu "Python" | Encontra quem trabalha com tecnologias similares |
| Perde candidatos que usam sinônimos | Captura variações semânticas |
| Depende de como candidato escreveu CV | Entende o significado, não apenas palavras |

#### 3.3.2 Funcionalidades

**1. Match por Cluster:**
```python
def find_candidates_for_job(job_id: str) -> List[CandidateMatch]:
    job = get_job(job_id)
    job_embedding = embed_job(job)
    
    # Busca por similaridade vetorial
    candidates = vector_search(
        query=job_embedding,
        collection="candidates",
        threshold=0.6
    )
    
    return rank_by_fit(candidates, job)
```

**2. "Candidatos Como Este":**
```python
def find_candidates_like(reference_candidate_id: str, job_id: str = None) -> List[CandidateMatch]:
    reference = get_candidate(reference_candidate_id)
    reference_embedding = embed_candidate(reference)
    
    similar = vector_search(
        query=reference_embedding,
        collection="candidates",
        top_k=50,
        exclude=[reference_candidate_id]
    )
    
    if job_id:
        # Filtra por requisitos da vaga
        job = get_job(job_id)
        similar = [c for c in similar if meets_requirements(c, job.requirements)]
    
    return similar
```

**3. Detecção de Talentos em Alta Demanda:**
```python
def find_high_demand_candidates() -> List[TalentOpportunity]:
    opportunities = []
    
    for cluster in get_all_clusters():
        # Conta vagas vs. candidatos no cluster
        job_count = count_jobs_in_cluster(cluster.id)
        candidate_count = count_candidates_in_cluster(cluster.id)
        
        if job_count > candidate_count * 1.5:  # 50% mais vagas que candidatos
            opportunities.append(TalentOpportunity(
                cluster=cluster,
                demand_ratio=job_count / candidate_count,
                candidates=get_candidates_in_cluster(cluster.id)
            ))
    
    return sorted(opportunities, key=lambda x: x.demand_ratio, reverse=True)
```

---

### 3.4 Analytics de Mercado em Tempo Real

#### 3.4.1 Tendências de Skills

Monitora a evolução da demanda por skills ao longo do tempo:

```
┌─────────────────────────────────────────────────────────────┐
│  📈 TENDÊNCIAS DE SKILLS - Últimos 12 meses                 │
│                                                             │
│  ↑ Em alta:                                                 │
│  ├── Kubernetes: +45% de demanda                            │
│  ├── Terraform: +38% de demanda                             │
│  └── TypeScript: +29% de demanda                            │
│                                                             │
│  ↓ Em queda:                                                │
│  ├── jQuery: -52% de demanda                                │
│  ├── AngularJS: -41% de demanda                             │
│  └── PHP 5: -38% de demanda                                 │
│                                                             │
│  → Estáveis:                                                │
│  ├── Python: +3% (consolidado)                              │
│  ├── Java: -2% (consolidado)                                │
│  └── SQL: +1% (consolidado)                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Fórmula de Tendência (do artigo):**

```
F(k,t) = Σ D(k,t,i) / n

Onde:
- F(k,t) = frequência da skill k no momento t
- D(k,t,i) = documentos contendo skill k no momento t
- n = total de documentos
```

#### 3.4.2 Clusters Emergentes

Detecta novas combinações de skills formando clusters:

```python
def detect_emerging_clusters(lookback_days: int = 90) -> List[EmergingCluster]:
    # 1. Compara clusters atuais vs. histórico
    current_clusters = get_current_clusters()
    historical_clusters = get_clusters_from_date(days_ago=lookback_days)
    
    emerging = []
    for cluster in current_clusters:
        if cluster.id not in [c.id for c in historical_clusters]:
            # Cluster novo
            emerging.append(EmergingCluster(
                cluster=cluster,
                type="new",
                growth_rate=None
            ))
        else:
            # Verifica crescimento
            historical = get_cluster_by_id(cluster.id, historical_clusters)
            growth = (cluster.size - historical.size) / historical.size
            
            if growth > 0.5:  # Cresceu mais de 50%
                emerging.append(EmergingCluster(
                    cluster=cluster,
                    type="growing",
                    growth_rate=growth
                ))
    
    return emerging
```

#### 3.4.3 Gap Analysis

Compara pool de candidatos vs. demanda por cluster:

```
┌─────────────────────────────────────────────────────────────┐
│  📊 GAP ANALYSIS - Seu Banco de Talentos                    │
│                                                             │
│  Cluster                    Candidatos    Vagas    Gap      │
│  ─────────────────────────────────────────────────────────  │
│  Backend Senior                 45          28    +17 ✓     │
│  Frontend React                 32          41     -9 ⚠️    │
│  Data Engineer                  12          38    -26 🔴    │
│  DevOps/SRE                      8          22    -14 🔴    │
│  Product Manager                28          15    +13 ✓     │
│  UX Designer                    19          23     -4 ⚠️    │
│                                                             │
│  💡 Recomendação: Focar sourcing em Data Engineer e DevOps  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Arquitetura Técnica

### 4.1 Novos Serviços

```
lia-agent-system/
└── app/
    └── services/
        ├── clustering/
        │   ├── __init__.py
        │   ├── embedding_service.py      # Vetorização com Sentence Transformers
        │   ├── cluster_service.py        # UMAP + HDBSCAN
        │   ├── similarity_service.py     # Busca por similaridade
        │   └── trend_service.py          # Análise de tendências
        │
        ├── job_wizard/
        │   ├── __init__.py
        │   ├── skill_suggester.py        # Sugestão de skills
        │   ├── conflict_detector.py      # Detecção de inconsistências
        │   ├── match_predictor.py        # Predição de match
        │   └── question_generator.py     # Geração de perguntas WSI
        │
        └── talent_map/
            ├── __init__.py
            ├── candidate_clusterer.py    # Clusterização de candidatos
            ├── similarity_finder.py      # Busca de similares
            └── visualization.py          # Coordenadas 2D para mapa
```

### 4.2 Dependências

```python
# requirements.txt - novas dependências

# NLP e Embeddings
sentence-transformers>=2.2.0  # Vetorização semântica
transformers>=4.30.0          # Base para sentence-transformers

# Redução Dimensional e Clustering
umap-learn>=0.5.3             # UMAP para redução dimensional
hdbscan>=0.8.29               # Clustering hierárquico

# Busca Vetorial (opções)
faiss-cpu>=1.7.4              # Facebook AI Similarity Search
# ou
redis[hiredis]>=4.5.0         # Redis com RediSearch para vetores

# Visualização (para Talent Map)
plotly>=5.15.0                # Gráficos interativos
```

### 4.3 Schemas de API

```python
# Schemas para novos endpoints

class SkillSuggestion(BaseModel):
    skill: str
    frequency: float  # 0.0 - 1.0
    category: Literal["frequent", "common", "differential"]
    
class SkillConflict(BaseModel):
    skills: List[str]
    cooccurrence: float
    severity: Literal["high", "medium", "low"]
    suggestion: str
    
class MatchPrediction(BaseModel):
    matching_count: int
    total_candidates: int
    suggestions: List[ImprovementSuggestion]
    
class SimilarCandidate(BaseModel):
    id: str
    name: str
    similarity_score: float
    status: str
    common_skills: List[str]
    
class TalentMapPosition(BaseModel):
    x: float
    y: float
    cluster_id: int
    cluster_name: str
    
class CandidateSimilarityResponse(BaseModel):
    cluster_name: str
    cluster_id: int
    similarity_score: float
    similar_candidates: List[SimilarCandidate]
    defining_skills: List[str]
    talent_map_position: TalentMapPosition
```

### 4.4 Endpoints Propostos

```python
# Job Wizard
POST /api/v1/jobs/wizard/suggest-skills
POST /api/v1/jobs/wizard/validate-requirements
POST /api/v1/jobs/wizard/predict-match
POST /api/v1/jobs/wizard/generate-questions
POST /api/v1/jobs/wizard/benchmark

# Talent Map
GET  /api/v1/candidates/{id}/similarity-cluster
GET  /api/v1/candidates/{id}/similar-candidates
GET  /api/v1/talent-map/clusters
GET  /api/v1/talent-map/visualization

# Analytics
GET  /api/v1/analytics/skill-trends
GET  /api/v1/analytics/emerging-clusters
GET  /api/v1/analytics/gap-analysis

# Sourcing
POST /api/v1/sourcing/semantic-search
POST /api/v1/sourcing/find-similar-to
GET  /api/v1/sourcing/high-demand-talents
```

---

## 5. Integração com Agentes Existentes

### 5.1 Mapeamento de Integrações

| Agente | Integração com Clustering | Benefício |
|--------|--------------------------|-----------|
| **JobIntakeAgent** | Usa `skill_suggester` durante criação | Sugestões contextualizadas |
| **SourcingAgent** | Usa `similarity_service` para match | Match semântico, não keywords |
| **AvaliadorWSI** | Enriquece com "fit de cluster" | Avaliação contextualizada |
| **AnalistaFeedback** | Analisa sucesso por cluster | Insights para melhorar vagas |
| **JobInsightsAgent** | Usa `trend_service` para analytics | Tendências de mercado |

### 5.2 Exemplo de Integração - JobIntakeAgent

```python
# job_intake_agent.py - integração com clustering

class JobIntakeAgent:
    def __init__(self):
        self.skill_suggester = SkillSuggester()
        self.conflict_detector = ConflictDetector()
        self.match_predictor = MatchPredictor()
    
    async def process_job_creation(self, job_data: dict) -> JobIntakeResponse:
        # 1. Identifica cluster do título
        cluster = self.skill_suggester.identify_cluster(job_data["title"])
        
        # 2. Sugere skills baseado no cluster
        suggested_skills = self.skill_suggester.suggest_skills(cluster.id)
        
        # 3. Valida skills inseridas
        if job_data.get("skills"):
            conflicts = self.conflict_detector.detect(
                skills=job_data["skills"],
                cluster_id=cluster.id
            )
        
        # 4. Prediz match com candidatos
        match_prediction = self.match_predictor.predict(job_data)
        
        return JobIntakeResponse(
            cluster=cluster,
            suggested_skills=suggested_skills,
            conflicts=conflicts,
            match_prediction=match_prediction
        )
```

---

## 6. Considerações de Implementação

### 6.1 Performance e Cache

| Operação | Latência Esperada | Estratégia de Cache |
|----------|-------------------|---------------------|
| Embedding de texto | 50-100ms | Cache Redis por hash do texto |
| Busca de similaridade (FAISS) | 10-50ms | Índice em memória |
| Clusterização HDBSCAN | 2-5min (batch) | Recalcula semanalmente |
| Projeção UMAP para 2D | 100-500ms | Cache por candidato |

### 6.2 Escalabilidade

```python
# Estratégias para escala

# 1. Batch Processing - Novos candidatos
@celery.task
def process_new_candidates_batch():
    """Processa candidatos novos em batch (a cada hora)"""
    new_candidates = get_unprocessed_candidates()
    embeddings = embed_batch(new_candidates)
    store_embeddings(embeddings)
    assign_clusters_batch(new_candidates)

# 2. Incremental Clustering - Não recalcula tudo
def assign_to_existing_cluster(new_embedding):
    """Atribui novo candidato a cluster existente (sem recalcular)"""
    return find_nearest_cluster(new_embedding, existing_clusters)

# 3. Reclusterização periódica
@celery.beat_schedule
def weekly_recluster():
    """Recalcula clusters semanalmente"""
    all_embeddings = get_all_embeddings()
    new_clusters = run_hdbscan(all_embeddings)
    update_cluster_assignments(new_clusters)
```

### 6.3 Limitações e Mitigações

| Limitação | Mitigação |
|-----------|-----------|
| Sentence Transformers requer GPU para escala | Usar modelos leves (all-MiniLM-L6-v2) ou API |
| HDBSCAN não escala bem para milhões | Clustering incremental + reclusterização periódica |
| Cold start para novos clusters | Bootstrap com dados sintéticos ou de mercado |
| Viés nos dados de treinamento | Auditoria periódica de distribuição dos clusters |

---

## 7. Roadmap de Implementação

### Fase 1: Foundation (2 semanas)
- [ ] Serviço de embedding com Sentence Transformers
- [ ] Cache Redis para embeddings
- [ ] Testes unitários e de integração

### Fase 2: Clustering (2 semanas)
- [ ] Implementação de UMAP + HDBSCAN
- [ ] Clusterização inicial do banco de candidatos
- [ ] API de similaridade entre candidatos

### Fase 3: Job Wizard (2 semanas)
- [ ] Integração com Job Creation Wizard existente
- [ ] Sugestão de skills por cluster
- [ ] Detecção de inconsistências
- [ ] Predição de match

### Fase 4: Talent Map (2 semanas)
- [ ] Visualização 2D do mapa de talentos
- [ ] "Candidatos similares" na página de candidato
- [ ] Integração com SourcingAgent

### Fase 5: Analytics (2 semanas)
- [ ] Dashboard de tendências de skills
- [ ] Gap analysis por cluster
- [ ] Alertas de clusters emergentes

---

## 8. Métricas de Sucesso

| Métrica | Baseline | Meta |
|---------|----------|------|
| Tempo médio de criação de vaga | 45 min | 25 min (-44%) |
| Candidatos qualificados por vaga | 12 | 20 (+67%) |
| Taxa de match semântico | N/A | 75% |
| Vagas com inconsistências detectadas | N/A | 30% (prevenção) |
| Uso do Talent Map por recrutador | N/A | 3x/semana |

---

## 9. Diferencial Competitivo

### O Que Concorrentes NÃO Fazem

| Funcionalidade | Gupy | Kenoby | Recruta Simples | LIA |
|----------------|------|--------|-----------------|-----|
| Match por keywords | ✓ | ✓ | ✓ | ✓ |
| Match semântico (vetorial) | ✗ | ✗ | ✗ | ✓ |
| Sugestão de skills por cluster | ✗ | ✗ | ✗ | ✓ |
| Detecção de inconsistências | ✗ | ✗ | ✗ | ✓ |
| Talent Map visual | ✗ | ✗ | ✗ | ✓ |
| Predição de match antes de publicar | ✗ | ✗ | ✗ | ✓ |
| Tendências de mercado em tempo real | ✗ | ✗ | ✗ | ✓ |

### Value Propositions

1. **Para Recrutadores**: "LIA me mostra se minha vaga faz sentido antes de publicar"
2. **Para Empresas**: "Entendo gaps de talento antes de começar a buscar"
3. **Para Candidatos**: "Sou matched com vagas mesmo sem keywords perfeitas"
4. **Para Head de TA**: "Visualizo meu pool de talentos sem depender de vagas abertas"

---

## 10. Próximos Passos

1. **Validação de Conceito**: Implementar PoC com subset de dados
2. **Coleta de Dados**: Definir fonte de dados de mercado para treinamento
3. **Priorização**: Escolher features prioritárias para MVP
4. **Especificação Técnica**: Detalhar implementação das features escolhidas
5. **Desenvolvimento**: Iniciar implementação da Fase 1

---

## Anexos

### A. Referência Acadêmica

**Título**: Job Advertisement Requirement Analysis Using Natural Language Processing and Unsupervised Clustering Methods  
**Autores**: Kazlauskaitė et al.  
**Publicação**: Applied Sciences 2023, 13, 6119  
**Dataset**: +500.000 anúncios de emprego (Lituânia)  
**Resultados**: UMAP + HDBSCAN produziram clusters de perfis profissionais validados por especialistas

### B. Modelos Recomendados

| Tarefa | Modelo | Dimensões | Latência |
|--------|--------|-----------|----------|
| Embedding de texto | all-MiniLM-L6-v2 | 384 | 50ms |
| Embedding multilíngue | paraphrase-multilingual-MiniLM-L12-v2 | 384 | 80ms |
| Redução dimensional | UMAP | 50 | 100ms |
| Clustering | HDBSCAN | N/A | 2min (batch) |

### C. Estimativa de Custos

| Recurso | Custo Mensal Estimado |
|---------|----------------------|
| GPU para embeddings (se necessário) | $50-200 |
| Redis para cache | Incluído no Replit |
| Storage para vetores | ~$10/1M candidatos |
| Processamento batch | ~$20/mês (Celery workers) |
