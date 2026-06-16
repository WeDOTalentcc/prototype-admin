class AddIsMainInJobStatuses < ActiveRecord::Migration[7.1]
  def change
    if !JobStatus.column_names.include?('is_main')
      add_column :job_statuses, :is_main, :boolean, default: true, null: false
    end
  end
end
