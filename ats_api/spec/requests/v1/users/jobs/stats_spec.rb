# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs#stats API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  before do
    JobStatus.create_default_statuses
    active_status = JobStatus.find_by(name: "Ativa")
    closed_status = JobStatus.find_by(name: "Fechada (preenchida)")

    create_list(:job, 3, user: user, account: account, job_status: active_status)
    create_list(:job, 2, user: user, account: account, job_status: closed_status)
  end

  describe 'GET /v1/users/jobs/stats' do
    context 'when authenticated' do
      it 'returns global statistics' do
        get "/v1/users/jobs/stats", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['success']).to be true
        expect(json['data']['by_status']).to be_an(Array)
        expect(json['data']['open_vs_closed']).to be_a(Hash)
        expect(json['data']['totals']).to be_a(Hash)
        expect(json['data']['totals']['total']).to eq(5)
      end
    end

    context 'with date range' do
      it 'accepts start_date and end_date' do
        get "/v1/users/jobs/stats",
            params: { start_date: 30.days.ago.to_date.to_s, end_date: Date.current.to_s },
            headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['period']['start_date']).to be_present
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/jobs/stats"

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
