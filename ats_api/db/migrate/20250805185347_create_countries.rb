class CreateCountries < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      create_table :countries, if_not_exists: true do |t|
        t.string :name
        t.timestamps
      end
      add_index :countries, :name, if_not_exists: true
    end
  end
end
