# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs#export API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  let!(:job) { create(:job, user: user, account: account, title: "Full Stack Developer") }

  before do
    JobStatus.create_default_statuses
    job.update!(job_status: JobStatus.find_by(name: "Ativa"))
  end

  describe 'GET /v1/users/jobs/:id/export' do
    context 'CSV export' do
      it 'returns a CSV file' do
        get "/v1/users/jobs/#{job.id}/export",
            params: { format: "csv" },
            headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(response.content_type).to include("text/csv")
        expect(response.body).to include("Full Stack Developer")
      end
    end

    context 'PDF export' do
      it 'returns a PDF file' do
        get "/v1/users/jobs/#{job.id}/export",
            params: { format: "pdf" },
            headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(response.content_type).to include("application/pdf")
      end
    end

    context 'default format (CSV)' do
      it 'returns CSV by default' do
        get "/v1/users/jobs/#{job.id}/export",
            headers: authentication_headers

        expect(response).to have_http_status(:ok)
        expect(response.content_type).to include("text/csv")
      end
    end

    context 'when job does not exist' do
      it 'returns not found' do
        get "/v1/users/jobs/999999/export",
            headers: authentication_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/jobs/#{job.id}/export"

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
