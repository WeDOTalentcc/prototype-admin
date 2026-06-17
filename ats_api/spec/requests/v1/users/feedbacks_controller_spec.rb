# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Feedbacks API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:auth) { auth_headers(user) }

  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token', 'Content-Type' => 'application/json' } }
  let(:no_auth_headers) { { 'Content-Type' => 'application/json' } }

  let!(:job) { create(:job, account: account) }
  let!(:selective_process) { create(:selective_process, account: account) }

  let(:valid_attributes) do
    {
      feedback: {
        title: 'Feedback técnico',
        description: 'Excelente domínio de Ruby.',
        name: 'Recrutador João',
        additional_text: 'Candidato se destacou na entrevista.',
        job_id: job.id,
        selective_process_id: selective_process.id
      }
    }
  end

  let(:invalid_attributes) do
    {
      feedback: {
        title: '',
        description: '',
        name: ''
      }
    }
  end

  describe 'GET /v1/users/feedbacks' do
    before do
      create_list(:feedback, 3, account: account, job: job, selective_process: selective_process, is_deleted: false)
      Feedback.reindex
    end

    it 'returns all feedbacks (not deleted)' do
      get '/v1/users/feedbacks', headers: auth
      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data'].size).to eq(3)
    end
  end

  describe 'GET /v1/users/feedbacks/:id' do
    let!(:feedback) { create(:feedback, account: account, job: job, selective_process: selective_process) }

    it 'returns the feedback' do
      get "/v1/users/feedbacks/#{feedback.id}", headers: auth
      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data']['attributes']['id']).to eq(feedback.id)
    end
  end

  describe 'POST /v1/users/feedbacks' do
    context 'with valid parameters' do
      it 'creates a new feedback' do
        expect {
          post '/v1/users/feedbacks', params: valid_attributes.to_json, headers: auth
        }.to change(Feedback, :count).by(1)

        expect(response).to have_http_status(:created)
      end
    end

    context 'with invalid parameters' do
      it 'returns unprocessable entity' do
        post '/v1/users/feedbacks', params: invalid_attributes.to_json, headers: auth
        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include("Title can't be blank")
      end
    end
  end

  describe 'PUT /v1/users/feedbacks/:id' do
    let!(:feedback) { create(:feedback, account: account, job: job, selective_process: selective_process) }
    let(:new_attributes) { { feedback: { title: 'Feedback atualizado' } } }

    it 'updates the feedback' do
      put "/v1/users/feedbacks/#{feedback.id}", params: new_attributes.to_json, headers: auth
      expect(response).to have_http_status(:ok)
      feedback.reload
      expect(feedback.title).to eq('Feedback atualizado')
    end
  end

  describe 'DELETE /v1/users/feedbacks/:id' do
    let!(:feedback) { create(:feedback, account: account, job: job, selective_process: selective_process) }

    it 'marks the feedback as deleted' do
      delete "/v1/users/feedbacks/#{feedback.id}", headers: auth
      expect(response).to have_http_status(:ok)
      feedback.reload
      expect(feedback.is_deleted).to be true
    end
  end
end
