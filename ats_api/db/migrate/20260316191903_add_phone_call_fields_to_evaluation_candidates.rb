class AddPhoneCallFieldsToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :evaluation_type, :integer, default: 0, null: false
    add_column :evaluation_candidates, :scheduled_at, :datetime
    add_column :evaluation_candidates, :scheduling_link_id, :bigint
    add_column :evaluation_candidates, :phone_call_status, :string
    add_column :evaluation_candidates, :custom_invite_message, :text
    add_column :evaluation_candidates, :interview_session_id, :bigint

    add_index :evaluation_candidates, :scheduling_link_id
    add_index :evaluation_candidates, :interview_session_id
    add_index :evaluation_candidates, :evaluation_type
  end
end
