# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Candidates#search_hints", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/candidates/search_hints" do
    context "when authenticated" do
      before do
        create_list(:candidate, 2, account: account)
        Candidate.reindex
      end

      it "returns facets, hints and meta" do
        get "/v1/users/candidates/search_hints",
            headers: headers,
            params: {
              search: "*",
              where: { is_deleted: false }.to_json,
              order: { created_at: :desc }.to_json
            }

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["entity"]).to eq("candidates")
        expect(body["facets"]).to be_a(Hash)
        expect(body["hints"]).to be_a(Hash)
        expect(body["hints"]["job_titles"]).to be_an(Array)
        expect(body["hints"]["skills"]).to be_an(Array)
        expect(body["hints"]["certifications"]).to be_an(Array)
        expect(body["hints"]["industries"]).to be_an(Array)
        expect(body["meta"]["catalog_version"]).to be_present
        expect(body["meta"]["facet_fields"]).to include("city", "skills")
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/candidates/search_hints"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
