class AddIsScreeningInEvaluationAndEvaluationCandidate < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :is_screening, :boolean, default: false if not column_exists?(:evaluations, :is_screening)
    add_column :evaluation_candidates, :is_screening, :boolean, default: false if not column_exists?(:evaluation_candidates, :is_screening)
  end
end
