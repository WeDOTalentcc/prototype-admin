class ChangeJobsEmbeddingDimTo1536 < ActiveRecord::Migration[7.1]
  def up
    if column_exists?(:jobs, :embedding)
      execute <<~SQL
        ALTER TABLE jobs
        ALTER COLUMN embedding TYPE extensions.vector(1536);
      SQL
    else
      execute <<~SQL
        ALTER TABLE jobs
        ADD COLUMN embedding extensions.vector(1536);
      SQL
    end
  end

  def down
    if column_exists?(:jobs, :embedding)
      execute <<~SQL
        ALTER TABLE jobs
        DROP COLUMN embedding;
      SQL
    end
  end
end
