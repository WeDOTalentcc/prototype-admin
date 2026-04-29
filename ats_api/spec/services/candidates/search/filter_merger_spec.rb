# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::FilterMerger do
  describe '.merge' do
    let(:base_filters) { { account_id: 123, is_deleted: false } }
    let(:user_filters) { { city: "São Paulo", position_level: "senior" } }

    before do
      allow(Candidates::Search::Configuration).to receive(:locked_filters)
        .and_return([ :account_id, :is_deleted ])
    end

    it 'combines base filters with user filters' do
      result = described_class.merge(base_filters, user_filters)

      expect(result).to include(
        account_id: 123,
        is_deleted: false,
        city: "São Paulo",
        position_level: "senior"
      )
    end

    it 'NUNCA permite sobrescrever account_id (locked filter)' do
      malicious_filters = { account_id: 999, city: "Rio" }

      result = described_class.merge(base_filters, malicious_filters)

      expect(result[:account_id]).to eq(123) # Keeps the base
      expect(result[:city]).to eq("Rio") # Allows the non-locked
    end

    it 'NUNCA permite sobrescrever is_deleted (locked filter)' do
      malicious_filters = { is_deleted: true }

      result = described_class.merge(base_filters, malicious_filters)

      expect(result[:is_deleted]).to eq(false)
    end

    it 'logs override attempt when warn_on_override=true' do
      malicious_filters = { account_id: 999, is_deleted: true }

      allow(Rails.logger).to receive(:warn)

      described_class.merge(base_filters, malicious_filters, warn_on_override: true)

      expect(Rails.logger).to have_received(:warn) do |arg|
        expect(arg).to match(/locked_filter_override_attempt/)
        expect(arg).to match(/account_id/)
        expect(arg).to match(/is_deleted/)
      end
    end

    it 'does not log when warn_on_override=false' do
      malicious_filters = { account_id: 999 }

      allow(Rails.logger).to receive(:warn)

      described_class.merge(base_filters, malicious_filters, warn_on_override: false)

      expect(Rails.logger).not_to have_received(:warn)
    end

    it 'allows non-locked filters normally' do
      user_filters = {
        city: "São Paulo",
        position_level: "senior",
        remote_work: true
      }

      result = described_class.merge(base_filters, user_filters)

      expect(result).to include(user_filters)
    end

    it 'converts string keys to symbol before checking locked' do
      malicious_filters = { "account_id" => 999 }

      result = described_class.merge(base_filters, malicious_filters)

      expect(result[:account_id]).to eq(123) # Protects even with string
    end
  end

  describe '.whitelist_for_pgvector' do
    before do
      allow(Candidates::Search::Configuration).to receive(:pgvector_allowed_filters)
        .and_return([ :city, :position_level, :remote_work ])
    end

    it 'returns only allowed filters for pgvector' do
      user_filters = {
        city: "São Paulo",
        position_level: "senior",
        malicious_field: "hack",
        __proto__: "injection"
      }

      result = described_class.whitelist_for_pgvector(user_filters)

      expect(result).to eq(
        city: "São Paulo",
        position_level: "senior"
      )
    end

    it 'returns empty hash when no filter is allowed' do
      user_filters = { malicious: "value", hack: "attempt" }

      result = described_class.whitelist_for_pgvector(user_filters)

      expect(result).to eq({})
    end

    it 'allows all filters if they are in the whitelist' do
      user_filters = {
        city: "São Paulo",
        position_level: "senior",
        remote_work: true
      }

      result = described_class.whitelist_for_pgvector(user_filters)

      expect(result).to eq(user_filters)
    end
  end
end
