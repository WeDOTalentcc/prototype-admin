require 'rails_helper'

RSpec.describe V1::Users::CompaniesController, type: :request do
  let(:account) { create(:account) }
  let(:user)    { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe 'GET /v1/users/companies' do
    before do
      create(:company, name: 'visible', is_deleted: false, account: account)
      create(:company, name: 'deleted', is_deleted: true, account: account)
      Company.reindex(refresh: true)
    end

    it 'returns only non-deleted companies' do
      get '/v1/users/companies', headers: headers
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data'].map { |c| c['attributes']['name'] }).to include('visible')
      expect(body['data'].map { |c| c['attributes']['name'] }).not_to include('deleted')
    end
  end

  describe 'GET /v1/users/companies/:id' do
    let(:company) { create(:company, account: account) }

    it 'returns the company' do
      get "/v1/users/companies/#{company.id}", headers: headers
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']['id']).to eq(company.id.to_s)
    end
  end

  describe 'POST /v1/users/companies' do
    let(:valid_params) do
      {
        company: {
          name: 'NewCo',
          linkedin_url: 'https://linkedin.com/newco'
        }
      }
    end

    it 'creates a company' do
      expect {
        post '/v1/users/companies', params: valid_params.to_json, headers: headers
        Company.reindex(refresh: true)
      }.to change(Company, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(JSON.parse(response.body)['data']['attributes']['name']).to eq('newco')
    end

    it 'returns existing company if name already exists for account' do
      existing = create(:company, name: 'newco', account: account)
      Company.reindex(refresh: true)

      expect {
        post '/v1/users/companies', params: valid_params.to_json, headers: headers
        Company.reindex(refresh: true)
      }.not_to change(Company, :count)

      expect(response).to have_http_status(:ok)
      expect(JSON.parse(response.body)['data']['id']).to eq(existing.id.to_s)
    end

    it 'attaches logo if present' do
      file = fixture_file_upload(Rails.root.join('spec/support/assets/test_image.png'), 'image/png')
      params = {
        company: {
          name: 'NewCoLogo',
          linkedin_url: 'https://linkedin.com/company/newcologo',
          logo: file
        }
      }

      post '/v1/users/companies', params: params, headers: headers
      expect(response).to have_http_status(:created)

      company = Company.last
      expect(company.logo).to be_attached
    end
  end

  describe 'PUT /v1/users/companies/:id' do
    let(:company) { create(:company, account: account, name: 'OldName') }

    it 'updates the company' do
      put "/v1/users/companies/#{company.id}", params: {
        company: { name: 'UpdatedName' }
      }.to_json, headers: headers

      expect(response).to have_http_status(:ok)
      expect(company.reload.name).to eq('updatedname')
    end
  end

  describe 'DELETE /v1/users/companies/:id' do
    let(:company) { create(:company, account: account) }

    it 'soft deletes the company' do
      delete "/v1/users/companies/#{company.id}", headers: headers
      expect(response).to have_http_status(:ok)
      expect(company.reload.is_deleted).to be true
    end
  end
end
