class CreateApplystatuses < ActiveRecord::Migration[7.1]
  def change
    create_table :apply_statuses do |t|
      t.references :apply, null: false, foreign_key: true
      t.references :selective_process, null: false, foreign_key: true
      t.integer :status_id
      t.string :status_name
      t.text :comment
      t.references :user, null: false, foreign_key: true
      t.boolean :is_deleted, default: false, null: false
      t.references :account, null: false, foreign_key: true
      t.timestamps
    end
  end
end
