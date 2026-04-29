class EnablePgvectorExtensionFirst < ActiveRecord::Migration[7.1]
  def up
    execute <<~SQL
      CREATE SCHEMA IF NOT EXISTS extensions;
    SQL

    # Create the extension in the 'extensions' schema if it does not exist,
    # or move it there if it exists in another schema (usually 'public').
    execute <<~SQL
      DO $$
      BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM pg_extension WHERE extname = 'vector'
        ) THEN
          CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
        ELSE
          -- Ensure it's located in the desired schema
          PERFORM 1 FROM pg_extension e
           JOIN pg_namespace n ON n.oid = e.extnamespace
          WHERE e.extname = 'vector' AND n.nspname = 'extensions';
          IF NOT FOUND THEN
            ALTER EXTENSION vector SET SCHEMA extensions;
          END IF;
        END IF;
      END$$;
    SQL
  end

  def down
    # No-op: keep the extension available
  end
end
