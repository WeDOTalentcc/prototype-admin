class MoveAiFieldsToSourcedProfileSourcing < ActiveRecord::Migration[7.1]
  def change
    # Clean up invalid JSON in analysis field first
    execute <<-SQL
      UPDATE sourced_profile_sourcings#{' '}
      SET analysis = NULL#{' '}
      WHERE analysis IS NOT NULL#{' '}
      AND analysis !~ '^[\\{\\[]'
    SQL

    change_column :sourced_profile_sourcings, :analysis, :jsonb, default: {}, using: 'CASE WHEN analysis IS NULL THEN \'{}\' ELSE analysis::jsonb END'
    add_column :sourced_profile_sourcings, :ai_metadata, :jsonb, default: {}

    remove_column :sourced_profiles, :ai_analysis, :jsonb
    remove_column :sourced_profiles, :ai_analyzed_at, :datetime
    remove_column :sourced_profiles, :score, :integer
    remove_column :sourced_profiles, :insights, :jsonb
  end
end
