# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgents::BuildSearchContextService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:agent) { create(:background_agent, :calibrated, user: user, account: account, job: job) }

  describe '#call' do
    subject { described_class.new(background_agent: agent).call }

    it 'returns agent context' do
      expect(subject[:agent][:id]).to eq(agent.id)
      expect(subject[:agent][:criteria_text]).to eq(agent.criteria_text)
      expect(subject[:agent][:calibration_state]).to eq("calibrated")
    end

    it 'returns job context' do
      expect(subject[:job][:id]).to eq(job.id)
      expect(subject[:job][:title]).to eq(job.title)
    end

    it 'returns feedback history' do
      expect(subject[:feedback_history]).to have_key(:recent)
      expect(subject[:feedback_history]).to have_key(:summary)
    end

    it 'returns search history limited to 10' do
      agent.update!(search_history: Array.new(20) { { q: "test" } })
      expect(subject[:search_history].size).to eq(10)
    end
  end
end
