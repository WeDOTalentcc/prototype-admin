class AddManagerFieldsInDepartment < ActiveRecord::Migration[7.1]
  def change
    add_column :departments, :manager_name, :string if !column_exists?(:departments, :manager_name)
    add_column :departments, :manager_email, :string if !column_exists?(:departments, :manager_email)
    add_column :departments, :manager_title, :string if !column_exists?(:departments, :manager_title)
    add_column :departments, :color, :string if !column_exists?(:departments, :color)
    add_column :departments, :headcount, :integer if !column_exists?(:departments, :headcount)
    add_column :departments, :order, :integer if !column_exists?(:departments, :order)

    add_column :team_members, :name, :string if !column_exists?(:team_members, :name)
    add_column :team_members, :email, :string if !column_exists?(:team_members, :email)
    add_column :team_members, :phone, :string if !column_exists?(:team_members, :phone)
    add_column :team_members, :position, :string if !column_exists?(:team_members, :position)
    add_column :team_members, :linkedin_url, :string if !column_exists?(:team_members, :linkedin_url)
  end
end
