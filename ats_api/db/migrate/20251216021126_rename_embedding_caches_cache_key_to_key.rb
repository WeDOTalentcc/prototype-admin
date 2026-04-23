class RenameEmbeddingCachesCacheKeyToKey < ActiveRecord::Migration[7.1]
  def change
    rename_column :embedding_caches, :cache_key, :key if column_exists?(:embedding_caches, :cache_key)
  end
end
