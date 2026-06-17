# frozen_string_literal: true

class AddQuestionsHashToEvaluations < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :questions_hash, :string, limit: 64 unless column_exists?(:evaluations, :questions_hash)
  end
end
