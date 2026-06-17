class CreateLists < ActiveRecord::Migration[7.1]
  def change
    create_table :lists do |t|
      t.string :name, null: false
      t.boolean :is_public, default: false
      t.boolean :is_deleted, default: false
      t.references :user, foreign_key: true, null: false
      t.references :account, foreign_key: true, null: false

      t.integer :candidates_count, default: 0
      t.integer :jobs_count, default: 0
      t.integer :applies_count, default: 0
      t.integer :selective_processes_count, default: 0

      t.timestamps
    end

    add_index :lists, :name
    add_index :lists, :is_deleted
    add_index :lists, [ :account_id, :is_deleted ]
  end
end
