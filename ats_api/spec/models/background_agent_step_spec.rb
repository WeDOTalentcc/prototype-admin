# frozen_string_literal: true

require 'rails_helper'

RSpec.describe BackgroundAgentStep, type: :model do
  describe "associations" do
    it { is_expected.to belong_to(:background_agent) }
    it { is_expected.to belong_to(:agent_cycle).optional }
  end

  describe "validations" do
    it { is_expected.to validate_presence_of(:step) }
    it { is_expected.to validate_inclusion_of(:step).in_array(BackgroundAgentStep::STEPS) }
    it { is_expected.to validate_inclusion_of(:status).in_array(BackgroundAgentStep::STATUSES) }
  end

  describe "constants" do
    it "defines all expected STEPS" do
      expected = %w[plan load_context generate_queries search deduplicate evaluate reformulate paginate score select_batch search_similar search_pearch search_linkedin search_semantic deliver completed error]
      expect(BackgroundAgentStep::STEPS).to eq(expected)
    end

    it "defines all expected STATUSES" do
      expect(BackgroundAgentStep::STATUSES).to eq(%w[running done error])
    end
  end

  describe "scopes" do
    let(:agent) { create(:background_agent) }
    let(:cycle) { create(:agent_cycle, background_agent: agent) }
    let(:other_cycle) { create(:agent_cycle, background_agent: agent) }

    let!(:step_a) { create(:background_agent_step, background_agent: agent, agent_cycle: cycle, step: "plan", created_at: 2.minutes.ago) }
    let!(:step_b) { create(:background_agent_step, background_agent: agent, agent_cycle: cycle, step: "search", created_at: 1.minute.ago) }
    let!(:step_c) { create(:background_agent_step, background_agent: agent, agent_cycle: other_cycle, step: "deliver") }

    describe ".by_cycle" do
      it "returns steps for the given cycle" do
        expect(described_class.by_cycle(cycle.id)).to contain_exactly(step_a, step_b)
      end
    end

    describe ".recent" do
      it "orders by created_at desc" do
        expect(described_class.recent.where(agent_cycle: cycle).to_a).to eq([step_b, step_a])
      end
    end

    describe ".chronological" do
      it "orders by created_at asc" do
        expect(described_class.chronological.where(agent_cycle: cycle).to_a).to eq([step_a, step_b])
      end
    end
  end

  describe "factory" do
    it "creates a valid record" do
      step = build(:background_agent_step)
      expect(step).to be_valid
    end

    it "creates an error step" do
      step = build(:background_agent_step, :error)
      expect(step.status).to eq("error")
    end
  end
end
