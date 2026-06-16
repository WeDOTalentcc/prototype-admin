# frozen_string_literal: true

require "rails_helper"

RSpec.describe "GET /v1/users/evaluation_candidates/:uid/wsi_decision", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }
  let(:evaluation) { create(:evaluation, account: account) }
  let(:candidate) { create(:candidate, account: account) }
  let(:job) { create(:job, account: account) }
  let(:ec) do
    create(
      :evaluation_candidate,
      account: account,
      user: user,
      candidate: candidate,
      evaluation: evaluation,
      job: job,
      uid: SecureRandom.uuid
    )
  end

  it "returns 200 with wsi_decision and wsi_red_flags" do
    ec.update_columns(
      wsi_decision: { "result" => "APROVADO", "confidence" => "alta", "decided_at" => Time.current.iso8601 },
      wsi_red_flags: [ { "code" => "RF-01", "level" => "medio", "description" => "x" } ]
    )

    get "/v1/users/evaluation_candidates/#{ec.uid}/wsi_decision", headers: headers

    expect(response).to have_http_status(:ok)
    body = JSON.parse(response.body)
    expect(body["data"]["wsi_decision"]["result"]).to eq("APROVADO")
    expect(body["data"]["wsi_red_flags"].first["code"]).to eq("RF-01")
  end

  it "returns 404 when uid belongs to another account" do
    other = create(:evaluation_candidate, uid: SecureRandom.uuid)
    get "/v1/users/evaluation_candidates/#{other.uid}/wsi_decision", headers: headers
    expect(response).to have_http_status(:not_found)
  end
end
