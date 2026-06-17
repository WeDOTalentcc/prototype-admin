# frozen_string_literal: true

class AddWorkosConnectionIdToAccounts < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists?('accounts')
      unless column_exists?(:accounts, :workos_connection_id)
        add_column :accounts, :workos_connection_id, :string
      end
    end
  end
end
