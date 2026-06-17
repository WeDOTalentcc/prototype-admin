require "rails_helper"

RSpec.describe "V1::Users::SourcedProfiles#analyze", type: :request do
  let!(:account)         { create(:account) }
  let!(:user)            { create(:user, account: account) }
  let!(:sourced_profile) { create(:sourced_profile, account: account) }
  let(:headers)          { auth_headers(user) }

  before do
    allow_any_instance_of(SourcedProfileAnalysisService).to receive(:invoke_llm).and_return(
      summary: "Strong candidate",
      skills_analysis: { strong: [ "ruby" ], moderate: [], gaps: [] },
      fit_score: 0.77,
      strengths: [], concerns: []
    )
    Rails.cache.clear
  end

  describe "POST /v1/users/sourced_profiles/:id/analyze" do
    it "returns 200 and analysis payload" do
      post "/v1/users/sourced_profiles/#{sourced_profile.id}/analyze", headers: headers
      expect(response).to have_http_status(:ok)
      data = json["data"]
      expect(data["summary"]).to eq("Strong candidate")
      expect(data["fit_score"]).to eq(0.77)
      expect(data["sourced_profile_id"]).to eq(sourced_profile.id)
    end

    it "second call hits cache (does not call LLM again)" do
      post "/v1/users/sourced_profiles/#{sourced_profile.id}/analyze", headers: headers
      expect_any_instance_of(SourcedProfileAnalysisService).not_to receive(:invoke_llm)
      post "/v1/users/sourced_profiles/#{sourced_profile.id}/analyze", headers: headers
      expect(response).to have_http_status(:ok)
    end

    it "returns 404 when sourced_profile does not belong to account" do
      other = create(:sourced_profile, account: create(:account))
      post "/v1/users/sourced_profiles/#{other.id}/analyze", headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end
end
