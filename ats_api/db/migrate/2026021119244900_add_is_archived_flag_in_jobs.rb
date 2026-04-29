class AddIsArchivedFlagInJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :is_archived, :boolean, default: false if not column_exists?(:jobs, :is_archived)
    add_index :jobs, :is_archived if not index_exists?(:jobs, :is_archived)
  end
end
