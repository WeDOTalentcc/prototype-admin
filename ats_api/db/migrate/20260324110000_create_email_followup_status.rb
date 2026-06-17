class CreateEmailFollowupStatus < ActiveRecord::Migration[7.1]
  def change
    create_table :email_followup_status do |t|
      t.references :dispatch, null: false, index: true, foreign_key: true
      t.references :candidate, null: false, index: true, foreign_key: true
      t.integer :attempt_count, default: 0, null: false
      t.timestamp :last_attempt_at
      t.timestamp :next_attempt_at
      t.timestamp :completed_at
      t.string :status, default: 'pending', null: false
      t.string :stop_reason
      t.timestamps
    end

    add_index :email_followup_status, [ :candidate_id, :status ]
    add_index :email_followup_status, :next_attempt_at
  end
end
