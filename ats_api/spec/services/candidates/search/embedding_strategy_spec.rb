require 'rails_helper'

RSpec.describe Candidates::Search::EmbeddingStrategy do
  subject(:strategy) { described_class.new(account_id: account_id) }

  let(:account_id) { 123 }
  let(:embedding) { Array.new(768) { rand(0.0..1.0) } }

  describe '#search' do
    let(:candidate1) { instance_double(Candidate, id: 1) }
    let(:candidate2) { instance_double(Candidate, id: 2) }
    let(:base_relation) { instance_double('ActiveRecord::Relation') }
    let(:filtered_relation) { instance_double('ActiveRecord::Relation') }
    let(:not_null_relation) { instance_double('ActiveRecord::Relation') }
    let(:nearest_relation) { instance_double('ActiveRecord::Relation') }

    before do
      allow(Candidate).to receive(:where).with(account_id: account_id, is_deleted: false)
        .and_return(base_relation)
      allow(base_relation).to receive(:where).and_return(filtered_relation)
      allow(filtered_relation).to receive(:not).with(embedding: nil).and_return(not_null_relation)
      allow(not_null_relation).to receive(:nearest_neighbors).and_return(nearest_relation)
      allow(nearest_relation).to receive(:limit).and_return([ candidate1, candidate2 ])
    end

    it 'returns empty array when query_embedding is blank' do
      expect(strategy.search(nil)).to eq([])
      expect(strategy.search([])).to eq([])
    end

    it 'returns ranked results with correct structure' do
      result = strategy.search(embedding)

      expect(result).to be_an(Array)
      expect(result.size).to eq(2)
      expect(result.first).to include(:id, :rank, :source)
      expect(result.first[:id]).to eq(1)
      expect(result.first[:rank]).to eq(1)
      expect(result.second[:rank]).to eq(2)
    end

    it 'filters candidates by account and active status' do
      expect(Candidate).to receive(:where).with(account_id: account_id, is_deleted: false)

      strategy.search(embedding)
    end

    it 'filters out candidates without embeddings' do
      expect(filtered_relation).to receive(:not).with(embedding: nil)

      strategy.search(embedding)
    end

    it 'uses cosine distance for similarity' do
      expect(not_null_relation).to receive(:nearest_neighbors)
        .with(:embedding, embedding, distance: "cosine")

      strategy.search(embedding)
    end

    it 'limits results to pool size' do
      pool_size = 200
      allow(Candidates::Search::Configuration).to receive(:initial_pool_size).and_return(pool_size)

      expect(nearest_relation).to receive(:limit).with(pool_size)

      strategy.search(embedding)
    end

    it 'returns empty array on error' do
      allow(Candidate).to receive(:where).and_raise(StandardError.new("DB error"))
      allow(Rails.logger).to receive(:error)

      result = strategy.search(embedding)

      expect(result).to eq([])
    end

    it 'applies whitelisted filters when provided' do
      filters = { city: "São Paulo", position_level: "senior" }

      expect(base_relation).to receive(:where).with(city: "São Paulo", position_level: "senior")

      strategy.search(embedding, user_filters: filters)
    end

    it 'ignores non-whitelisted filters' do
      filters = { city: "São Paulo", malicious_field: "hack" }

      expect(base_relation).to receive(:where).with(city: "São Paulo")

      strategy.search(embedding, user_filters: filters)
    end
  end
end
