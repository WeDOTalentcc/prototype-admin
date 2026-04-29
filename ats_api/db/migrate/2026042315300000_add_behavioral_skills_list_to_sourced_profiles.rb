# frozen_string_literal: true

class AddBehavioralSkillsListToSourcedProfiles < ActiveRecord::Migration[7.1]
  def change
    add_column :sourced_profiles, :behavioral_skills_list, :jsonb, default: [], null: false unless column_exists?(:sourced_profiles, :behavioral_skills_list)
    add_index :sourced_profiles, :behavioral_skills_list, using: :gin unless index_exists?(:sourced_profiles, :behavioral_skills_list)
  end
end
