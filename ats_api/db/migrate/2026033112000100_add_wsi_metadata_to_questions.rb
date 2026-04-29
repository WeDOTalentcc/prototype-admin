# frozen_string_literal: true

class AddWsiMetadataToQuestions < ActiveRecord::Migration[7.1]
  def change
    return if column_exists?(:questions, :wsi_metadata)

    add_column :questions, :wsi_metadata, :jsonb, default: {}, null: false
  end
end
