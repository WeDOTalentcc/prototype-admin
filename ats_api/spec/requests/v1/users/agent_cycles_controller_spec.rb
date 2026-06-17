# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::AgentCycles API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:job) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, user: user, account: account, job: job) }

  let(:authentication_headers) { auth_headers(user) }

  describe 'GET /v1/users/background_agents/:background_agent_id/cycles' do
    let!(:cycles) do
      3.times.map do |i|
        sourcing = create(:sourcing, user: user, account: account)
        create(:agent_cycle, background_agent: agent, sourcing: sourcing, cycle_number: i + 1)
      end
    end

    it 'returns cycles ordered by cycle_number desc' do
      get "/v1/users/background_agents/#{agent.id}/cycles", headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(json['data'].size).to eq(3)
      numbers = json['data'].map { |d| d['attributes']['cycle_number'] }
      expect(numbers).to eq(numbers.sort.reverse)
    end

    it 'returns not found for other accounts agent' do
      other_agent = create(:background_agent)
      get "/v1/users/background_agents/#{other_agent.id}/cycles", headers: authentication_headers
      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'GET /v1/users/background_agents/:background_agent_id/cycles/:id' do
    let(:sourcing) { create(:sourcing, user: user, account: account) }
    let!(:cycle) { create(:agent_cycle, background_agent: agent, sourcing: sourcing) }

    it 'returns the cycle' do
      get "/v1/users/background_agents/#{agent.id}/cycles/#{cycle.id}", headers: authentication_headers
      expect(response).to have_http_status(:ok)
      expect(json['data']['id'].to_i).to eq(cycle.id)
    end

    it 'returns not found for nonexistent cycle' do
      get "/v1/users/background_agents/#{agent.id}/cycles/999999", headers: authentication_headers
      expect(response).to have_http_status(:not_found)
    end
  end
end
