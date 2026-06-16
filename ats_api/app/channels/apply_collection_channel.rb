# frozen_string_literal: true

class ApplyCollectionChannel < ApplicationCable::Channel
  private

  def after_authentication
    unless params[:job_id]
      Rails.logger.warn "[ApplyCollectionChannel] Rejected: No job_id provided"
      return reject
    end

    stream_for stream_identifier
  end

  def stream_identifier
    parts = [ current_user.id, "apply_collection", params[:job_id] ]
    parts << params[:selective_process_id] if params[:selective_process_id].present?
    parts.join("_")
  end
end
