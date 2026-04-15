# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Auth::MagicLinks', type: :request do
  describe 'GET /v1/auth/magic-link/verify' do
    it 'route exists and does not return 404' do
      get '/v1/auth/magic-link/verify', params: { token: 'test', uid: '1' }

      # Should NOT be 404 (route not found).
      # Will be 401/unauthorized without valid token — that's correct behavior.
      expect(response.status).not_to eq(404)
    end
  end
end
