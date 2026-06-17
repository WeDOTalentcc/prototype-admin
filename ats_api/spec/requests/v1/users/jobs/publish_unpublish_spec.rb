# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs publish/unpublish API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  before do
    JobStatus.create_default_statuses
  end

  let(:active_status) { JobStatus.find_by(name: "Ativa") }
  let(:draft_status) { JobStatus.find_by(name: "Rascunho") }

  describe 'POST /v1/users/jobs/:id/publish' do
    let!(:job) { create(:job, user: user, account: account, job_status: draft_status) }

    context 'when job is ready' do
      before do
        checker = instance_double(Jobs::FieldRequirementChecker, is_ready_for_publication?: true)
        allow(Jobs::FieldRequirementChecker).to receive(:new).and_return(checker)
      end

      it 'publishes the job' do
        post "/v1/users/jobs/#{job.id}/publish", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['published_date']).to be_present
        expect(json['data']['attributes']['is_active']).to be true
      end
    end

    context 'when job is not ready' do
      before do
        missing = [ { field: "salary_from", category: "critical" } ]
        checker = instance_double(
          Jobs::FieldRequirementChecker,
          is_ready_for_publication?: false,
          make_missing_fields: missing
        )
        allow(Jobs::FieldRequirementChecker).to receive(:new).and_return(checker)
      end

      it 'returns error with missing fields' do
        post "/v1/users/jobs/#{job.id}/publish", headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['missing_fields']).to be_present
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/jobs/#{job.id}/publish"

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/jobs/:id/unpublish' do
    let!(:job) { create(:job, user: user, account: account, job_status: active_status, published_date: Time.current, is_active: true) }

    context 'when authenticated' do
      it 'unpublishes the job' do
        post "/v1/users/jobs/#{job.id}/unpublish", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['published_date']).to be_nil
        expect(json['data']['attributes']['is_active']).to be false
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/jobs/#{job.id}/unpublish"

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
