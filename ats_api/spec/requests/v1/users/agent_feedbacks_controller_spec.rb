# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::AgentFeedbacks API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:job) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, user: user, account: account, job: job) }
  let(:sourcing) { create(:sourcing, user: user, account: account) }
  let(:cycle) { create(:agent_cycle, background_agent: agent, sourcing: sourcing, status: "running") }
  let(:sps) { create(:sourced_profile_sourcing, account: account, user: user) }

  let(:authentication_headers) { auth_headers(user) }

  before do
    allow(BackgroundAgents::ExtractPreferencesJob).to receive(:perform_async)
  end

  describe 'POST /v1/users/background_agents/:background_agent_id/feedbacks' do
    let(:valid_params) do
      {
        feedback: {
          sourced_profile_sourcing_id: sps.id,
          agent_cycle_id: cycle.id,
          action: "approved"
        }
      }
    end

    it 'creates feedback' do
      expect {
        post "/v1/users/background_agents/#{agent.id}/feedbacks",
             params: valid_params.to_json,
             headers: authentication_headers
      }.to change(AgentFeedback, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json['processed']).to eq(1)
    end

    it 'returns not found for other accounts agent' do
      other_agent = create(:background_agent)
      post "/v1/users/background_agents/#{other_agent.id}/feedbacks",
           params: valid_params.to_json,
           headers: authentication_headers
      expect(response).to have_http_status(:not_found)
    end

    it 'accepts agent_candidate_id alias for sourced_profile_sourcing_id' do
      params = {
        feedback: {
          agent_candidate_id: sps.id,
          agent_cycle_id: cycle.id,
          action: "approved"
        }
      }

      expect {
        post "/v1/users/background_agents/#{agent.id}/feedbacks",
             params: params.to_json,
             headers: authentication_headers
      }.to change(AgentFeedback, :count).by(1)

      expect(response).to have_http_status(:created)
    end

    it 'accepts status alias for action' do
      params = {
        feedback: {
          sourced_profile_sourcing_id: sps.id,
          agent_cycle_id: cycle.id,
          status: "rejected"
        }
      }

      post "/v1/users/background_agents/#{agent.id}/feedbacks",
           params: params.to_json,
           headers: authentication_headers

      expect(response).to have_http_status(:created)
      expect(AgentFeedback.last.action).to eq("rejected")
    end

    it 'returns 422 when feedback param is missing' do
      post "/v1/users/background_agents/#{agent.id}/feedbacks",
           params: {}.to_json,
           headers: authentication_headers
      expect(response).to have_http_status(:bad_request)
    end

    it 'returns 401 without authentication' do
      post "/v1/users/background_agents/#{agent.id}/feedbacks",
           params: valid_params.to_json,
           headers: no_auth_headers
      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'POST /v1/users/background_agents/:background_agent_id/feedbacks/bulk' do
    let(:sps2) { create(:sourced_profile_sourcing, account: account, user: user) }

    let(:valid_params) do
      {
        feedbacks: [
          { sourced_profile_sourcing_id: sps.id, agent_cycle_id: cycle.id, action: "approved" },
          { sourced_profile_sourcing_id: sps2.id, agent_cycle_id: cycle.id, action: "rejected", reason: "Not enough experience" }
        ]
      }
    end

    it 'creates multiple feedbacks' do
      expect {
        post "/v1/users/background_agents/#{agent.id}/feedbacks/bulk",
             params: valid_params.to_json,
             headers: authentication_headers
      }.to change(AgentFeedback, :count).by(2)

      expect(response).to have_http_status(:created)
      expect(json['processed']).to eq(2)
    end

    it 'rejects bulk over limit' do
      feedbacks = 101.times.map do |i|
        { sourced_profile_sourcing_id: i, agent_cycle_id: cycle.id, action: "approved" }
      end

      post "/v1/users/background_agents/#{agent.id}/feedbacks/bulk",
           params: { feedbacks: feedbacks }.to_json,
           headers: authentication_headers
      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
