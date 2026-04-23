class AddTimeoutAndRetryFieldsInEvaluationCandidate < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :timeout_count, :integer, default: 0 unless column_exists?(:evaluation_candidates, :timeout_count)
    add_column :evaluation_candidates, :last_reminder_at, :datetime unless column_exists?(:evaluation_candidates, :last_reminder_at)
    add_column :evaluation_candidates, :retry_attempts, :integer, default: 0 unless column_exists?(:evaluation_candidates, :retry_attempts)
    add_column :evaluation_candidates, :session_status, :string unless column_exists?(:evaluation_candidates, :session_status)
    add_column :evaluation_candidates, :last_timeout_at, :datetime unless column_exists?(:evaluation_candidates, :last_timeout_at)
    add_column :evaluation_candidates, :last_question_index, :integer unless column_exists?(:evaluation_candidates, :last_question_index)
  end
end
