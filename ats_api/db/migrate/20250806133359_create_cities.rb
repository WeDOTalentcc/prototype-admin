class CreateCities < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      create_table :cities do |t|
        t.string :name
        t.references :state, null: false, foreign_key: true

        t.timestamps
      end
    end
  end
end
