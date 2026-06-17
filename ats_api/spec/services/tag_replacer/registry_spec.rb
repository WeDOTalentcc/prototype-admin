# frozen_string_literal: true

require 'rails_helper'

RSpec.describe TagReplacer::Registry do
  describe ".tags_in" do
    it "returns only tags present in message" do
      message = "Hello {{candidate_name}} and {{candidate_email}}"
      tags = described_class.tags_in(message)

      expect(tags.size).to eq(2)
      expect(tags.map(&:tag)).to include("{{candidate_name}}", "{{candidate_email}}")
    end

    it "returns empty array for message without tags" do
      tags = described_class.tags_in("No tags here")
      expect(tags).to be_empty
    end

    it "returns empty array for blank message" do
      expect(described_class.tags_in("")).to be_empty
      expect(described_class.tags_in(nil)).to be_empty
    end
  end

  describe ".available_tags" do
    it "returns all tags when no filter" do
      tags = described_class.available_tags
      expect(tags).not_to be_empty
      expect(tags.first).to have_key(:tag)
      expect(tags.first).to have_key(:entity)
      expect(tags.first).to have_key(:description)
    end

    it "filters tags by entity" do
      tags = described_class.available_tags(entities: [ :candidate ])
      expect(tags.map { |t| t[:entity] }.uniq).to eq([ :candidate ])
    end
  end
end
