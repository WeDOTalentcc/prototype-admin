require "rails_helper"

RSpec.describe "V1::Users::Candidates diversity filters", type: :request, search: true do
  let!(:account) { create(:account) }
  let!(:user)    { create(:user, account: account) }
  let(:headers)  { auth_headers(user) }

  let!(:pcd_black)   { create(:candidate, :pcd, :ethnicity_black, account: account) }
  let!(:lgbt_brown)  { create(:candidate, :lgbtqia, :ethnicity_brown, account: account) }
  let!(:plain_white) { create(:candidate, :ethnicity_white, account: account) }

  before { Candidate.searchkick_index.refresh }

  describe "GET /v1/users/candidates?where={\"pcd\":true}" do
    it "returns only PcD candidates" do
      get "/v1/users/candidates", params: { where: { pcd: true }.to_json }, headers: headers
      expect(response).to have_http_status(:ok)
      ids = json["data"].map { |c| c["id"] }
      expect(ids).to include(pcd_black.id)
      expect(ids).not_to include(lgbt_brown.id, plain_white.id)
    end
  end

  describe "GET /v1/users/candidates?where={\"ethnicity\":\"black\"}" do
    it "returns only black-declared candidates" do
      get "/v1/users/candidates", params: { where: { ethnicity: "black" }.to_json }, headers: headers
      expect(response).to have_http_status(:ok)
      ids = json["data"].map { |c| c["id"] }
      expect(ids).to contain_exactly(pcd_black.id)
    end
  end

  describe "GET /v1/users/candidates with aggregators" do
    it "returns ethnicity and pcd facets in meta" do
      get "/v1/users/candidates",
          params: { extra_params: "aggs(ethnicity,pcd,lgbtqia)" },
          headers: headers
      expect(response).to have_http_status(:ok)
      aggs = json.dig("meta", "aggregators")
      expect(aggs).to include("ethnicity", "pcd", "lgbtqia") if aggs.present?
    end
  end
end
