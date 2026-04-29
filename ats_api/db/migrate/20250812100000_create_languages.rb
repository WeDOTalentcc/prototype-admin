class CreateLanguages < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      create_table :languages do |t|
        t.string :name, null: false
        t.string :acronym, null: false
        t.string :name_ptbr, null: false
        t.timestamps
      end unless table_exists?(:languages)

      add_index :languages, :name, unique: true unless index_exists?(:languages, :name)
      add_index :languages, :acronym, unique: true unless index_exists?(:languages, :acronym)
    end
  end
end
