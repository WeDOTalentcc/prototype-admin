class ChangeAccountIdOnWorkflowTemplate < ActiveRecord::Migration[7.1]
  def change
    def up
      remove_column :workflow_templates, :account_id
      add_reference :workflow_templates, :account, null: true, foreign_key: true
    end

    def down
      remove_reference :workflow_templates, :account, foreign_key: true
      add_column :workflow_templates, :account_id, :integer, array: true, default: []
    end
  end
end
