class AddNotificationChannelsToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :notification_channels, :text, array: true, default: []
  end
end
