class ChangeIndexProviderOnJob < ActiveRecord::Migration[7.1]
  def change
    remove_index :jobs, name: "index_jobs_on_provider_and_job_id"
  end
end
