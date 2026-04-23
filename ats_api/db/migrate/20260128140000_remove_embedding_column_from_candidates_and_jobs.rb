# frozen_string_literal: true

class RemoveEmbeddingColumnFromCandidatesAndJobs < ActiveRecord::Migration[7.1]
  def up
    # candidates: remover índices que dependem da coluna embedding e depois a coluna
    remove_index :candidates, name: "idx_candidates_embedding_hnsw", if_exists: true
    remove_index :candidates, name: "idx_candidates_hybrid_city", if_exists: true
    remove_index :candidates, name: "idx_candidates_hybrid_level", if_exists: true
    remove_index :candidates, name: "idx_candidates_hybrid_remote", if_exists: true
    remove_index :candidates, name: "idx_candidates_hybrid_state", if_exists: true
    remove_column :candidates, :embedding, if_exists: true

    # jobs: remover índice HNSW e coluna embedding
    remove_index :jobs, name: "idx_jobs_embedding_hnsw", if_exists: true
    remove_column :jobs, :embedding, if_exists: true
  end

  def down
    # jobs: recriar coluna e índice
    add_column :jobs, :embedding, :vector, limit: 768
    add_index :jobs, :embedding, name: "idx_jobs_embedding_hnsw",
              opclass: :vector_cosine_ops, where: "embedding IS NOT NULL", using: :hnsw

    # candidates: recriar coluna e índices
    add_column :candidates, :embedding, :vector, limit: 768
    add_index :candidates, :embedding, name: "idx_candidates_embedding_hnsw",
               opclass: :vector_cosine_ops, where: "embedding IS NOT NULL", using: :hnsw
    add_index :candidates, %i[account_id is_deleted city], name: "idx_candidates_hybrid_city", where: "embedding IS NOT NULL"
    add_index :candidates, %i[account_id is_deleted position_level], name: "idx_candidates_hybrid_level", where: "embedding IS NOT NULL"
    add_index :candidates, %i[account_id is_deleted remote_work], name: "idx_candidates_hybrid_remote", where: "embedding IS NOT NULL"
    add_index :candidates, %i[account_id is_deleted state], name: "idx_candidates_hybrid_state", where: "embedding IS NOT NULL"
  end
end
