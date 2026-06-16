# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs#duplicate_selective_processes API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  let!(:source_job) { create(:job, user: user, account: account) }
  let!(:target_job) { create(:job, user: user, account: account) }

  before do
    create(:selective_process, job: source_job, account: account, name: "Triagem", position: 0, status: :screening)
    create(:selective_process, job: source_job, account: account, name: "Entrevista", position: 1, status: :interview)
  end

  describe 'POST /v1/users/jobs/:id/duplicate_selective_processes' do
    context 'when authenticated with valid params' do
      it 'copies selective processes' do
        post "/v1/users/jobs/#{target_job.id}/duplicate_selective_processes",
             params: { source_job_id: source_job.id }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(target_job.selective_processes.where(is_deleted: false).count).to eq(2)
      end

      it 'replaces existing processes when replace=true' do
        create(:selective_process, job: target_job, account: account, name: "Old", position: 0)

        post "/v1/users/jobs/#{target_job.id}/duplicate_selective_processes",
             params: { source_job_id: source_job.id, replace: true }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:ok)
        active = target_job.selective_processes.where(is_deleted: false)
        expect(active.count).to eq(2)
        expect(active.pluck(:name)).not_to include("Old")
      end
    end

    context 'when source_job_id is missing' do
      it 'returns bad request' do
        post "/v1/users/jobs/#{target_job.id}/duplicate_selective_processes",
             params: {}.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:bad_request)
      end
    end

    context 'when source job does not exist' do
      it 'returns error' do
        post "/v1/users/jobs/#{target_job.id}/duplicate_selective_processes",
             params: { source_job_id: 999999 }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/jobs/#{target_job.id}/duplicate_selective_processes",
             params: { source_job_id: source_job.id }.to_json

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
