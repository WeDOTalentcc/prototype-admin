require "rails_helper"

RSpec.describe "V1::Users::Candidates hidden filter", type: :request, search: true do
  let!(:account) { create(:account) }
  let!(:user)    { create(:user, account: account) }
  let(:headers)  { auth_headers(user) }

  let!(:visible_a) { create(:candidate, is_hidden: false, account: account) }
  let!(:visible_b) { create(:candidate, is_hidden: false, account: account) }
  let!(:hidden_a)  { create(:candidate, :hidden, account: account) }

  before { Candidate.searchkick_index.refresh }

  it "returns non-hidden by default (no filter)" do
    get "/v1/users/candidates", headers: headers
    expect(response).to have_http_status(:ok)
    ids = json["data"].map { |c| c["id"] }
    expect(ids).to match_array([ visible_a.id, visible_b.id ])
  end

  it "returns hidden when is_hidden:true explicitly requested" do
    get "/v1/users/candidates",
        params: { where: { is_hidden: true }.to_json },
        headers: headers
    expect(response).to have_http_status(:ok)
    ids = json["data"].map { |c| c["id"] }
    expect(ids).to contain_exactly(hidden_a.id)
  end
end
