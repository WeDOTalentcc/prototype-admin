class UpdateAgentPlansMessageFkOnDelete < ActiveRecord::Migration[7.1]
  def up
    # # agent_plans.message_id -> messages.id should cascade on delete of message
    # if foreign_key_exists?(:agent_plans, :messages)
    # 	remove_foreign_key :agent_plans, :messages
    # end
    # add_foreign_key :agent_plans, :messages, column: :message_id, on_delete: :cascade
  end

  def down
    # remove_foreign_key :agent_plans, :messages if foreign_key_exists?(:agent_plans, :messages)
    # add_foreign_key :agent_plans, :messages, column: :message_id
  end
end
