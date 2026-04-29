class CreateEmbeddingCache < ActiveRecord::Migration[7.1]
  def change
    create_table :embedding_caches do |t|
      t.string :key, null: false, index: { unique: true }
      t.string :model_version, null: false
      t.text :query_text, null: false
      t.column :embedding, 'extensions.vector(1536)', null: false
      t.bigint :account_id, null: false
      t.integer :hit_count, default: 0, null: false
      t.datetime :last_accessed_at
      t.timestamps
    end

    add_index :embedding_caches, [ :account_id, :model_version ]
    add_index :embedding_caches, :last_accessed_at
  end
end
