class AddHiringManagerNameAndEmailInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :hiring_manager_name, :string, null: true, default: nil unless column_exists?(:jobs, :hiring_manager_name)
    add_column :jobs, :hiring_manager_email, :string, null: true, default: nil unless column_exists?(:jobs, :hiring_manager_email)
  end
end
