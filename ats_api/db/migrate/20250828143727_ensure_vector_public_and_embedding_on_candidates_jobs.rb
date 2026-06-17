class EnsureVectorPublicAndEmbeddingOnCandidatesJobs < ActiveRecord::Migration[7.1]
  def up
    # # garante que a extensão está no public
    # execute %(CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;)
    # execute %(ALTER EXTENSION vector SET SCHEMA public;)

    # # CANDIDATES
    # if column_exists?(:candidates, :embedding)
    #   remove_column :candidates, :embedding
    # end
    # # add_column :candidates, :embedding, "public.vector(1536)"

    # # JOBS
    # if column_exists?(:jobs, :embedding)
    #   remove_column :jobs, :embedding
    # end
    # # add_column :jobs, :embedding, "public.vector(1536)"
  end

  def down
  end
end
