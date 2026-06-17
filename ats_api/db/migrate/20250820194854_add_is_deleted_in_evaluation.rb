class AddIsDeletedInEvaluation < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :is_deleted, :boolean, default: false if !column_exists?(:evaluations, :is_deleted)
  end
end
