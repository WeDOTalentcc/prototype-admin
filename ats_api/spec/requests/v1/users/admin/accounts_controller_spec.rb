require 'rails_helper'

RSpec.describe 'V1::Users::Admin::Accounts API', type: :request do
  let!(:super_admin) { create(:user, roles: [ :super_admin ]) }
  let!(:admin) { create(:user, roles: [ :admin ]) }
  let!(:regular_user) { create(:user, roles: [ :user ]) }

  let!(:accounts) { create_list(:account, 3) }
  let(:account_id) { accounts.first.id }

  let(:valid_attributes) { { account: { name: 'Nova Conta Criada' } } }

  def auth_headers_for(user)
    { 'Authorization' => "Bearer #{JsonWebToken.encode(user_id: user.id)}", 'Content-Type' => 'application/json' }
  end

  #===========================================================================
  #
  # Testes para GET /v1/users/admin/accounts (Listagem)
  #
  #===========================================================================
  describe 'GET /v1/users/admin/accounts' do
    context 'when user is a super_admin' do
      it 'returns a list of all accounts' do
        Account.reindex
        get '/v1/users/admin/accounts', headers: auth_headers_for(super_admin)
        expect(response).to have_http_status(:ok)
        expect(JSON.parse(response.body)['data'].size).to eq(Account.count)
      end
    end

    context 'when user is a regular user' do
      it 'returns forbidden' do
        get '/v1/users/admin/accounts', headers: auth_headers_for(regular_user)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  #===========================================================================
  #
  # Testes para POST /v1/users/admin/accounts (Criação)
  #
  #===========================================================================
  describe 'POST /v1/users/admin/accounts' do
    context 'when user is a super_admin' do
      it 'creates a new account' do
        expect {
          post '/v1/users/admin/accounts', params: valid_attributes.to_json, headers: auth_headers_for(super_admin)
        }.to change(Account, :count).by(1)
        expect(response).to have_http_status(:created)
      end
    end

    context 'when user is an admin' do
      it 'returns forbidden' do
        post '/v1/users/admin/accounts', params: valid_attributes.to_json, headers: auth_headers_for(admin)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  #===========================================================================
  #
  # Testes para DELETE /v1/users/admin/accounts/:id (Deleção)
  #
  #===========================================================================
  describe 'DELETE /v1/users/admin/accounts/:id' do
    context 'when user is a super_admin' do
      it 'deletes the account' do
        expect {
          delete "/v1/users/admin/accounts/#{account_id}", headers: auth_headers_for(super_admin)
        }.to change(Account, :count).by(-1)
        expect(response).to have_http_status(:ok)
      end
    end

    context 'when user is an admin' do
      it 'returns forbidden' do
        delete "/v1/users/admin/accounts/#{account_id}", headers: auth_headers_for(admin)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end
end
