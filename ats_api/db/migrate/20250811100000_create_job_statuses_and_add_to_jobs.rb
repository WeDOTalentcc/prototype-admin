class CreateJobStatusesAndAddToJobs < ActiveRecord::Migration[7.1]
  def change
    create_table :job_statuses do |t|
      t.string :name, null: false
      t.string :color, null: false
      t.timestamps
    end unless table_exists?(:job_statuses)

    if table_exists?(:jobs) && !column_exists?(:jobs, :job_status_id)
      add_reference :jobs, :job_status, foreign_key: true, null: true
    end
  end
end
