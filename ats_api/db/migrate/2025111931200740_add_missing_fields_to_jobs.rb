class AddMissingFieldsToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :missing_fields, :jsonb, default: [] unless column_exists?(:jobs, :missing_fields)
  end
end
