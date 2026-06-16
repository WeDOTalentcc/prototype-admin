# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Services::BackgroundAgents API', type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, user: user, account: account, job: job) }

  let(:service_headers) do
    token = JsonWebToken.encode(role: "service", account_id: account.id, user_id: user.id)
    { 'Authorization' => "Bearer #{token}", 'Content-Type' => 'application/json' }
  end

  let(:user_headers) { auth_headers(user) }

  describe 'authentication' do
    it 'rejects non-service tokens' do
      get '/v1/services/background_agents/runnable', headers: user_headers
      expect(response).to have_http_status(:forbidden)
    end
  end

  describe 'GET /v1/services/background_agents/runnable' do
    let!(:runnable_agent) { create(:background_agent, user: user, account: account, job: job) }
    let!(:paused_agent) { create(:background_agent, :paused, user: user, account: account, job: job) }

    it 'returns only runnable agents' do
      get '/v1/services/background_agents/runnable', headers: service_headers
      expect(response).to have_http_status(:ok)
      ids = json.map { |a| a['id'] }
      expect(ids).to include(runnable_agent.id)
      expect(ids).not_to include(paused_agent.id)
    end
  end

  describe 'POST /v1/services/background_agents/:id/deliver_cycle' do
    let(:sourcing) { create(:sourcing, user: user, account: account) }
    let!(:cycle) { create(:agent_cycle, background_agent: agent, sourcing: sourcing, status: "running") }

    before do
      allow(BackgroundAgentChannel).to receive(:broadcast_to)
    end

    it 'delivers cycle with valid values' do
      post "/v1/services/background_agents/#{agent.id}/deliver_cycle",
           params: { cycle_id: cycle.id, candidates_count: 15, total_found: 100 }.to_json,
           headers: service_headers

      expect(response).to have_http_status(:ok)
      expect(json['success']).to be true
      expect(cycle.reload.status).to eq("delivered")
      expect(cycle.candidates_delivered).to eq(15)
    end

    it 'rejects negative values' do
      post "/v1/services/background_agents/#{agent.id}/deliver_cycle",
           params: { cycle_id: cycle.id, candidates_count: -1, total_found: 100 }.to_json,
           headers: service_headers

      expect(response).to have_http_status(:unprocessable_entity)
    end

    it 'returns not found for missing cycle' do
      post "/v1/services/background_agents/#{agent.id}/deliver_cycle",
           params: { cycle_id: 999999, candidates_count: 5, total_found: 10 }.to_json,
           headers: service_headers

      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'PATCH /v1/services/background_agents/:id/update_status' do
    it 'updates with valid status' do
      patch "/v1/services/background_agents/#{agent.id}/update_status",
            params: { status: "paused" }.to_json,
            headers: service_headers

      expect(response).to have_http_status(:ok)
      expect(agent.reload.status).to eq("paused")
    end

    it 'rejects invalid status' do
      patch "/v1/services/background_agents/#{agent.id}/update_status",
            params: { status: "hacked" }.to_json,
            headers: service_headers

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end

  describe 'PATCH /v1/services/background_agents/:id/update_preferences' do
    it 'updates preferences' do
      patch "/v1/services/background_agents/#{agent.id}/update_preferences",
            params: { preferences: { skill_weights: { ruby: 0.9 } } }.to_json,
            headers: service_headers

      expect(response).to have_http_status(:ok)
      expect(agent.reload.extracted_preferences).to have_key("skill_weights")
    end

    it 'rejects empty preferences' do
      patch "/v1/services/background_agents/#{agent.id}/update_preferences",
            params: { preferences: nil }.to_json,
            headers: service_headers

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end

  describe 'POST /v1/services/background_agents/:id/log_search_iteration' do
    it 'logs iteration' do
      post "/v1/services/background_agents/#{agent.id}/log_search_iteration",
           params: { iteration_number: 1, query_used: "ruby senior sp", results_count: 50, selected_count: 10, strategy: "diversity" }.to_json,
           headers: service_headers

      expect(response).to have_http_status(:ok)
      expect(json['history_size']).to eq(1)
    end
  end
end
