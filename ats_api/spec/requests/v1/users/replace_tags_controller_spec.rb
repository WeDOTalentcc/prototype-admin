# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::ReplaceTags API", type: :request do
  let(:user) { create(:user) }

  describe "GET /v1/users/replace_tags" do
    it "returns empty array when no entities given" do
      get "/v1/users/replace_tags", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to eq([])
    end

    it "returns tags for the given entities" do
      get "/v1/users/replace_tags", params: { entities: [ "candidate" ] }, headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
    end

    it "returns unauthorized without token" do
      get "/v1/users/replace_tags", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end
end
