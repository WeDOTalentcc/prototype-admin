# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Cities API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:country) { create(:country) }
  let!(:state) { create(:state, country: country) }

  let(:authentication_headers) { auth_headers(user) }
  let(:no_authentication_headers) { {} }

  describe 'GET /v1/users/cities' do
    # Create cities for one state, and also for another to ensure the test
    # correctly fetches all of them without filtering.
    let!(:cities) { create_list(:city, 3, state: state) }
    let!(:other_state) { create(:state, country: country) }
    let!(:other_cities) { create_list(:city, 2, state: other_state) }


    before do
      City.reindex
    end

    context 'when authenticated' do
      before do
        get '/v1/users/cities', headers: authentication_headers
      end

      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns all cities' do
        json = JSON.parse(response.body)
        # Should return all 5 cities since there is no filter
        expect(json['data'].size).to eq(5)
      end
    end

    context 'when not authenticated' do
      before do
        get '/v1/users/cities', headers: no_authentication_headers
      end

      it 'returns unauthorized' do
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/cities/:id' do
    let!(:city) { create(:city, state: state) }

    context 'when authenticated' do
      before do
        get "/v1/users/cities/#{city.id}", headers: authentication_headers
      end

      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns the city data' do
        json = JSON.parse(response.body)
        expect(json['data']['id']).to eq(city.id.to_s)
        expect(json['data']['attributes']['name']).to eq(city.name)
      end
    end

    context 'when city does not exist' do
      before do
        get '/v1/users/cities/999999', headers: authentication_headers
      end

      it 'returns not found' do
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'POST /v1/users/cities' do
    let(:valid_params) do
      {
        city: {
          name: 'Nova Cidade',
          state_id: state.id,
          country_id: country.id
        }
      }
    end

    context 'when authenticated with valid params' do
      it 'creates a new city' do
        expect {
          post '/v1/users/cities', params: valid_params, headers: authentication_headers, as: :json
        }.to change(City, :count).by(1)
        expect(response).to have_http_status(:created)
      end

      it 'returns the created city data' do
        post '/v1/users/cities', params: valid_params, headers: authentication_headers, as: :json
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['name']).to eq('Nova Cidade')
        expect(json['data']['attributes']['state_id']).to eq(state.id)
      end
    end

    context 'when authenticated with invalid params' do
      let(:invalid_params) { { city: { name: '' } } }

      it 'does not create a city' do
         expect {
          post '/v1/users/cities', params: invalid_params, headers: authentication_headers, as: :json
        }.not_to change(City, :count)
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe 'PUT /v1/users/cities/:id' do
    let!(:city) { create(:city, state: state) }
    let(:valid_params) { { city: { name: 'Cidade Atualizada' } } }

    context 'when authenticated with valid params' do
      before do
        put "/v1/users/cities/#{city.id}", params: valid_params, headers: authentication_headers, as: :json
      end

      it 'updates the city' do
        expect(response).to have_http_status(:ok)
        city.reload
        expect(city.name).to eq('Cidade Atualizada')
      end
    end
  end

  describe 'DELETE /v1/users/cities/:id' do
    let!(:city) { create(:city, state: state) }

    context 'when authenticated' do
      it 'deletes the city' do
        expect {
          delete "/v1/users/cities/#{city.id}", headers: authentication_headers
        }.to change(City, :count).by(-1)
        expect(response).to have_http_status(:ok)
      end
    end
  end
end
