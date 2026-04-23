# frozen_string_literal: true

class RemoveDuplicateAtsSyncFields < ActiveRecord::Migration[7.1]
  def change
    remove_column :candidates, :ats_candidate_id, :string if column_exists?(:candidates, :ats_candidate_id)
    remove_column :candidates, :ats_synced_at, :datetime if column_exists?(:candidates, :ats_synced_at)
    remove_index :candidates, name: :index_candidates_on_ats_candidate_id, if_exists: true

    remove_column :applies, :ats_apply_id, :string if column_exists?(:applies, :ats_apply_id)
    remove_column :applies, :ats_synced_at, :datetime if column_exists?(:applies, :ats_synced_at)
    remove_index :applies, name: :index_applies_on_ats_apply_id, if_exists: true

    remove_column :experiences, :ats_experience_id, :string if column_exists?(:experiences, :ats_experience_id)
    remove_index :experiences, name: :index_experiences_on_ats_experience_id, if_exists: true

    remove_column :educations, :ats_education_id, :string if column_exists?(:educations, :ats_education_id)
    remove_index :educations, name: :index_educations_on_ats_education_id, if_exists: true
  end
end
