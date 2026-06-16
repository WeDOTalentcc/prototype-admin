class CreateWorkflowTemplates < ActiveRecord::Migration[7.1]
  def change
    create_table :workflow_templates do |t|
      t.string :name
      t.boolean :is_deleted, default: false
      t.references :user, null: false, foreign_key: { to_table: 'public.users' }
      t.references :account, null: false, foreign_key: { to_table: 'public.accounts' }
      t.timestamps
    end
  end
end
