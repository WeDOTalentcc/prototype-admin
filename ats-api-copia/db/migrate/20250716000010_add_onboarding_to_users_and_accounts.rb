# frozen_string_literal: true

class AddOnboardingToUsersAndAccounts < ActiveRecord::Migration[7.1]
  def change
    # === Users table: onboarding fields (follows ClientUser invitation pattern) ===
    change_table :users, bulk: true do |t|
      # Contact
      t.string :phone, limit: 20

      # Invitation (copied from ClientUser pattern)
      t.string :invitation_token
      t.datetime :invitation_expires_at
      t.datetime :invited_at
      t.bigint :invited_by_user_id

      # Activation lifecycle
      t.string :activation_state, limit: 30, default: "active"

      # Onboarding tracking
      t.datetime :first_login_at
      t.datetime :onboarding_completed_at

      # LGPD consent
      t.datetime :lgpd_consent_at
      t.string :lgpd_consent_channel, limit: 20

      # Onboarding preferences learned from WhatsApp Flow
      t.jsonb :onboarding_metadata, default: {}

      # Override: admin can disable LIA onboarding per user
      t.boolean :onboarding_lia_override, default: nil
    end

    add_index :users, :activation_state
    add_index :users, :invitation_token, unique: true
    add_index :users, :phone
    add_foreign_key :users, :users, column: :invited_by_user_id, on_delete: :nullify

    # === Accounts table: company-level onboarding toggle ===
    add_column :accounts, :onboarding_lia_enabled, :boolean, default: true
  end
end
