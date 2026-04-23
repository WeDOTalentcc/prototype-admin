class AddUniqueIndexToJobStatusesName < ActiveRecord::Migration[7.1]
  def change
    add_index :job_statuses, :name, unique: true if table_exists?(:job_statuses) && !index_exists?(:job_statuses, :name, unique: true)
  end
end
