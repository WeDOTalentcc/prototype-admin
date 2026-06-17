# spec/requests/v1/users/admin/roles_spec.rb
require 'rails_helper'

RSpec.describe "V1::Users::Admin::Roles", type: :request do
  # Criamos usuários com diferentes papéis para testar os cenários de permissão.
  let!(:super_admin) { create(:user, roles: [ :super_admin ]) }
  let!(:admin) { create(:user, roles: [ :admin ]) }
  let!(:regular_user) { create(:user, roles: [ :user ]) }

  # Criamos alguns dados de exemplo.
  let!(:roles) { create_list(:role, 3) }
  let(:role_id) { roles.first.id }

  # Helper para gerar o header de autorização.
  def auth_headers_for(user)
    { 'Authorization' => "Bearer #{JsonWebToken.encode(user_id: user.id)}" }
  end

  describe 'GET /v1/users/admin/roles' do
    context 'when user is an admin or super_admin' do
      it 'returns a list of roles' do
        Role.reindex
        get '/v1/users/admin/roles', headers: auth_headers_for(admin)

        expect(response).to have_http_status(:ok)
        expect(json['data'].size).to eq(Role.count) # Conta todas as roles, incluindo as criadas nos lets.
      end
    end

    context 'when user is a regular user' do
      it 'returns forbidden' do
        get '/v1/users/admin/roles', headers: auth_headers_for(regular_user)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'POST /v1/users/admin/roles' do
    let(:valid_attributes) { { role: { name: 'new_role', description: 'A new role' } } }

    context 'when user is an admin' do
      it 'creates a new role' do
        expect {
          post '/v1/users/admin/roles', params: valid_attributes, headers: auth_headers_for(admin)
        }.to change(Role, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('new_role')
      end
    end

    context 'when user is a regular user' do
      it 'returns forbidden' do
        post '/v1/users/admin/roles', params: valid_attributes, headers: auth_headers_for(regular_user)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'PUT /v1/users/admin/roles/:id' do
    let(:new_attributes) { { role: { description: 'Updated description' } } }

    context 'when user is a super_admin' do
      it 'updates the role' do
        put "/v1/users/admin/roles/#{role_id}", params: new_attributes, headers: auth_headers_for(super_admin)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['description']).to eq('Updated description')
      end
    end

    context 'when user is a regular user' do
      it 'returns forbidden' do
        put "/v1/users/admin/roles/#{role_id}", params: new_attributes, headers: auth_headers_for(regular_user)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /v1/users/admin/roles/:id' do
    context 'when user is an admin' do
      it 'deletes the role' do
        expect {
          delete "/v1/users/admin/roles/#{role_id}", headers: auth_headers_for(admin)
        }.to change(Role, :count).by(-1)

        expect(response).to have_http_status(:ok)
      end
    end
  end
end
