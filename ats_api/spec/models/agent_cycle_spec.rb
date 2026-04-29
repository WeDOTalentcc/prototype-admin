# frozen_string_literal: true

require 'rails_helper'

RSpec.describe AgentCycle, type: :model do
  subject { build(:agent_cycle) }

  describe 'associations' do
    it { should belong_to(:background_agent) }
    it { should belong_to(:sourcing) }
    it { should have_many(:agent_feedbacks).dependent(:destroy) }
  end

  describe 'validations' do
    it { should validate_presence_of(:cycle_number) }
    it { should validate_inclusion_of(:status).in_array(AgentCycle::STATUSES) }
  end

  describe '#deliver!' do
    let(:cycle) { create(:agent_cycle) }

    it 'updates to delivered with stats' do
      cycle.deliver!(candidates_count: 15, total_found: 100)
      cycle.reload

      expect(cycle.status).to eq("delivered")
      expect(cycle.candidates_delivered).to eq(15)
      expect(cycle.candidates_total_found).to eq(100)
      expect(cycle.delivered_at).to be_present
      expect(cycle.expires_at).to be_present
    end
  end

  describe '#mark_reviewed!' do
    let(:cycle) { create(:agent_cycle, :delivered) }

    it 'updates to reviewed with timestamp' do
      cycle.mark_reviewed!
      expect(cycle.status).to eq("reviewed")
      expect(cycle.reviewed_at).to be_present
    end
  end

  describe '#expired?' do
    it 'returns false when no expires_at' do
      cycle = build(:agent_cycle, expires_at: nil)
      expect(cycle.expired?).to be false
    end

    it 'returns true when expired' do
      cycle = build(:agent_cycle, expires_at: 1.hour.ago)
      expect(cycle.expired?).to be true
    end

    it 'returns false when not yet expired' do
      cycle = build(:agent_cycle, expires_at: 1.hour.from_now)
      expect(cycle.expired?).to be false
    end
  end

  describe '#feedback_summary' do
    let(:cycle) { create(:agent_cycle) }
    let(:agent) { cycle.background_agent }

    it 'returns correct counts' do
      sps1 = create(:sourced_profile_sourcing, account: agent.account, user: agent.user)
      sps2 = create(:sourced_profile_sourcing, account: agent.account, user: agent.user)

      create(:agent_feedback, :approved, background_agent: agent, agent_cycle: cycle, sourced_profile_sourcing: sps1)
      create(:agent_feedback, :rejected, background_agent: agent, agent_cycle: cycle, sourced_profile_sourcing: sps2)

      summary = cycle.feedback_summary
      expect(summary[:approved]).to eq(1)
      expect(summary[:rejected]).to eq(1)
      expect(summary[:total]).to eq(2)
    end

    it 'returns zeros when no feedbacks' do
      summary = cycle.feedback_summary
      expect(summary[:approved]).to eq(0)
      expect(summary[:rejected]).to eq(0)
      expect(summary[:total]).to eq(0)
    end
  end

  describe 'factory' do
    it 'is valid' do
      expect(build(:agent_cycle)).to be_valid
    end
  end
end
