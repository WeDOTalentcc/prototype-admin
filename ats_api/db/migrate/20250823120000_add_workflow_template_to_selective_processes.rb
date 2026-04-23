# frozen_string_literal: true

class AddWorkflowTemplateToSelectiveProcesses < ActiveRecord::Migration[7.1]
  def change
    # Add the reference only if the column truly doesn't exist yet
    unless column_exists?(:selective_processes, :workflow_template_id)
      add_reference :selective_processes,
                    :workflow_template,
                    null: true,
                    index: true,
                    foreign_key: true
    else
      # If the column exists, ensure index and foreign key are present
      unless index_exists?(:selective_processes, :workflow_template_id)
        add_index :selective_processes, :workflow_template_id
      end

      unless foreign_key_exists?(:selective_processes, :workflow_templates)
        add_foreign_key :selective_processes, :workflow_templates
      end
    end
  end
end
