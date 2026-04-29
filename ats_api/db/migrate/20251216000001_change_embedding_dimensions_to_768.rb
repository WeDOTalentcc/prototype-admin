class ChangeEmbeddingDimensionsTo768 < ActiveRecord::Migration[7.1]
  def up
    say "Alterando dimensão de embeddings de 1536 para 768"
    say "ATENÇÃO: Isso vai DROPAR índices HNSW temporariamente"

    execute <<-SQL
      DROP INDEX IF EXISTS idx_candidates_embedding_hnsw;
      DROP INDEX IF EXISTS idx_jobs_embedding_hnsw;
    SQL

    say "Limpando cache de embeddings antigos"
    execute "TRUNCATE TABLE embedding_caches;"

    say "Alterando tipo das colunas embedding para vector(768)"

    execute <<-SQL
      ALTER TABLE candidates#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(768)
      USING NULL;
    SQL

    execute <<-SQL
      ALTER TABLE jobs#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(768)
      USING NULL;
    SQL

    execute <<-SQL
      ALTER TABLE embedding_caches#{' '}
      ALTER COLUMN embedding DROP NOT NULL;
    SQL

    execute <<-SQL
      ALTER TABLE embedding_caches#{' '}
      ALTER COLUMN embedding TYPE extensions.vector(768);
    SQL

    say "✓ Embeddings foram resetados. Execute rake task para re-embedar:"
    say "  rake embeddings:sync_all_candidates"
    say "  rake embeddings:sync_all_jobs"
  end

  def down
    raise ActiveRecord::IrreversibleMigration,
          "Não é possível reverter alteração de dimensão sem perder dados"
  end
end
