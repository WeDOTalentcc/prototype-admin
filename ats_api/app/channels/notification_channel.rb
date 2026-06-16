# frozen_string_literal: true

class NotificationChannel < ApplicationCable::Channel
  private

  def after_authentication
    stream_from "notifications_user_#{current_user.id}"
  end
end
