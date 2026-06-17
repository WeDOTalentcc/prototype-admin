# frozen_string_literal: true

class SourcingChannel < ApplicationCable::Channel
  private

  def after_authentication
    return reject unless params[:sourcing_id]

    stream_for "#{current_user.id}_sourcing_#{params[:sourcing_id]}"
  end
end
