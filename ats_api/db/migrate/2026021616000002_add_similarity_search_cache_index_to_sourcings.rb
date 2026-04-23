# frozen_string_literal: true

class AddSimilaritySearchCacheIndexToSourcings < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def up
    add_index :sourcings,
              [ :account_id, :user_id, :provider, :status, :searched_at ],
              where: "parameters->>'search_type' = 'similarity'",
              name: "index_sourcings_on_similarity_cache_lookup",
              algorithm: :concurrently

    add_index :sourcings,
              "(parameters->>'base_candidate_ids')",
              name: "index_sourcings_on_parameters_base_candidate_ids",
              algorithm: :concurrently

    add_index :sourcings,
              "(search_metadata->>'threshold')",
              name: "index_sourcings_on_search_metadata_threshold",
              algorithm: :concurrently
  end

  def down
    remove_index :sourcings,
                 name: "index_sourcings_on_similarity_cache_lookup",
                 algorithm: :concurrently

    remove_index :sourcings,
                 name: "index_sourcings_on_parameters_base_candidate_ids",
                 algorithm: :concurrently

    remove_index :sourcings,
                 name: "index_sourcings_on_search_metadata_threshold",
                 algorithm: :concurrently
  end
end
