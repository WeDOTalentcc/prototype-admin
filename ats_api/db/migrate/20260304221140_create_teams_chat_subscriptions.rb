class CreateTeamsChatSubscriptions < ActiveRecord::Migration[7.1]
  def change
    create_table :teams_chat_subscriptions do |t|
      t.bigint :lia_user_id, null: false
      t.bigint :recruiter_user_id, null: false
      t.bigint :account_id, null: false
      t.string :chat_id, null: false
      t.string :subscription_id
      t.string :tenant, null: false
      t.datetime :subscription_expires_at
      t.string :status, default: "active", null: false

      t.timestamps
    end

    add_index :teams_chat_subscriptions, :chat_id, unique: true
    add_index :teams_chat_subscriptions, :subscription_id, unique: true
    add_index :teams_chat_subscriptions, :recruiter_user_id
    add_index :teams_chat_subscriptions, :account_id
    add_index :teams_chat_subscriptions, %i[lia_user_id recruiter_user_id], unique: true, name: "idx_teams_chat_unique_pair"
    add_index :teams_chat_subscriptions, :status
  end
end
