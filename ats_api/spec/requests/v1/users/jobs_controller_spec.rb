# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:other_user) { create(:user) }

  let(:authentication_headers) { auth_headers(user) }
  let(:invalid_authentication_headers) { { 'Authorization' => 'Bearer invalid_token' } }
  let(:no_authentication_headers) { {} }

  describe 'GET /v1/users/jobs' do
    let!(:user_jobs) { create_list(:job, 3, user: user, account: user.account) }
    let!(:other_jobs) { create_list(:job, 2, user: other_user, account: other_user.account) }

    before do
      Job.reindex
    end

    context 'when authenticated' do
      it 'returns all jobs' do
        get '/v1/users/jobs', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(5)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/jobs', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/jobs/:id' do
    let!(:job) { create(:job, user: user, account: user.account) }

    context 'when authenticated' do
      it 'returns the job' do
        get "/v1/users/jobs/#{job.id}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['id']).to eq(job.id.to_s)
        expect(json['data']['attributes']['title']).to eq(job.title)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/jobs/#{job.id}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/jobs' do
    let(:valid_attributes) { { job: { title: 'New Senior Developer Job', description: 'A great job opportunity.' } } }
    let(:invalid_attributes) { { job: { title: '' } } }

    context 'when authenticated with valid attributes' do
      it 'creates a new job' do
        post '/v1/users/jobs', params: valid_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['title']).to eq('New Senior Developer Job')
        expect(json['data']['attributes']['user_id']).to eq(user.id)
        expect(json['data']['attributes']['account_id']).to eq(user.account.id)
      end

      it 'changes the job count by 1' do
        expect {
          post '/v1/users/jobs', params: valid_attributes.to_json, headers: authentication_headers
        }.to change(Job, :count).by(1)
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns an unprocessable entity status' do
        post '/v1/users/jobs', params: invalid_attributes.to_json, headers: authentication_headers
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post '/v1/users/jobs', params: valid_attributes.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/jobs/:id' do
    let!(:job) { create(:job, user: user, account: user.account) }
    let!(:other_user_job) { create(:job, user: other_user, account: other_user.account) }
    let(:new_attributes) { { job: { title: 'Updated Job Title' } } }

    context 'when authenticated and updating their own job' do
      it 'updates the job' do
        put "/v1/users/jobs/#{job.id}", params: new_attributes.to_json, headers: authentication_headers

        job.reload
        expect(response).to have_http_status(:ok)
        expect(job.title).to eq('Updated Job Title')
      end

      it 'permits only known keys on jd_quality_score and drops unknown nested keys' do
        payload = {
          job: {
            title: job.title,
            jd_quality_score: {
              score: 90,
              status: 'excellent',
              evaluated_at: '2026-03-31T11:24:07Z',
              evil_injection: 'rejected',
              dimensions: [
                {
                  score: 10,
                  status: 'ok',
                  finding: 'Título: Example',
                  dimension: 'title_clarity',
                  max_score: 10,
                  extra_dimension: 'rejected'
                }
              ]
            }
          }
        }
        put "/v1/users/jobs/#{job.id}", params: payload.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        job.reload
        expect(job.jd_quality_score['evil_injection']).to be_nil
        expect(job.jd_quality_score['dimensions'].first['extra_dimension']).to be_nil
        expect(job.jd_quality_score['score']).to eq(90)
        expect(job.jd_quality_score['dimensions'].first['dimension']).to eq('title_clarity')
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        put "/v1/users/jobs/#{job.id}", params: new_attributes.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/jobs/:id' do
    let!(:job) { create(:job, user: user, account: user.account) }
    let!(:other_user_job) { create(:job, user: other_user, account: other_user.account) }

    context 'when authenticated and deleting their own job' do
      xit 'deletes the job (pending - investigate delete behavior)' do
        expect {
          delete "/v1/users/jobs/#{job.id}", headers: authentication_headers
        }.to change(Job, :count).by(-1)
      end

      xit 'returns an ok status (pending - investigate delete behavior)' do
        delete "/v1/users/jobs/#{job.id}", headers: authentication_headers
        expect(response).to have_http_status(:ok)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/jobs/#{job.id}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/jobs with virtual remuneration attributes' do
    context 'with salary_from and salary_to' do
      let(:job_with_salary) do
        {
          job: {
            title: 'Developer with Salary Range',
            description: 'Test job with salary',
            salary_from: 5000,
            salary_to: 8000,
            salary_currency: 'BRL',
            salary_period: 'monthly',
            salary_contract_type: 'CLT'
          }
        }
      end

      it 'creates job with salary remuneration relationships' do
        post '/v1/users/jobs', params: job_with_salary.to_json, headers: authentication_headers

        expect(response).to have_http_status(:created)

        job = Job.last
        relationships = job.remuneration_relationships.where(is_deleted: false)
        expect(relationships.count).to eq(2)

        salary_from = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (De)' })
        expect(salary_from.value).to eq(5000.0)
        expect(salary_from.currency).to eq('BRL')
        expect(salary_from.contract_type).to eq('CLT')

        salary_to = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (Até)' })
        expect(salary_to.value).to eq(8000.0)
      end

      it 'returns salary attributes in response' do
        post '/v1/users/jobs', params: job_with_salary.to_json, headers: authentication_headers

        json = JSON.parse(response.body)
        attributes = json['data']['attributes']

        expect(attributes['salary_from']).to eq(5000.0)
        expect(attributes['salary_to']).to eq(8000.0)
        expect(attributes['salary_currency']).to eq('BRL')
        expect(attributes['salary_period']).to eq('monthly')
        expect(attributes['salary_contract_type']).to eq('CLT')
      end
    end

    context 'with multiple remuneration types' do
      let(:job_with_all_remunerations) do
        {
          job: {
            title: 'Full Package Job',
            description: 'Job with all remuneration types',
            salary_from: 5000,
            salary_to: 8000,
            salary_currency: 'BRL',
            commission_from: 1000,
            commission_to: 2000,
            commission_currency: 'USD',
            bonus_from: 3000,
            bonus_to: 5000,
            bonus_currency: 'EUR'
          }
        }
      end

      it 'creates all remuneration types' do
        post '/v1/users/jobs', params: job_with_all_remunerations.to_json, headers: authentication_headers

        expect(response).to have_http_status(:created)

        job = Job.last
        relationships = job.remuneration_relationships.where(is_deleted: false)
        expect(relationships.count).to eq(6)

        remuneration_names = relationships.joins(:remuneration).pluck('remunerations.name')
        expect(remuneration_names).to include('Salário (De)', 'Salário (Até)')
        expect(remuneration_names).to include('Comissão (De)', 'Comissão (Até)')
        expect(remuneration_names).to include('Pacote de Bônus (De)', 'Pacote de Bônus (Até)')
      end
    end
  end

  describe 'PUT /v1/users/jobs/:id with virtual remuneration attributes' do
    let!(:job) { create(:job, user: user, account: user.account) }

    context 'updating salary values' do
      before do
        job.salary_from = 4000
        job.salary_to = 6000
        job.save!
      end

      let(:updated_salary) do
        {
          job: {
            salary_from: 6000,
            salary_to: 9000,
            salary_currency: 'USD'
          }
        }
      end

      it 'updates existing relationships without creating duplicates' do
        initial_count = job.remuneration_relationships.count

        put "/v1/users/jobs/#{job.id}", params: updated_salary.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)

        job.reload
        expect(job.remuneration_relationships.count).to eq(initial_count)

        relationships = job.remuneration_relationships.where(is_deleted: false)
        salary_from = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (De)' })
        expect(salary_from.value).to eq(6000.0)
        expect(salary_from.currency).to eq('USD')

        salary_to = relationships.joins(:remuneration).find_by(remunerations: { name: 'Salário (Até)' })
        expect(salary_to.value).to eq(9000.0)
      end
    end

    context 'removing salary values' do
      before do
        job.salary_from = 5000
        job.salary_to = 8000
        job.save!
      end

      let(:remove_salary) do
        {
          job: {
            salary_from: nil,
            salary_to: nil
          }
        }
      end

      it 'soft deletes the relationships' do
        put "/v1/users/jobs/#{job.id}", params: remove_salary.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)

        job.reload
        active_relationships = job.remuneration_relationships.where(is_deleted: false)
        salary_relationships = active_relationships.joins(:remuneration)
          .where(remunerations: { name: [ 'Salário (De)', 'Salário (Até)' ] })

        expect(salary_relationships.count).to eq(0)
      end
    end

    context 'adding new remuneration types to existing job' do
      let(:add_commission) do
        {
          job: {
            commission_from: 1000,
            commission_to: 3000,
            commission_currency: 'BRL'
          }
        }
      end

      it 'adds commission without affecting existing data' do
        put "/v1/users/jobs/#{job.id}", params: add_commission.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)

        job.reload
        relationships = job.remuneration_relationships.where(is_deleted: false)

        commission_from = relationships.joins(:remuneration).find_by(remunerations: { name: 'Comissão (De)' })
        expect(commission_from.value).to eq(1000.0)

        commission_to = relationships.joins(:remuneration).find_by(remunerations: { name: 'Comissão (Até)' })
        expect(commission_to.value).to eq(3000.0)
      end
    end
  end
end
