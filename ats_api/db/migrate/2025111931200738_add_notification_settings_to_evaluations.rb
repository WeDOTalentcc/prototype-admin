class AddNotificationSettingsToEvaluations < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :notification_type, :integer, default: 0, null: false, comment: "0: per_candidate, 1: daily, 2: weekly"
    add_column :evaluations, :notification_enabled, :boolean, default: false, null: false
    add_column :evaluations, :notification_days, :integer, array: true, default: [], comment: "Week days: 0=sunday, 1=monday, ..., 6=saturday"
    add_column :evaluations, :notification_hour, :integer, comment: "Notification hour (0-23), business hours only (9-18)"

    add_index :evaluations, :notification_type
    add_index :evaluations, :notification_enabled
    add_index :evaluations, [ :notification_enabled, :notification_type, :notification_hour ], name: 'index_evaluations_on_notification_settings'
  end
end
