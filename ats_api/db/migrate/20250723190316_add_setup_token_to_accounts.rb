class AddSetupTokenToAccounts < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      unless index_exists?(:accounts, :setup_token, unique: true)
        add_column :accounts, :setup_token, :string
        add_column :accounts, :setup_token_expires_at, :datetime
        add_index :accounts, :setup_token, unique: true
      end
    end
  end
end
