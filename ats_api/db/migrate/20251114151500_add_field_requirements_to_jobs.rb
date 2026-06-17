class AddFieldRequirementsToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :field_requirements, :jsonb, default: [], null: false

    add_index :jobs, :field_requirements, using: :gin
  end
end
