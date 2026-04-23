# frozen_string_literal: true

class AddApplyIdToFeedbacks < ActiveRecord::Migration[7.1]
  def change
    return if column_exists?(:feedbacks, :apply_id)

    add_reference :feedbacks, :apply, foreign_key: true, index: true
  end
end
