class AddWorkspace < ActiveRecord::Migration[7.1]
  def up
    create_table :workspaces do |t|
      t.string :name, null: true
      t.string :uid, null: true
      t.references :account, null: false, foreign_key: false
      t.references :user, null: false, foreign_key: false
      t.boolean :is_deleted, default: false
      t.datetime :last_message_date
      t.timestamps
    end

    add_index :workspaces, [ :user_id, :name ], unique: true

    unless column_exists?(:messages, :workspace_id)
      add_reference :messages, :workspace, foreign_key: true
    end
  end

  def down
    remove_index :workspaces, [ :user_id, :name ] if index_exists?(:workspaces, [ :user_id, :name ])

    if foreign_key_exists?(:messages, :workspaces)
      remove_foreign_key :messages, :workspaces
    end

    if column_exists?(:messages, :workspace_id)
      remove_column :messages, :workspace_id
    end

    drop_table :workspaces, force: :cascade
  end
end
