# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Embedding, type: :model do
  describe 'validations' do
    subject { build(:embedding) }

    it { is_expected.to validate_presence_of(:reference_type) }
    it { is_expected.to validate_presence_of(:reference_id) }
    it { is_expected.to validate_presence_of(:embedding) }

    it 'validates uniqueness of reference_id scoped to reference_type' do
      candidate = create(:candidate)
      create(:embedding, reference: candidate)

      duplicate = build(:embedding, reference: candidate)

      expect(duplicate).not_to be_valid
      expect(duplicate.errors[:reference_id]).to include('has already been taken')
    end
  end

  describe 'associations' do
    it { is_expected.to belong_to(:reference) }

    it 'accepts Candidate as reference' do
      candidate = create(:candidate)
      embedding = create(:embedding, reference: candidate)

      expect(embedding.reference).to eq(candidate)
      expect(embedding.reference_type).to eq('Candidate')
    end

    it 'accepts Job as reference' do
      job = create(:job)
      embedding = create(:embedding, reference: job)

      expect(embedding.reference).to eq(job)
      expect(embedding.reference_type).to eq('Job')
    end
  end

  describe 'scopes' do
    describe '.for_candidates' do
      it 'returns only candidate embeddings' do
        candidate_emb = create(:embedding, reference: create(:candidate))
        job_emb = create(:embedding, reference: create(:job))

        result = described_class.for_candidates

        expect(result).to include(candidate_emb)
        expect(result).not_to include(job_emb)
      end
    end

    describe '.for_jobs' do
      it 'returns only job embeddings' do
        candidate_emb = create(:embedding, reference: create(:candidate))
        job_emb = create(:embedding, reference: create(:job))

        result = described_class.for_jobs

        expect(result).to include(job_emb)
        expect(result).not_to include(candidate_emb)
      end
    end
  end

  describe '.nearest_for_type' do
    let(:query_vector) { Array.new(768) { rand } }

    it 'finds nearest neighbors for specific type' do
      candidate1 = create(:candidate)
      candidate2 = create(:candidate)
      job = create(:job)

      emb1 = create(:embedding, reference: candidate1, embedding: Array.new(768) { rand })
      emb2 = create(:embedding, reference: candidate2, embedding: Array.new(768) { rand })
      emb_job = create(:embedding, reference: job, embedding: Array.new(768) { rand })

      result = described_class.nearest_for_type('Candidate', query_vector, limit: 10)

      expect(result.pluck(:reference_type).uniq).to eq([ 'Candidate' ])
    end

    it 'respects the limit parameter' do
      5.times do
        create(:embedding, reference: create(:candidate), embedding: Array.new(768) { rand })
      end

      result = described_class.nearest_for_type('Candidate', query_vector, limit: 3)

      expect(result.size).to be <= 3
    end

    it 'uses cosine distance by default' do
      candidate = create(:candidate)
      create(:embedding, reference: candidate, embedding: Array.new(768) { rand })

      expect(described_class).to receive(:nearest_neighbors)
        .with(:embedding, query_vector, hash_including(distance: 'cosine'))
        .and_call_original

      described_class.nearest_for_type('Candidate', query_vector)
    end

    it 'allows specifying custom distance' do
      candidate = create(:candidate)
      create(:embedding, reference: candidate, embedding: Array.new(768) { rand })

      expect(described_class).to receive(:nearest_neighbors)
        .with(:embedding, query_vector, hash_including(distance: 'euclidean'))
        .and_call_original

      described_class.nearest_for_type('Candidate', query_vector, distance: 'euclidean')
    end
  end
end
