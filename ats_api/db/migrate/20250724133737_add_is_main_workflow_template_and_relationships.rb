class AddIsMainWorkflowTemplateAndRelationships < ActiveRecord::Migration[7.1]
  def up
    unless column_exists?(:workflow_templates, :is_main)
      add_column :workflow_templates, :is_main, :boolean, default: false
    end

    unless column_exists?(:selective_processes, :workflow_template_id)
      add_reference :selective_processes, :workflow_template, null: true, foreign_key: true
    end
  end

  def down
    if column_exists?(:workflow_templates, :is_main)
      remove_column :workflow_templates, :is_main
    end

    if column_exists?(:selective_processes, :workflow_template_id)
      remove_reference :selective_processes, :workflow_template, foreign_key: true
    end
  end
end
