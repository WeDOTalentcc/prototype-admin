# frozen_string_literal: true

require "rails_helper"

RSpec.describe TagReplacer::Sanitizer do
  describe ".allowed_method?" do
    it "returns true for whitelisted methods" do
      %i[name email phone title description].each do |method|
        expect(described_class.allowed_method?(method)).to be true
      end
    end

    it "returns true when passed as a string" do
      expect(described_class.allowed_method?("name")).to be true
    end

    it "returns false for dangerous methods" do
      %i[destroy delete update save].each do |method|
        expect(described_class.allowed_method?(method)).to be false
      end
    end

    it "returns false for arbitrary unknown methods" do
      expect(described_class.allowed_method?(:system)).to be false
      expect(described_class.allowed_method?(:eval)).to be false
    end
  end

  describe ".allowed_entity?" do
    it "returns true for whitelisted entities" do
      %i[candidate recruiter job user client_contact client_company].each do |entity|
        expect(described_class.allowed_entity?(entity)).to be true
      end
    end

    it "returns true when passed as a string" do
      expect(described_class.allowed_entity?("candidate")).to be true
    end

    it "returns false for unknown entities" do
      expect(described_class.allowed_entity?(:admin)).to be false
      expect(described_class.allowed_entity?(:internal)).to be false
    end
  end
end
