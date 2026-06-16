# frozen_string_literal: true

require 'rails_helper'

RSpec.describe EmbeddingCache, type: :model do
  include ActiveSupport::Testing::TimeHelpers
  describe 'validations' do
    subject { build(:embedding_cache) }

    it { is_expected.to validate_presence_of(:key) }
    it { is_expected.to validate_presence_of(:model_version) }
    it { is_expected.to validate_presence_of(:query_text) }
    it { is_expected.to validate_presence_of(:embedding) }
    it { is_expected.to validate_presence_of(:account_id) }
    it { is_expected.to validate_uniqueness_of(:key) }
  end

  describe 'associations' do
    it { is_expected.to belong_to(:account) }
  end

  describe 'scopes' do
    let(:account1) { create(:account) }
    let(:account2) { create(:account) }

    describe '.by_account' do
      it 'filters by account_id' do
        cache1 = create(:embedding_cache, account: account1)
        cache2 = create(:embedding_cache, account: account2)

        result = described_class.by_account(account1.id)

        expect(result).to include(cache1)
        expect(result).not_to include(cache2)
      end
    end

    describe '.by_model_version' do
      it 'filters by model version' do
        cache1 = create(:embedding_cache, model_version: 'v1')
        cache2 = create(:embedding_cache, model_version: 'v2')

        result = described_class.by_model_version('v1')

        expect(result).to include(cache1)
        expect(result).not_to include(cache2)
      end
    end

    describe '.stale' do
      it 'returns records with old last_accessed_at' do
        fresh = create(:embedding_cache, last_accessed_at: 1.day.ago)
        stale = create(:embedding_cache, last_accessed_at: 31.days.ago)

        result = described_class.stale(30.days)

        expect(result).to include(stale)
        expect(result).not_to include(fresh)
      end
    end
  end

  describe '#touch_access' do
    it 'increments hit_count' do
      cache = create(:embedding_cache, hit_count: 5)

      expect { cache.touch_access }.to change { cache.reload.hit_count }.by(1)
    end

    it 'updates last_accessed_at' do
      cache = create(:embedding_cache, last_accessed_at: 10.days.ago)
      freeze_time = Time.current

      travel_to freeze_time do
        cache.touch_access
      end

      expect(cache.reload.last_accessed_at).to be_within(1.second).of(freeze_time)
    end
  end

  describe '.cleanup_stale!' do
    before { described_class.delete_all }

    it 'deletes stale records' do
      fresh = create(:embedding_cache, last_accessed_at: 1.day.ago)
      stale1 = create(:embedding_cache, last_accessed_at: 31.days.ago)
      stale2 = create(:embedding_cache, last_accessed_at: 45.days.ago)

      expect {
        described_class.cleanup_stale!(ttl: 30.days)
      }.to change { described_class.count }.by(-2)

      expect(described_class.exists?(fresh.id)).to be true
      expect(described_class.exists?(stale1.id)).to be false
      expect(described_class.exists?(stale2.id)).to be false
    end

    it 'returns number of deleted records' do
      create(:embedding_cache, last_accessed_at: 31.days.ago)
      create(:embedding_cache, last_accessed_at: 45.days.ago)

      result = described_class.cleanup_stale!(ttl: 30.days)

      expect(result).to eq(2)
    end

    it 'logs cleanup result' do
      create(:embedding_cache, last_accessed_at: 31.days.ago)

      allow(Rails.logger).to receive(:info)

      described_class.cleanup_stale!(ttl: 30.days)

      expect(Rails.logger).to have_received(:info).with(/Cleaned up 1 stale entri/)
    end
  end
end
