class AddParentEvaluationIdInEvaluation < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :parent_evaluation_id, :bigint unless column_exists?(:evaluations, :parent_evaluation_id)
  end
end
