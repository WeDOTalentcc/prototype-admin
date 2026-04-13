class CreateClientAccounts < ActiveRecord::Migration[7.1]
  def change
    create_table :client_accounts, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :name, limit: 255
      t.string :trade_name, limit: 255
      t.string :cnpj, limit: 20
      t.string :website, limit: 500
      t.string :logo_url, limit: 500
      t.jsonb :address, default: {}
      t.string :primary_email, limit: 255
      t.string :primary_phone, limit: 50
      t.string :status, limit: 50, default: "trial"
      t.string :plan_id, limit: 100
      t.datetime :contract_start_date
      t.datetime :contract_end_date
      t.integer :user_limit
      t.integer :job_limit
      t.integer :ai_credits_monthly
      t.jsonb :settings, default: {}
      t.jsonb :features_enabled, default: {}
      t.string :account_manager_id, limit: 255
      t.string :implementation_manager_id, limit: 255
      t.string :industry, limit: 100
      t.string :company_size, limit: 50
      t.datetime :onboarding_completed_at
      t.boolean :welcome_email_sent, default: false
      t.datetime :welcome_email_sent_at
      t.boolean :workos_organization_created, default: false
      t.datetime :workos_organization_created_at
      t.boolean :sso_configured, default: false
      t.datetime :sso_configured_at
      t.boolean :is_deleted, default: false
      t.datetime :deleted_at
      t.string :deleted_by, limit: 255
      t.timestamps
    end

    add_index :client_accounts, :cnpj, unique: true
    add_index :client_accounts, :status
    add_index :client_accounts, :plan_id
    add_index :client_accounts, :is_deleted
  end
end
