# frozen_string_literal: true

class WorkflowChannel < ApplicationCable::Channel
  def subscribed
    stream_from "workflow_user_#{current_user.id}"
  end

  def unsubscribed
    # Cleanup if needed
  end
end
