-- HNSW indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_tpc_candidate_embedding
ON talent_pool_candidates USING hnsw (candidate_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_talent_pools_archetype_embedding
ON talent_pools USING hnsw (archetype_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_twin_decisions_embedding
ON twin_decisions USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_digital_twins_embedding
ON digital_twins USING hnsw (twin_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
