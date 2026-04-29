class AddDeclinedFieldsToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :declined_at, :datetime
    add_column :evaluation_candidates, :declined_reason, :text
  end
end
