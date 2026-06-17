# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Applies#timeline", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/applies/:id/timeline" do
    context "when authenticated" do
      let!(:job) { create(:job, user: user, account: account) }
      let!(:sp) { create(:selective_process, job: job, account: account, status: :screening) }
      let!(:apply) { create(:apply, job: job, selective_process: sp, account_id: account.id) }

      before do
        create(:apply_status, apply: apply, selective_process: sp, user: user, account: account)
      end

      it "returns timeline data" do
        get "/v1/users/applies/#{apply.id}/timeline", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["apply_id"]).to eq(apply.id)
        expect(body["timeline"]).to be_an(Array)
        expect(body["timeline"].size).to be >= 1
        expect(body["summary"]).to be_a(Hash)
        expect(body["summary"]["days_in_pipeline"]).to be_a(Integer)
      end

      it "includes creation event" do
        get "/v1/users/applies/#{apply.id}/timeline", headers: headers

        body = json
        types = body["timeline"].map { |e| e["type"] }
        expect(types).to include("apply_created")
      end
    end

    context "when apply not found" do
      it "returns not found" do
        get "/v1/users/applies/999999/timeline", headers: headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/applies/1/timeline"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
