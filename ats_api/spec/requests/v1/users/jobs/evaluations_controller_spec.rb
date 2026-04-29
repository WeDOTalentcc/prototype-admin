# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs::Evaluations API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:authentication_headers) { auth_headers(user) }

  let!(:job) { create(:job, user: user, account: account) }
  let!(:other_job) { create(:job, user: user, account: account) }

  before do
    create(:evaluation, job: job, user: user, account: account, name: "Triagem Técnica")
    create(:evaluation, job: job, user: user, account: account, name: "Avaliação Comportamental")
    create(:evaluation, job: other_job, user: user, account: account, name: "Outra Avaliação")

    Evaluation.reindex
  end

  describe 'GET /v1/users/jobs/:job_id/evaluations' do
    context 'when authenticated' do
      it 'returns evaluations for the specific job' do
        get "/v1/users/jobs/#{job.id}/evaluations", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(2)
      end
    end

    context 'when job does not exist' do
      it 'returns not found' do
        get "/v1/users/jobs/999999/evaluations", headers: authentication_headers

        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/jobs/#{job.id}/evaluations"

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
