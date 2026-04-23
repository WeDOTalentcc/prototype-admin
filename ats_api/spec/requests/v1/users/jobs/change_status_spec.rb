# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs#change_status API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  before do
    JobStatus.create_default_statuses
  end

  let(:active_status) { JobStatus.find_by(name: "Ativa") }
  let(:draft_status) { JobStatus.find_by(name: "Rascunho") }
  let(:paused_status) { JobStatus.find_by(name: "Paralisada") }
  let(:closed_status) { JobStatus.find_by(name: "Fechada (preenchida)") }

  describe 'POST /v1/users/jobs/:id/change_status' do
    let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

    context 'when transition is valid' do
      it 'changes job status' do
        post "/v1/users/jobs/#{job.id}/change_status",
             params: { job_status_id: active_status.id }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(job.reload.job_status).to eq(active_status)
      end
    end

    context 'when transition is invalid' do
      it 'returns error with allowed transitions' do
        post "/v1/users/jobs/#{job.id}/change_status",
             params: { job_status_id: closed_status.id }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
        expect(json['allowed_transitions']).to be_present
      end
    end

    context 'when job_status_id is missing' do
      it 'returns bad request' do
        post "/v1/users/jobs/#{job.id}/change_status",
             params: {}.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:bad_request)
      end
    end

    context 'with reason for pause' do
      before { job.update!(job_status: active_status) }

      it 'saves the reason' do
        post "/v1/users/jobs/#{job.id}/change_status",
             params: { job_status_id: paused_status.id, reason: "Budget freeze" }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(job.reload.reason_for_pause).to eq("Budget freeze")
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/jobs/#{job.id}/change_status",
             params: { job_status_id: active_status.id }.to_json

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
