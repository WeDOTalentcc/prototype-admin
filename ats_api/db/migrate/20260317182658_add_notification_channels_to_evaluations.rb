class AddNotificationChannelsToEvaluations < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :notification_channels, :jsonb
  end
end
