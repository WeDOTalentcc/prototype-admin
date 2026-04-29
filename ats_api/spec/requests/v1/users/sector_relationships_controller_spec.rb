# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::SectorRelationships API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:sector) { create(:sector) }
  let(:job) { create(:job, account: account) }

  describe "GET /v1/users/sector_relationships" do
    let!(:rel) { create(:sector_relationship, sector: sector, account: account, reference_type: "Job", reference_id: job.id) }

    before { SectorRelationship.reindex }

    it "returns sector relationships for the account" do
      get "/v1/users/sector_relationships", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
    end

    it "returns unauthorized without token" do
      get "/v1/users/sector_relationships", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "GET /v1/users/sector_relationships/:id" do
    let!(:rel) { create(:sector_relationship, sector: sector, account: account, reference_type: "Job", reference_id: job.id) }

    it "returns the sector relationship" do
      get "/v1/users/sector_relationships/#{rel.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]["attributes"]["sector_id"]).to eq(sector.id)
    end
  end

  describe "POST /v1/users/sector_relationships" do
    let(:valid_params) do
      {
        sector_relationship: {
          sector_id: sector.id,
          sector_name: sector.name,
          reference_type: "Job",
          reference_id: job.id
        }
      }
    end

    it "creates a sector relationship" do
      expect {
        post "/v1/users/sector_relationships", params: valid_params.to_json, headers: auth_headers(user)
      }.to change(SectorRelationship, :count).by(1)

      expect(response).to have_http_status(:created)
    end

    it "returns unauthorized without token" do
      post "/v1/users/sector_relationships", params: valid_params.to_json, headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /v1/users/sector_relationships/:id" do
    let!(:rel) { create(:sector_relationship, sector: sector, account: account, reference_type: "Job", reference_id: job.id) }
    let(:new_sector) { create(:sector) }

    it "updates the sector relationship" do
      put "/v1/users/sector_relationships/#{rel.id}",
          params: { sector_relationship: { sector_id: new_sector.id, sector_name: new_sector.name } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(rel.reload.sector_id).to eq(new_sector.id)
    end
  end

  describe "DELETE /v1/users/sector_relationships/:id" do
    let!(:rel) { create(:sector_relationship, sector: sector, account: account, reference_type: "Job", reference_id: job.id) }

    it "soft deletes the sector relationship" do
      delete "/v1/users/sector_relationships/#{rel.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(rel.reload.is_deleted).to be true
    end
  end
end
