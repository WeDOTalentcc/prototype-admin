# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::SkillRelationships API", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:skill) { create(:skill, account: account) }
  let(:job) { create(:job, account: account) }

  describe "GET /v1/users/skill_relationships" do
    let!(:rel) { create(:skill_relationship, skill: skill, account: account) }

    before { SkillRelationship.reindex }

    it "returns skill relationships" do
      get "/v1/users/skill_relationships", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
    end

    it "returns unauthorized without token" do
      get "/v1/users/skill_relationships", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "GET /v1/users/skill_relationships/:id" do
    let!(:rel) { create(:skill_relationship, skill: skill, account: account) }

    it "returns the skill relationship" do
      get "/v1/users/skill_relationships/#{rel.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]["attributes"]["skill_id"]).to eq(skill.id)
    end

    it "returns not found for non-existent id" do
      get "/v1/users/skill_relationships/99999", headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end
  end

  describe "POST /v1/users/skill_relationships" do
    let(:valid_params) do
      {
        skill_relationship: {
          skill_id: skill.id,
          reference_type: "Job",
          reference_id: job.id,
          level_skill: 3
        }
      }
    end

    it "creates a skill relationship" do
      expect {
        post "/v1/users/skill_relationships", params: valid_params.to_json, headers: auth_headers(user)
      }.to change(SkillRelationship, :count).by(1)

      expect(response).to have_http_status(:created)
    end

    it "creates via skill_name when skill_id is absent" do
      params = { skill_relationship: { skill_name: "NewSkill#{SecureRandom.hex(3)}", reference_type: "Job", reference_id: job.id } }

      expect {
        post "/v1/users/skill_relationships", params: params.to_json, headers: auth_headers(user)
      }.to change(SkillRelationship, :count).by(1)

      expect(response).to have_http_status(:created)
    end

    it "returns unauthorized without token" do
      post "/v1/users/skill_relationships", params: valid_params.to_json, headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe "PUT /v1/users/skill_relationships/:id" do
    let!(:rel) { create(:skill_relationship, skill: skill, account: account, level_skill: 1) }

    it "updates the skill relationship" do
      put "/v1/users/skill_relationships/#{rel.id}",
          params: { skill_relationship: { level_skill: 3 } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(rel.reload.level_skill).to eq(3)
    end

    it "returns forbidden for another account's relationship" do
      other_rel = create(:skill_relationship)

      put "/v1/users/skill_relationships/#{other_rel.id}",
          params: { skill_relationship: { level: "básico" } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:forbidden)
    end
  end

  describe "DELETE /v1/users/skill_relationships/:id" do
    let!(:rel) { create(:skill_relationship, skill: skill, account: account) }

    it "soft deletes the skill relationship" do
      delete "/v1/users/skill_relationships/#{rel.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(rel.reload.is_deleted).to be true
    end
  end

  describe "GET /v1/users/skill_relationships/experience_times" do
    it "returns experience time options" do
      get "/v1/users/skill_relationships/experience_times", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      expect(json["data"]).not_to be_empty
    end
  end

  describe "GET /v1/users/skill_relationships/skill_levels" do
    it "returns skill level options" do
      get "/v1/users/skill_relationships/skill_levels", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json["data"]).to be_an(Array)
      expect(json["data"]).not_to be_empty
    end
  end
end
