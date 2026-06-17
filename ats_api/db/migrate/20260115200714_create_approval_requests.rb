class CreateApprovalRequests < ActiveRecord::Migration[7.1]
  def change
    create_table :approval_requests do |t|
      t.references :account, null: false, foreign_key: { to_table: "public.accounts" }
      t.references :approver, null: false, foreign_key: true
      t.references :requested_by, foreign_key: { to_table: "public.users" }
      t.references :approved_by, foreign_key: { to_table: "public.users" }
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.integer :approval_level, null: false, default: 1
      t.integer :status, null: false, default: 0
      t.text :comments
      t.datetime :approved_at
      t.datetime :rejected_at
      t.datetime :expires_at
      t.boolean :is_deleted, default: false, null: false

      t.timestamps
    end

    add_index :approval_requests, [ :reference_type, :reference_id ]
    add_index :approval_requests, [ :account_id, :status ]
    add_index :approval_requests, [ :approver_id, :status ]
    add_index :approval_requests, [ :account_id, :is_deleted ]
  end
end
