# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs::ActivityLogs API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  let!(:job) { create(:job, user: user, account: account) }

  before do
    create(:activity_log, reference_type: "Job", reference_id: job.id, user: user, account: account, action: "create")
    create(:activity_log, reference_type: "Job", reference_id: job.id, user: user, account: account, action: "update",
           changeset: { "title" => { "from" => "Old", "to" => "New" } })
    create(:activity_log, reference_type: "Candidate", reference_id: 999, user: user, account: account, action: "create")

    ActivityLog.reindex
  end

  describe 'GET /v1/users/jobs/:job_id/activity_log' do
    context 'when authenticated' do
      it 'returns activity logs for the specific job' do
        get "/v1/users/jobs/#{job.id}/activity_log", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(2)
      end
    end

    context 'when job does not exist' do
      it 'returns not found' do
        get "/v1/users/jobs/999999/activity_log", headers: authentication_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/jobs/#{job.id}/activity_log"

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
