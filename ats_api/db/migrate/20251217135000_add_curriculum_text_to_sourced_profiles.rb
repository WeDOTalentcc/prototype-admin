class AddCurriculumTextToSourcedProfiles < ActiveRecord::Migration[7.1]
  def change
    add_column :sourced_profiles, :curriculum_text, :text unless column_exists?(:sourced_profiles, :curriculum_text)
  end
end
