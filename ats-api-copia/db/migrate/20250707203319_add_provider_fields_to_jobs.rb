class AddProviderFieldsToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :provider, :string, null: false, default: ""
    add_column :jobs, :provider_job_id, :string, null: false, default: ""
    add_column :jobs, :company_id, :bigint
    add_column :jobs, :published_date, :datetime
    add_column :jobs, :application_deadline, :datetime
    add_column :jobs, :is_remote, :boolean
    add_column :jobs, :city, :string
    add_column :jobs, :state, :string
    add_column :jobs, :country, :string
    add_column :jobs, :job_url, :string
    add_column :jobs, :career_page_id, :bigint
    add_column :jobs, :career_page_name, :string
    add_column :jobs, :career_page_url, :string
    add_column :jobs, :career_page_logo, :string
    add_column :jobs, :friendly_badge, :boolean
    add_column :jobs, :disabilities, :boolean
    add_column :jobs, :workplace_type, :string

    add_index :jobs, [:provider, :provider_job_id], unique: true, name: "index_jobs_on_provider_and_job_id"
  end
end
