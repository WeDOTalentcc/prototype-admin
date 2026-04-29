class CreateEmailUnsubscribes < ActiveRecord::Migration[7.1]
  def change
    create_table :email_unsubscribes do |t|
      t.references :account, null: false, index: true
      t.references :candidate, null: false, index: true, foreign_key: true
      t.string :email, null: false
      t.string :token, null: false, index: { unique: true }
      t.timestamp :unsubscribed_at
      t.string :reason
      t.text :user_agent
      t.string :ip_address
      t.timestamps
    end

    add_index :email_unsubscribes, [ :account_id, :email ], unique: true
  end
end
