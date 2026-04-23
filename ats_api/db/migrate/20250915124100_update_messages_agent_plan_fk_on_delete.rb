class UpdateMessagesAgentPlanFkOnDelete < ActiveRecord::Migration[7.1]
  def up
    # messages.agent_plan_id -> agent_plans.id should nullify on delete of agent_plan
    # if foreign_key_exists?(:messages, :agent_plans)
    # 	remove_foreign_key :messages, :agent_plans
    # end
    # add_foreign_key :messages, :agent_plans, column: :agent_plan_id, on_delete: :nullify
  end

  def down
    # remove_foreign_key :messages, :agent_plans if foreign_key_exists?(:messages, :agent_plans)
    # add_foreign_key :messages, :agent_plans, column: :agent_plan_id
  end
end
