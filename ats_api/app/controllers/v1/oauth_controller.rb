# frozen_string_literal: true

class V1::OauthController < ActionController::API
  include RenderDefault

  def create
    client = ApiClient.authenticate(params[:client_id], params[:client_secret])
    return render_simple_error("Invalid client credentials", status: :unauthorized) unless client

  token = JsonWebToken.encode_service_token(account_id: client.account_id)

    render json: { access_token: token, token_type: "Bearer", expires_in: 300 }
  end
end
