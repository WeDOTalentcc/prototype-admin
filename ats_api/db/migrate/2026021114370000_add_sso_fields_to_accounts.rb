# frozen_string_literal: true

class AddSsoFieldsToAccounts < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists?('accounts')
      unless column_exists?(:accounts, :domain)
        add_column :accounts, :domain, :string
        add_index :accounts, :domain, unique: true, where: "domain IS NOT NULL"
      end

      unless column_exists?(:accounts, :allowed_domains)
        add_column :accounts, :allowed_domains, :string, array: true, default: []
      end

      unless column_exists?(:accounts, :sso_providers)
        add_column :accounts, :sso_providers, :jsonb, default: []
      end

      unless column_exists?(:accounts, :sso_enforced)
        add_column :accounts, :sso_enforced, :boolean, default: false
      end

      unless column_exists?(:accounts, :jit_provisioning_enabled)
        add_column :accounts, :jit_provisioning_enabled, :boolean, default: true
      end
    end
  end
end
