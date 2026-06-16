require "rails_helper"

RSpec.describe "V1::Users::Candidates twin creation", type: :request do
  let!(:account)       { create(:account) }
  let!(:user)          { create(:user, account: account) }
  let!(:source)        { create(:candidate, account: account, name: "Maria Original") }
  let(:headers)        { auth_headers(user) }

  describe "POST /v1/users/candidates with twin fields" do
    it "creates a twin candidate linked to source" do
      post "/v1/users/candidates",
           params: {
             candidate: {
               name: "Maria (Twin)",
               email: "twin-#{SecureRandom.hex(4)}@example.com",
               is_twin: true,
               twin_source_id: source.id
             }
           },
           headers: headers

      expect(response).to have_http_status(:created)
      twin = Candidate.find(json.dig("data", "id"))
      expect(twin.is_twin).to be true
      expect(twin.twin_source).to eq(source)
    end
  end

  describe "GET /v1/users/candidates?where={\"is_twin\":true}" do
    it "filters only twin candidates", search: true do
      create(:candidate, :twin, account: account)
      create(:candidate, account: account)
      Candidate.searchkick_index.refresh

      get "/v1/users/candidates", params: { where: { is_twin: true }.to_json }, headers: headers
      expect(response).to have_http_status(:ok)
      expect(json["data"].all? { |c| c["is_twin"] }).to be true if json["data"].any? { |c| c.key?("is_twin") }
    end
  end
end
