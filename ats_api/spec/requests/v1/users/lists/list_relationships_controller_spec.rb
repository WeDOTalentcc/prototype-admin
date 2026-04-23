require 'rails_helper'

RSpec.describe 'V1::Users::Lists::ListRelationships API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:authentication_headers) { auth_headers(user) }
  let(:list) { create(:list, user: user, account: account) }
  let(:candidate) { create(:candidate, account: account) }

  describe 'GET /v1/users/lists/:id/relationships_by_reference/:reference_type' do
    let!(:relationship) do
      create(:list_relationship, list: list, reference: candidate, account: account)
    end

    it 'returns relationships by reference type' do
      get "/v1/users/lists/#{list.id}/relationships_by_reference/Candidate",
          headers: authentication_headers
      expect(response).to have_http_status(:success)
    end
  end

  describe 'GET /v1/users/lists/:id/list_relationships/:relationship_id' do
    let(:relationship) do
      create(:list_relationship, list: list, reference: candidate, account: account)
    end

    it 'returns the relationship' do
      get "/v1/users/lists/#{list.id}/list_relationships/#{relationship.id}",
          headers: authentication_headers
      expect(response).to have_http_status(:success)
    end
  end

  describe 'POST /v1/users/lists/:id/list_relationships' do
    let(:valid_params) do
      {
        list_relationship: {
          reference_type: 'Candidate',
          reference_id: candidate.id
        }
      }
    end

    it 'creates a new relationship' do
      expect {
        post "/v1/users/lists/#{list.id}/list_relationships",
             params: valid_params.to_json,
             headers: authentication_headers
      }.to change(ListRelationship, :count).by(1)
    end

    it 'assigns account_id' do
      post "/v1/users/lists/#{list.id}/list_relationships",
           params: valid_params.to_json,
           headers: authentication_headers
      relationship = ListRelationship.last
      expect(relationship.account_id).to eq(account.id)
    end
  end

  describe 'PUT /v1/users/lists/:id/list_relationships/:relationship_id' do
    let(:relationship) do
      create(:list_relationship, list: list, reference: candidate, account: account, position: 0)
    end

    it 'updates the relationship' do
      put "/v1/users/lists/#{list.id}/list_relationships/#{relationship.id}",
          params: { list_relationship: { position: 5 } }.to_json,
          headers: authentication_headers
      expect(relationship.reload.position).to eq(5)
    end
  end

  describe 'DELETE /v1/users/lists/:id/list_relationships/:relationship_id' do
    let!(:relationship) do
      create(:list_relationship, list: list, reference: candidate, account: account)
    end

    it 'soft deletes the relationship' do
      delete "/v1/users/lists/#{list.id}/list_relationships/#{relationship.id}",
             headers: authentication_headers
      expect(relationship.reload.is_deleted).to be true
    end
  end

  describe 'POST /v1/users/lists/:id/list_relationships/sort' do
    let!(:relationships) do
      3.times.map do |i|
        create(:list_relationship, list: list, reference: create(:candidate, account: account),
               account: account, position: i)
      end
    end

    it 'updates positions' do
      sorted_ids = relationships.reverse.map(&:id)
      post "/v1/users/lists/#{list.id}/list_relationships/sort",
           params: { sorted_ids: sorted_ids }.to_json,
           headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(relationships.first.reload.position).to eq(2)
    end
  end

  describe 'POST /v1/users/lists/:id/list_relationships/collection' do
    it 'triggers background job for select_all' do
      search_params = { query: 'test' }
      post "/v1/users/lists/#{list.id}/list_relationships/collection",
           params: { search_params: search_params, select_all: true }.to_json,
           headers: authentication_headers
      expect(response).to have_http_status(:accepted)
    end
  end

  describe 'POST /v1/users/lists/:id/list_relationships/delete_collection' do
    let!(:relationships) do
      2.times.map do
        create(:list_relationship, list: list, reference: create(:candidate, account: account),
               account: account)
      end
    end

    it 'deletes multiple relationships' do
      ids = relationships.map(&:id)
      post "/v1/users/lists/#{list.id}/list_relationships/delete_collection",
           params: { ids: ids }.to_json,
           headers: authentication_headers
      expect(response).to have_http_status(:ok)
      relationships.each { |r| expect(r.reload.is_deleted).to be true }
    end
  end
end
