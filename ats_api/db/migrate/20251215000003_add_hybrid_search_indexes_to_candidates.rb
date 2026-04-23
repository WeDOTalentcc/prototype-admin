# frozen_string_literal: true

class AddHybridSearchIndexesToCandidates < ActiveRecord::Migration[7.0]
  def change
    # Índices compostos para filtros whitelisted do pgvector
    # APENAS para colunas usadas em EmbeddingStrategy.apply_whitelisted_filters

    add_index :candidates,
              [ :account_id, :is_deleted, :city ],
              where: "embedding IS NOT NULL",
              name: "idx_candidates_hybrid_city"

    add_index :candidates,
              [ :account_id, :is_deleted, :state ],
              where: "embedding IS NOT NULL",
              name: "idx_candidates_hybrid_state"

    add_index :candidates,
              [ :account_id, :is_deleted, :remote_work ],
              where: "embedding IS NOT NULL",
              name: "idx_candidates_hybrid_remote"

    add_index :candidates,
              [ :account_id, :is_deleted, :position_level ],
              where: "embedding IS NOT NULL",
              name: "idx_candidates_hybrid_level"
  end
end
