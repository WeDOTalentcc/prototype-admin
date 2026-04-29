# frozen_string_literal: true

class AddWsiBigFiveObservedToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :wsi_big_five_observed, :jsonb, default: {}, null: false unless column_exists?(:evaluation_candidates, :wsi_big_five_observed)
  end
end
