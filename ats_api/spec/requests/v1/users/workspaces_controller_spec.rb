# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Workspaces API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }

  describe "GET /v1/users/workspaces" do
    let!(:workspace) { create(:workspace, uid: SecureRandom.uuid, user: user, account: account) }
    let!(:deleted_workspace) { create(:workspace, :deleted, uid: SecureRandom.uuid, user: user, account: account) }

    before { Workspace.reindex }

    it "returns active workspaces for the user" do
      get "/v1/users/workspaces", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      uids = json["data"].map { |w| w["attributes"]["uid"] }
      expect(uids).to include(workspace.uid)
      expect(uids).not_to include(deleted_workspace.uid)
    end

    it "returns unauthorized without token" do
      get "/v1/users/workspaces", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "GET /v1/users/workspaces/:id" do
    let!(:workspace) { create(:workspace, uid: SecureRandom.uuid, user: user, account: account) }

    it "returns the workspace" do
      get "/v1/users/workspaces/#{workspace.uid}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]["attributes"]["uid"]).to eq(workspace.uid)
    end
  end

  describe "POST /v1/users/workspaces" do
    it "creates a workspace" do
      expect {
        post "/v1/users/workspaces",
             params: { workspace: { name: "My Workspace" } }.to_json,
             headers: auth_headers(user)
      }.to change(Workspace, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json["data"]["attributes"]["name"]).to eq("My Workspace")
    end

    it "returns unauthorized without token" do
      post "/v1/users/workspaces",
           params: { workspace: { name: "Test" } }.to_json,
           headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /v1/users/workspaces/:id" do
    let!(:workspace) { create(:workspace, uid: SecureRandom.uuid, user: user, account: account, name: "Old Name") }

    it "updates the workspace" do
      put "/v1/users/workspaces/#{workspace.uid}",
          params: { workspace: { name: "New Name" } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(workspace.reload.name).to eq("New Name")
    end
  end

  describe "DELETE /v1/users/workspaces/:id" do
    let!(:workspace) { create(:workspace, uid: SecureRandom.uuid, user: user, account: account) }

    it "soft deletes the workspace" do
      delete "/v1/users/workspaces/#{workspace.uid}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(workspace.reload.is_deleted).to be true
    end
  end
end
