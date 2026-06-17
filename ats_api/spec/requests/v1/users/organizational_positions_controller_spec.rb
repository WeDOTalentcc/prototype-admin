# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::OrganizationalPositions API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:department) { create(:department, account: account) }

  describe "GET /v1/users/organizational_positions" do
    let!(:pos1) { create(:organizational_position, account: account, department: department, title: "CEO") }
    let!(:pos2) { create(:organizational_position, account: account, department: department, title: "CTO") }

    before { OrganizationalPosition.reindex }

    it "returns active positions for the account" do
      get "/v1/users/organizational_positions", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      expect(json["data"].size).to be >= 2
    end

    it "returns unauthorized without token" do
      get "/v1/users/organizational_positions", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "GET /v1/users/organizational_positions/:id" do
    let!(:position) { create(:organizational_position, account: account, department: department, title: "VP Engineering") }

    it "returns the position" do
      get "/v1/users/organizational_positions/#{position.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]["attributes"]["title"]).to eq("VP Engineering")
    end

    it "returns not found for another account's position" do
      other_position = create(:organizational_position)

      get "/v1/users/organizational_positions/#{other_position.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end
  end

  describe "POST /v1/users/organizational_positions" do
    let(:valid_params) { { organizational_position: { title: "Senior Engineer", department_id: department.id } } }

    it "creates a position" do
      expect {
        post "/v1/users/organizational_positions", params: valid_params.to_json, headers: auth_headers(user)
      }.to change(OrganizationalPosition, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json["data"]["attributes"]["title"]).to eq("Senior Engineer")
    end

    it "returns unauthorized without token" do
      post "/v1/users/organizational_positions", params: valid_params.to_json, headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /v1/users/organizational_positions/:id" do
    let!(:position) { create(:organizational_position, account: account, department: department, title: "Engineer") }

    it "updates the position" do
      put "/v1/users/organizational_positions/#{position.id}",
          params: { organizational_position: { title: "Senior Engineer" } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(position.reload.title).to eq("Senior Engineer")
    end
  end

  describe "DELETE /v1/users/organizational_positions/:id" do
    let!(:position) { create(:organizational_position, account: account, department: department) }

    it "deactivates the position" do
      delete "/v1/users/organizational_positions/#{position.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(position.reload.is_active).to be false
    end
  end

  describe "GET /v1/users/organizational_positions/:id/reporting_chain" do
    let!(:position) { create(:organizational_position, account: account, department: department) }

    it "returns the reporting chain" do
      get "/v1/users/organizational_positions/#{position.id}/reporting_chain", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json).to have_key("reporting_chain")
    end
  end

  describe "GET /v1/users/organizational_positions/:id/direct_reports" do
    let!(:position) { create(:organizational_position, account: account, department: department) }

    it "returns direct reports" do
      get "/v1/users/organizational_positions/#{position.id}/direct_reports", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json).to have_key("direct_reports")
    end
  end
end
