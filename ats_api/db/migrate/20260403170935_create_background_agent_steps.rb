class CreateBackgroundAgentSteps < ActiveRecord::Migration[7.1]
  def change
    create_table :background_agent_steps do |t|

      t.timestamps
    end
  end
end
