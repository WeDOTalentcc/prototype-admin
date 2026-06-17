require 'rails_helper'

RSpec.describe V1::Users::ExperiencesController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }
  let(:occupation) { create(:occupation, account: account, user: user, name: 'Product Manager') }
  let(:company) { create(:company, account: account, user: user, name: 'microsoft') }

  describe 'GET /v1/users/experiences' do
    before do
      create(:experience, account: account, user: user, occupation: occupation, company: company, is_deleted: false)
      create(:experience, account: account, user: user, occupation: occupation, company: company, is_deleted: true)
      Experience.reindex(refresh: true)
    end

    it 'returns only non-deleted experiences' do
      get '/v1/users/experiences', headers: headers

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data'].size).to eq(1)
      expect(body['data'].first['attributes']['is_deleted']).to eq(false)
    end
  end

  describe 'GET /v1/users/experiences/:id' do
    let(:experience) { create(:experience, account: account, user: user, occupation: occupation, company: company) }

    it 'returns the experience' do
      get "/v1/users/experiences/#{experience.id}", headers: headers
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']['id']).to eq(experience.id.to_s)
    end

    it 'returns 404 when experience not found' do
      get "/v1/users/experiences/999999", headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /v1/users/experiences' do
    context 'with valid parameters using IDs' do
      let(:params) do
        {
          experience: {
            occupation_id: occupation.id,
            company_id: company.id,
            start_date: '2023-01-01',
            end_date: '2024-01-01',
            description: 'Great experience',
            contract_type: 'CLT',
            reference_type: 'Candidate',
            reference_id: 1
          }
        }
      end

      it 'creates an experience' do
        expect {
          post '/v1/users/experiences', params: params.to_json, headers: headers
          Experience.reindex(refresh: true)
        }.to change(Experience, :count).by(1)

        expect(response).to have_http_status(:created)
        body = JSON.parse(response.body)
        expect(body['data']['attributes']['description']).to eq('Great experience')
        expect(body['data']['attributes']['account_id']).to eq(account.id)
        expect(body['data']['attributes']['user_id']).to eq(user.id)
      end
    end

    context 'with valid parameters using names' do
      let(:params) do
        {
          experience: {
            company_name: 'Google',
            occupation_name: 'Software Engineer',
            start_date: '2023-01-01',
            description: 'Great experience at Google',
            contract_type: 'CLT',
            reference_type: 'Candidate',
            reference_id: 1
          }
        }
      end

      it 'creates an experience and finds/creates company and occupation' do
        expect {
          post '/v1/users/experiences', params: params.to_json, headers: headers
          Experience.reindex(refresh: true)
        }.to change(Experience, :count).by(1)
         .and change(Company, :count).by(1)
         .and change(Occupation, :count).by(1)

        expect(response).to have_http_status(:created)
        body = JSON.parse(response.body)

        experience = Experience.find(body['data']['id'])
        expect(experience.company.name).to eq('google')
        expect(experience.occupation.name).to eq('Software Engineer')
        expect(body['data']['attributes']['company_name']).to eq('google')
        expect(body['data']['attributes']['occupation_name']).to eq('Software Engineer')
      end

      it 'finds existing company and occupation by name' do
        existing_company = create(:company, name: 'google', account: account)
        existing_occupation = create(:occupation, name: 'Software Engineer', account: account)

        expect {
          post '/v1/users/experiences', params: params.to_json, headers: headers
          Experience.reindex(refresh: true)
        }.to change(Experience, :count).by(1)
         .and change(Company, :count).by(0)
         .and change(Occupation, :count).by(0)

        expect(response).to have_http_status(:created)
        body = JSON.parse(response.body)

        experience = Experience.find(body['data']['id'])
        expect(experience.company_id).to eq(existing_company.id)
        expect(experience.occupation_id).to eq(existing_occupation.id)
      end
    end

    context 'with invalid parameters' do
      let(:params) do
        {
          experience: {
            description: 'Missing required fields'
          }
        }
      end

      it 'returns validation errors' do
        expect {
          post '/v1/users/experiences', params: params.to_json, headers: headers
          Experience.reindex(refresh: true)
        }.not_to change(Experience, :count)

        expect(response).to have_http_status(:unprocessable_entity)
        body = JSON.parse(response.body)
        expect(body['errors']).to be_present
      end
    end
  end

  describe 'PUT /v1/users/experiences/:id' do
    let(:experience) { create(:experience, account: account, user: user, occupation: occupation, company: company) }

    context 'with valid parameters' do
      let(:params) do
        {
          experience: {
            description: 'Updated description',
            contract_type: 'PJ'
          }
        }
      end

      it 'updates the experience' do
        put "/v1/users/experiences/#{experience.id}", params: params.to_json, headers: headers
        Experience.reindex(refresh: true)
        expect(response).to have_http_status(:ok)

        body = JSON.parse(response.body)
        expect(body['data']['attributes']['description']).to eq('Updated description')
        expect(body['data']['attributes']['contract_type']).to eq('PJ')
      end
    end

    context 'with company_name and occupation_name' do
      let(:params) do
        {
          experience: {
            company_name: 'Microsoft',
            occupation_name: 'Product Manager'
          }
        }
      end

      it 'updates company and occupation by name' do
        expect {
          put "/v1/users/experiences/#{experience.id}", params: params.to_json, headers: headers
          Experience.reindex(refresh: true)
        }.to change(Company, :count).by(1)
         .and change(Occupation, :count).by(1)

        expect(response).to have_http_status(:ok)

        experience.reload
        expect(experience.company.name).to eq('microsoft')
        expect(experience.occupation.name).to eq('Product Manager')
      end
    end
  end

  describe 'DELETE /v1/users/experiences/:id' do
    let(:experience) { create(:experience, account: account, user: user, occupation: occupation, company: company) }

    it 'soft deletes the experience' do
      delete "/v1/users/experiences/#{experience.id}", headers: headers
      expect(response).to have_http_status(:ok)

      experience.reload
      expect(experience.is_deleted).to eq(true)

      body = JSON.parse(response.body)
      expect(body['data']['attributes']['is_deleted']).to eq(true)
    end
  end
end
