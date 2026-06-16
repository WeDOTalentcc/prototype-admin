# frozen_string_literal: true

require "rails_helper"

RSpec.describe PhoneNormalizable do
  let(:test_class) { Class.new { include PhoneNormalizable } }
  let(:normalizer) { test_class.new }

  describe "#normalize_phone" do
    context "with blank input" do
      it "returns nil for nil" do
        expect(normalizer.normalize_phone(nil)).to be_nil
      end

      it "returns nil for empty string" do
        expect(normalizer.normalize_phone("")).to be_nil
      end
    end

    context "with Brazilian numbers" do
      it "keeps 11-digit numbers that match US country code 1" do
        expect(normalizer.normalize_phone("11987654321")).to eq("11987654321")
      end

      it "prepends 55 for 10-digit landline numbers" do
        expect(normalizer.normalize_phone("1133334444")).to eq("551133334444")
      end

      it "keeps already-prefixed Brazilian numbers unchanged" do
        expect(normalizer.normalize_phone("5511987654321")).to eq("5511987654321")
      end

      it "strips non-digit characters" do
        expect(normalizer.normalize_phone("+55 (11) 98765-4321")).to eq("5511987654321")
      end
    end

    context "with US numbers (country code 1)" do
      it "recognizes US numbers with country code" do
        expect(normalizer.normalize_phone("12025551234")).to eq("12025551234")
      end

      it "strips formatting" do
        expect(normalizer.normalize_phone("+1 (202) 555-1234")).to eq("12025551234")
      end
    end

    context "with Portuguese numbers (country code 351)" do
      it "recognizes Portuguese numbers with country code" do
        expect(normalizer.normalize_phone("351912345678")).to eq("351912345678")
      end
    end

    context "with UK numbers (country code 44)" do
      it "recognizes UK numbers with country code" do
        expect(normalizer.normalize_phone("442071234567")).to eq("442071234567")
      end
    end

    context "with Argentine numbers (country code 54)" do
      it "recognizes Argentine numbers with country code" do
        expect(normalizer.normalize_phone("5491112345678")).to eq("5491112345678")
      end
    end

    context "with numbers that do not match any pattern" do
      it "returns nil for too-short numbers" do
        expect(normalizer.normalize_phone("12345")).to be_nil
      end
    end
  end

  describe ".normalize_phone (module function)" do
    it "can be called directly on the module" do
      expect(PhoneNormalizable.normalize_phone("5511987654321")).to eq("5511987654321")
    end

    it "normalizes unrecognized 10-digit numbers as Brazilian" do
      expect(PhoneNormalizable.normalize_phone("1133334444")).to eq("551133334444")
    end
  end

  describe ".valid_country_code?" do
    it "returns true for valid country code with correct national length" do
      expect(PhoneNormalizable.valid_country_code?("5511987654321")).to be true
    end

    it "returns false for digits without valid country code" do
      expect(PhoneNormalizable.valid_country_code?("987654321")).to be false
    end

    it "handles 3-digit country codes" do
      expect(PhoneNormalizable.valid_country_code?("351912345678")).to be true
    end
  end
end
