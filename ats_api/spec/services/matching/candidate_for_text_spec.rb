# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Matching::CandidateForText do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:fake_embedding) { Array.new(768) { rand(-1.0..1.0) } }

  before { Apartment::Tenant.switch!(account.tenant) }

  describe '#call' do
    subject(:result) do
      described_class.new(
        text: text,
        account_id: account.id,
        top_k: top_k,
        filters: filters,
        page: page,
        per_page: per_page,
        min_score: min_score,
        max_score: max_score
      ).call
    end

    let(:text) { 'Senior Ruby developer with 5 years experience in São Paulo' }
    let(:top_k) { 500 }
    let(:filters) { {} }
    let(:page) { 1 }
    let(:per_page) { 20 }
    let(:min_score) { 0.0 }
    let(:max_score) { 1.0 }

    context 'when text is blank' do
      let(:text) { '' }

      it 'returns error' do
        expect(result[:success]).to be false
        expect(result[:error]).to include('required')
      end
    end

    context 'when text is too short' do
      let(:text) { 'short' }

      it 'returns error' do
        expect(result[:success]).to be false
        expect(result[:error]).to include('minimum')
      end
    end

    context 'when embedding generation fails' do
      let(:text) { 'Senior Ruby developer with experience' }

      before do
        allow_any_instance_of(Embeddings::Encoder).to receive(:call).and_return(nil)
      end

      it 'returns error' do
        expect(result[:success]).to be false
        expect(result[:error]).to include('embedding')
      end
    end

    context 'when embedding generation raises' do
      let(:text) { 'Senior Ruby developer with experience' }

      before do
        allow_any_instance_of(Embeddings::Encoder).to receive(:call).and_raise(StandardError, 'API timeout')
      end

      it 'returns error' do
        expect(result[:success]).to be false
        expect(result[:error]).to include('embedding')
      end
    end

    context 'when no candidates match' do
      let(:text) { 'Senior Ruby developer with experience' }

      before do
        allow_any_instance_of(Embeddings::Encoder).to receive(:call).and_return(fake_embedding)
        allow(Embedding).to receive_message_chain(:for_candidates, :nearest_neighbors, :limit).and_return([])
      end

      it 'returns empty success result' do
        expect(result[:success]).to be true
        expect(result[:records]).to eq([])
        expect(result[:meta][:total]).to eq(0)
      end
    end

    context 'with valid text and matching candidates' do
      let(:text) { 'Senior Ruby developer with experience' }
      let!(:candidate) { create(:candidate, account_id: account.id, name: 'John Developer') }

      let(:mock_embedding_result) do
        double('EmbeddingResult', reference_id: candidate.id, neighbor_distance: 0.2)
      end

      let(:mock_search_result) do
        candidate.define_singleton_method(:score=) { |v| @score = v }
        candidate.define_singleton_method(:score) { @score }
        { records: [candidate], aggs: {} }
      end

      before do
        allow_any_instance_of(Embeddings::Encoder).to receive(:call).and_return(fake_embedding)
        allow(Embedding).to receive_message_chain(:for_candidates, :nearest_neighbors, :limit)
          .and_return([mock_embedding_result])
        allow(Candidate).to receive(:search_default).and_return(mock_search_result)
      end

      it 'returns success with candidates' do
        expect(result[:success]).to be true
        expect(result[:records]).not_to be_empty
      end

      it 'includes pagination meta' do
        expect(result[:meta]).to include(:total, :page, :per_page, :total_pages)
      end

      it 'includes score meta' do
        expect(result[:meta]).to include(:min_score, :max_score)
      end
    end
  end

  describe 'parameter clamping' do
    context 'with top_k above max' do
      it 'clamps to MAX_TOP_K' do
        service = described_class.new(text: 'test text long enough', account_id: account.id, top_k: 5000)
        expect(service.instance_variable_get(:@top_k)).to eq(described_class::MAX_TOP_K)
      end
    end

    context 'with negative page' do
      it 'clamps to 1' do
        service = described_class.new(text: 'test text long enough', account_id: account.id, page: -1)
        expect(service.instance_variable_get(:@page)).to eq(1)
      end
    end

    context 'with per_page above max' do
      it 'clamps to MAX_PER_PAGE' do
        service = described_class.new(text: 'test text long enough', account_id: account.id, per_page: 500)
        expect(service.instance_variable_get(:@per_page)).to eq(described_class::MAX_PER_PAGE)
      end
    end

    context 'with min_score below zero' do
      it 'clamps to 0.0' do
        service = described_class.new(text: 'test text long enough', account_id: account.id, min_score: -0.5)
        expect(service.instance_variable_get(:@min_score)).to eq(0.0)
      end
    end

    context 'with max_score above 1' do
      it 'clamps to 1.0' do
        service = described_class.new(text: 'test text long enough', account_id: account.id, max_score: 2.0)
        expect(service.instance_variable_get(:@max_score)).to eq(1.0)
      end
    end
  end
end
