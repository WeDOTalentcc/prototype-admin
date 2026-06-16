# frozen_string_literal: true

require 'rails_helper'

RSpec.describe AgentFeedback, type: :model do
  subject { build(:agent_feedback) }

  describe 'associations' do
    it { should belong_to(:background_agent) }
    it { should belong_to(:agent_cycle) }
    it { should belong_to(:sourced_profile_sourcing) }
  end

  describe 'validations' do
    it { should validate_presence_of(:action) }
    it { should validate_inclusion_of(:action).in_array(AgentFeedback::ACTIONS) }
  end

  describe 'scopes' do
    let(:agent) { create(:background_agent) }
    let(:cycle) { create(:agent_cycle, background_agent: agent) }

    let!(:approved_feedback) do
      create(:agent_feedback, :approved, background_agent: agent, agent_cycle: cycle)
    end

    let!(:rejected_feedback) do
      create(:agent_feedback, :rejected, background_agent: agent, agent_cycle: cycle)
    end

    it '.approved returns only approved' do
      expect(AgentFeedback.approved).to contain_exactly(approved_feedback)
    end

    it '.rejected returns only rejected' do
      expect(AgentFeedback.rejected).to contain_exactly(rejected_feedback)
    end
  end

  describe 'uniqueness' do
    let(:agent) { create(:background_agent) }
    let(:cycle) { create(:agent_cycle, background_agent: agent) }
    let(:sps) { create(:sourced_profile_sourcing) }

    it 'prevents duplicate feedback per agent + sourced_profile_sourcing' do
      create(:agent_feedback, background_agent: agent, agent_cycle: cycle, sourced_profile_sourcing: sps)
      duplicate = build(:agent_feedback, background_agent: agent, agent_cycle: cycle, sourced_profile_sourcing: sps)
      expect(duplicate).not_to be_valid
    end
  end

  describe 'factory' do
    it 'is valid' do
      expect(build(:agent_feedback)).to be_valid
    end
  end
end
