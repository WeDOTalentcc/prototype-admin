# spec/requests/v1/users/job_journeys_controller_spec.rb
require 'rails_helper'

RSpec.describe V1::Users::JobJourneysController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe 'GET /v1/users/job_journeys' do
    before do
      # Limpa os job_journeys criados automaticamente
      JobJourney.where(account_id: account.id).delete_all

      create(:job_journey, account: account, name: 'Informações Básicas', position: 1)
      create(:job_journey, account: account, name: 'Remuneração', position: 2)
      JobJourney.reindex(refresh: true)
    end

    it 'returns job journeys for the account' do
      get '/v1/users/job_journeys', headers: headers

      expect(response).to have_http_status(:ok)
      response_body = JSON.parse(response.body)
      expect(response_body['data'].size).to eq(2)
    end
  end

  describe 'GET /v1/users/job_journeys/:id' do
    before do
      JobJourney.where(account_id: account.id).delete_all
    end

    let(:job_journey) { create(:job_journey, account: account, name: 'Informações Básicas') }

    it 'returns the job journey' do
      get "/v1/users/job_journeys/#{job_journey.id}", headers: headers

      expect(response).to have_http_status(:ok)
      response_body = JSON.parse(response.body)
      expect(response_body['data']['id']).to eq(job_journey.id.to_s)
      expect(response_body['data']['attributes']['name']).to eq('Informações Básicas')
    end
  end

  describe 'POST /v1/users/job_journeys' do
    before do
      JobJourney.where(account_id: account.id).delete_all
    end

    let(:params) do
      {
        job_journey: {
          name: 'Nova Etapa',
          description: 'Descrição da nova etapa',
          position: 16,
          active: true,
          required: false
        }
      }
    end

    it 'creates a job journey' do
      initial_count = JobJourney.where(account_id: account.id).count

      post '/v1/users/job_journeys', params: params.to_json, headers: headers
      JobJourney.reindex(refresh: true)

      expect(JobJourney.where(account_id: account.id).count).to eq(initial_count + 1)

      expect(response).to have_http_status(:created)
      response_body = JSON.parse(response.body)
      expect(response_body['data']['attributes']['name']).to eq('Nova Etapa')
      expect(response_body['data']['attributes']['position']).to eq(16)
    end
  end

  describe 'PUT /v1/users/job_journeys/:id' do
    before do
      JobJourney.where(account_id: account.id).delete_all
    end

    let(:job_journey) { create(:job_journey, account: account, name: 'Old Name', position: 1) }

    it 'updates the job journey' do
      put "/v1/users/job_journeys/#{job_journey.id}", params: {
        job_journey: { name: 'Updated Name', position: 2 }
      }.to_json, headers: headers

      JobJourney.reindex(refresh: true)

      expect(response).to have_http_status(:ok)
      response_body = JSON.parse(response.body)
      expect(response_body['data']['attributes']['name']).to eq('Updated Name')
      expect(response_body['data']['attributes']['position']).to eq(2)
    end

    context 'when user does not own the job journey' do
      let(:other_account) { create(:account) }
      let(:other_journey) { create(:job_journey, account: other_account) }

      it 'returns forbidden' do
        put "/v1/users/job_journeys/#{other_journey.id}", params: {
          job_journey: { name: 'Hacked' }
        }.to_json, headers: headers

        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'DELETE /v1/users/job_journeys/:id' do
    before do
      JobJourney.where(account_id: account.id).delete_all
    end

    let(:job_journey) { create(:job_journey, account: account) }

    it 'destroys the job journey' do
      delete "/v1/users/job_journeys/#{job_journey.id}", headers: headers

      expect(response).to have_http_status(:no_content)
      expect(JobJourney.find_by(id: job_journey.id)).to be_nil
    end

    context 'when user does not own the job journey' do
      let(:other_account) { create(:account) }
      let(:other_journey) { create(:job_journey, account: other_account) }

      it 'returns forbidden' do
        delete "/v1/users/job_journeys/#{other_journey.id}", headers: headers

        expect(response).to have_http_status(:not_found)
      end
    end
  end
end
