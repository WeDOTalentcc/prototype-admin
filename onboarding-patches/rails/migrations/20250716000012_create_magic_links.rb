# frozen_string_literal: true

class CreateMagicLinks < ActiveRecord::Migration[7.1]
  def change
    create_table :magic_links do |t|
      t.references :user, null: false, foreign_key: { on_delete: :cascade }

      t.string :token_digest, null: false    # bcrypt hash (never store raw token)
      t.string :purpose, limit: 30, null: false, default: "onboarding" # onboarding, login
      t.datetime :expires_at, null: false
      t.datetime :used_at                    # NULL until consumed (single-use)

      # Security audit
      t.string :ip_address, limit: 45        # IPv6 max
      t.string :user_agent, limit: 500

      t.timestamps
    end

    add_index :magic_links, :token_digest, unique: true
    add_index :magic_links, [:user_id, :purpose]
    add_index :magic_links, :expires_at
  end
end
