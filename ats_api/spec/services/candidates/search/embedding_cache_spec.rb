# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::EmbeddingCache do
  subject(:cache_service) { described_class.new(embedding_service: embedding_service) }

  let(:embedding_service) { instance_double(Candidates::Search::EmbeddingService) }
  let(:query_text) { "ruby developer with 5 years experience" }
  let(:account) { create(:account) }
  let(:account_id) { account.id }
  let(:embedding) { Array.new(768) { rand } }

  before do
    allow(Candidates::Search::Configuration).to receive(:embedding_model_version).and_return('v1')
  end

  describe '#fetch' do
    context 'when embedding is in cache' do
      it 'returns embedding from cache without calling API' do
        # Stub to not call API even if not in cache
        allow(embedding_service).to receive(:generate).and_return(embedding)

        # First call creates cache
        cache_service.fetch(query_text, account_id: account_id)

        # Second call should use cache (service should only be called once)
        cache_service.fetch(query_text, account_id: account_id)

        expect(embedding_service).to have_received(:generate).once
      end

      it 'increments record hit_count' do
        allow(embedding_service).to receive(:generate).and_return(embedding)

        # Create cache
        cache_service.fetch(query_text, account_id: account_id)
        record = ::EmbeddingCache.last
        initial_count = record.hit_count

        # Access again
        cache_service.fetch(query_text, account_id: account_id)

        expect(record.reload.hit_count).to eq(initial_count + 1)
      end

      it 'updates last_accessed_at' do
        allow(embedding_service).to receive(:generate).and_return(embedding)

        cache_service.fetch(query_text, account_id: account_id)
        record = ::EmbeddingCache.last

        sleep 0.1 # Ensures time difference
        cache_service.fetch(query_text, account_id: account_id)

        expect(record.reload.last_accessed_at).to be > 1.second.ago
      end
    end

    context 'when embedding is NOT in cache' do
      it 'generates new embedding via service' do
        allow(embedding_service).to receive(:generate).with(query_text).and_return(embedding)

        cache_service.fetch(query_text, account_id: account_id)

        expect(embedding_service).to have_received(:generate).with(query_text)
      end

      it 'saves embedding to database' do
        allow(embedding_service).to receive(:generate).and_return(embedding)

        expect {
          cache_service.fetch(query_text, account_id: account_id)
        }.to change { ::EmbeddingCache.count }.by(1)
      end

      it 'normalizes query_text before saving' do
        allow(embedding_service).to receive(:generate).and_return(embedding)

        cache_service.fetch("  RUBY   Developer  ", account_id: account_id)

        record = ::EmbeddingCache.last
        expect(record.query_text).to eq("ruby developer")
      end

      it 'returns the generated embedding' do
        allow(embedding_service).to receive(:generate).and_return(embedding)

        result = cache_service.fetch(query_text, account_id: account_id)

        expect(result).to eq(embedding)
      end
    end
  end

  describe '#invalidate' do
    it 'deletes cache record' do
      allow(embedding_service).to receive(:generate).and_return(embedding)

      # Create cache first
      cache_service.fetch(query_text, account_id: account_id)

      expect {
        cache_service.invalidate(query_text, account_id: account_id)
      }.to change { ::EmbeddingCache.count }.by(-1)
    end

    it 'does not fail when record does not exist' do
      expect {
        cache_service.invalidate("nonexistent", account_id: 999)
      }.not_to raise_error
    end
  end

  describe '.invalidate_all!' do
    it 'deletes all records' do
      create_list(:embedding_cache, 3)

      expect {
        described_class.invalidate_all!
      }.to change { ::EmbeddingCache.count }.to(0)
    end

    it 'logs cleanup action' do
      allow(Rails.logger).to receive(:info)

      described_class.invalidate_all!

      expect(Rails.logger).to have_received(:info).with(/All cache entries deleted/)
    end
  end

  describe 'text normalization' do
    it 'converts to lowercase' do
      allow(embedding_service).to receive(:generate).and_return(embedding)

      cache_service.fetch("RUBY DEVELOPER", account_id: account_id)

      record = ::EmbeddingCache.last
      expect(record.query_text).to eq("ruby developer")
    end

    it 'removes extra spaces' do
      allow(embedding_service).to receive(:generate).and_return(embedding)

      cache_service.fetch("  ruby    developer   ", account_id: account_id)

      record = ::EmbeddingCache.last
      expect(record.query_text).to eq("ruby developer")
    end

    it 'strips leading and trailing spaces' do
      allow(embedding_service).to receive(:generate).and_return(embedding)

      cache_service.fetch("\n\t ruby developer \n\t", account_id: account_id)

      record = ::EmbeddingCache.last
      expect(record.query_text).to eq("ruby developer")
    end
  end

  describe 'key generation' do
    it 'includes model_version in key' do
      allow(embedding_service).to receive(:generate).and_return(embedding)

      cache_service.fetch(query_text, account_id: account_id)
      record = ::EmbeddingCache.last

      expect(record.key).to include('v1')
    end

    it 'includes account_id in key (isolation)' do
      ::EmbeddingCache.delete_all # Clean before

      account2 = create(:account)
      cache_service2 = described_class.new(embedding_service: embedding_service)

      allow(embedding_service).to receive(:generate).and_return(embedding)

      # Create cache for account 1
      cache_service.fetch("ruby", account_id: account_id)

      # Create cache for account 2 - should be different
      cache_service2.fetch("ruby", account_id: account2.id)

      expect(::EmbeddingCache.count).to eq(2) # Two different records
    end
  end
end
