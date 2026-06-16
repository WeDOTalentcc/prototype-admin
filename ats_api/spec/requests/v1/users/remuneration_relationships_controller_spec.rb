require 'rails_helper'

RSpec.describe V1::Users::RemunerationRelationshipsController, type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }
  let!(:remuneration) { create(:remuneration, account: account, user: user) }

  describe 'GET /v1/users/remuneration_relationships', search: true do
    let!(:active_relationship) { create(:remuneration_relationship, account: account, user: user, remuneration: remuneration, is_deleted: false) }
    let!(:deleted_relationship) { create(:remuneration_relationship, account: account, user: user, remuneration: remuneration, is_deleted: true) }

    it 'returns only non-deleted remuneration relationships' do
      get '/v1/users/remuneration_relationships', headers: headers

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data'].size).to eq(1)
      expect(body['data'].first['attributes']['is_deleted']).to eq(false)
    end
  end

  describe 'GET /v1/users/remuneration_relationships/:id' do
    let!(:relationship) { create(:remuneration_relationship, account: account, user: user, remuneration: remuneration) }

    it 'returns the relationship' do
      get "/v1/users/remuneration_relationships/#{relationship.id}", headers: headers
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']['id']).to eq(relationship.id.to_s)
    end
  end

  describe 'POST /v1/users/remuneration_relationships' do
    let(:params) do
      {
        remuneration_relationship: {
          remuneration_id: remuneration.id,
          reference_type: "Job",
          reference_id: 123,
          currency: "BRL",
          value: 5000.00
        }
      }
    end

    it 'creates a relationship' do
      expect {
        post '/v1/users/remuneration_relationships', params: params.to_json, headers: headers
      }.to change(RemunerationRelationship, :count).by(1)

      expect(response).to have_http_status(:created)
      body = JSON.parse(response.body)
      expect(body['data']['attributes']['reference_type']).to eq('Job')
    end
  end

  describe 'PUT /v1/users/remuneration_relationships/:id' do
    let!(:relationship) { create(:remuneration_relationship, account: account, user: user, remuneration: remuneration, comments: "old") }

    it 'updates the relationship' do
      put "/v1/users/remuneration_relationships/#{relationship.id}", params: {
        remuneration_relationship: { comments: "new" }
    }.to_json, headers: headers

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']['attributes']['comments']).to eq('new')
    end
  end

  describe 'DELETE /v1/users/remuneration_relationships/:id' do
    let!(:relationship) { create(:remuneration_relationship, account: account, user: user, remuneration: remuneration) }

    it 'soft deletes the relationship' do
      delete "/v1/users/remuneration_relationships/#{relationship.id}", headers: headers

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']['attributes']['is_deleted']).to eq(true)
    end
  end

  describe 'POST /v1/users/remuneration_relationships/bulk_upsert' do
    let!(:job1) { create(:job, account: account) }
    let!(:job2) { create(:job, account: account) }

    context 'with valid params' do
      let(:params) do
        {
          remuneration_relationships: [
            {
              remuneration_id: remuneration.id,
              reference_type: "Job",
              reference_id: job1.id,
              currency: "BRL",
              value: 5000.00,
              contract_type: [ "CLT" ]
            },
            {
              remuneration_id: remuneration.id,
              reference_type: "Job",
              reference_id: job2.id,
              currency: "USD",
              value: 3000.00,
              contract_type: [ "PJ" ]
            }
          ]
        }
      end

      it 'creates multiple relationships' do
        post '/v1/users/remuneration_relationships/bulk_upsert', params: params.to_json, headers: headers

        expect(response).to have_http_status(:ok)
        body = JSON.parse(response.body)
        expect(body['success']).to eq(true)
        expect(body['data']['created']).to eq(2)
        expect(body['data']['updated']).to eq(0)
        expect(body['data']['total']).to eq(2)
        expect(body['data']['relationships'].size).to eq(2)
      end

      context 'when relationships already exist' do
        before do
          create(:remuneration_relationship,
            account: account,
            user: user,
            remuneration: remuneration,
            reference_type: "Job",
            reference_id: job1.id,
            value: 4000.00
          )
        end

        it 'updates existing and creates new' do
          post '/v1/users/remuneration_relationships/bulk_upsert', params: params.to_json, headers: headers

          expect(response).to have_http_status(:ok)
          body = JSON.parse(response.body)
          expect(body['success']).to eq(true)
          expect(body['data']['created']).to eq(1)
          expect(body['data']['updated']).to eq(1)
          expect(body['data']['total']).to eq(2)

          updated = RemunerationRelationship.find_by(reference_id: job1.id, remuneration_id: remuneration.id)
          expect(updated.value).to eq(5000.00)
        end
      end
    end

    context 'with invalid params' do
      it 'returns error when params is not an array' do
        post '/v1/users/remuneration_relationships/bulk_upsert', params: {
          remuneration_relationships: "invalid"
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        body = JSON.parse(response.body)
        expect(body['errors'].first).to include("obrigatório")
      end

      it 'returns error when array is empty' do
        post '/v1/users/remuneration_relationships/bulk_upsert', params: {
          remuneration_relationships: []
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        body = JSON.parse(response.body)
        expect(body['errors'].first).to include("ao menos uma")
      end

      it 'returns error when required fields are missing' do
        post '/v1/users/remuneration_relationships/bulk_upsert', params: {
          remuneration_relationships: [
            { currency: "BRL", value: 5000 }
          ]
        }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        body = JSON.parse(response.body)
        expect(body['success']).to eq(false)
        expect(body['errors'].first['errors']).to include("Campos obrigatórios")
      end
    end

    context 'when one item fails validation' do
      let(:params) do
        {
          remuneration_relationships: [
            {
              remuneration_id: remuneration.id,
              reference_type: "Job",
              reference_id: job1.id,
              currency: "BRL",
              value: 5000.00
            },
            {
              remuneration_id: nil,
              reference_type: "Job",
              reference_id: job2.id,
              currency: "USD"
            }
          ]
        }
      end

      it 'rolls back all changes' do
        expect {
          post '/v1/users/remuneration_relationships/bulk_upsert', params: params.to_json, headers: headers
        }.not_to change(RemunerationRelationship, :count)

        expect(response).to have_http_status(:unprocessable_entity)
        body = JSON.parse(response.body)
        expect(body['success']).to eq(false)
        expect(body['errors']).to be_present
      end
    end
  end

  describe 'authorization' do
    let!(:other_user) { create(:user) }
    let(:other_account) { other_user.account }
    let!(:other_remuneration) { create(:remuneration, account: other_account, user: other_user) }
    let!(:relationship) { create(:remuneration_relationship, account: other_account, user: other_user, remuneration: other_remuneration) }

    it 'forbids update if not owner' do
      put "/v1/users/remuneration_relationships/#{relationship.id}", params: {
        remuneration_relationship: { comments: "hacked" }
    }.to_json, headers: headers

      expect(response).to have_http_status(:forbidden)
    end

    it 'forbids destroy if not owner' do
      delete "/v1/users/remuneration_relationships/#{relationship.id}", headers: headers
      expect(response).to have_http_status(:forbidden)
    end
  end
end
