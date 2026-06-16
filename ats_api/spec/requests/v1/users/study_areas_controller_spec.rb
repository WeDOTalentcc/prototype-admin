# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::StudyAreas API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  let(:authentication_headers) { auth_headers(user) }

  describe 'GET /v1/users/study_areas' do
    let!(:study_areas) { create_list(:study_area, 3, account: account) }
    let!(:other_study_area) { create(:study_area) }

    before do
      StudyArea.reindex
      get '/v1/users/study_areas', headers: authentication_headers
    end

    it 'returns a successful response' do
      expect(response).to have_http_status(:ok)
    end

    it 'returns all study areas' do
      json = JSON.parse(response.body)
      expect(json['data'].size).to eq(4)
    end
  end

  describe 'GET /v1/users/study_areas/:id' do
    let!(:study_area) { create(:study_area, account: account) }

    before do
      get "/v1/users/study_areas/#{study_area.id}", headers: authentication_headers
    end

    it 'returns the study area data' do
      json = JSON.parse(response.body)
      expect(json['data']['id']).to eq(study_area.id.to_s)
      expect(json['data']['attributes']['name']).to eq(study_area.name)
    end
  end

  describe 'POST /v1/users/study_areas' do
    let(:valid_params) do
      {
        study_area: {
          name: 'Engenharia de Software',
          account_id: account.id
        }
      }
    end

    it 'creates a new study area' do
      expect {
        post '/v1/users/study_areas', params: valid_params, headers: authentication_headers, as: :json
      }.to change(StudyArea, :count).by(1)
      expect(response).to have_http_status(:created)
    end
  end

  describe 'PUT /v1/users/study_areas/:id' do
    let!(:study_area) { create(:study_area, account: account) }
    let(:valid_params) { { study_area: { name: 'Ciência da Computação' } } }

    before do
      put "/v1/users/study_areas/#{study_area.id}", params: valid_params, headers: authentication_headers, as: :json
    end

    it 'updates the study area' do
      expect(response).to have_http_status(:ok)
      study_area.reload
      expect(study_area.name).to eq('Ciência da Computação')
    end
  end

  describe 'DELETE /v1/users/study_areas/:id' do
    let!(:study_area) { create(:study_area, account: account) }

    it 'deletes the study area' do
      expect {
        delete "/v1/users/study_areas/#{study_area.id}", headers: authentication_headers
      }.to change(StudyArea, :count).by(-1)
      expect(response).to have_http_status(:ok)
    end
  end
end
