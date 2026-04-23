# frozen_string_literal: true

class AddWsiDecisionAndRedFlagsToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :wsi_decision, :jsonb, default: {}, null: false unless column_exists?(:evaluation_candidates, :wsi_decision)
    add_column :evaluation_candidates, :wsi_red_flags, :jsonb, default: [], null: false unless column_exists?(:evaluation_candidates, :wsi_red_flags)
  end
end
