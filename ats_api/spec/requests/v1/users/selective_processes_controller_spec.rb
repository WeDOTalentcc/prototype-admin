# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::SelectiveProcesses API', type: :request do
  let(:user) { create(:user) }
  let(:other_user) { create(:user) }

  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token', 'Content-Type' => 'application/json' } }
  let(:no_auth_headers) { { 'Content-Type' => 'application/json' } }

  describe 'GET /v1/users/selective_processes' do
    before do
      SelectiveProcess.destroy_all
      SelectiveProcess.reindex
      create_list(:job, 1)
      create_list(:job, 2)

      SelectiveProcess.reindex
    end

    context 'when authenticated' do
      it 'returns ALL selective processes in the system' do
        get '/v1/users/selective_processes', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(15)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users/selective_processes', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'with invalid token' do
      it 'returns unauthorized' do
        get '/v1/users/selective_processes', headers: invalid_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/selective_processes/:id' do
    let!(:selective_process) { create(:selective_process) }
    let!(:other_process) { create(:selective_process) }

    context 'when authenticated and accessing own selective process' do
      it 'returns the selective process' do
        get "/v1/users/selective_processes/#{selective_process.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['id']).to eq(selective_process.id)
        expect(json['data']['attributes']['name']).to eq(selective_process.name)
      end
    end

    context 'when authenticated and accessing another user\'s selective process' do
      it 'returns the selective process' do
        get "/v1/users/selective_processes/#{other_process.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['id']).to eq(other_process.id)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get "/v1/users/selective_processes/#{selective_process.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/selective_processes' do
    let(:job) { create(:job) }
    let(:valid_attributes) do
      {
        selective_process: {
          name: 'New Process',
          position: 1,
          status: 0,
          job_id: job.id,
          uid: SecureRandom.uuid,
          sub_status: [ 'pending' ]
        }
      }
    end

    let(:invalid_attributes) do
      {
        selective_process: {
          name: '',
          position: nil
        }
      }
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users/selective_processes', params: invalid_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include("Name can't be blank")
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        post '/v1/users/selective_processes', params: valid_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/selective_processes/:id' do
    let!(:selective_process) { create(:selective_process) }
    let!(:other_process) { create(:selective_process) }
    let(:new_attributes) { { selective_process: { name: 'Updated Name' } } }

    context 'when authenticated and updating own selective process' do
      it 'updates the selective process' do
        put "/v1/users/selective_processes/#{selective_process.id}", params: new_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        selective_process.reload
        expect(selective_process.name).to eq('Updated Name')
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        put "/v1/users/selective_processes/#{selective_process.id}", params: new_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/selective_processes/:id' do
    let!(:selective_process) { create(:selective_process) }

    context 'when authenticated and deleting own selective process' do
      it 'deletes the selective process' do
        expect do
          delete "/v1/users/selective_processes/#{selective_process.id}", headers: auth_headers(user)
        end.to change(SelectiveProcess, :count).by(-1)
        # expect(response).to have_http_status(:no_content)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/selective_processes/#{selective_process.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
