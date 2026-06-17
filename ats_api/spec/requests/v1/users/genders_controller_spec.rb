# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Genders API", type: :request do
  let(:user) { create(:user) }

  describe "GET /v1/users/genders" do
    it "returns genders list" do
      get "/v1/users/genders", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      expect(json["data"]).not_to be_empty
    end

    it "returns unauthorized without token" do
      get "/v1/users/genders", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end
end
