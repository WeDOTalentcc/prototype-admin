class CreateApprovers < ActiveRecord::Migration[7.1]
  def change
    create_table :approvers do |t|
      t.references :account, null: false, foreign_key: { to_table: "public.accounts" }
      t.references :user, null: false, foreign_key: { to_table: "public.users" }
      t.references :department, foreign_key: true
      t.string :approval_type, null: false
      t.integer :approval_level, null: false, default: 1
      t.decimal :limit_value, precision: 15, scale: 2
      t.string :name
      t.string :email
      t.string :title
      t.boolean :is_active, default: true, null: false
      t.boolean :is_deleted, default: false, null: false

      t.timestamps
    end

    add_index :approvers, [ :account_id, :approval_type, :approval_level ]
    add_index :approvers, [ :account_id, :department_id, :approval_type ]
    add_index :approvers, [ :account_id, :is_deleted ]
  end
end
