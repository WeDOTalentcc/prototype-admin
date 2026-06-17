# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::States API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:country) { create(:country) }

  let(:authentication_headers) { auth_headers(user) }
  let(:no_authentication_headers) { {} }

  describe 'GET /v1/users/states' do
    let!(:states) { create_list(:state, 3, country: country) }

    before do
      State.reindex
    end

    context 'when authenticated' do
      before do
        get '/v1/users/states', headers: authentication_headers
      end

      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns all states' do
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
      end
    end

    context 'when filtering by country_id' do
      let!(:other_country) { create(:country) }
      let!(:other_states) { create_list(:state, 2, country: other_country) }

      before do
        State.reindex
        get "/v1/users/states?country_id=#{country.id}", headers: authentication_headers
      end

      it 'returns only states from the specified country' do
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
        json['data'].each do |state_data|
          expect(state_data['attributes']['country_id']).to eq(country.id)
        end
      end
    end

    context 'when not authenticated' do
      before do
        get '/v1/users/states', headers: no_authentication_headers
      end

      it 'returns unauthorized' do
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/states/:id' do
    let!(:state) { create(:state, country: country) }

    context 'when authenticated' do
      before do
        get "/v1/users/states/#{state.id}", headers: authentication_headers
      end

      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns the state data' do
        json = JSON.parse(response.body)
        expect(json['data']['id']).to eq(state.id.to_s)
        expect(json['data']['attributes']['name']).to eq(state.name)
      end
    end

    context 'when state does not exist' do
      before do
        get '/v1/users/states/999999', headers: authentication_headers
      end

      it 'returns not found' do
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'POST /v1/users/states' do
    let(:valid_params) do
      {
        state: {
          name: 'São Paulo',
          country_id: country.id
        }
      }
    end

    context 'when authenticated with valid params' do
      before do
        post '/v1/users/states', params: valid_params, headers: authentication_headers
      end

      it 'creates a new state' do
        expect(response).to have_http_status(:created)
        expect(State.count).to eq(1)
      end

      it 'returns the created state data' do
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['name']).to eq('São Paulo')
        expect(json['data']['attributes']['country_id']).to eq(country.id)
      end
    end

    context 'when authenticated with invalid params' do
      let(:invalid_params) do
        {
          state: {
            name: '',
            country_id: country.id
          }
        }
      end

      before do
        post '/v1/users/states', params: invalid_params, headers: authentication_headers
      end

      it 'returns unprocessable entity' do
        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'does not create a state' do
        expect(State.count).to eq(0)
      end
    end
  end

  describe 'PUT /v1/users/states/:id' do
    let!(:state) { create(:state, country: country) }

    let(:valid_params) do
      {
        state: {
          name: 'Rio de Janeiro'
        }
      }
    end

    context 'when authenticated with valid params' do
      before do
        put "/v1/users/states/#{state.id}", params: valid_params, headers: authentication_headers
      end

      it 'updates the state' do
        expect(response).to have_http_status(:ok)
        state.reload
        expect(state.name).to eq('Rio de Janeiro')
      end
    end

    context 'when state does not exist' do
      before do
        put '/v1/users/states/999999', params: valid_params, headers: authentication_headers
      end

      it 'returns not found' do
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'DELETE /v1/users/states/:id' do
    let!(:state) { create(:state, country: country) }

    context 'when authenticated' do
      before do
        delete "/v1/users/states/#{state.id}", headers: authentication_headers
      end

      it 'deletes the state' do
        expect(response).to have_http_status(:ok)
        expect(State.count).to eq(0)
      end
    end

    context 'when state does not exist' do
      before do
        delete '/v1/users/states/999999', headers: authentication_headers
      end

      it 'returns not found' do
        expect(response).to have_http_status(:not_found)
      end
    end
  end
end
