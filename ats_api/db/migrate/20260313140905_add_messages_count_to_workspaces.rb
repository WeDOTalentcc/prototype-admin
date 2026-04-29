class AddMessagesCountToWorkspaces < ActiveRecord::Migration[7.1]
  def up
    unless column_exists?(:workspaces, :messages_count)
      add_column :workspaces, :messages_count, :integer, default: 0, null: false
    end

    change_column_default :workspaces, :messages_count, 0
    execute "UPDATE workspaces SET messages_count = 0 WHERE messages_count IS NULL"
    change_column_null :workspaces, :messages_count, false

    execute <<-SQL.squish
      UPDATE workspaces
      SET messages_count = (
        SELECT COUNT(*)
        FROM messages
        WHERE messages.workspace_id = workspaces.id
      )
    SQL
  end

  def down
    remove_column :workspaces, :messages_count
  end
end
