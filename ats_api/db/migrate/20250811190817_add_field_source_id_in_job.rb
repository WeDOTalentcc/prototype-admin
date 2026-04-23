class AddFieldSourceIdInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :source_job_id, :integer
    add_index :jobs, :source_job_id
  end
end
