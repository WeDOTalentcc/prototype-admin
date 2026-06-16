# frozen_string_literal: true

class AddVoiceChannelAndNotificationChannelsToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :use_voice_channel, :boolean, default: false
    add_column :jobs, :notification_channels, :jsonb
  end
end
