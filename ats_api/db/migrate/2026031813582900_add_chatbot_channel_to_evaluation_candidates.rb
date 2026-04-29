class AddChatbotChannelToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :chatbot_channel, :integer unless column_exists?(:evaluation_candidates, :chatbot_channel)
    add_column :evaluation_candidates, :escalations, :jsonb, default: {} unless column_exists?(:evaluation_candidates, :escalations)
  end
end
