class AddSimilarityScoreToSourcedProfileSourcings < ActiveRecord::Migration[7.1]
  def change
    add_column :sourced_profile_sourcings, :similarity_score, :float if not column_exists?(:sourced_profile_sourcings, :similarity_score)
  end
end
