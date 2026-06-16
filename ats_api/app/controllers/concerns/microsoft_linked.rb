# frozen_string_literal: true

module MicrosoftLinked
  extend ActiveSupport::Concern

  included do
    before_action :require_microsoft_linked
  end

  private

  def require_microsoft_linked
    return if current_user_has_microsoft_tokens?

    render json: { error: "Conta Microsoft não vinculada" }, status: :bad_request
  end

  def current_user_has_microsoft_tokens?
    @current_user.present? && (
      @current_user.ms_access_token.present? || @current_user.ms_refresh_token.present?
    )
  end
end
