class CreatePasswordResetTable < ActiveRecord::Migration[7.1]
  def change
    create_table :password_reset_tokens do |t|
      t.references :user, null: false, foreign_key: false
      t.references :account, null: false, foreign_key: false
      t.string :token_digest, null: false
      t.string :ip_address, null: false
      t.datetime :expires_at, null: false
      t.datetime :used_at
      t.timestamps
    end
    add_index :password_reset_tokens, :token_digest, unique: true
  end
end
