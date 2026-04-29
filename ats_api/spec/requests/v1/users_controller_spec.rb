require 'rails_helper'

RSpec.describe 'V1::Users API', type: :request do
  let!(:account) { create(:account) }
  let!(:user_for_auth) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user_for_auth) }
  let(:no_auth_headers) { { 'Content-Type' => 'application/json' } }

  # --- INDEX ---
  describe 'GET /v1/users' do
    before do
      create_list(:user, 2, account: account)
      User.reindex
    end

    context 'when authenticated' do
      it 'returns all users for the account' do
        get '/v1/users', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  # --- SHOW ---
  describe 'GET /v1/users/:id' do
    let!(:target_user) { create(:user, account: account) }

    context 'when authenticated' do
      it 'returns the specified user' do
        get "/v1/users/#{target_user.id}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['id']).to eq(target_user.id.to_s)
        expect(json['data']['attributes']['email']).to eq(target_user.email)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get "/v1/users/#{target_user.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  # --- CREATE ---
  describe 'POST /v1/users' do
    let(:valid_attributes) do
      { user: { name: 'New User', email: 'new.user@example.com', password: 'password123' } }
    end
    let(:invalid_attributes) { { user: { email: '' } } }

    context 'when authenticated with valid attributes' do
      it 'creates a new user' do
        expect {
          post '/v1/users', params: valid_attributes.to_json, headers: authentication_headers
        }.to change(User, :count).by(1)

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['email']).to eq('new.user@example.com')

        expect(User.last.account).to eq(user_for_auth.account)
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users', params: invalid_attributes.to_json, headers: authentication_headers
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        post '/v1/users', params: valid_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  # --- UPDATE ---
  describe 'PUT /v1/users/:id' do
    let!(:target_user) { create(:user, account: account) }
    let(:new_attributes) { { user: { name: 'Updated Name' } } }

    context 'when authenticated' do
      it 'updates the user' do
        put "/v1/users/#{target_user.id}", params: new_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        target_user.reload
        expect(target_user.name).to eq('Updated Name')
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        put "/v1/users/#{target_user.id}", params: new_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  # --- DESTROY ---
  describe 'DELETE /v1/users/:id' do
    let!(:target_user) { create(:user, account: account) }

    context 'when authenticated' do
      it 'deletes the user' do
        expect {
          delete "/v1/users/#{target_user.id}", headers: authentication_headers
        }.to change(User, :count).by(-1)
        # Seu controller retorna 200 OK com o objeto deletado, não 204 No Content
        expect(response).to have_http_status(:ok)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/#{target_user.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
