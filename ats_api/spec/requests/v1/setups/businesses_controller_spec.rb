# spec/requests/v1/setups/businesses_spec.rb
require 'rails_helper'

RSpec.describe "V1::Setups::Businesses API", type: :request do
  let!(:account) { create(:account) }


  let!(:business) { create(:business, account: account) }

  let(:valid_token) { account.setup_token }

  describe 'GET /v1/setups/:setup_token/business' do
    context 'with a valid and unexpired token' do
      it 'returns the business details' do
        get "/v1/setups/#{valid_token}/business"

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)


        expect(json['data']['id']).to eq(business.id.to_s)
        expect(json['data']['attributes']['name']).to eq(business.name)
      end
    end

    context 'with an invalid token' do
      it 'returns a not found error' do
        get "/v1/setups/invalid-token-123/business"

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'with an expired token' do
      it 'returns a gone error' do
        account.update_columns(setup_token_expires_at: 1.day.ago)

        get "/v1/setups/#{valid_token}/business"

        expect(response).to have_http_status(:gone)
        json = JSON.parse(response.body)
        expect(json['error']).to include("expirou")
      end
    end
  end

  # --- Testes para PUT /v1/setups/:setup_token/business ---
  describe 'PUT /v1/setups/:setup_token/business' do
    let(:valid_attributes) { { business: { name: "New Updated Name", cnpj: "12345678901234" } } }

    context 'with a valid and unexpired token' do
      it 'updates the business' do
        put "/v1/setups/#{valid_token}/business", params: valid_attributes.to_json, headers: { 'Content-Type' => 'application/json' }

        # Recarregamos o objeto do banco de dados para verificar a alteração.
        business.reload

        expect(response).to have_http_status(:ok)
        expect(business.name).to eq("New Updated Name")
        expect(business.cnpj).to eq("12345678901234")
      end
    end

    context 'with invalid data' do
      it 'returns an unprocessable entity status' do
        # Forçamos um nome em branco, que deve ser inválido.
        invalid_attributes = { business: { name: "" } }
        put "/v1/setups/#{valid_token}/business", params: invalid_attributes.to_json, headers: { 'Content-Type' => 'application/json' }

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'with an invalid token' do
      it 'returns a not found error' do
        put "/v1/setups/invalid-token-123/business", params: valid_attributes.to_json, headers: { 'Content-Type' => 'application/json' }
        expect(response).to have_http_status(:not_found)
      end
    end
  end
end
