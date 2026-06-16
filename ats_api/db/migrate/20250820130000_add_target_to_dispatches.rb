class AddTargetToDispatches < ActiveRecord::Migration[7.1]
  def change
    add_column :dispatches, :target_type, :string, null: false, default: 'ids' unless column_exists?(:dispatches, :target_type)
    add_column :dispatches, :target_payload, :jsonb, null: false, default: {} unless column_exists?(:dispatches, :target_payload)
    add_index :dispatches, :target_type unless index_exists?(:dispatches, :target_type)
  end
end
