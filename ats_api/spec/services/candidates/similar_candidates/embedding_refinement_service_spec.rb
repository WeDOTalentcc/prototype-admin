# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::EmbeddingRefinementService do
  describe "#refine" do
    let(:dims) { 768 }
    let(:original_centroid) { Array.new(dims) { rand } }
    let(:service) { described_class.new(original_centroid: original_centroid) }

    context "when only liked candidates are provided" do
      let(:liked_embedding) { Array.new(dims) { rand } }
      let(:liked_candidate) { create(:candidate) }

      before do
        allow(Embedding).to receive(:where).and_return(
          double(pluck: [ liked_embedding ])
        )
      end

      it "moves centroid towards liked candidates" do
        result = service.refine(liked_ids: [ liked_candidate.id ], disliked_ids: [])

        expect(result.size).to eq(dims)
        expect(result).not_to eq(original_centroid)

        magnitude = Math.sqrt(result.sum { |v| v**2 })
        expect(magnitude).to be_within(0.001).of(1.0)
      end
    end

    context "when only disliked candidates are provided" do
      let(:disliked_embedding) { Array.new(dims) { rand } }
      let(:disliked_candidate) { create(:candidate) }

      before do
        allow(Embedding).to receive(:where).and_return(
          double(pluck: [ disliked_embedding ])
        )
      end

      it "moves centroid away from disliked candidates" do
        result = service.refine(liked_ids: [], disliked_ids: [ disliked_candidate.id ])

        expect(result.size).to eq(dims)
        expect(result).not_to eq(original_centroid)

        magnitude = Math.sqrt(result.sum { |v| v**2 })
        expect(magnitude).to be_within(0.001).of(1.0)
      end
    end

    context "when both liked and disliked candidates are provided" do
      let(:liked_embedding) { Array.new(dims) { rand } }
      let(:disliked_embedding) { Array.new(dims) { rand } }
      let(:liked_candidate) { create(:candidate) }
      let(:disliked_candidate) { create(:candidate) }

      before do
        allow(Embedding).to receive(:where).and_return(
          double(pluck: [ liked_embedding ]),
          double(pluck: [ disliked_embedding ])
        )
      end

      it "refines centroid with both positive and negative feedback" do
        result = service.refine(
          liked_ids: [ liked_candidate.id ],
          disliked_ids: [ disliked_candidate.id ]
        )

        expect(result.size).to eq(dims)
        expect(result).not_to eq(original_centroid)

        magnitude = Math.sqrt(result.sum { |v| v**2 })
        expect(magnitude).to be_within(0.001).of(1.0)
      end
    end

    context "when no embeddings are found" do
      before do
        allow(Embedding).to receive(:where).and_return(double(pluck: []))
      end

      it "returns normalized original centroid" do
        result = service.refine(liked_ids: [ 999 ], disliked_ids: [])

        expect(result.size).to eq(dims)

        magnitude = Math.sqrt(result.sum { |v| v**2 })
        expect(magnitude).to be_within(0.001).of(1.0)
      end
    end

    context "when multiple liked candidates" do
      let(:embedding1) { Array.new(dims) { rand } }
      let(:embedding2) { Array.new(dims) { rand } }
      let(:candidate1) { create(:candidate) }
      let(:candidate2) { create(:candidate) }

      before do
        allow(Embedding).to receive(:where).and_return(
          double(pluck: [ embedding1, embedding2 ])
        )
      end

      it "computes centroid of liked embeddings" do
        result = service.refine(
          liked_ids: [ candidate1.id, candidate2.id ],
          disliked_ids: []
        )

        expect(result.size).to eq(dims)

        magnitude = Math.sqrt(result.sum { |v| v**2 })
        expect(magnitude).to be_within(0.001).of(1.0)
      end
    end

    describe "weight constants" do
      it "uses expected alpha and beta values" do
        expect(described_class::ALPHA).to eq(0.3)
        expect(described_class::BETA).to eq(0.2)
      end
    end
  end
end
