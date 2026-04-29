# frozen_string_literal: true

class MessageChannel < ApplicationCable::Channel
  private

  def after_authentication
    stream_from "messages_user_#{current_user.id}"
  end
end
