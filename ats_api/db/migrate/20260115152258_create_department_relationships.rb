class CreateDepartmentRelationships < ActiveRecord::Migration[7.1]
  def change
    create_table :department_relationships do |t|
      t.references :department, null: false, foreign_key: true
      t.references :user, foreign_key: true
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.string :role, default: "member", null: false
      t.string :title
      t.boolean :is_primary, default: false, null: false
      t.boolean :is_deleted, default: false, null: false
      t.references :account, null: false, foreign_key: true
      t.timestamps

      t.index %i[reference_type reference_id], name: "index_department_relationships_on_reference"
      t.index %i[department_id role], name: "index_department_relationships_on_department_role"
      t.index %i[department_id user_id], name: "index_department_relationships_on_dept_user", unique: true, where: "user_id IS NOT NULL AND is_deleted = false"
    end
  end
end
