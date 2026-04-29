class AddAtsProviderToAccounts < ActiveRecord::Migration[7.1]
  def change
    add_column :accounts, :ats_provider, :string
  end
end
