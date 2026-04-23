# frozen_string_literal: true

class BackgroundAgentChannel < ApplicationCable::Channel
  def after_authentication
    agent = BackgroundAgent.where(is_deleted: false).find_by(id: params[:agent_id])
    reject unless agent&.user_id == current_user.id

    stream_for "#{current_user.id}_agent_#{params[:agent_id]}"
  end
end
