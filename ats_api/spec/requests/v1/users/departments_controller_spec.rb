# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Departments API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe "GET /v1/users/departments" do
    let!(:dept1) { create(:department, account: account, name: "Engineering") }
    let!(:dept2) { create(:department, account: account, name: "Marketing") }

    before { Department.reindex }

    it "returns departments for the account" do
      get "/v1/users/departments", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      expect(json["data"].size).to be >= 2
    end

    it "returns unauthorized without token" do
      get "/v1/users/departments", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "GET /v1/users/departments/:id" do
    let!(:dept) { create(:department, account: account, name: "Finance") }

    it "returns the department" do
      get "/v1/users/departments/#{dept.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]["attributes"]["name"]).to eq("Finance")
    end

    it "returns not found for another account's department" do
      other_dept = create(:department)

      get "/v1/users/departments/#{other_dept.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end
  end

  describe "POST /v1/users/departments" do
    let(:valid_params) { { department: { name: "Operations" } } }

    it "creates a department" do
      expect {
        post "/v1/users/departments", params: valid_params.to_json, headers: auth_headers(user)
      }.to change(Department, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json["data"]["attributes"]["name"]).to eq("Operations")
    end

    it "returns unauthorized without token" do
      post "/v1/users/departments", params: valid_params.to_json, headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /v1/users/departments/:id" do
    let!(:dept) { create(:department, account: account, name: "Sales") }

    it "updates the department" do
      put "/v1/users/departments/#{dept.id}",
          params: { department: { name: "Sales & Marketing" } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(dept.reload.name).to eq("Sales & Marketing")
    end
  end

  describe "DELETE /v1/users/departments/:id" do
    let!(:dept) { create(:department, account: account, name: "Old Dept") }

    it "soft deletes the department" do
      delete "/v1/users/departments/#{dept.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(dept.reload.is_deleted).to be true
    end
  end

  describe "GET /v1/users/departments/tree" do
    let!(:root) { create(:department, account: account, name: "Root", level: 0) }

    it "returns departments tree" do
      get "/v1/users/departments/tree", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json).to be_an(Array)
    end
  end

  describe "GET /v1/users/departments/:id/ancestors" do
    let!(:dept) { create(:department, account: account) }

    it "returns ancestors list" do
      get "/v1/users/departments/#{dept.id}/ancestors", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json).to have_key("ancestors")
    end
  end

  describe "GET /v1/users/departments/:id/descendants" do
    let!(:dept) { create(:department, account: account) }

    it "returns descendants list" do
      get "/v1/users/departments/#{dept.id}/descendants", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json).to have_key("descendants")
    end
  end
end
