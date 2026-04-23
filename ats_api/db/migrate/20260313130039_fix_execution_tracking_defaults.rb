# frozen_string_literal: true

class FixExecutionTrackingDefaults < ActiveRecord::Migration[7.1]
  def change
    change_column_default :messages, :is_thinking, from: nil, to: false
    change_column_null :messages, :is_thinking, false, false
    change_column_default :messages, :execution_tracking, from: nil, to: {}

    add_index :messages, :is_thinking, where: "is_thinking = true", name: "idx_messages_thinking_active"
    add_index :messages, [ :reference_id, :is_thinking ], name: "idx_messages_ref_thinking"
  end
end
