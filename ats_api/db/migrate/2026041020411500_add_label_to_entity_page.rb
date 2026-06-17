class AddLabelToEntityPage < ActiveRecord::Migration[7.1]
  def change
    add_column :entity_pages, :label, :string, null: true, default: nil unless column_exists?(:entity_pages, :label)
    add_column :entity_pages, :icon, :string, null: true, default: nil unless column_exists?(:entity_pages, :icon)
  end
end
