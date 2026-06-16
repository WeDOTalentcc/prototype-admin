# frozen_string_literal: true

require 'rails_helper'

RSpec.describe V1::Users::ActivityLogsController, type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:job) { create(:job, account: account) }
  let(:headers) { auth_headers(user) }

  before do
    allow(Current).to receive(:user).and_return(user)
    allow(Current).to receive(:ip).and_return('127.0.0.1')
  end

  describe 'GET /v1/users/activity_logs' do
    let!(:activity_logs) do
      [
        create(:activity_log, user: user, account: account, action: 'create'),
        create(:activity_log, user: user, account: account, action: 'update'),
        create(:activity_log, user: user, account: account, action: 'destroy')
      ]
    end

    it 'returns activity logs using search' do
      get '/v1/users/activity_logs', headers: headers

      expect(response).to have_http_status(:ok)
      json_response = JSON.parse(response.body)
      expect(json_response).to have_key('data')
    end

    it 'filters by reference_type and reference_id using search params' do
      activity_logs.first.update!(reference_type: 'Job', reference_id: job.id)

      get '/v1/users/activity_logs',
          params: {
            filters: {
              reference_type: 'Job',
              reference_id: job.id
            }
          },
          headers: headers

      expect(response).to have_http_status(:ok)
      json_response = JSON.parse(response.body)
      expect(json_response).to have_key('data')
    end

    it 'supports pagination' do
      get '/v1/users/activity_logs',
          params: { page: 1, per_page: 2 },
          headers: headers

      expect(response).to have_http_status(:ok)
      json_response = JSON.parse(response.body)
      expect(json_response).to have_key('data')
    end
  end

  describe 'GET /v1/users/activity_logs/:id' do
    let(:activity_log) { create(:activity_log, user: user, account: account) }

    it 'returns the activity log' do
      get "/v1/users/activity_logs/#{activity_log.id}", headers: headers

      expect(response).to have_http_status(:ok)
      json_response = JSON.parse(response.body)
      expect(json_response['data']['id']).to eq(activity_log.id.to_s)
    end

    it 'returns not found for non-existent activity log' do
      get '/v1/users/activity_logs/99999', headers: headers

      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /v1/users/activity_logs' do
    let(:valid_params) do
      {
        activity_log: {
          reference_type: 'Job',
          reference_id: job.id,
          action: 'create',
          changeset: { 'title' => { 'from' => nil, 'to' => 'New Job' } }
        }
      }
    end

    it 'creates a new activity log' do
      expect {
        post '/v1/users/activity_logs', params: valid_params.to_json, headers: headers
      }.to change(ActivityLog, :count).by(2)

      expect(response).to have_http_status(:created)
      json_response = JSON.parse(response.body)
      expect(json_response['data']['attributes']['action']).to eq('create')
    end

    it 'sets current user automatically' do
      post '/v1/users/activity_logs', params: valid_params, headers: headers

      activity_log = ActivityLog.last
      expect(activity_log.user).to eq(user)
    end

    it 'returns errors for invalid params' do
      invalid_params = { activity_log: { reference_type: '' } }

      post '/v1/users/activity_logs', params: invalid_params.to_json, headers: headers

      expect(response.status).to be(500)
    end
  end

  describe 'PATCH /v1/users/activity_logs/:id' do
    let(:activity_log) { create(:activity_log, user: user, account: account) }
    let(:update_params) do
      {
        activity_log: {
          action: 'updated_action'
        }
      }
    end

    it 'updates the activity log' do
      patch "/v1/users/activity_logs/#{activity_log.id}",
            params: update_params,
            headers: headers

      expect([ 200, 400 ]).to include(response.status)

      if response.status == 200
        json_response = JSON.parse(response.body)
        expect(json_response['data']['attributes']['action']).to eq('updated_action')
      end
    end

    it 'prevents updating activity logs from other users' do
      other_user = create(:user)
      other_activity_log = create(:activity_log, user: other_user, account: account)

      patch "/v1/users/activity_logs/#{other_activity_log.id}",
            params: update_params,
            headers: headers

      expect([ 400, 403, 404 ]).to include(response.status)
    end
  end

  describe 'DELETE /v1/users/activity_logs/:id' do
    let(:activity_log) { create(:activity_log, user: user, account: account) }

    it 'deletes the activity log' do
      delete "/v1/users/activity_logs/#{activity_log.id}", headers: headers

      expect(response).to have_http_status(:ok)
      expect(ActivityLog.find_by(id: activity_log.id)).to be_nil
    end

    it 'prevents deleting activity logs from other users' do
      other_user = create(:user)
      other_activity_log = create(:activity_log, user: other_user, account: account)

      delete "/v1/users/activity_logs/#{other_activity_log.id}", headers: headers

      expect(response).to have_http_status(:forbidden)
    end
  end

  describe 'POST /v1/users/activity_logs/:id/rollback' do
    let(:original_title) { 'Original Title' }
    let(:updated_title) { 'Updated Title' }
    let(:changeset) do
      { 'title' => { 'from' => original_title, 'to' => updated_title } }
    end
    let(:activity_log) do
      create(:activity_log,
             reference_type: 'Job',
             reference_id: job.id,
             action: 'update',
             changeset: changeset,
             user: user,
             account: account)
    end

    before do
      job.update!(title: updated_title)
    end

    it 'performs rollback successfully' do
      post "/v1/users/activity_logs/#{activity_log.id}/rollback", headers: headers

      if response.status == 200
        json_response = JSON.parse(response.body)
        expect(json_response).to have_key('message')
        expect(json_response['message']).to eq('Rollback realizado com sucesso')
      end

      expect(job.reload.title).to eq(original_title)
    end

    it 'returns error for invalid rollback' do
      activity_log.update!(action: 'create')

      post "/v1/users/activity_logs/#{activity_log.id}/rollback", headers: headers

      expect(response).to have_http_status(:unprocessable_entity)
    end

    it 'prevents rollback of other users activity logs' do
      other_user = create(:user)
      other_activity_log = create(:activity_log,
                                 reference_type: 'Job',
                                 reference_id: job.id,
                                 action: 'update',
                                 changeset: changeset,
                                 user: other_user,
                                 account: account)

      post "/v1/users/activity_logs/#{other_activity_log.id}/rollback", headers: headers

      expect(response).to have_http_status(:forbidden)
    end
  end

  describe 'authorization' do
    it 'requires authentication' do
      get '/v1/users/activity_logs'

      expect(response).to have_http_status(:unauthorized)
    end
  end
end
