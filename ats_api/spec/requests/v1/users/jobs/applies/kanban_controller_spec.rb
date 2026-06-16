# spec/requests/v1/users/jobs/kanban_spec.rb
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs::Kanban API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:job) { create(:job, user: user, account: account) }

  let!(:stage1) { create(:selective_process, job: job, name: 'Triagem', position: 1) }
  let!(:stage2) { create(:selective_process, job: job, name: 'Entrevista RH', position: 2) }
  let!(:stage3) { create(:selective_process, job: job, name: 'Entrevista Técnica', position: 3) }

  let!(:candidate1) { create(:candidate, account: account) }
  let!(:candidate2) { create(:candidate, account: account) }
  let!(:candidate3) { create(:candidate, account: account) }

  let!(:apply1) { create(:apply, job: job, candidate: candidate1, selective_process: stage1, account: account) }
  let!(:apply2) { create(:apply, job: job, candidate: candidate2, selective_process: stage2, account: account) }
  let!(:apply3) { create(:apply, job: job, candidate: candidate3, selective_process: stage3, account: account) }

  let(:authentication_headers) { auth_headers(user) }

  before do
    Apply.reindex
  end

  describe 'GET /v1/users/jobs/:job_id/kanban' do
    context 'when authenticated' do
      before do
        get "/v1/users/jobs/#{job.id}/kanban", headers: authentication_headers
      end

      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns the correct kanban structure' do
        json = JSON.parse(response.body)

        expect(json['data']['job_id']).to eq(job.id)
        expect(json['data']['job_title']).to eq(job.title)
      end

      it 'returns the correct data inside columns' do
        json = JSON.parse(response.body)

        triagem_column = json['data']['columns'].find { |c| c['selective_process_id'] == stage1.id }

        expect(triagem_column['applies']).to have_key('records')
        expect(triagem_column['applies']).to have_key('total_count')

        technical_column = json['data']['columns'].find { |c| c['selective_process_id'] == stage3.id }

        expect(technical_column['selective_process_title']).to eq('Entrevista Técnica')
        expect(technical_column['applies']['records'].size).to eq(1)

        rh_column = json['data']['columns'].find { |c| c['selective_process_id'] == stage2.id }
        expect(rh_column['selective_process_title']).to eq('Entrevista RH')
        expect(rh_column['applies']['records'].size).to eq(1)
      end

      context 'when filtering by a specific selective_process_id' do
        it 'returns only the specified column' do
          get "/v1/users/jobs/#{job.id}/kanban", params: { selective_process_id: stage2.id }, headers: authentication_headers

          json = JSON.parse(response.body)

          expect(response).to have_http_status(:ok)
          expect(json['data']['columns'].size).to eq(1)
          expect(json['data']['columns'][0]['selective_process_id']).to eq(stage2.id)
        end
      end
    end

    context 'when not authenticated' do
      it 'returns an unauthorized status' do
        get "/v1/users/jobs/#{job.id}/kanban"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
