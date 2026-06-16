class RecreateHnswIndexesFor768Dims < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def up
    say "Criando índice HNSW para candidates (768 dims)"
    say "Isso pode levar 5-10 min para 100k registros..."

    execute <<-SQL
      CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_candidates_embedding_hnsw
      ON candidates#{' '}
      USING hnsw (embedding extensions.vector_cosine_ops)
      WITH (m = 16, ef_construction = 64)
      WHERE embedding IS NOT NULL;
    SQL

    say "Criando índice HNSW para jobs (768 dims)"

    execute <<-SQL
      CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_embedding_hnsw
      ON jobs#{' '}
      USING hnsw (embedding extensions.vector_cosine_ops)
      WITH (m = 16, ef_construction = 64)
      WHERE embedding IS NOT NULL;
    SQL

    say "✓ Índices HNSW criados com sucesso!"
  end

  def down
    remove_index :candidates, name: :idx_candidates_embedding_hnsw, algorithm: :concurrently
    remove_index :jobs, name: :idx_jobs_embedding_hnsw, algorithm: :concurrently
  end
end
