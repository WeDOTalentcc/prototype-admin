# frozen_string_literal: true

class AddEvaluationCandidateStatusToApplies < ActiveRecord::Migration[7.1]
  def change
    # 0: not_sent, 1: sent, 2: answered
    unless column_exists?(:applies, :evaluation_candidate_status)
      add_column :applies, :evaluation_candidate_status, :integer, default: 0, null: false
      add_index  :applies, :evaluation_candidate_status
    end
  end
end
