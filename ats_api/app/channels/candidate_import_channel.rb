# frozen_string_literal: true

class CandidateImportChannel < ApplicationCable::Channel
  private

  def after_authentication
    stream_from "candidate_import_#{current_user.account_id}"
  end
end
