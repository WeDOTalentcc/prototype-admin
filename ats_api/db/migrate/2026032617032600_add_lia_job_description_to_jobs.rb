class AddLiaJobDescriptionToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :lia_job_description, :jsonb, default: {} if !column_exists?(:jobs, :lia_job_description)
  end
end
