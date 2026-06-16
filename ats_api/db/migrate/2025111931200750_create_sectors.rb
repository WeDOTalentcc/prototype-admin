class CreateSectors < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      create_table :sectors, if_not_exists: true do |t|
        t.string :name, null: false
        t.text :description
        t.references :parent_sector, foreign_key: { to_table: :sectors }, index: true
        t.string :icon
        t.string :tags, array: true, default: []
        t.integer :level, default: 0, null: false
        t.references :account, foreign_key: false, index: true
        t.boolean :is_public, default: true, null: false
        t.boolean :is_deleted, default: false, null: false

        t.timestamps
      end

      add_index :sectors, :name, if_not_exists: true
      add_index :sectors, :level, if_not_exists: true
      add_index :sectors, :is_public, if_not_exists: true
      add_index :sectors, :is_deleted, if_not_exists: true
      add_index :sectors, :tags, using: :gin, if_not_exists: true
    end
  end
end
