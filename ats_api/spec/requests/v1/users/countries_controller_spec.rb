# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Countries API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  let(:authentication_headers) { auth_headers(user) }
  let(:no_authentication_headers) { {} }

  describe 'GET /v1/users/countries' do
    let!(:countries) { create_list(:country, 5) }
    before do
      Country.reindex
    end

    context 'when authenticated' do
      before do
        get '/v1/users/countries', headers: authentication_headers
      end

      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns all countries' do
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(5)
      end
    end

    context 'when not authenticated' do
      it 'returns an unauthorized status' do
        get '/v1/users/countries', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/countries/:id' do
    let!(:country) { create(:country) }

    context 'when authenticated' do
      context 'when the country exists' do
        before do
          get "/v1/users/countries/#{country.id}", headers: authentication_headers
        end

        it 'returns a successful response' do
          expect(response).to have_http_status(:ok)
        end

        it 'returns the correct country' do
          json = JSON.parse(response.body)
          expect(json['data']['id']).to eq(country.id.to_s)
          expect(json['data']['attributes']['name']).to eq(country.name)
        end
      end

      context 'when the country does not exist' do
        it 'returns a not found status' do
          get "/v1/users/countries/0", headers: authentication_headers
          expect(response).to have_http_status(:not_found)
        end
      end
    end

    context 'when not authenticated' do
      it 'returns an unauthorized status' do
        get "/v1/users/countries/#{country.id}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
