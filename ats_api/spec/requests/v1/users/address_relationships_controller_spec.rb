require 'rails_helper'

RSpec.describe V1::Users::AddressRelationshipsController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  let!(:address) { create(:address, account: account) }
  let!(:address_relationship) { create(:address_relationship, address: address, account: account) }

  describe 'GET /v1/users/address_relationships' do
    it 'returns a list of address relationships' do
      get v1_users_address_relationships_path, headers: headers
      expect(response).to have_http_status(:ok)
      expect(json['data']).to be_an(Array)
    end
  end

  describe 'GET /v1/users/address_relationships/:id' do
    it 'returns a specific address relationship' do
      get v1_users_address_relationship_path(address_relationship), headers: headers
      expect(response).to have_http_status(:ok)
      expect(json['data']['id']).to eq(address_relationship.id.to_s)
    end
  end

  describe 'POST /v1/users/address_relationships' do
    let(:valid_params) do
      {
        address_relationship: {
          reference_type: 'TestType',
          reference_id: 123,
          address_id: address.id
        }
      }
    end

    let(:invalid_params) do
      {
        address_relationshipss: {
          reference_type: '',
          reference_id: ''
        }
      }
    end

    context 'when params are valid' do
      it 'creates a new address relationship' do
        expect {
          post v1_users_address_relationships_path, params: valid_params.to_json, headers: headers
        }.to change(AddressRelationship, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['reference_type']).to eq('TestType')
      end
    end

    context 'when params are invalid' do
      it 'returns an error' do
        post v1_users_address_relationships_path, params: invalid_params.to_json, headers: headers
        expect(response).to have_http_status(:bad_request)
      end
    end
  end

  describe 'PUT /v1/users/address_relationships/:id' do
    let(:update_params) do
      { address_relationship: { reference_type: 'UpdatedType' } }
    end

    context 'when update is successful' do
      it 'updates the address relationship' do
        put v1_users_address_relationship_path(address_relationship), params: update_params.to_json, headers: headers
        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['reference_type']).to eq('UpdatedType')
      end
    end

    context 'when update fails' do
      it 'returns an error' do
        put v1_users_address_relationship_path(address_relationship),
            params: { address_relationship: { reference_type: '' } },
            headers: headers
        expect(response).to have_http_status(:bad_request)
      end
    end
  end

  describe 'DELETE /v1/users/address_relationships/:id' do
    it 'soft deletes the address relationship' do
      delete v1_users_address_relationship_path(address_relationship), headers: headers
      expect(response).to have_http_status(:ok)
      expect(address_relationship.reload.is_deleted).to eq(true)
    end
  end
end
