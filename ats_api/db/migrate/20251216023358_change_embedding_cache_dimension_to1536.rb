class ChangeEmbeddingCacheDimensionTo1536 < ActiveRecord::Migration[7.1]
  def up
    # Primeiro, deletar dados existentes (são apenas caches, podem ser regenerados)
    execute "DELETE FROM embedding_caches"

    # Alterar dimensão da coluna de 768 para 1536
    execute <<-SQL
      ALTER TABLE embedding_caches#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(1536)
      USING embedding::extensions.vector(1536)
    SQL
  end

  def down
    execute "DELETE FROM embedding_caches"

    execute <<-SQL
      ALTER TABLE embedding_caches#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(768)
      USING embedding::extensions.vector(768)
    SQL
  end
end
