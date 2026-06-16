class AddIndexEvaluationCandidatesUpdatedAt < ActiveRecord::Migration[7.0]
  disable_ddl_transaction!

  def change
    add_index :evaluation_candidates, [ :completed, :declined_at, :session_status, :updated_at ],
              name: "idx_eval_candidates_abandonment_lookup",
              algorithm: :concurrently
  end
end
