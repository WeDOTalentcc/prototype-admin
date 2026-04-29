class ConvertAnalysisStringToJsonb < ActiveRecord::Migration[7.0]
  def up
    # Converter strings JSON existentes para JSONB
    execute <<-SQL
      UPDATE sourced_profile_sourcings
      SET analysis =#{' '}
        CASE#{' '}
          WHEN analysis IS NULL THEN '{}'::jsonb
          WHEN jsonb_typeof(analysis) = 'string' THEN#{' '}
            CASE#{' '}
              WHEN analysis::text = '' THEN '{}'::jsonb
              WHEN analysis::text = '{}' THEN '{}'::jsonb
              ELSE (analysis::text)::jsonb
            END
          ELSE analysis
        END
      WHERE jsonb_typeof(analysis) = 'string' OR analysis IS NULL;
    SQL
  end

  def down
    # Não há como reverter de forma segura (perda de dados)
    raise ActiveRecord::IrreversibleMigration
  end
end
