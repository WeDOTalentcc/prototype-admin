# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::RefinementService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:service) { described_class.new(account: account, user: user) }

  let!(:base_candidate1) { create(:candidate, account: account, name: "João Silva", role_name: "Senior Ruby Dev") }
  let!(:base_candidate2) { create(:candidate, account: account, name: "Maria Santos", role_name: "Backend Engineer") }

  let!(:similar_candidate) { create(:candidate, account: account, name: "Ana Costa", role_name: "Tech Lead") }
  let!(:rejected_candidate) { create(:candidate, account: account, name: "Pedro Junior", role_name: "Junior Dev") }

  let(:sourcing) do
    create(:sourcing,
      account: account,
      user: user,
      provider: "local",
      query: "Similar to 2 candidates",
      parameters: {
        "search_type" => "similarity",
        "base_candidate_ids" => [ base_candidate1.id, base_candidate2.id ],
        "job_id" => nil,
        "method" => "centroid"
      },
      search_metadata: {
        "embedding_model" => "gemini-embedding-001",
        "threshold" => 0.60
      }
    )
  end

  let!(:profile1) do
    create(:sourced_profile, account: account, candidate: similar_candidate, sourcing: sourcing)
  end

  let!(:profile2) do
    create(:sourced_profile, account: account, candidate: rejected_candidate, sourcing: sourcing)
  end

  let!(:sps1) do
    create(:sourced_profile_sourcing,
      sourcing: sourcing,
      sourced_profile: profile1,
      account: account,
      user: user,
      similarity_score: 85.0,
      search_score: 0.85
    )
  end

  let!(:sps2) do
    create(:sourced_profile_sourcing,
      sourcing: sourcing,
      sourced_profile: profile2,
      account: account,
      user: user,
      similarity_score: 70.0,
      search_score: 0.70
    )
  end

  before do
    Apartment::Tenant.switch!(account.tenant)

    [ base_candidate1, base_candidate2, similar_candidate, rejected_candidate ].each do |candidate|
      embedding_vector = Array.new(768) { rand }
      Embedding.create!(
        reference_type: "Candidate",
        reference_id: candidate.id,
        embedding: embedding_vector
      )
    end
  end

  after do
    Apartment::Tenant.switch!("public")
  end

  describe "#call" do
    context "with valid feedback" do
      let(:liked_ids) { [ similar_candidate.id ] }
      let(:disliked_feedbacks) do
        [
          { candidate_id: rejected_candidate.id, reason: "Too junior" }
        ]
      end

      it "saves feedbacks" do
        expect {
          service.call(
            sourcing: sourcing,
            liked_candidate_ids: liked_ids,
            disliked_feedbacks: disliked_feedbacks
          )
        }.to change(CandidateFeedback, :count).by(2)

        like_feedback = CandidateFeedback.find_by(candidate_id: similar_candidate.id)
        expect(like_feedback.feedback_type).to eq("like")

        dislike_feedback = CandidateFeedback.find_by(candidate_id: rejected_candidate.id)
        expect(dislike_feedback.feedback_type).to eq("dislike")
        expect(dislike_feedback.reason).to eq("Too junior")
      end

      it "returns response with updated candidates" do
        result = service.call(
          sourcing: sourcing,
          liked_candidate_ids: liked_ids,
          disliked_feedbacks: disliked_feedbacks
        )

        expect(result[:sourcing_id]).to eq(sourcing.id)
        expect(result[:search_type]).to eq("similarity_refined")
        expect(result[:candidates]).to be_an(Array)
        expect(result[:summary][:existing_updated]).to be >= 0
        expect(result[:metadata]).to include(:duration_ms, :embedding_model)
      end

      it "updates sourcing metadata" do
        service.call(
          sourcing: sourcing,
          liked_candidate_ids: liked_ids,
          disliked_feedbacks: disliked_feedbacks
        )

        sourcing.reload
        expect(sourcing.search_metadata["refinements"]).to be_present
        expect(sourcing.search_metadata["refinements"].size).to eq(1)
        expect(sourcing.search_metadata["last_refined_at"]).to be_present
      end

      it "recomputes similarity scores for existing candidates" do
        old_score = sps1.similarity_score

        service.call(
          sourcing: sourcing,
          liked_candidate_ids: liked_ids,
          disliked_feedbacks: disliked_feedbacks
        )

        sps1.reload
        expect(sps1.similarity_score).to be_a(Float)
      end

      it "excludes rejected candidates from response" do
        result = service.call(
          sourcing: sourcing,
          liked_candidate_ids: liked_ids,
          disliked_feedbacks: disliked_feedbacks
        )

        candidate_ids = result[:candidates].map { |c| c[:candidate_id] }
        expect(candidate_ids).not_to include(rejected_candidate.id)
      end
    end

    context "with multiple rounds of refinement" do
      let(:liked_ids) { [ similar_candidate.id ] }
      let(:disliked_feedbacks) do
        [ { candidate_id: rejected_candidate.id, reason: "Too junior" } ]
      end

      it "tracks multiple refinement rounds" do
        service.call(
          sourcing: sourcing,
          liked_candidate_ids: liked_ids,
          disliked_feedbacks: disliked_feedbacks
        )

        service.call(
          sourcing: sourcing,
          liked_candidate_ids: liked_ids,
          disliked_feedbacks: []
        )

        sourcing.reload
        expect(sourcing.search_metadata["refinements"].size).to eq(2)
        expect(sourcing.search_metadata["total_refinement_rounds"]).to eq(2)
      end
    end

    context "validation errors" do
      it "raises error when sourcing is not a similarity search" do
        sourcing.update!(parameters: { "search_type" => "other" })

        expect {
          service.call(
            sourcing: sourcing,
            liked_candidate_ids: [ similar_candidate.id ]
          )
        }.to raise_error(ArgumentError, /not a similarity search/)
      end

      it "raises error when no feedback provided" do
        expect {
          service.call(
            sourcing: sourcing,
            liked_candidate_ids: [],
            disliked_feedbacks: []
          )
        }.to raise_error(ArgumentError, /At least 1 like or 1 dislike/)
      end

      it "raises error when candidate does not belong to sourcing" do
        other_candidate = create(:candidate, account: account)

        expect {
          service.call(
            sourcing: sourcing,
            liked_candidate_ids: [ other_candidate.id ]
          )
        }.to raise_error(ArgumentError, /do not belong to Sourcing/)
      end

      it "raises error when dislike reason is missing" do
        expect {
          service.call(
            sourcing: sourcing,
            disliked_feedbacks: [
              { candidate_id: rejected_candidate.id, reason: "" }
            ]
          )
        }.to raise_error(ArgumentError, /Reason is required/)
      end
    end

    context "when updating existing feedback" do
      let!(:existing_feedback) do
        create(:candidate_feedback,
          sourcing: sourcing,
          candidate_id: similar_candidate.id,
          user: user,
          account: account,
          feedback_type: "dislike"
        )
      end

      it "updates feedback type from dislike to like" do
        service.call(
          sourcing: sourcing,
          liked_candidate_ids: [ similar_candidate.id ],
          disliked_feedbacks: []
        )

        existing_feedback.reload
        expect(existing_feedback.feedback_type).to eq("like")
      end
    end

    context "feedback analysis with LLM" do
      let(:disliked_feedbacks) do
        [
          { candidate_id: rejected_candidate.id, reason: "Too junior" },
          { candidate_id: similar_candidate.id, reason: "Wrong industry" }
        ]
      end

      let(:analyzer_service) { instance_double(Candidates::SimilarCandidates::FeedbackAnalyzerService) }

      before do
        allow(Candidates::SimilarCandidates::FeedbackAnalyzerService).to receive(:new).and_return(analyzer_service)
        allow(analyzer_service).to receive(:analyze).and_return(
          {
            desired_profile: "Senior fintech developer",
            rejection_patterns: [ "junior", "non-fintech" ],
            positive_patterns: [ "senior level" ],
            explanation: "test explanation"
          }
        )
      end

      it "includes feedback analysis in response when 2+ dislikes" do
        result = service.call(
          sourcing: sourcing,
          liked_candidate_ids: [],
          disliked_feedbacks: disliked_feedbacks
        )

        expect(result[:feedback_analysis]).to be_present
        expect(result[:feedback_analysis][:desired_profile]).to eq("Senior fintech developer")
        expect(result[:feedback_analysis][:rejection_patterns]).to include("junior", "non-fintech")
      end
    end
  end
end
