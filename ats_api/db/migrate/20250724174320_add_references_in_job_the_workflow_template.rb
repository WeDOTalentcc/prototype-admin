class AddReferencesInJobTheWorkflowTemplate < ActiveRecord::Migration[7.1]
  def change
    add_reference :jobs, :workflow_template, null: true, foreign_key: true
  end
end
