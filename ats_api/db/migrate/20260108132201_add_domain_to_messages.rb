class AddDomainToMessages < ActiveRecord::Migration[7.1]
  def change
    add_column :messages, :domain, :string
    add_index :messages, :domain
  end
end
