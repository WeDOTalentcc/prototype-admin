# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::HybridSearchService do
  subject(:service) { described_class.new(account_id: account_id, tenant: tenant) }

  let(:account_id) { 123 }
  let(:tenant) { "public" }
  let(:query_text) { "ruby developer senior" }
  let(:filters) { { city: "são paulo" } }

  before do
    allow(Apartment::Tenant).to receive(:switch!).and_yield
    allow(Candidates::Search::SimpleQueryDetector).to receive(:detect).and_return(:simple)
    allow(Candidate).to receive(:where).and_return(instance_double('ActiveRecord::Relation', includes: instance_double('ActiveRecord::Relation')))
  end

  describe '#search' do
    it 'coordinates both search strategies' do
      embedding = Array.new(768) { rand }
      es_results = [ { id: 1, rank: 1, score: 2.0, source: :elasticsearch } ]
      emb_results = [ { id: 2, rank: 1, distance: 0.2, source: :embedding } ]

      allow_any_instance_of(Candidates::Search::EmbeddingService).to receive(:generate).with(query_text).and_return(embedding)
      allow_any_instance_of(Candidates::Search::ElasticsearchStrategy).to receive(:search).and_return(es_results)
      allow_any_instance_of(Candidates::Search::EmbeddingStrategy).to receive(:search).and_return(emb_results)

      result = service.search(query_text, user_filters: filters)

      expect(result).to respond_to(:candidates, :metadata)
    end

    it 'works when embedding returns empty' do
      allow_any_instance_of(Candidates::Search::EmbeddingService).to receive(:generate).and_return(nil)
      allow_any_instance_of(Candidates::Search::ElasticsearchStrategy).to receive(:search).and_return([ { id: 1, rank: 1, score: 1.0 } ])

      result = service.search(query_text)

      expect(result.candidates).to be_an(Array)
    end

    it 'works when ES returns empty' do
      embedding = Array.new(768) { rand }

      allow_any_instance_of(Candidates::Search::EmbeddingService).to receive(:generate).and_return(embedding)
      allow_any_instance_of(Candidates::Search::ElasticsearchStrategy).to receive(:search).and_return([])
      allow_any_instance_of(Candidates::Search::EmbeddingStrategy).to receive(:search).and_return([ { id: 2, rank: 1, distance: 0.1 } ])

      result = service.search(query_text)

      expect(result.candidates).to be_an(Array)
    end

    it 'switches tenant before searching' do
      embedding = Array.new(768) { rand }

      allow_any_instance_of(Candidates::Search::EmbeddingService).to receive(:generate).and_return(embedding)
      allow_any_instance_of(Candidates::Search::ElasticsearchStrategy).to receive(:search).and_return([])
      allow_any_instance_of(Candidates::Search::EmbeddingStrategy).to receive(:search).and_return([])

      service.search(query_text)

      expect(Apartment::Tenant).to have_received(:switch!).with(tenant)
    end

    it 'returns empty Result on error' do
      allow_any_instance_of(Candidates::Search::ElasticsearchStrategy).to receive(:search).and_raise(StandardError.new("Search failed"))

      result = service.search(query_text)

      expect(result.candidates).to eq([])
    end

    it 'logs search execution' do
      embedding = Array.new(768) { rand }

      allow(Rails.logger).to receive(:info)
      allow_any_instance_of(Candidates::Search::EmbeddingService).to receive(:generate).and_return(embedding)
      allow_any_instance_of(Candidates::Search::ElasticsearchStrategy).to receive(:search).and_return([])
      allow_any_instance_of(Candidates::Search::EmbeddingStrategy).to receive(:search).and_return([])

      service.search(query_text)

      expect(Rails.logger).to have_received(:info).at_least(:once)
    end
  end
end
