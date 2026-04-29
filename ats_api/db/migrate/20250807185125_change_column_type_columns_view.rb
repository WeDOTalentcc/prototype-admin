class ChangeColumnTypeColumnsView < ActiveRecord::Migration[7.1]
  def change
    remove_column :entity_columns, :columns_view
    add_column :entity_columns, :columns_view, :jsonb, default: {}, null: false
  end
end
