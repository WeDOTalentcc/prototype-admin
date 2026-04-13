class CreateApprovalTables < ActiveRecord::Migration[7.1]
  def change
    create_table :approval_requests, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.string :request_type, limit: 50, default: "vacancy_approval"
      t.uuid :requester_id
      t.string :requester_name, limit: 255
      t.string :requester_email, limit: 255
      t.string :target_id, limit: 255
      t.string :target_type, limit: 100
      t.string :target_name, limit: 255
      t.text :target_description
      t.jsonb :target_data, default: {}
      t.uuid :approver_id
      t.string :approver_name, limit: 255
      t.string :approver_email, limit: 255
      t.integer :approval_level, default: 1
      t.string :status, limit: 20, default: "pending"
      t.string :priority, limit: 20, default: "normal"
      t.datetime :due_date
      t.text :approval_notes
      t.text :rejection_reason
      t.boolean :email_sent, default: false
      t.datetime :email_sent_at
      t.integer :reminder_count, default: 0
      t.datetime :last_reminder_at
      t.datetime :resolved_at
      t.string :resolved_by, limit: 255
      t.string :resource_type, limit: 100
      t.string :resource_id, limit: 255
      t.datetime :expires_at
      t.timestamps
    end

    add_index :approval_requests, :company_id
    add_index :approval_requests, :status
    add_index :approval_requests, :requester_id
    add_index :approval_requests, :approver_id

    create_table :pending_approvals, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.uuid :approval_request_id
      t.string :approver_id, limit: 255, null: false
      t.string :approver_email, limit: 255
      t.string :status, limit: 20, default: "pending"
      t.text :notes
      t.datetime :responded_at
      t.timestamps
    end

    add_index :pending_approvals, :company_id
    add_index :pending_approvals, :approval_request_id
    add_index :pending_approvals, :approver_id
    add_index :pending_approvals, :status
    add_foreign_key :pending_approvals, :approval_requests
  end
end
