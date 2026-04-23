# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::BackgroundAgents API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:other_user) { create(:user) }
  let(:job) { create(:job, user: user, account: account) }

  let(:authentication_headers) { auth_headers(user) }
  let(:no_authentication_headers) { {} }

  describe 'GET /v1/users/background_agents' do
    let!(:agents) { create_list(:background_agent, 3, user: user, account: account, job: job) }
    let!(:other_agent) { create(:background_agent, user: other_user, account: other_user.account) }
    let!(:deleted_agent) { create(:background_agent, :deleted, user: user, account: account, job: job) }

    context 'when authenticated' do
      it 'returns only current account agents' do
        get '/v1/users/background_agents', headers: authentication_headers
        expect(response).to have_http_status(:ok)
        expect(json['data'].size).to eq(3)
      end

      it 'excludes deleted agents' do
        get '/v1/users/background_agents', headers: authentication_headers
        ids = json['data'].map { |d| d['id'].to_i }
        expect(ids).not_to include(deleted_agent.id)
      end

      it 'filters by status' do
        agents.first.update!(status: "paused", paused_at: Time.current)
        get '/v1/users/background_agents', params: { status: "paused" }, headers: authentication_headers
        expect(json['data'].size).to eq(1)
      end

      it 'filters by job_id' do
        other_job = create(:job, user: user, account: account)
        create(:background_agent, user: user, account: account, job: other_job)
        get '/v1/users/background_agents', params: { job_id: job.id }, headers: authentication_headers
        json['data'].each do |d|
          expect(d['relationships']['job']['data']['id'].to_i).to eq(job.id)
        end
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/background_agents', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/background_agents/:id' do
    let!(:agent) { create(:background_agent, user: user, account: account, job: job) }

    it 'returns the agent' do
      get "/v1/users/background_agents/#{agent.id}", headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(json['data']['id'].to_i).to eq(agent.id)
    end

    it 'returns not found for other accounts agent' do
      other_agent = create(:background_agent, user: other_user, account: other_user.account)
      get "/v1/users/background_agents/#{other_agent.id}", headers: authentication_headers
      expect(response).to have_http_status(:not_found)
    end

    it 'returns not found for deleted agent' do
      agent.update!(is_deleted: true)
      get "/v1/users/background_agents/#{agent.id}", headers: authentication_headers
      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /v1/users/background_agents' do
    let(:valid_attributes) do
      {
        background_agent: {
          name: "Senior Ruby Dev Sourcing",
          job_id: job.id,
          criteria_text: "Senior Ruby developer in SP",
          mode: "review",
          daily_limit: 20,
          sources: ["local"]
        }
      }
    end

    context 'with valid attributes' do
      before do
        allow(BackgroundAgents::SetupJob).to receive(:perform_async)
      end

      it 'creates a new agent' do
        expect {
          post '/v1/users/background_agents', params: valid_attributes.to_json, headers: authentication_headers
        }.to change(BackgroundAgent, :count).by(1)

        expect(response).to have_http_status(:created)
      end

      it 'assigns current user and account' do
        post '/v1/users/background_agents', params: valid_attributes.to_json, headers: authentication_headers
        created = BackgroundAgent.last
        expect(created.user_id).to eq(user.id)
        expect(created.account_id).to eq(account.id)
      end

      it 'enqueues setup job' do
        post '/v1/users/background_agents', params: valid_attributes.to_json, headers: authentication_headers
        expect(BackgroundAgents::SetupJob).to have_received(:perform_async)
      end
    end

    context 'with invalid attributes' do
      it 'returns unprocessable entity for missing name' do
        post '/v1/users/background_agents',
             params: { background_agent: { job_id: job.id } }.to_json,
             headers: authentication_headers
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe 'PATCH /v1/users/background_agents/:id' do
    let!(:agent) { create(:background_agent, user: user, account: account, job: job) }

    it 'updates the agent' do
      patch "/v1/users/background_agents/#{agent.id}",
            params: { background_agent: { name: "Updated Name" } }.to_json,
            headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(agent.reload.name).to eq("Updated Name")
    end

    it 'rejects open hash params like criteria_structured' do
      patch "/v1/users/background_agents/#{agent.id}",
            params: { background_agent: { criteria_structured: { skills: ["ruby"] } } }.to_json,
            headers: authentication_headers
      expect(agent.reload.criteria_structured).to eq({})
    end
  end

  describe 'DELETE /v1/users/background_agents/:id' do
    let!(:agent) { create(:background_agent, user: user, account: account, job: job) }

    it 'soft deletes the agent' do
      delete "/v1/users/background_agents/#{agent.id}", headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(agent.reload.is_deleted).to be true
      expect(agent.status).to eq("stopped")
    end

    it 'cancels running cycles' do
      sourcing = create(:sourcing, user: user, account: account)
      cycle = create(:agent_cycle, background_agent: agent, sourcing: sourcing, status: "running")
      delete "/v1/users/background_agents/#{agent.id}", headers: authentication_headers
      expect(cycle.reload.status).to eq("cancelled")
    end
  end

  describe 'POST /v1/users/background_agents/:id/pause' do
    let!(:agent) { create(:background_agent, user: user, account: account, job: job) }

    it 'pauses the agent' do
      post "/v1/users/background_agents/#{agent.id}/pause", headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(agent.reload.status).to eq("paused")
    end
  end

  describe 'POST /v1/users/background_agents/:id/resume' do
    let!(:agent) { create(:background_agent, :paused, user: user, account: account, job: job) }

    it 'resumes the agent' do
      post "/v1/users/background_agents/#{agent.id}/resume", headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(agent.reload.status).to eq("active")
    end
  end

  describe 'POST /v1/users/background_agents/:id/stop' do
    let!(:agent) { create(:background_agent, user: user, account: account, job: job) }

    it 'stops the agent' do
      post "/v1/users/background_agents/#{agent.id}/stop", headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(agent.reload.status).to eq("stopped")
    end
  end
end
