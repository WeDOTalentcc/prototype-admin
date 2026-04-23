require 'rails_helper'

RSpec.describe Candidates::Search::SimpleQueryDetector do
  describe '.detect' do
    it 'returns :simple for blank or wildcard' do
      expect(described_class.detect("")).to eq(:simple)
      expect(described_class.detect(nil)).to eq(:simple)
      expect(described_class.detect("*")).to eq(:simple)
      expect(described_class.detect("  *  ")).to eq(:simple)
    end

    it 'returns :simple for short keyword-like queries' do
      expect(described_class.detect("react")).to eq(:simple)
      expect(described_class.detect("desenvolvedor react senior")).to eq(:simple)
      expect(described_class.detect("dev frontend vue.js")).to eq(:simple)
    end

    it 'returns :complex for queries with experience/connectors' do
      expect(described_class.detect("desenvolvedor com 5 anos de experiencia em react")).to eq(:complex)
      expect(described_class.detect("preciso de alguem que saiba react e node.js")).to eq(:complex)
      expect(described_class.detect("fullstack sem experiencia com java")).to eq(:complex)
    end

    it 'returns :resume for long text with resume indicators' do
      long_with_indicators = ("a " * 300) + "experiencia profissional formacao academica 2018-2022"
      expect(described_class.detect(long_with_indicators)).to eq(:resume)
    end
  end

  describe '.simple?' do
    it 'is true for simple queries' do
      expect(described_class.simple?("react")).to be true
      expect(described_class.simple?("dev senior")).to be true
    end

    it 'is false for complex or resume' do
      expect(described_class.simple?("5 anos de experiencia")).to be false
    end
  end

  describe '.complex?' do
    it 'is true for complex queries' do
      expect(described_class.complex?("react e node")).to be true
    end

    it 'is false for simple queries' do
      expect(described_class.complex?("react")).to be false
    end
  end

  describe '.resume?' do
    it 'is false for short queries' do
      expect(described_class.resume?("react")).to be false
    end

    it 'is true for very long text with multiple resume indicators' do
      text = " " * 600 + "Experiencia profissional. Formacao academica. 2018-2022."
      expect(described_class.resume?(text)).to be true
    end
  end
end
