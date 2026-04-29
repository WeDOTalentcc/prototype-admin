# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::JobUsers API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:other_user) { create(:user) }

  let(:authentication_headers) { auth_headers(user) }
  let(:invalid_authentication_headers) { invalid_auth_headers }
  let(:no_authentication_headers) { no_auth_headers }

  describe 'GET /v1/users/job_users' do
    let!(:job) { create(:job, user: user, account: account) }
    let!(:user_job_users) { create_list(:job_user, 3, user: user, job: job, account: account) }
    let!(:other_job_users) { create_list(:job_user, 2, user: other_user, account: other_user.account) }

    before do
      JobUser.reindex
    end

    context 'when authenticated' do
      it 'returns all job_users' do
        get '/v1/users/job_users', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(5)
      end

      it 'filters by job_id' do
        params = { where: { job_id: job.id }.to_json }
        get '/v1/users/job_users', params: params, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/job_users', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/job_users/:id' do
    let!(:job) { create(:job, user: user, account: account) }
    let!(:job_user) { create(:job_user, user: user, job: job, account: account) }

    context 'when authenticated' do
      it 'returns the job_user' do
        get "/v1/users/job_users/#{job_user.id}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['id']).to eq(job_user.id.to_s)
        expect(json['data']['attributes']['user_id']).to eq(user.id)
        expect(json['data']['attributes']['job_id']).to eq(job.id)
      end

      it 'includes user information' do
        get "/v1/users/job_users/#{job_user.id}", headers: authentication_headers

        json = JSON.parse(response.body)
        expect(json['data']['attributes']['user_name']).to eq(user.name)
        expect(json['data']['attributes']['user_email']).to eq(user.email)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/job_users/#{job_user.id}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'when job_user does not exist' do
      it 'returns not found' do
        get "/v1/users/job_users/999999", headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'POST /v1/users/job_users' do
    let!(:job) { create(:job, user: user, account: account) }
    let!(:another_user) { create(:user, account: account) }

    let(:valid_attributes) do
      {
        job_user: {
          user_id: another_user.id,
          job_id: job.id,
          person_function: 'Senior Recruiter',
          split: 50.0
        }
      }
    end

    let(:invalid_attributes) do
      {
        job_user: {
          user_id: nil,
          job_id: job.id
        }
      }
    end

    context 'when authenticated with valid attributes' do
      it 'creates a new job_user' do
        post '/v1/users/job_users', params: valid_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['person_function']).to eq('Senior Recruiter')
        expect(json['data']['attributes']['split']).to eq(50.0)
        expect(json['data']['attributes']['account_id']).to eq(account.id)
      end

      it 'changes the job_user count by 1' do
        expect {
          post '/v1/users/job_users', params: valid_attributes.to_json, headers: authentication_headers
        }.to change(JobUser, :count).by(1)
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users/job_users', params: invalid_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'does not create a job_user' do
        expect {
          post '/v1/users/job_users', params: invalid_attributes.to_json, headers: authentication_headers
        }.not_to change(JobUser, :count)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post '/v1/users/job_users', params: valid_attributes.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/job_users/:id' do
    let!(:job) { create(:job, user: user, account: account) }
    let!(:job_user) { create(:job_user, user: user, job: job, account: account, person_function: 'Junior Recruiter', split: 30.0) }

    let(:valid_update_attributes) do
      {
        job_user: {
          person_function: 'Lead Recruiter',
          split: 70.0
        }
      }
    end

    let(:invalid_update_attributes) do
      {
        job_user: {
          split: 150.0
        }
      }
    end

    context 'when authenticated with valid attributes' do
      it 'updates the job_user' do
        put "/v1/users/job_users/#{job_user.id}", params: valid_update_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['person_function']).to eq('Lead Recruiter')
        expect(json['data']['attributes']['split']).to eq(70.0)
      end

      it 'persists the changes' do
        put "/v1/users/job_users/#{job_user.id}", params: valid_update_attributes.to_json, headers: authentication_headers

        job_user.reload
        expect(job_user.person_function).to eq('Lead Recruiter')
        expect(job_user.split).to eq(70.0)
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        put "/v1/users/job_users/#{job_user.id}", params: invalid_update_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        put "/v1/users/job_users/#{job_user.id}", params: valid_update_attributes.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'when job_user does not exist' do
      it 'returns not found' do
        put "/v1/users/job_users/999999", params: valid_update_attributes.to_json, headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'DELETE /v1/users/job_users/:id' do
    let!(:job) { create(:job, user: user, account: account) }
    let!(:job_user) { create(:job_user, user: user, job: job, account: account) }

    context 'when authenticated' do
      it 'deletes the job_user' do
        expect {
          delete "/v1/users/job_users/#{job_user.id}", headers: authentication_headers
        }.to change(JobUser, :count).by(-1)

        expect(response).to have_http_status(:ok)
      end

      it 'returns the deleted job_user' do
        delete "/v1/users/job_users/#{job_user.id}", headers: authentication_headers

        json = JSON.parse(response.body)
        expect(json['data']['id']).to eq(job_user.id.to_s)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/job_users/#{job_user.id}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end

      it 'does not delete the job_user' do
        expect {
          delete "/v1/users/job_users/#{job_user.id}", headers: no_authentication_headers
        }.not_to change(JobUser, :count)
      end
    end

    context 'when job_user does not exist' do
      it 'returns not found' do
        delete "/v1/users/job_users/999999", headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'Performance tests' do
    let!(:job) { create(:job, user: user, account: account) }

    it 'handles bulk creation efficiently' do
      job_users_data = 10.times.map do |i|
        {
          job_user: {
            user_id: user.id,
            job_id: job.id,
            person_function: "Recruiter #{i}",
            split: i * 10
          }
        }
      end

      start_time = Time.current

      job_users_data.each do |data|
        post '/v1/users/job_users', params: data.to_json, headers: authentication_headers
      end

      elapsed_time = Time.current - start_time

      expect(JobUser.where(job_id: job.id).count).to eq(10)
      expect(elapsed_time).to be < 5.seconds
    end

    it 'index endpoint performs well with many records' do
      create_list(:job_user, 50, user: user, job: job, account: account)
      JobUser.reindex

      start_time = Time.current
      get '/v1/users/job_users', headers: authentication_headers
      elapsed_time = Time.current - start_time

      expect(response).to have_http_status(:ok)
      expect(elapsed_time).to be < 2.seconds
    end
  end

  describe 'Edge cases' do
    let!(:job) { create(:job, user: user, account: account) }

    it 'handles split at boundary values' do
      job_user_zero = create(:job_user, user: user, job: job, account: account, split: 0)
      job_user_hundred = create(:job_user, user: user, job: job, account: account, split: 100)

      expect(job_user_zero).to be_valid
      expect(job_user_hundred).to be_valid
    end

    it 'allows multiple users for same job' do
      user1 = create(:user, account: account)
      user2 = create(:user, account: account)

      job_user1 = create(:job_user, user: user1, job: job, account: account, split: 50)
      job_user2 = create(:job_user, user: user2, job: job, account: account, split: 50)

      expect(JobUser.where(job_id: job.id).count).to eq(2)
    end
  end
end
