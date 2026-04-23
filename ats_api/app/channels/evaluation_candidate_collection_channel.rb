# frozen_string_literal: true

class EvaluationCandidateCollectionChannel < ApplicationCable::Channel
  private

  def after_authentication
    stream_for "#{current_user.id}_collection"
  end
end
