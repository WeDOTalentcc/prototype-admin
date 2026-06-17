# frozen_string_literal: true

class AddMfaToAccountsAndUsers < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists?('accounts')
      unless column_exists?(:accounts, :mfa_enabled)
        add_column :accounts, :mfa_enabled, :boolean, default: true
      end

      unless column_exists?(:accounts, :mfa_method)
        add_column :accounts, :mfa_method, :string, default: 'email_otp'
      end

      unless column_exists?(:accounts, :mfa_required_for_admins)
        add_column :accounts, :mfa_required_for_admins, :boolean, default: false
      end
    end

    if ActiveRecord::Base.connection.table_exists?('users')
      unless column_exists?(:users, :mfa_enabled)
        add_column :users, :mfa_enabled, :boolean, default: true
      end
    end
  end
end
