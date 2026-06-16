# frozen_string_literal: true

class AddSearchMetadataToSourcings < ActiveRecord::Migration[7.0]
  def change
    add_column :sourcings, :search_metadata, :jsonb
    add_column :sourcings, :search_explanation, :jsonb

    add_index :sourcings, :search_metadata, using: :gin
  end
end
