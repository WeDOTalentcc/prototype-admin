class AddWsiSeniorityFieldToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :wsi_suggested_seniority_key, :string, null: true unless column_exists?(:jobs, :wsi_suggested_seniority_key)
    add_column :jobs, :seniority_override_log, :jsonb, default: {} unless column_exists?(:jobs, :seniority_override_log)
  end
end
