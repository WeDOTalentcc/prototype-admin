require 'rails_helper'

RSpec.describe Candidates::Search::EmbeddingService do
  subject(:service) { described_class.new }

  let(:text) { "ruby developer senior" }
  let(:embedding) { Array.new(768) { rand(0.0..1.0) } }
  let(:cache_key) { "embedding:#{Digest::SHA256.hexdigest(text)}" }

  describe '#generate' do
    it 'returns nil when text is blank' do
      expect(service.generate(nil)).to be_nil
      expect(service.generate("")).to be_nil
      expect(service.generate("  ")).to be_nil
    end

    it 'checks cache before calling API' do
      expect(Rails.cache).to receive(:fetch)
        .with(cache_key, expires_in: 1.hour)
        .and_return(embedding)

      result = service.generate(text)

      expect(result).to eq(embedding)
    end

    it 'returns nil on error and logs' do
      allow(Rails.cache).to receive(:fetch).and_raise(StandardError.new("Connection failed"))
      allow(Rails.logger).to receive(:error)

      result = service.generate(text)

      expect(result).to be_nil
      expect(Rails.logger).to have_received(:error).with(/Error generating embedding/)
    end

    it 'normalizes text before hashing' do
      text_with_spaces = "  ruby developer senior  "
      expected_key = "embedding:#{Digest::SHA256.hexdigest(text)}"

      expect(Rails.cache).to receive(:fetch).with(expected_key, expires_in: 1.hour)

      service.generate(text_with_spaces)
    end
  end
end
