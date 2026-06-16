# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Onboarding routes', type: :request do
  describe 'route existence (not 404)' do
    it 'GET /v1/onboarding/status is routed' do
      get '/v1/onboarding/status'
      expect(response.status).not_to eq(404)
    end

    it 'PATCH /v1/onboarding/progress is routed' do
      patch '/v1/onboarding/progress'
      expect(response.status).not_to eq(404)
    end

    it 'GET /v1/onboarding/settings is routed' do
      get '/v1/onboarding/settings'
      expect(response.status).not_to eq(404)
    end

    it 'POST /v1/onboarding/consent is routed' do
      post '/v1/onboarding/consent'
      expect(response.status).not_to eq(404)
    end

    it 'POST /v1/users/invite is routed' do
      post '/v1/users/invite'
      expect(response.status).not_to eq(404)
    end
  end
end
