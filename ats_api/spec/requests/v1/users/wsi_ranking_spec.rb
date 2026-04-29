# frozen_string_literal: true

require "rails_helper"

RSpec.describe "WSI ranking and report endpoints", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }
  let(:job) { create(:job, account: account, user: user) }
  let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }
  let(:candidates) { create_list(:candidate, 3, account: account) }

  before do
    candidates.each_with_index do |cand, i|
      ec = create(
        :evaluation_candidate,
        account: account,
        user: user,
        candidate: cand,
        evaluation: evaluation,
        job: job,
        completed: true,
        score: 9.0 - i,
        wsi_decision: { "result" => "APROVADO", "confidence" => "alta" },
        wsi_red_flags: [ { "code" => "RF-01" } ]
      )
      ec.update_columns(f11_report_json: { "x" => 1 }, f11_report_stale: false) if ec.respond_to?(:f11_report_json)
    end
  end

  it "returns candidates ordered by wsi_final desc for wsi_ranking" do
    get "/v1/users/jobs/#{job.id}/wsi_ranking", headers: headers
    expect(response).to have_http_status(:ok)
    body = JSON.parse(response.body)
    scores = body["data"].map { |r| r["wsi_final"] }
    expect(scores).to eq(scores.sort.reverse)
    expect(body["data"].first).to include("uid", "name", "wsi_final", "decision", "red_flags_count")
    expect(body["data"].first["red_flags_count"]).to eq(1)
  end

  it "returns wsi_report json for a candidate" do
    ec = EvaluationCandidate.find_by(job_id: job.id, account_id: account.id)
    get "/v1/users/evaluation_candidates/#{ec.uid}/wsi_report", headers: headers
    expect(response).to have_http_status(:ok)
    body = JSON.parse(response.body)
    expect(body["data"]["report"]).to be_present
  end
end
