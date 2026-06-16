# frozen_string_literal: true

class AddHnswIndexToCandidatesEmbedding < ActiveRecord::Migration[7.0]
  disable_ddl_transaction!

  def up
    # Primeiro, precisamos garantir que a coluna tem dimensões especificadas
    # Se não tiver, o HNSW não consegue criar o índice
    execute <<-SQL
      ALTER TABLE candidates#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(1536)
      USING embedding::extensions.vector(1536)
    SQL

    # HNSW index para busca vetorial rápida
    # CRÍTICO: Sem isso, pgvector faz sequential scan (lento demais em produção)
    #
    # Parâmetros HNSW:
    # - m: 16 (número de conexões por layer, trade-off entre velocidade e recall)
    # - ef_construction: 64 (quanto maior, melhor o índice mas mais lento o build)
    #
    # Trade-offs:
    # - Build time: ~5-10 min para 100k candidatos
    # - Query time: 10-50ms (vs 2-5s sem índice)
    # - Recall: ~95% (vs 100% do sequential scan)

    execute <<-SQL
      CREATE INDEX CONCURRENTLY idx_candidates_embedding_hnsw#{' '}
      ON candidates#{' '}
      USING hnsw (embedding extensions.vector_cosine_ops)
      WITH (m = 16, ef_construction = 64)
      WHERE embedding IS NOT NULL
    SQL
  end

  def down
    remove_index :candidates, name: :idx_candidates_embedding_hnsw
  end
end
