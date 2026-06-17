# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Candidates#communications", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/candidates/:id/communications" do
    context "when authenticated" do
      let!(:candidate) { create(:candidate, account: account) }
      let!(:job) { create(:job, account: account, user: user) }
      let!(:apply) { create(:apply, candidate: candidate, job: job, account: account, is_deleted: false) }

      it "returns communication timeline" do
        get "/v1/users/candidates/#{candidate.id}/communications", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body["candidate_id"]).to eq(candidate.id)
        expect(body["candidate_name"]).to eq(candidate.name)
        expect(body["communications"]).to be_an(Array)
        expect(body["summary"]).to be_a(Hash)
        expect(body["summary"]).to have_key("total_communications")
        expect(body["summary"]).to have_key("days_since_last_contact")
      end

      it "includes dispatches in communications" do
        dispatch = create(:dispatch, user: user, account: account)
        create(:dispatch_message, dispatch: dispatch, recipient: candidate, sent_at: 1.day.ago)

        get "/v1/users/candidates/#{candidate.id}/communications", headers: headers

        expect(response).to have_http_status(:ok)
        body = json
        dispatch_comms = body["communications"].select { |c| c["type"] == "dispatch" }
        expect(dispatch_comms).not_to be_empty
      end

      it "returns not found for invalid candidate" do
        get "/v1/users/candidates/0/communications", headers: headers
        expect(response).to have_http_status(:not_found)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/candidates/1/communications"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
