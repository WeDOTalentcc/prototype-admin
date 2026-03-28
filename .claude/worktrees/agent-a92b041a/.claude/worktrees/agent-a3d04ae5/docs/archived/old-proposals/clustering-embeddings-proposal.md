# Proposta: Clustering e Embeddings para LIA

> **Status**: Proposta para implementação futura  
> **Prioridade**: Baixa (aguardar volume de dados)  
> **Pré-requisitos**: 500+ vagas criadas, Learning Engine consolidado

---

## 1. Visão Geral

### 1.1 Objetivo
Implementar um sistema de clustering e embeddings vetoriais para:
- Encontrar vagas similares automaticamente
- Agrupar candidatos por perfil
- Melhorar sugestões baseadas em similaridade semântica
- Habilitar busca por contexto (não apenas keywords)

### 1.2 Por que não agora?
- ROI baixo com volume atual de dados
- Foco atual: melhorar experiência básica do wizard
- Clustering eficaz requer 500+ vagas para padrões significativos
- Investimento maior (pgvector, embeddings, infra)

---

## 2. Arquitetura Proposta

### 2.1 Modelo de Dados

```python
# Extensão para JobVacancy
class JobVacancy(Base):
    # ... campos existentes ...
    
    # Novos campos para embeddings
    embedding_vector = Column(ARRAY(Float))  # 1536 dims (OpenAI) ou 768 (Gemini)
    embedding_model = Column(String(50))  # "text-embedding-3-small"
    embedding_generated_at = Column(DateTime)
    cluster_id = Column(UUID, ForeignKey("job_clusters.id"), nullable=True)
    cluster_confidence = Column(Float, nullable=True)

class JobCluster(Base):
    """Agrupamentos automáticos de vagas"""
    __tablename__ = "job_clusters"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID, nullable=False)
    
    # Identificação
    name = Column(String(200))  # Gerado automaticamente
    description = Column(Text)
    
    # Centróide
    centroid_vector = Column(ARRAY(Float))
    
    # Características comuns
    common_skills = Column(ARRAY(String))
    common_seniorities = Column(ARRAY(String))
    common_departments = Column(ARRAY(String))
    avg_salary_min = Column(Float)
    avg_salary_max = Column(Float)
    
    # Métricas
    job_count = Column(Integer, default=0)
    avg_time_to_fill = Column(Float)
    avg_success_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CandidateEmbedding(Base):
    """Embeddings para candidatos"""
    __tablename__ = "candidate_embeddings"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID, ForeignKey("candidates.id"), nullable=False)
    
    embedding_vector = Column(ARRAY(Float))
    embedding_model = Column(String(50))
    source_text_hash = Column(String(64))  # Para detectar mudanças
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2.2 Serviço de Embeddings

```python
class EmbeddingService:
    """
    Gera e gerencia embeddings para vagas e candidatos.
    
    Modelo recomendado: text-embedding-3-small (OpenAI)
    - 1536 dimensões
    - Custo: $0.02/1M tokens
    - Melhor custo-benefício para busca semântica
    """
    
    MODEL = "text-embedding-3-small"
    DIMENSION = 1536
    
    async def generate_job_embedding(self, job: JobVacancy) -> List[float]:
        """Gera embedding para uma vaga"""
        text = self._build_job_text(job)
        return await self._embed(text)
    
    def _build_job_text(self, job: JobVacancy) -> str:
        """Constrói texto representativo da vaga"""
        parts = [
            f"Cargo: {job.title}",
            f"Departamento: {job.department}" if job.department else "",
            f"Senioridade: {job.seniority_level}" if job.seniority_level else "",
            f"Skills: {', '.join(job.skills or [])}",
            f"Descrição: {job.description[:500]}" if job.description else "",
        ]
        return "\n".join(p for p in parts if p)
    
    async def find_similar_jobs(
        self,
        embedding: List[float],
        company_id: str,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Tuple[JobVacancy, float]]:
        """
        Busca vagas similares usando similaridade de cosseno.
        Requer extensão pgvector no PostgreSQL.
        """
        # SELECT *, 1 - (embedding_vector <=> query_vector) as similarity
        # FROM job_vacancies
        # WHERE company_id = ? AND similarity >= ?
        # ORDER BY similarity DESC
        # LIMIT ?
        pass
    
    async def cluster_jobs(
        self,
        company_id: str,
        min_jobs: int = 20,
        n_clusters: int = None
    ) -> List[JobCluster]:
        """
        Agrupa vagas similares usando K-Means ou HDBSCAN.
        
        Se n_clusters=None, determina automaticamente usando silhouette score.
        """
        pass
```

### 2.3 Integração com Wizard

```python
class SimilarJobsSuggestionService:
    """Sugere baseado em vagas similares"""
    
    async def get_suggestions_from_similar(
        self,
        draft: JobDraft,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Encontra vagas similares e extrai sugestões.
        
        Returns:
            {
                "similar_jobs": [...],
                "suggested_skills": [...],
                "suggested_salary": {...},
                "avg_time_to_fill": 30,
                "success_rate": 0.85
            }
        """
        # 1. Gerar embedding do draft atual
        embedding = await self.embedding_service.generate_draft_embedding(draft)
        
        # 2. Encontrar vagas similares bem-sucedidas
        similar = await self.embedding_service.find_similar_jobs(
            embedding,
            draft.company_id,
            limit=limit
        )
        
        # 3. Extrair padrões de sucesso
        successful = [j for j, _ in similar if j.status == "closed" and j.outcome == "filled"]
        
        return {
            "similar_jobs": [
                {"id": j.id, "title": j.title, "similarity": s}
                for j, s in similar
            ],
            "suggested_skills": self._extract_common_skills(successful),
            "suggested_salary": self._extract_salary_benchmark(successful),
            "avg_time_to_fill": self._avg_ttf(successful),
            "success_rate": len(successful) / len(similar) if similar else 0
        }
```

---

## 3. Infraestrutura Necessária

### 3.1 PostgreSQL pgvector

```sql
-- Habilitar extensão (já disponível no Neon/Replit)
CREATE EXTENSION IF NOT EXISTS vector;

-- Índice para busca eficiente
CREATE INDEX job_embeddings_idx ON job_vacancies 
USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);

-- Função de similaridade
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float AS $$
  SELECT 1 - (a <=> b);
$$ LANGUAGE SQL IMMUTABLE STRICT;
```

### 3.2 Pipeline de Geração

```python
class EmbeddingPipeline:
    """
    Pipeline assíncrono para gerar embeddings.
    Executa em background após criação/atualização de vagas.
    """
    
    async def process_job(self, job_id: UUID):
        """Gera embedding para uma vaga"""
        job = await self.get_job(job_id)
        
        # Verificar se embedding já existe e está atualizado
        text_hash = hashlib.sha256(self._build_job_text(job).encode()).hexdigest()
        if job.embedding_vector and job.source_text_hash == text_hash:
            return  # Já processado
        
        embedding = await self.embedding_service.generate_job_embedding(job)
        
        await self.update_job_embedding(job_id, embedding, text_hash)
    
    async def rebuild_all_embeddings(self, company_id: str):
        """Reconstrói todos os embeddings (ex: após mudança de modelo)"""
        jobs = await self.get_all_jobs(company_id)
        
        for batch in self._batch(jobs, 100):
            tasks = [self.process_job(j.id) for j in batch]
            await asyncio.gather(*tasks)
    
    async def recluster(self, company_id: str):
        """Recalcula clusters após novos dados"""
        clusters = await self.embedding_service.cluster_jobs(company_id)
        
        # Atualizar vagas com novo cluster_id
        for cluster in clusters:
            for job_id in cluster.job_ids:
                await self.update_job_cluster(job_id, cluster.id)
```

---

## 4. Casos de Uso

### 4.1 No Wizard de Criação

```
Recrutador: "Preciso de um Dev Python Sênior"

LIA (com clustering):
"Entendi! Encontrei 5 vagas similares que você criou nos últimos 12 meses.
Baseado no sucesso dessas vagas:
• Skills mais comuns: Python, FastAPI, PostgreSQL, Docker
• Faixa salarial típica: R$ 18.000 - R$ 25.000
• Tempo médio de preenchimento: 28 dias

Vou usar essas referências como base. Confirma?"
```

### 4.2 Sugestão de Candidatos

```
# Ao publicar vaga, encontrar candidatos similares
similar_candidates = await embedding_service.find_similar_candidates(
    job_embedding,
    company_id,
    limit=20
)
```

### 4.3 Análise de Clusters

```
# Dashboard de RH
clusters = await embedding_service.get_clusters(company_id)

for cluster in clusters:
    print(f"""
    Cluster: {cluster.name}
    Vagas: {cluster.job_count}
    Skills comuns: {cluster.common_skills}
    Tempo médio: {cluster.avg_time_to_fill} dias
    Taxa de sucesso: {cluster.avg_success_rate}%
    """)
```

---

## 5. Métricas de Sucesso

| Métrica | Baseline | Target |
|---------|----------|--------|
| Precisão de sugestões | - | >80% aceitas |
| Tempo de criação de vaga | atual | -20% |
| Qualidade de matches | score atual | +15% |
| Custo de embeddings | - | <$50/mês |

---

## 6. Cronograma Sugerido

### Fase 1: Preparação (1 semana)
- [ ] Adicionar campos de embedding ao modelo
- [ ] Configurar pgvector
- [ ] Criar migration

### Fase 2: Geração (2 semanas)
- [ ] Implementar EmbeddingService
- [ ] Pipeline de geração assíncrona
- [ ] API para busca por similaridade

### Fase 3: Clustering (2 semanas)
- [ ] Algoritmo de clustering
- [ ] Análise automática de padrões
- [ ] Dashboard de clusters

### Fase 4: Integração (1 semana)
- [ ] Integrar com wizard
- [ ] Sugestões baseadas em similaridade
- [ ] Métricas e monitoramento

---

## 7. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Volume insuficiente | Alta | Alto | Adiar até 500+ vagas |
| Custo de embeddings | Baixa | Médio | Cache agressivo, batch processing |
| Performance de busca | Média | Alto | Índices IVFFlat, limitar scope |
| Qualidade de clusters | Média | Médio | Validação manual inicial |

---

## 8. Dependências

- PostgreSQL com pgvector (já disponível no Neon)
- API OpenAI ou Gemini para embeddings
- ~500+ vagas para clustering significativo
- Learning Engine funcionando para correlacionar outcomes
