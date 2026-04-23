# frozen_string_literal: true

class JobCopyChannel < ApplicationCable::Channel
  private

  def after_authentication
    stream_for "#{current_user.id}_job_copy_collection"
  end
end
