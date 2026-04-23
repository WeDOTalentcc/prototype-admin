class CreateStates < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      create_table :states, if_not_exists: true do |t|
        t.string :name
        t.references :country, null: false, foreign_key: true
        t.timestamps
      end
      add_index :states, :name, if_not_exists: true
      add_index :states, :country_id, if_not_exists: true
    end
  end
end
