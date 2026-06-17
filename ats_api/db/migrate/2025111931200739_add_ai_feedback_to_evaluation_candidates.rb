class AddAiFeedbackToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :ai_feedback, :jsonb
  end
end
