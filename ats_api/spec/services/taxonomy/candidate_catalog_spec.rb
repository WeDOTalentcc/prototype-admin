# frozen_string_literal: true

require "rails_helper"

RSpec.describe Taxonomy::CandidateCatalog do
  describe ".version" do
    it "returns version from YAML" do
      expect(described_class.version).to match(/\A\d{4}\.\d{2}\.\d+\z/)
    end
  end

  describe ".hints_for" do
    it "returns default taxonomy categories" do
      h = described_class.hints_for(q: "", categories: [])
      expect(h[:job_titles]).to be_an(Array)
      expect(h[:skills]).to be_an(Array)
      expect(h[:certifications]).to be_an(Array)
      expect(h[:industries]).to be_an(Array)
      expect(h[:job_titles].first).to include("text", "group")
    end

    it "filters by q" do
      h = described_class.hints_for(q: "python", categories: %w[job_titles skills])
      texts = (h[:job_titles] + h[:skills]).map { |x| x["text"].downcase }
      expect(texts.any? { |t| t.include?("python") }).to be true
    end

    it "respects categories list" do
      h = described_class.hints_for(q: "", categories: %w[job_titles])
      expect(h).to have_key(:job_titles)
      expect(h).not_to have_key(:skills)
      expect(h).not_to have_key(:certifications)
    end
  end
end
