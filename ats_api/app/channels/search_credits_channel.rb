# frozen_string_literal: true

class SearchCreditsChannel < ApplicationCable::Channel
  private

  def after_authentication
    account = current_user.account
    return reject unless account

    stream_from "search_credits_account_#{account.id}"
  end
end
