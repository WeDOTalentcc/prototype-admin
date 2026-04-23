class CreateDataFiles < ActiveRecord::Migration[7.1]
  def change
    create_table :data_files do |t|
      t.references :user, null: true, foreign_key: true
      t.string :name
      t.string :reference_type
      t.bigint :reference_id
      t.string :file_type
      t.boolean :is_downloaded, default: false
      t.boolean :is_deleted, default: false
      t.references :account, null: false, foreign_key: true
      t.timestamps
    end

    add_index :data_files, [ :reference_type, :reference_id ], name: 'index_data_files_on_reference'
  end
end
