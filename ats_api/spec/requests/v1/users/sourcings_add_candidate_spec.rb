require "rails_helper"

RSpec.describe "V1::Users::Sourcings#add_candidate", type: :request do
  let!(:account)   { create(:account) }
  let!(:user)      { create(:user, account: account) }
  let!(:sourcing)  { create(:sourcing, account: account, user: user) }
  let!(:candidate) { create(:candidate, account: account) }
  let(:headers)    { auth_headers(user) }

  describe "POST /v1/users/sourcings/:id/add_candidate" do
    it "creates SourcedProfileSourcing with candidate_id" do
      expect {
        post "/v1/users/sourcings/#{sourcing.id}/add_candidate",
             params: { candidate_id: candidate.id, score: 85, notes: "manual" },
             headers: headers
      }.to change(SourcedProfileSourcing, :count).by(1)

      expect(response).to have_http_status(:created).or have_http_status(:ok)
      expect(json.dig("data", "sourcing_id")).to eq(sourcing.id)
      expect(json.dig("data", "score")).to eq(85)
    end

    it "is idempotent — second call returns existing relation without creating new" do
      post "/v1/users/sourcings/#{sourcing.id}/add_candidate",
           params: { candidate_id: candidate.id }, headers: headers

      expect {
        post "/v1/users/sourcings/#{sourcing.id}/add_candidate",
             params: { candidate_id: candidate.id }, headers: headers
      }.not_to change(SourcedProfileSourcing, :count)

      expect(response).to have_http_status(:ok)
    end

    it "returns 422 without candidate_id or sourced_profile_id" do
      post "/v1/users/sourcings/#{sourcing.id}/add_candidate", headers: headers
      expect(response).to have_http_status(:unprocessable_entity)
    end

    it "returns 404 for sourcing of another account" do
      other = create(:sourcing, account: create(:account))
      post "/v1/users/sourcings/#{other.id}/add_candidate",
           params: { candidate_id: candidate.id }, headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end
end
