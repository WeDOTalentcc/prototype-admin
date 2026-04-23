require 'rails_helper'

RSpec.describe 'V1::Users::Lists API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:authentication_headers) { auth_headers(user) }

  describe 'GET /v1/users/lists' do
    let!(:my_list) { create(:list, user: user, account: account) }
    let!(:other_list) { create(:list) }

    it 'returns only lists from my account' do
      get '/v1/users/lists', headers: authentication_headers
      expect(response).to have_http_status(:success)
    end
  end

  describe 'GET /v1/users/lists/:id' do
    let(:list) { create(:list, user: user, account: account) }

    it 'returns the list' do
      get "/v1/users/lists/#{list.id}", headers: authentication_headers
      expect(response).to have_http_status(:success)
    end

    it 'returns 404 for list from another account' do
      other_list = create(:list)
      get "/v1/users/lists/#{other_list.id}", headers: authentication_headers
      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /v1/users/lists' do
    let(:valid_params) { { list: { name: 'Test List' } } }

    it 'creates a new list' do
      expect {
        post '/v1/users/lists', params: valid_params.to_json, headers: authentication_headers
      }.to change(List, :count).by(1)
    end

    it 'assigns current user and account' do
      post '/v1/users/lists', params: valid_params.to_json, headers: authentication_headers
      list = List.last
      expect(list.user_id).to eq(user.id)
      expect(list.account_id).to eq(account.id)
    end

    it 'returns error with invalid params' do
      post '/v1/users/lists', params: { list: { name: '' } }.to_json, headers: authentication_headers
      expect(response).to have_http_status(:unprocessable_entity)
    end
  end

  describe 'PUT /v1/users/lists/:id' do
    let(:list) { create(:list, user: user, account: account) }

    it 'updates the list' do
      put "/v1/users/lists/#{list.id}",
          params: { list: { name: 'Updated Name' } }.to_json,
          headers: authentication_headers
      expect(list.reload.name).to eq('Updated Name')
    end
  end

  describe 'DELETE /v1/users/lists/:id' do
    let!(:list) { create(:list, user: user, account: account) }

    it 'soft deletes the list' do
      delete "/v1/users/lists/#{list.id}", headers: authentication_headers
      expect(list.reload.is_deleted).to be true
    end
  end
end
