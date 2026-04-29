# frozen_string_literal: true

class CleanupRequestKeysJob < ApplicationJob
  queue_as :low_priority

  def perform
    RequestKey.where("expires_at < ?", Time.current).delete_all
  end
end
