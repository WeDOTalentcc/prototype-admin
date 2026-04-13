class CreateDepartments < ActiveRecord::Migration[7.1]
  def change
    create_table :departments, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.string :name, limit: 255, null: false
      t.string :code, limit: 50
      t.text :description
      t.uuid :parent_id
      t.string :manager_name, limit: 255
      t.string :manager_email, limit: 255
      t.string :manager_title, limit: 255
      t.string :manager_phone, limit: 50
      t.uuid :manager_id
      t.integer :headcount
      t.float :budget_annual
      t.string :cost_center, limit: 100
      t.string :location, limit: 255
      t.boolean :is_active, default: true
      t.integer :order
      t.string :hiring_priority, limit: 50
      t.timestamps
    end

    add_index :departments, :company_id
    add_foreign_key :departments, :company_profiles, column: :company_id
    add_foreign_key :departments, :departments, column: :parent_id
  end
end
