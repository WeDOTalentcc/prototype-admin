class AddJobIdInEntityPage < ActiveRecord::Migration[7.1]
  def change
    add_column :entity_pages, :job_id, :bigint, null: true, default: nil if !column_exists?(:entity_pages, :job_id)
  end
end
