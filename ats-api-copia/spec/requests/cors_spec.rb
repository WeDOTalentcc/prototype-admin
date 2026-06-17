# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'CORS', type: :request do
  describe 'preflight OPTIONS request' do
    it 'allows requests from the default localhost origin' do
      options '/v1/users', headers: {
        'Origin' => 'http://localhost:3000',
        'Access-Control-Request-Method' => 'GET',
        'Access-Control-Request-Headers' => 'Authorization'
      }

      expect(response.headers['Access-Control-Allow-Origin']).to eq('http://localhost:3000')
      expect(response.headers['Access-Control-Allow-Methods']).to include('GET')
      expect(response.headers['Access-Control-Allow-Credentials']).to eq('true')
    end

    it 'rejects requests from unknown origins' do
      options '/v1/users', headers: {
        'Origin' => 'https://evil.example.com',
        'Access-Control-Request-Method' => 'GET'
      }

      expect(response.headers['Access-Control-Allow-Origin']).to be_nil
    end
  end
end
