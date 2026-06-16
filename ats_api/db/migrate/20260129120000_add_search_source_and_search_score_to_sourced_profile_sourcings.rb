# frozen_string_literal: true

class AddSearchSourceAndSearchScoreToSourcedProfileSourcings < ActiveRecord::Migration[7.0]
  def change
    add_column :sourced_profile_sourcings, :search_source, :string, default: nil
    add_column :sourced_profile_sourcings, :search_score, :decimal, precision: 12, scale: 6, default: nil

    add_index :sourced_profile_sourcings, :search_source, where: "search_source IS NOT NULL"
  end
end
