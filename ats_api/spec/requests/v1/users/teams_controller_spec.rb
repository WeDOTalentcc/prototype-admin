# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Teams API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:department) { create(:department, account: account) }

  describe "GET /v1/users/teams" do
    let!(:team1) { create(:team, account: account, department: department, name: "Alpha Team") }
    let!(:team2) { create(:team, account: account, department: department, name: "Beta Team") }

    before { Team.reindex }

    it "returns active teams for the account" do
      get "/v1/users/teams", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      expect(json["data"].size).to be >= 2
    end

    it "returns unauthorized without token" do
      get "/v1/users/teams", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "GET /v1/users/teams/:id" do
    let!(:team) { create(:team, account: account, department: department, name: "Dev Team") }

    it "returns the team" do
      get "/v1/users/teams/#{team.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]["attributes"]["name"]).to eq("Dev Team")
    end

    it "returns not found for another account's team" do
      other_team = create(:team)

      get "/v1/users/teams/#{other_team.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end
  end

  describe "POST /v1/users/teams" do
    let(:valid_params) { { team: { name: "New Team", department_id: department.id } } }

    it "creates a team" do
      expect {
        post "/v1/users/teams", params: valid_params.to_json, headers: auth_headers(user)
      }.to change(Team, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json["data"]["attributes"]["name"]).to eq("New Team")
    end

    it "returns unauthorized without token" do
      post "/v1/users/teams", params: valid_params.to_json, headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /v1/users/teams/:id" do
    let!(:team) { create(:team, account: account, department: department, name: "Old Name") }

    it "updates the team" do
      put "/v1/users/teams/#{team.id}",
          params: { team: { name: "New Name" } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(team.reload.name).to eq("New Name")
    end
  end

  describe "DELETE /v1/users/teams/:id" do
    let!(:team) { create(:team, account: account, department: department) }

    it "deactivates the team" do
      delete "/v1/users/teams/#{team.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(team.reload.is_active).to be false
    end
  end

  describe "GET /v1/users/teams/:id/composition" do
    let!(:team) { create(:team, account: account, department: department) }

    it "returns team composition" do
      get "/v1/users/teams/#{team.id}/composition", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json).to have_key("team_id")
      expect(json).to have_key("composition")
    end
  end
end
