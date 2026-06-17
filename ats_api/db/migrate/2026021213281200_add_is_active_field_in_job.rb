class AddIsActiveFieldInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :is_active, :boolean, default: true if not column_exists?(:jobs, :is_active)
    add_column :jobs, :reason_for_pause, :string if not column_exists?(:jobs, :reason_for_pause)
    add_index :jobs, :is_active if not index_exists?(:jobs, :is_active)
  end
end
