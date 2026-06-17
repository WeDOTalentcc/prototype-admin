class AddAnswersHashToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :answers_hash, :string unless column_exists?(:evaluation_candidates, :answers_hash)
  end
end
