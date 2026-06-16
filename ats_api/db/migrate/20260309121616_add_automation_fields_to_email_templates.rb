# frozen_string_literal: true

class AddAutomationFieldsToEmailTemplates < ActiveRecord::Migration[7.1]
  def change
    add_column :email_templates, :is_automated, :boolean, default: false, null: false
    add_column :email_templates, :delay_hours, :integer
    add_column :email_templates, :response_deadline_days, :integer
    add_column :email_templates, :trigger_event, :string

    add_index :email_templates, %i[account_id trigger_event],
              where: "is_automated = true",
              name: "idx_email_templates_automated_trigger"
  end
end
