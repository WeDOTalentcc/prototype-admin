class CleanupDuplicateLiaGeneralWorkspaces < ActiveRecord::Migration[7.1]
  def up
    execute <<-SQL.squish
      UPDATE workspaces
      SET is_deleted = true
      WHERE domain = 'lia_general'
        AND is_deleted = false
        AND id NOT IN (
          SELECT MIN(id)
          FROM workspaces
          WHERE domain = 'lia_general'
            AND is_deleted = false
          GROUP BY user_id, account_id
        )
    SQL
  end

  def down; end
end
