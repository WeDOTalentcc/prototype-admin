# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::RankFusionService do
  let(:service) { described_class.new }

  describe "#fuse" do
    context "with results from both sources" do
      let(:vector_results) do
        [
          { candidate_id: 1, similarity: 0.95 },
          { candidate_id: 2, similarity: 0.90 },
          { candidate_id: 3, similarity: 0.85 }
        ]
      end

      let(:text_results) do
        [
          { candidate_id: 2, similarity: 0.88 },
          { candidate_id: 4, similarity: 0.82 },
          { candidate_id: 3, similarity: 0.75 }
        ]
      end

      it "ranks candidates appearing in both sources higher" do
        fused = service.fuse(vector_results: vector_results, text_results: text_results, limit: 5)

        ids = fused.map { |r| r[:candidate_id] }
        both_ids = [ 2, 3 ]

        both_ids.each do |id|
          expect(ids.index(id)).to be < ids.size
        end

        candidate_2 = fused.find { |r| r[:candidate_id] == 2 }
        candidate_1 = fused.find { |r| r[:candidate_id] == 1 }
        expect(candidate_2[:rrf_score]).to be > candidate_1[:rrf_score]
      end

      it "marks source correctly" do
        fused = service.fuse(vector_results: vector_results, text_results: text_results, limit: 5)

        expect(fused.find { |r| r[:candidate_id] == 1 }[:source]).to eq(:vector)
        expect(fused.find { |r| r[:candidate_id] == 4 }[:source]).to eq(:text)
        expect(fused.find { |r| r[:candidate_id] == 2 }[:source]).to eq(:both)
      end

      it "respects limit" do
        fused = service.fuse(vector_results: vector_results, text_results: text_results, limit: 2)

        expect(fused.size).to eq(2)
      end

      it "includes all unique candidates" do
        fused = service.fuse(vector_results: vector_results, text_results: text_results, limit: 10)

        expect(fused.map { |r| r[:candidate_id] }).to contain_exactly(1, 2, 3, 4)
      end
    end

    context "with empty text results" do
      let(:vector_results) { [ { candidate_id: 1, similarity: 0.9 } ] }

      it "returns vector results unchanged" do
        result = service.fuse(vector_results: vector_results, text_results: [], limit: 5)

        expect(result).to eq(vector_results)
      end
    end

    context "with empty vector results" do
      let(:text_results) { [ { candidate_id: 1, similarity: 0.8 } ] }

      it "returns text results" do
        result = service.fuse(vector_results: [], text_results: text_results, limit: 5)

        expect(result).to eq(text_results)
      end
    end

    context "with custom weights" do
      let(:service) { described_class.new(vector_weight: 0.3, text_weight: 0.7) }

      let(:vector_results) { [ { candidate_id: 1, similarity: 0.95 } ] }
      let(:text_results) { [ { candidate_id: 2, similarity: 0.80 } ] }

      it "applies weights to RRF scores" do
        fused = service.fuse(vector_results: vector_results, text_results: text_results, limit: 5)

        text_candidate = fused.find { |r| r[:candidate_id] == 2 }
        vector_candidate = fused.find { |r| r[:candidate_id] == 1 }

        expect(text_candidate[:rrf_score]).to be > vector_candidate[:rrf_score]
      end
    end

    context "RRF formula correctness" do
      let(:service) { described_class.new(k: 60, vector_weight: 1.0, text_weight: 1.0) }

      it "computes correct RRF score for candidate in both" do
        vector_results = [ { candidate_id: 1, similarity: 0.9 } ]
        text_results = [ { candidate_id: 1, similarity: 0.8 } ]

        fused = service.fuse(vector_results: vector_results, text_results: text_results, limit: 1)

        expected_score = (1.0 / (60 + 1)) + (1.0 / (60 + 1))
        expect(fused.first[:rrf_score]).to be_within(0.0001).of(expected_score)
      end

      it "computes correct RRF score for candidate in one source" do
        vector_results = [
          { candidate_id: 1, similarity: 0.9 },
          { candidate_id: 2, similarity: 0.8 }
        ]
        text_results = [ { candidate_id: 3, similarity: 0.7 } ]

        fused = service.fuse(vector_results: vector_results, text_results: text_results, limit: 5)

        candidate_2 = fused.find { |r| r[:candidate_id] == 2 }
        expected_score = 1.0 / (60 + 2)
        expect(candidate_2[:rrf_score]).to be_within(0.0001).of(expected_score)
      end
    end
  end
end
