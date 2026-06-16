class AddIsUrgentToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :is_urgent, :boolean, default: false, null: false
  end
end
