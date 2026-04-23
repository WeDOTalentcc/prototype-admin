class AddUfOnState < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      add_column :states, :uf, :string
      add_index :states, :uf
    end
  end
end
