class RemoveForeignKeyFromTeamsAndDepartmentTable < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :teams, :accounts if foreign_key_exists?(:teams, :accounts)
    remove_foreign_key :departments, :accounts if foreign_key_exists?(:departments, :accounts)
    remove_foreign_key :departments, :users, column: :manager_id if foreign_key_exists?(:departments, :users, column: :manager_id)
    remove_foreign_key :organizational_positions, :accounts if foreign_key_exists?(:organizational_positions, :accounts)
    remove_foreign_key :position_assignments, :accounts if foreign_key_exists?(:position_assignments, :accounts)
    remove_foreign_key :position_assignments, :users if foreign_key_exists?(:position_assignments, :users)
    remove_foreign_key :team_members, :accounts if foreign_key_exists?(:team_members, :accounts)
    remove_foreign_key :team_members, :users if foreign_key_exists?(:team_members, :users)
    remove_foreign_key :teams, :users, column: :team_lead_id if foreign_key_exists?(:teams, :users, column: :team_lead_id)
    remove_foreign_key :jobs, :users, column: :hiring_manager_id if foreign_key_exists?(:jobs, :users, column: :hiring_manager_id)
  end
end
