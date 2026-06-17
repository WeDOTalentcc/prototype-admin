class RevertEmbeddingCacheTo768 < ActiveRecord::Migration[7.1]
  def up
    # Primeiro, deletar dados existentes (são apenas caches, podem ser regenerados)
    execute "DELETE FROM embedding_caches"

    # Reverter dimensão da coluna de 1536 para 768
    # O modelo text-embedding-004 do Gemini só suporta 768 dimensões
    execute <<-SQL
      ALTER TABLE embedding_caches#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(768)
      USING embedding::extensions.vector(768)
    SQL
  end

  def down
    execute "DELETE FROM embedding_caches"

    execute <<-SQL
      ALTER TABLE embedding_caches#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(1536)
      USING embedding::extensions.vector(1536)
    SQL
  end
end
