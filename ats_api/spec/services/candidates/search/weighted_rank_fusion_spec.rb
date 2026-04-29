# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::Search::WeightedRankFusion do
  describe '.combine' do
    it 'combines rankings with RRF when both strategies have results' do
      result_sets = {
        elasticsearch: [
          { id: 1, rank: 1, score: 2.5 },
          { id: 2, rank: 2, score: 1.8 },
          { id: 3, rank: 3, score: 1.2 }
        ],
        embedding: [
          { id: 2, rank: 1, distance: 0.1 },
          { id: 3, rank: 2, distance: 0.2 },
          { id: 1, rank: 3, distance: 0.3 }
        ]
      }

      result = described_class.combine(result_sets)

      expect(result).to be_an(Array)
      expect(result.size).to eq(3)
      expect(result.map(&:id)).to contain_exactly(1, 2, 3)
    end

    it 'combines with different weights favoring Elasticsearch' do
      result_sets = {
        elasticsearch: [ { id: 1, rank: 1, score: 2.5 } ],
        embedding: [ { id: 2, rank: 1, distance: 0.1 } ]
      }

      result = described_class.combine(
        result_sets,
        weights: { elasticsearch: 0.9, embedding: 0.1 }
      )

      expect(result.first.id).to eq(1) # ES has higher weight
    end

    it 'combines with different weights favoring Embeddings' do
      result_sets = {
        elasticsearch: [ { id: 1, rank: 1, score: 2.5 } ],
        embedding: [ { id: 2, rank: 1, distance: 0.1 } ]
      }

      result = described_class.combine(
        result_sets,
        weights: { elasticsearch: 0.1, embedding: 0.9 }
      )

      expect(result.first.id).to eq(2) # Embedding has higher weight
    end

    it 'returns empty array when both strategies are empty' do
      result = described_class.combine({})

      expect(result).to eq([])
    end

    it 'returns only Elasticsearch rankings when embedding is empty' do
      result_sets = {
        elasticsearch: [
          { id: 1, rank: 1, score: 2.5 },
          { id: 2, rank: 2, score: 1.8 }
        ]
      }

      result = described_class.combine(result_sets)

      expect(result.map(&:id)).to contain_exactly(1, 2)
    end

    it 'returns only Embedding rankings when elasticsearch is empty' do
      result_sets = {
        embedding: [
          { id: 3, rank: 1, distance: 0.1 },
          { id: 4, rank: 2, distance: 0.2 }
        ]
      }

      result = described_class.combine(result_sets)

      expect(result.map(&:id)).to contain_exactly(3, 4)
    end

    it 'orders by descending score' do
      result_sets = {
        elasticsearch: [
          { id: 1, rank: 1, score: 3.0 },
          { id: 2, rank: 2, score: 2.0 },
          { id: 3, rank: 3, score: 1.0 }
        ],
        embedding: [
          { id: 1, rank: 3, distance: 0.3 },
          { id: 2, rank: 2, distance: 0.2 },
          { id: 3, rank: 1, distance: 0.1 }
        ]
      }

      result = described_class.combine(result_sets)

      scores = result.map(&:final_score)
      expect(scores).to eq(scores.sort.reverse)
    end

    it 'includes contributions from each source' do
      result_sets = {
        elasticsearch: [ { id: 1, rank: 1, score: 2.5 } ],
        embedding: [ { id: 1, rank: 2, distance: 0.2 } ]
      }

      result = described_class.combine(result_sets)

      expect(result.first.contributions).to have_key(:elasticsearch)
      expect(result.first.contributions).to have_key(:embedding)
    end

    it 'handles many candidates' do
      es_results = (1..100).map { |i| { id: i, rank: i, score: 100.0 / i } }
      emb_results = (1..100).map { |i| { id: i, rank: 101 - i, distance: i * 0.01 } }

      result_sets = {
        elasticsearch: es_results,
        embedding: emb_results
      }

      result = described_class.combine(result_sets)

      expect(result.size).to eq(100)
      expect(result.map(&:id)).to contain_exactly(*(1..100))
    end
  end
end
