class AddUidToAccountAndDataFile < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      add_column :accounts, :uid, :string
      add_index :accounts, :uid, unique: true
    end

    add_column :data_files, :uid, :string
    add_index :data_files, :uid, unique: true
  end
end
