# frozen_string_literal: true

require "rails_helper"

RSpec.describe "POST /v1/users/sourcings/:id/refine", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { authenticated_header(user) }

  let!(:base_candidate1) { create(:candidate, account: account, name: "João Silva") }
  let!(:base_candidate2) { create(:candidate, account: account, name: "Maria Santos") }
  let!(:liked_candidate) { create(:candidate, account: account, name: "Ana Costa") }
  let!(:disliked_candidate) { create(:candidate, account: account, name: "Pedro Junior") }

  let(:sourcing) do
    create(:sourcing,
      account: account,
      user: user,
      provider: "local",
      query: "Similar to 2 candidates",
      parameters: {
        "search_type" => "similarity",
        "base_candidate_ids" => [ base_candidate1.id, base_candidate2.id ]
      },
      search_metadata: { "threshold" => 0.60 }
    )
  end

  let!(:liked_profile) do
    create(:sourced_profile, account: account, candidate: liked_candidate, sourcing: sourcing)
  end

  let!(:disliked_profile) do
    create(:sourced_profile, account: account, candidate: disliked_candidate, sourcing: sourcing)
  end

  let!(:liked_sps) do
    create(:sourced_profile_sourcing,
      sourcing: sourcing,
      sourced_profile: liked_profile,
      account: account,
      user: user,
      similarity_score: 85.0
    )
  end

  let!(:disliked_sps) do
    create(:sourced_profile_sourcing,
      sourcing: sourcing,
      sourced_profile: disliked_profile,
      account: account,
      user: user,
      similarity_score: 70.0
    )
  end

  before do
    Apartment::Tenant.switch!(account.tenant)

    [ base_candidate1, base_candidate2, liked_candidate, disliked_candidate ].each do |candidate|
      Embedding.create!(
        reference_type: "Candidate",
        reference_id: candidate.id,
        embedding: Array.new(768) { rand }
      )
    end
  end

  after do
    Apartment::Tenant.switch!("public")
  end

  describe "POST /v1/users/sourcings/:id/refine" do
    context "with valid parameters" do
      let(:params) do
        {
          liked_candidate_ids: [ liked_candidate.id ],
          disliked_feedbacks: [
            { candidate_id: disliked_candidate.id, reason: "Too junior for this role" }
          ],
          limit: 10
        }
      end

      it "returns 200 OK" do
        post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

        expect(response).to have_http_status(:ok)
      end

      it "returns refinement response" do
        post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

        json = JSON.parse(response.body, symbolize_names: true)

        expect(json[:sourcing_id]).to eq(sourcing.id)
        expect(json[:search_type]).to eq("similarity_refined")
        expect(json[:refinement_round]).to be_a(Integer)
        expect(json[:candidates]).to be_an(Array)
        expect(json[:summary]).to include(:total, :existing_updated, :new_found)
        expect(json[:metadata]).to include(:duration_ms, :embedding_model)
      end

      it "creates feedback records" do
        expect {
          post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers
        }.to change(CandidateFeedback, :count).by(2)
      end

      it "excludes disliked candidates from response" do
        post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

        json = JSON.parse(response.body, symbolize_names: true)
        candidate_ids = json[:candidates].map { |c| c[:candidate_id] }

        expect(candidate_ids).not_to include(disliked_candidate.id)
      end
    end

    context "with only likes" do
      let(:params) do
        {
          liked_candidate_ids: [ liked_candidate.id ]
        }
      end

      it "returns 200 OK" do
        post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

        expect(response).to have_http_status(:ok)
      end
    end

    context "with only dislikes" do
      let(:params) do
        {
          disliked_feedbacks: [
            { candidate_id: disliked_candidate.id, reason: "Not a good fit" }
          ]
        }
      end

      it "returns 200 OK" do
        post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

        expect(response).to have_http_status(:ok)
      end
    end

    context "validation errors" do
      context "when no feedback provided" do
        let(:params) do
          {
            liked_candidate_ids: [],
            disliked_feedbacks: []
          }
        end

        it "returns 422 Unprocessable Entity" do
          post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

          expect(response).to have_http_status(:unprocessable_entity)

          json = JSON.parse(response.body, symbolize_names: true)
          expect(json[:error]).to eq("invalid_params")
          expect(json[:message]).to include("At least 1 like or 1 dislike")
        end
      end

      context "when dislike reason is missing" do
        let(:params) do
          {
            disliked_feedbacks: [
              { candidate_id: disliked_candidate.id, reason: "" }
            ]
          }
        end

        it "returns 422 Unprocessable Entity" do
          post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

          expect(response).to have_http_status(:unprocessable_entity)

          json = JSON.parse(response.body, symbolize_names: true)
          expect(json[:error]).to eq("invalid_params")
          expect(json[:message]).to include("Reason is required")
        end
      end

      context "when candidate does not belong to sourcing" do
        let(:other_candidate) { create(:candidate, account: account) }
        let(:params) do
          {
            liked_candidate_ids: [ other_candidate.id ]
          }
        end

        it "returns 422 Unprocessable Entity" do
          post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

          expect(response).to have_http_status(:unprocessable_entity)

          json = JSON.parse(response.body, symbolize_names: true)
          expect(json[:error]).to eq("invalid_params")
          expect(json[:message]).to include("do not belong to Sourcing")
        end
      end

      context "when sourcing is not a similarity search" do
        before do
          sourcing.update!(parameters: { "search_type" => "other" })
        end

        let(:params) do
          {
            liked_candidate_ids: [ liked_candidate.id ]
          }
        end

        it "returns 422 Unprocessable Entity" do
          post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

          expect(response).to have_http_status(:unprocessable_entity)

          json = JSON.parse(response.body, symbolize_names: true)
          expect(json[:error]).to eq("invalid_params")
          expect(json[:message]).to include("not a similarity search")
        end
      end
    end

    context "when sourcing does not exist" do
      it "returns 404 Not Found" do
        post "/v1/users/sourcings/999999/refine",
             params: { liked_candidate_ids: [ liked_candidate.id ] },
             headers: headers

        expect(response).to have_http_status(:not_found)

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:error]).to eq("not_found")
      end
    end

    context "when sourcing belongs to another account" do
      let(:other_account) { create(:account) }
      let(:other_user) { create(:user, account: other_account) }
      let(:other_headers) { authenticated_header(other_user) }

      it "returns 404 Not Found" do
        post "/v1/users/sourcings/#{sourcing.id}/refine",
             params: { liked_candidate_ids: [ liked_candidate.id ] },
             headers: other_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context "with custom limit" do
      let(:params) do
        {
          liked_candidate_ids: [ liked_candidate.id ],
          limit: 30
        }
      end

      it "accepts custom limit" do
        post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

        expect(response).to have_http_status(:ok)
      end
    end

    context "with sources parameter" do
      let(:params) do
        {
          liked_candidate_ids: [ liked_candidate.id ],
          sources: [ "local" ]
        }
      end

      it "accepts sources parameter" do
        post "/v1/users/sourcings/#{sourcing.id}/refine", params: params, headers: headers

        expect(response).to have_http_status(:ok)
      end
    end
  end
end
