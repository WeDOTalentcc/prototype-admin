# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::OceanTraitCanonical do
  describe ".to_api" do
    it "maps neuroticism to stability" do
      expect(described_class.to_api("neuroticism")).to eq("stability")
    end

    it "keeps stability as stability" do
      expect(described_class.to_api("stability")).to eq("stability")
    end

    it "passes through other traits" do
      expect(described_class.to_api("openness")).to eq("openness")
    end

    it "returns nil for blank" do
      expect(described_class.to_api(nil)).to be_nil
      expect(described_class.to_api("")).to be_nil
    end

    it "returns unknown values unchanged" do
      expect(described_class.to_api("custom_trait")).to eq("custom_trait")
    end
  end

  describe ".to_storage" do
    it "maps stability to neuroticism" do
      expect(described_class.to_storage("stability")).to eq("neuroticism")
    end

    it "keeps neuroticism as neuroticism" do
      expect(described_class.to_storage("neuroticism")).to eq("neuroticism")
    end

    it "round-trips with to_api" do
      api = described_class.to_api("neuroticism")
      expect(described_class.to_storage(api)).to eq("neuroticism")
    end

    it "returns nil for blank" do
      expect(described_class.to_storage(nil)).to be_nil
    end
  end
end
