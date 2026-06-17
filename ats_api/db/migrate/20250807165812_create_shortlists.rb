class CreateShortlists < ActiveRecord::Migration[7.1]
  def change
    create_table :shortlists do |t|
      t.string :name, null: false
      t.text :description
      t.boolean :is_deleted, default: false, null: false
      t.bigint :account_id, null: false
      t.bigint :user_id, null: true

      t.timestamps
    end

    add_index :shortlists, [ :account_id, :name ]
    add_index :shortlists, :account_id
    add_index :shortlists, :user_id
  end
end
