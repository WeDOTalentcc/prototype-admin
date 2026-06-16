# frozen_string_literal: true

class CreateNotificationPreferences < ActiveRecord::Migration[7.1]
  def change
    create_table :notification_preferences do |t|
      t.references :user, null: false, foreign_key: true, index: { unique: true }
      t.boolean :briefing_enabled, default: true, null: false
      t.string :briefing_time, default: "08:00", null: false
      t.string :briefing_channel, default: "web", null: false
      t.boolean :alert_aging_enabled, default: true, null: false
      t.boolean :alert_deadline_enabled, default: true, null: false
      t.boolean :alert_no_show_enabled, default: true, null: false
      t.boolean :alert_evaluation_enabled, default: true, null: false
      t.boolean :alert_strong_fit_enabled, default: true, null: false
      t.boolean :alert_stale_job_enabled, default: true, null: false
      t.integer :aging_threshold_days, default: 3, null: false
      t.string :alert_channels, array: true, default: [ "web" ], null: false
      t.string :timezone, default: "America/Sao_Paulo", null: false
      t.timestamps
    end
  end
end
