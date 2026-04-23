# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Sourcings - Find Similar Candidates", type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:headers) { auth_headers(user) }

  let(:base_candidate) do
    create(:candidate, account: account, name: "Ana Costa", role_name: "Senior Ruby Developer",
           curriculum_text: "ruby rails postgresql microservices")
  end

  let(:similar_candidate) do
    create(:candidate, account: account, name: "Pedro Lima", role_name: "Backend Developer",
           curriculum_text: "ruby rails redis backend")
  end

  let(:embedding_vector) { Array.new(768) { 0.5 } }
  let(:similar_vector) { Array.new(768) { 0.48 } }

  before do
    allow_any_instance_of(Candidate).to receive(:sync_vector_after_commit)
    allow_any_instance_of(SourcedProfileSourcing).to receive(:enqueue_ai_analysis)
    allow_any_instance_of(SourcedProfileSourcing).to receive(:enqueue_stats_recalculation)
  end

  describe "POST /v1/users/sourcings/find_similar_candidates" do
    let(:endpoint) { "/v1/users/sourcings/find_similar_candidates" }

    context "when authenticated with valid params" do
      before do
        create(:embedding, reference: base_candidate, embedding: embedding_vector)
        create(:embedding, reference: similar_candidate, embedding: similar_vector)
      end

      it "returns 200 with similar candidates" do
        post endpoint, params: { candidate_ids: [ base_candidate.id ] }.to_json, headers: headers

        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body)
        expect(json).to have_key("search_type")
        expect(json["search_type"]).to eq("similarity")
        expect(json).to have_key("similar_candidates")
        expect(json).to have_key("metadata")
      end

      it "creates a sourcing record" do
        expect {
          post endpoint, params: { candidate_ids: [ base_candidate.id ] }.to_json, headers: headers
        }.to change(Sourcing, :count)
      end

      it "accepts optional limit and threshold" do
        post endpoint, params: {
          candidate_ids: [ base_candidate.id ],
          limit: 5,
          threshold: 0.75
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body)
        expect(json["metadata"]["threshold_used"]).to be >= 0.75
      end

      it "accepts exclude_ids" do
        post endpoint, params: {
          candidate_ids: [ base_candidate.id ],
          exclude_ids: [ similar_candidate.id ]
        }.to_json, headers: headers

        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body)
        ids = json["similar_candidates"].map { |c| c["candidate_id"] }
        expect(ids).not_to include(similar_candidate.id)
      end
    end

    context "when candidate has no embedding" do
      it "returns 422 with missing embedding IDs" do
        post endpoint, params: { candidate_ids: [ base_candidate.id ] }.to_json, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)

        json = JSON.parse(response.body)
        expect(json["error"]).to eq("missing_embeddings")
        expect(json["missing_ids"]).to include(base_candidate.id)
      end
    end

    context "when candidate does not exist" do
      it "returns 404" do
        post endpoint, params: { candidate_ids: [ 999_999 ] }.to_json, headers: headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context "when candidate_ids is missing" do
      it "returns 400" do
        post endpoint, params: {}.to_json, headers: headers

        expect(response).to have_http_status(:bad_request).or have_http_status(:unprocessable_entity)
      end
    end

    context "when unauthenticated" do
      it "returns 401" do
        post endpoint, params: { candidate_ids: [ base_candidate.id ] }.to_json,
             headers: { "Content-Type" => "application/json" }

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
