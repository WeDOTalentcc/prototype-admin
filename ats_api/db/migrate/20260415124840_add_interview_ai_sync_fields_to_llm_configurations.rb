class AddInterviewAiSyncFieldsToLlmConfigurations < ActiveRecord::Migration[7.1]
  def change
    add_column :llm_configurations, :interview_ai_synced_at, :datetime
    add_column :llm_configurations, :interview_ai_sync_error, :text
  end
end
