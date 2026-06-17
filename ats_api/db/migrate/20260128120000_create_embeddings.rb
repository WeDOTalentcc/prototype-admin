# frozen_string_literal: true

class CreateEmbeddings < ActiveRecord::Migration[7.1]
  def change
    create_table :embeddings do |t|
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.column :embedding, "extensions.vector(768)", null: false
      t.string :model_version, default: "gemini-embedding-001"
      t.integer :dimensions, default: 768
      t.timestamps
    end

    add_index :embeddings, %i[reference_type reference_id],
              unique: true,
              name: "idx_embeddings_reference"

    reversible do |dir|
      dir.up do
        execute <<-SQL
          CREATE INDEX idx_embeddings_hnsw ON embeddings
          USING hnsw (embedding extensions.vector_cosine_ops);
        SQL
      end
      dir.down do
        remove_index :embeddings, name: "idx_embeddings_hnsw"
      end
    end
  end
end
