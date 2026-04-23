class RemoveForeignKeyFromJobFieldTemplates < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :job_field_templates, :accounts if foreign_key_exists?(:job_field_templates, :accounts)
  end
end
