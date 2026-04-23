class RecreateWorkflowTemplatesTable < ActiveRecord::Migration[7.1]
  def change
    remove_reference :selective_processes, :workflow_template, foreign_key: true if column_exists?(:selective_processes, :workflow_template_id)
    drop_table :workflow_templates if ActiveRecord::Base.connection.table_exists?(:workflow_templates)
    create_table :workflow_templates, force: :cascade do |t|
      t.string :name
      t.boolean :is_deleted, default: false
      t.boolean :is_main, default: false
      t.references :user, null: false, foreign_key: { to_table: 'public.users' }
      t.references :account, null: false, foreign_key: { to_table: 'public.accounts' }

      t.timestamps
    end
  end
end
