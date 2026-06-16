class AddLiaUserOnUsers < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      add_column :users, :lia_user, :boolean, default: false
    end
  end
end
