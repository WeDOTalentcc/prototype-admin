# spec/support/auth.rb

module AuthHelper
  def auth_headers(user)
    token = JsonWebToken.encode(user_id: user.id)
    {
      'Authorization' => "Bearer #{token}",
      'Content-Type' => 'application/json'
    }
  end

  def default_auth_headers
    unless defined?(user) && user.present?
      raise "Você precisa definir `let(:user)` no spec ou passar explicitamente um usuário"
    end

    auth_headers(user)
  end

  def invalid_auth_headers
    {
      'Authorization' => 'Bearer invalid_token',
      'Content-Type' => 'application/json'
    }
  end

  def no_auth_headers
    {
      'Content-Type' => 'application/json'
    }
  end
end
