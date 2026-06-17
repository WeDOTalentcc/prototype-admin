# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs#bulk_update API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  let!(:jobs) { create_list(:job, 3, user: user, account: account) }

  before do
    allow(Current).to receive(:user).and_return(user)
    allow(Current).to receive(:ip).and_return('127.0.0.1')
  end

  describe 'POST /v1/users/jobs/bulk_update' do
    context 'with valid params' do
      it 'updates multiple jobs' do
        post "/v1/users/jobs/bulk_update",
             params: {
               job_ids: jobs.map(&:id),
               fields: { priority: 1 }
             }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['updated']).to eq(3)
        expect(json['data']['batch_id']).to be_present
      end

      it 'creates activity logs with batch_id' do
        post "/v1/users/jobs/bulk_update",
             params: {
               job_ids: jobs.map(&:id),
               fields: { priority: 2 }
             }.to_json,
             headers: authentication_headers

        logs = ActivityLog.where(reference_type: "Job", reference_id: jobs.map(&:id))
        expect(logs.count).to eq(3)
        expect(logs.all? { |l| l.category.start_with?("bulk_update:") }).to be true
      end
    end

    context 'when job_ids is missing' do
      it 'returns bad request' do
        post "/v1/users/jobs/bulk_update",
             params: { fields: { priority: 1 } }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:bad_request)
      end
    end

    context 'when fields is missing' do
      it 'returns bad request' do
        post "/v1/users/jobs/bulk_update",
             params: { job_ids: jobs.map(&:id) }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:bad_request)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/jobs/bulk_update",
             params: { job_ids: jobs.map(&:id), fields: { priority: 1 } }.to_json

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
