# frozen_string_literal: true

require "rails_helper"

RSpec.describe LiaEvents::EventRegistry do
  describe "EVENT_VERSIONS" do
    it "registers all 6 LIA event types in sync with Python repo" do
      expected_events = %w[
        screening.completed
        interview.scheduled
        interview.completed
        offer.sent
        candidate.enriched
        pipeline.moved
      ]
      expect(described_class::EVENT_VERSIONS.keys).to match_array(expected_events)
    end

    it "is frozen to prevent runtime mutation" do
      expect(described_class::EVENT_VERSIONS).to be_frozen
    end
  end

  describe ".validate_version" do
    context "with same major version" do
      it "accepts 1.0" do
        expect(described_class.validate_version("screening.completed", "1.0")).to be true
      end

      it "accepts 1.1 (forward-compatible minor)" do
        expect(described_class.validate_version("screening.completed", "1.1")).to be true
      end

      it "accepts 1.99" do
        expect(described_class.validate_version("screening.completed", "1.99")).to be true
      end
    end

    context "with different major version" do
      it "rejects 2.0" do
        expect(described_class.validate_version("screening.completed", "2.0")).to be false
      end

      it "rejects 0.9" do
        expect(described_class.validate_version("screening.completed", "0.9")).to be false
      end
    end

    context "with unknown event type" do
      it "rejects" do
        expect(described_class.validate_version("unknown.event", "1.0")).to be false
      end
    end

    context "with nil/empty inputs" do
      it "rejects nil event_type" do
        expect(described_class.validate_version(nil, "1.0")).to be false
      end

      it "rejects nil version" do
        expect(described_class.validate_version("screening.completed", nil)).to be false
      end

      it "rejects empty version" do
        expect(described_class.validate_version("screening.completed", "")).to be false
      end
    end
  end

  describe ".current_version" do
    it "returns version for known events" do
      expect(described_class.current_version("screening.completed")).to eq("1.0")
    end

    it "returns nil for unknown events" do
      expect(described_class.current_version("unknown.event")).to be_nil
    end
  end

  describe ".known_event?" do
    it "returns true for known events" do
      expect(described_class.known_event?("screening.completed")).to be true
    end

    it "returns false for unknown events" do
      expect(described_class.known_event?("unknown.event")).to be false
    end
  end
end
