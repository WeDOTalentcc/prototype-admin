# frozen_string_literal: true

require "rails_helper"

RSpec.describe "Similar Candidates Search - Cache", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { authenticated_header(user) }

  let!(:candidate1) { create(:candidate, account: account, name: "João Silva") }
  let!(:candidate2) { create(:candidate, account: account, name: "Maria Santos") }
  let!(:similar_candidate) { create(:candidate, account: account, name: "Ana Costa") }

  before do
    Apartment::Tenant.switch!(account.tenant)

    [ candidate1, candidate2, similar_candidate ].each do |candidate|
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

  describe "cache behavior" do
    let(:params) do
      {
        candidate_ids: [ candidate1.id, candidate2.id ],
        limit: 10
      }
    end

    context "first search (no cache)" do
      it "performs fresh search" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers

        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be_falsy
        expect(json[:sourcing_id]).to be_present
      end
    end

    context "second search with same parameters (cache hit)" do
      before do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
        @first_response = JSON.parse(response.body, symbolize_names: true)
      end

      it "returns cached results" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers

        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be true
        expect(json[:cached_at]).to be_present
        expect(json[:sourcing_id]).to eq(@first_response[:sourcing_id])
      end

      it "has much faster response time" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:metadata][:duration_ms]).to be < 20
        expect(json[:metadata][:original_duration_ms]).to be_present
      end
    end

    context "with skip_cache parameter" do
      before do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
      end

      it "performs fresh search when skip_cache=true" do
        post "/v1/users/sourcings/find_similar_candidates",
             params: params.merge(skip_cache: true),
             headers: headers

        expect(response).to have_http_status(:ok)

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be_falsy
      end
    end

    context "cache miss scenarios" do
      before do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
      end

      it "misses cache with different candidate_ids" do
        different_params = params.merge(candidate_ids: [ candidate1.id, similar_candidate.id ])

        post "/v1/users/sourcings/find_similar_candidates",
             params: different_params,
             headers: headers

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be_falsy
      end

      it "misses cache with different threshold" do
        different_params = params.merge(threshold: 0.8)

        post "/v1/users/sourcings/find_similar_candidates",
             params: different_params,
             headers: headers

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be_falsy
      end

      it "misses cache with different job_id" do
        different_params = params.merge(job_id: 999)

        post "/v1/users/sourcings/find_similar_candidates",
             params: different_params,
             headers: headers

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be_falsy
      end
    end

    context "cache expiration" do
      it "misses cache after 24 hours" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
        sourcing = Sourcing.last

        travel 25.hours do
          post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers

          json = JSON.parse(response.body, symbolize_names: true)
          expect(json[:from_cache]).to be_falsy
          expect(json[:sourcing_id]).not_to eq(sourcing.id)
        end
      end

      it "hits cache before 24 hours" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
        first_response = JSON.parse(response.body, symbolize_names: true)

        travel 23.hours do
          post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers

          json = JSON.parse(response.body, symbolize_names: true)
          expect(json[:from_cache]).to be true
          expect(json[:sourcing_id]).to eq(first_response[:sourcing_id])
        end
      end
    end

    context "candidate_ids order normalization" do
      it "hits cache regardless of candidate_ids order" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
        first_response = JSON.parse(response.body, symbolize_names: true)

        reversed_params = params.merge(candidate_ids: [ candidate2.id, candidate1.id ])
        post "/v1/users/sourcings/find_similar_candidates", params: reversed_params, headers: headers

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be true
        expect(json[:sourcing_id]).to eq(first_response[:sourcing_id])
      end
    end

    context "multi-user behavior" do
      let(:other_user) { create(:user, account: account) }
      let(:other_headers) { authenticated_header(other_user) }

      it "does not share cache between different users" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
        first_response = JSON.parse(response.body, symbolize_names: true)

        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: other_headers
        second_response = JSON.parse(response.body, symbolize_names: true)

        expect(second_response[:from_cache]).to be_falsy
        expect(second_response[:sourcing_id]).not_to eq(first_response[:sourcing_id])
      end
    end

    context "failed sourcing status" do
      it "does not use cache from failed sourcing" do
        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers
        sourcing = Sourcing.last
        sourcing.update!(status: "failed")

        post "/v1/users/sourcings/find_similar_candidates", params: params, headers: headers

        json = JSON.parse(response.body, symbolize_names: true)
        expect(json[:from_cache]).to be_falsy
      end
    end
  end
end
