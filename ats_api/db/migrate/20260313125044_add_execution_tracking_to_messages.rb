# frozen_string_literal: true

class AddExecutionTrackingToMessages < ActiveRecord::Migration[7.1]
  def change
    add_column :messages, :is_thinking, :boolean
    add_column :messages, :thinking_status, :string
    add_column :messages, :execution_tracking, :jsonb
  end
end
