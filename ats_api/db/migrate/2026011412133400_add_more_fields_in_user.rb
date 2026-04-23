class AddMoreFieldsInUser < ActiveRecord::Migration[7.1]
  def change
    add_column :users, :role_name, :string, null: true, default: nil if !column_exists?(:users, :role_name)
    add_column :users, :department_id, :integer, null: true, default: nil if !column_exists?(:users, :department_id)
    add_column :users, :phone, :string, null: true, default: nil if !column_exists?(:users, :phone)
    add_column :users, :position_level, :string, null: true, default: nil if !column_exists?(:users, :position_level)
    add_column :users, :whatsapp, :string, null: true, default: nil if !column_exists?(:users, :whatsapp)
    add_column :users, :status, :integer, null: true, default: 1 if !column_exists?(:users, :status)
    add_column :users, :city_id, :integer, null: true, default: nil if !column_exists?(:users, :city_id)
    add_column :users, :state_id, :integer, null: true, default: nil if !column_exists?(:users, :state_id)
    add_column :users, :is_manager, :boolean, null: true, default: false if !column_exists?(:users, :is_manager)
    add_column :users, :email_signature, :text, null: true, default: nil if !column_exists?(:users, :email_signature)
  end
end
