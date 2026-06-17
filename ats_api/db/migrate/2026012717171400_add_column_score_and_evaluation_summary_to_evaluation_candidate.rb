class AddColumnScoreAndEvaluationSummaryToEvaluationCandidate < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :score, :float, default: 0.0 if not column_exists?(:evaluation_candidates, :score)
    add_column :evaluation_candidates, :evaluation_summary, :text, default: nil if not column_exists?(:evaluation_candidates, :evaluation_summary)
  end
end
