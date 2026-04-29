# frozen_string_literal: true

# Com Apartment, candidates e jobs ficam no schema de cada tenant.
# A migration 20260128140000 remove embedding só no schema onde rodou (ex.: public).
# Esta migration aplica a mesma remoção em todos os tenant schemas.
class RemoveEmbeddingFromCandidatesAndJobsInTenantSchemas < ActiveRecord::Migration[7.1]
  def up
    each_schema do
      remove_embedding_column_and_indexes
    end
  end

  def down
    each_schema do
      add_embedding_column_and_indexes_back
    end
  end

  private

  def each_schema
    # Schema atual (ex.: public)
    yield

    # Cada tenant (wedotalent, etc.)
    return unless defined?(Apartment::Tenant) && Apartment::Tenant.respond_to?(:adapter)

    tenant_names = (Apartment::Tenant.adapter.respond_to?(:list) ? Apartment::Tenant.adapter.list.to_a : []) - [ "public", "extensions" ]
    tenant_names.each do |tenant_name|
      Apartment::Tenant.switch(tenant_name) do
        yield
      end
    end
  end

  def remove_embedding_column_and_indexes
    if table_exists?(:candidates) && column_exists?(:candidates, :embedding)
      remove_index :candidates, name: "idx_candidates_embedding_hnsw", if_exists: true
      remove_index :candidates, name: "idx_candidates_hybrid_city", if_exists: true
      remove_index :candidates, name: "idx_candidates_hybrid_level", if_exists: true
      remove_index :candidates, name: "idx_candidates_hybrid_remote", if_exists: true
      remove_index :candidates, name: "idx_candidates_hybrid_state", if_exists: true
      remove_column :candidates, :embedding, if_exists: true
    end

    if table_exists?(:jobs) && column_exists?(:jobs, :embedding)
      remove_index :jobs, name: "idx_jobs_embedding_hnsw", if_exists: true
      remove_column :jobs, :embedding, if_exists: true
    end
  end

  def add_embedding_column_and_indexes_back
    if table_exists?(:candidates) && !column_exists?(:candidates, :embedding)
      add_column :candidates, :embedding, :vector, limit: 768
      add_index :candidates, :embedding, name: "idx_candidates_embedding_hnsw",
                 opclass: :vector_cosine_ops, where: "embedding IS NOT NULL", using: :hnsw
      add_index :candidates, %i[account_id is_deleted city], name: "idx_candidates_hybrid_city", where: "embedding IS NOT NULL"
      add_index :candidates, %i[account_id is_deleted position_level], name: "idx_candidates_hybrid_level", where: "embedding IS NOT NULL"
      add_index :candidates, %i[account_id is_deleted remote_work], name: "idx_candidates_hybrid_remote", where: "embedding IS NOT NULL"
      add_index :candidates, %i[account_id is_deleted state], name: "idx_candidates_hybrid_state", where: "embedding IS NOT NULL"
    end

    if table_exists?(:jobs) && !column_exists?(:jobs, :embedding)
      add_column :jobs, :embedding, :vector, limit: 768
      add_index :jobs, :embedding, name: "idx_jobs_embedding_hnsw",
              opclass: :vector_cosine_ops, where: "embedding IS NOT NULL", using: :hnsw
    end
  end
end
