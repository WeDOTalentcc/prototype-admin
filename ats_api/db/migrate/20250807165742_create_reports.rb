class CreateReports < ActiveRecord::Migration[7.1]
  def change
    create_table :reports do |t|
      t.string :name, null: false
      t.text :description
      t.boolean :is_deleted, default: false, null: false
      t.boolean :is_main, default: false, null: false
      t.bigint :account_id, null: false
      t.bigint :user_id, null: true

      t.timestamps
    end

    add_index :reports, [ :account_id, :name ]
    add_index :reports, :is_main
    add_index :reports, :account_id
    add_index :reports, :user_id
  end
end
