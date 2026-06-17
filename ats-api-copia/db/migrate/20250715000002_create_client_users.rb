class CreateClientUsers < ActiveRecord::Migration[7.1]
  def change
    create_table :client_users, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.uuid :user_id
      t.string :email, limit: 255
      t.string :name, limit: 255
      t.string :role, limit: 50, default: "viewer"
      t.jsonb :permissions, default: {}
      t.string :status, limit: 20, default: "invited"
      t.string :invitation_token, limit: 255
      t.datetime :invitation_expires_at
      t.datetime :invited_at
      t.datetime :accepted_at
      t.datetime :last_login_at
      t.boolean :is_deleted, default: false
      t.datetime :deleted_at
      t.string :deleted_by, limit: 255
      t.timestamps
    end

    add_index :client_users, :company_id
    add_index :client_users, :status
    add_index :client_users, :invitation_token
    add_index :client_users, [:company_id, :email], unique: true
    add_foreign_key :client_users, :client_accounts, column: :company_id
  end
end
