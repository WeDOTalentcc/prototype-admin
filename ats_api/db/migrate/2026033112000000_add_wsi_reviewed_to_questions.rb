# frozen_string_literal: true

class AddWsiReviewedToQuestions < ActiveRecord::Migration[7.1]
  def change
    return if column_exists?(:questions, :wsi_reviewed)

    add_column :questions, :wsi_reviewed, :boolean, default: false, null: false
  end
end
