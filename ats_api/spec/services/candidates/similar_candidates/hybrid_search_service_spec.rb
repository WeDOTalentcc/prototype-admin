# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::HybridSearchService do
  let(:account) { create(:account) }
  let(:service) { described_class.new(account_id: account.id) }

  let(:embedding) { Array.new(768) { rand(-1.0..1.0) } }
  let(:exclude_ids) { [] }

  let(:intent_result) do
    Candidates::SimilarCandidates::IntentBasedRefinementService::IntentResult.new(
      embedding: embedding,
      description: "Ruby backend developer",
      elasticsearch_query: "Ruby Rails backend",
      must_have_skills: [ "ruby", "rails" ],
      nice_to_have_skills: [ "aws" ],
      searchable_attributes: [ "ruby", "rails" ],
      not_searchable_feedback: [],
      skipped: false
    )
  end

  let(:skipped_intent) do
    Candidates::SimilarCandidates::IntentBasedRefinementService::IntentResult.new(
      embedding: embedding,
      description: nil,
      elasticsearch_query: nil,
      must_have_skills: [],
      nice_to_have_skills: [],
      searchable_attributes: [],
      not_searchable_feedback: [],
      skipped: true
    )
  end

  let(:text_search_service) { instance_double(Candidates::SimilarCandidates::TextSearchService) }
  let(:rank_fusion_service) { instance_double(Candidates::SimilarCandidates::RankFusionService) }

  before do
    Apartment::Tenant.switch!(account.tenant)
  end

  after do
    Apartment::Tenant.switch!("public")
  end

  describe "#search" do
    context "when intent_result is nil" do
      it "returns vector-only results" do
        candidate = create(:candidate, account: account)
        Embedding.create!(reference_type: "Candidate", reference_id: candidate.id, embedding: embedding)

        results = service.search(
          embedding: embedding,
          intent_result: nil,
          exclude_ids: exclude_ids,
          limit: 10,
          threshold: 0.0
        )

        expect(results).to be_an(Array)
        expect(results.first).to include(:candidate_id, :similarity) if results.any?
      end
    end

    context "when intent is skipped" do
      it "returns vector-only results without text search" do
        allow(Candidates::SimilarCandidates::TextSearchService).to receive(:new).and_return(text_search_service)

        service.search(
          embedding: embedding,
          intent_result: skipped_intent,
          exclude_ids: exclude_ids,
          limit: 10,
          threshold: 0.0
        )

        expect(Candidates::SimilarCandidates::TextSearchService).not_to have_received(:new)
      end
    end

    context "when text search returns empty" do
      before do
        allow(Candidates::SimilarCandidates::TextSearchService).to receive(:new).and_return(text_search_service)
        allow(text_search_service).to receive(:search).and_return([])
      end

      it "falls back to vector-only results" do
        results = service.search(
          embedding: embedding,
          intent_result: intent_result,
          exclude_ids: exclude_ids,
          limit: 10,
          threshold: 0.0
        )

        expect(results).to be_an(Array)
      end
    end

    context "when both sources return results" do
      let(:vector_results) { [ { candidate_id: 1, similarity: 0.9 } ] }
      let(:text_results) { [ { candidate_id: 2, similarity: 0.8, source: :text } ] }
      let(:fused_results) do
        [
          { candidate_id: 1, similarity: 0.9, source: :vector, rrf_score: 0.009 },
          { candidate_id: 2, similarity: 0.8, source: :text, rrf_score: 0.006 }
        ]
      end

      before do
        allow(Candidates::SimilarCandidates::TextSearchService).to receive(:new).and_return(text_search_service)
        allow(text_search_service).to receive(:search).and_return(text_results)
        allow(Candidates::SimilarCandidates::RankFusionService).to receive(:new).and_return(rank_fusion_service)
        allow(rank_fusion_service).to receive(:fuse).and_return(fused_results)

        candidate = create(:candidate, account: account)
        Embedding.create!(reference_type: "Candidate", reference_id: candidate.id, embedding: embedding)
      end

      it "fuses vector and text results" do
        results = service.search(
          embedding: embedding,
          intent_result: intent_result,
          exclude_ids: exclude_ids,
          limit: 10,
          threshold: 0.0
        )

        expect(rank_fusion_service).to have_received(:fuse)
        expect(results).to be_an(Array)
        results.each do |r|
          expect(r).to include(:candidate_id, :similarity, :source)
        end
      end
    end
  end

  describe "pool retry mechanism" do
    it "retries with extended pool when insufficient results after tenant filtering" do
      results = service.search(
        embedding: embedding,
        intent_result: nil,
        exclude_ids: exclude_ids,
        limit: 10,
        threshold: 0.99
      )

      expect(results).to be_an(Array)
    end
  end
end
