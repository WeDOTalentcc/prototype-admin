require 'rails_helper'


require 'rails_helper'

RSpec.describe 'V1::Users::JobStatuses API', type: :request do
  let(:admin) { create(:user, :admin) }
  let(:user) { create(:user) }
  let!(:job_status) { create(:job_status, name: 'Ativo', color: '#00FF00') }

  describe 'GET /v1/users/job_statuses' do
    before do
      JobStatus.reindex
    end

    context 'when authenticated as admin' do
      it 'returns all job statuses' do
        get '/v1/users/job_statuses', headers: auth_headers(admin)
        expect(response).to have_http_status(:ok)

        expect(json['data'].first['attributes']['name']).to eq('Ativo')
      end
    end
    context 'when authenticated as user' do
      it 'returns all job statuses' do
        get '/v1/users/job_statuses', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        expect(json['data'].first['attributes']['name']).to eq('Ativo')
      end
    end
    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users/job_statuses', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/job_statuses/:id' do
    context 'when authenticated as admin' do
      it 'returns a job status' do
        get "/v1/users/job_statuses/#{job_status.id}", headers: auth_headers(admin)
        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['name']).to eq('Ativo')
      end
    end
    context 'when authenticated as user' do
      it 'returns a job status' do
        get "/v1/users/job_statuses/#{job_status.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['name']).to eq('Ativo')
      end
    end
    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get "/v1/users/job_statuses/#{job_status.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/job_statuses' do
    context 'when authenticated as admin' do
      it 'allows admin to create' do
        post '/v1/users/job_statuses', params: { job_status: { name: 'Novo', color: '#123456' } }.to_json, headers: auth_headers(admin)
        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('Novo')
      end
    end
    context 'when authenticated as user' do
      it 'forbids user to create' do
        post '/v1/users/job_statuses', params: { job_status: { name: 'Novo', color: '#123456' } }.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden).or have_http_status(:unauthorized)
      end
    end
    context 'when unauthenticated' do
      it 'returns unauthorized' do
        post '/v1/users/job_statuses', params: { job_status: { name: 'Novo', color: '#123456' } }.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/job_statuses/:id' do
    context 'when authenticated as admin' do
      it 'allows admin to update' do
        put "/v1/users/job_statuses/#{job_status.id}", params: { job_status: { color: '#000000' } }.to_json, headers: auth_headers(admin)
        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['color']).to eq('#000000')
      end
    end
    context 'when authenticated as user' do
      it 'forbids user to update' do
        put "/v1/users/job_statuses/#{job_status.id}", params: { job_status: { color: '#000000' } }.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden).or have_http_status(:unauthorized)
      end
    end
    context 'when unauthenticated' do
      it 'returns unauthorized' do
        put "/v1/users/job_statuses/#{job_status.id}", params: { job_status: { color: '#000000' } }.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/job_statuses/:id' do
    context 'when authenticated as admin' do
      it 'allows admin to destroy' do
        delete "/v1/users/job_statuses/#{job_status.id}", headers: auth_headers(admin)
        expect(response).to have_http_status(:ok)
      end
    end
    context 'when authenticated as user' do
      it 'forbids user to destroy' do
        delete "/v1/users/job_statuses/#{job_status.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden).or have_http_status(:unauthorized)
      end
    end
    context 'when unauthenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/job_statuses/#{job_status.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
