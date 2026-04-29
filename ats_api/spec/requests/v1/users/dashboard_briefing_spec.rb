# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::Dashboard#briefing", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "GET /v1/users/dashboard/briefing" do
    context "when authenticated" do
      let!(:job) { create(:job, account: account, user: user, is_active: true, is_deleted: false, is_archived: false) }
      let!(:candidate) { create(:candidate, account: account) }
      let!(:apply) { create(:apply, job: job, candidate: candidate, account: account, is_deleted: false) }

      before do
        allow(Jobs::AlertsService).to receive(:new).and_return(
          double(call: { summary: { total_alerts: 0, critical: 0, warning: 0 }, alerts: [] })
        )
      end

      it "returns briefing data" do
        get "/v1/users/dashboard/briefing", headers: headers

        expect(response).to have_http_status(:ok)
        body = json

        expect(body).to have_key("generated_at")
        expect(body).to have_key("user_name")
        expect(body).to have_key("summary")
        expect(body).to have_key("alerts")
        expect(body).to have_key("new_applies")
        expect(body).to have_key("todays_agenda")
        expect(body).to have_key("completed_evaluations")
        expect(body).to have_key("aging_applies")
        expect(body).to have_key("recent_movements")
        expect(body).to have_key("no_shows")

        summary = body["summary"]
        expect(summary).to have_key("new_applies")
        expect(summary).to have_key("active_jobs")
        expect(summary).to have_key("interviews_today")
      end

      it "accepts since parameter in hours" do
        get "/v1/users/dashboard/briefing", headers: headers, params: { since: 48 }

        expect(response).to have_http_status(:ok)
      end

      it "accepts timezone parameter" do
        get "/v1/users/dashboard/briefing", headers: headers, params: { timezone: "America/New_York" }

        expect(response).to have_http_status(:ok)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        get "/v1/users/dashboard/briefing"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
