require 'rails_helper'

RSpec.describe V1::Users::AddressesController, type: :request do
  let(:account) { create(:account) }
  let(:user)    { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  let!(:address) { create(:address, account: account) }

  describe 'GET /v1/users/addresses' do
    it 'returns a list of addresses' do
      get v1_users_addresses_path, headers: headers
      expect(response).to have_http_status(:ok)
      expect(json['data']).to be_an(Array)
    end
  end

  describe 'GET /v1/users/addresses/:id' do
    it 'returns a specific address' do
      get v1_users_address_path(address), headers: headers
      expect(response).to have_http_status(:ok)
      expect(json['data']['id']).to eq(address.id.to_s)
    end
  end

  describe 'POST /v1/users/addresses' do
    let(:valid_params) do
      {
        address: {
          street: 'Rua Teste',
          number: '123',
          zip_code: '12345-678'
        }
      }
    end

    let(:invalid_params) do
      { addresess: { street: '' } }
    end

    context 'when params are valid' do
      it 'creates a new address' do
        expect {
          post v1_users_addresses_path, params: valid_params.to_json, headers: headers
        }.to change(Address, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['street']).to eq('Rua Teste')
      end
    end

    context 'when params are invalid' do
      it 'returns an error' do
        post v1_users_addresses_path, params: invalid_params.to_json, headers: headers
        expect(response).to have_http_status(:bad_request)
      end
    end
  end

  describe 'PUT /v1/users/addresses/:id' do
    let(:update_params) { { address: { street: 'Nova Rua' } } }

    context 'when update is successful' do
      it 'updates the address' do
        put v1_users_address_path(address), params: update_params.to_json, headers: headers
        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['street']).to eq('Nova Rua')
      end
    end

    context 'when update fails' do
      it 'returns an error' do
        put v1_users_address_path(address), params: { addresses: { street: '' } }.to_json, headers: headers
        expect(response).to have_http_status(:bad_request)
      end
    end
  end

  describe 'DELETE /v1/users/addresses/:id' do
    it 'soft deletes the address' do
      delete v1_users_address_path(address), headers: headers
      expect(response).to have_http_status(:ok)
      expect(address.reload.is_deleted).to eq(true)
    end
  end
end
