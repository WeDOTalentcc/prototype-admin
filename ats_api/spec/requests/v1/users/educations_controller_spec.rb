# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Educations API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:candidate) { create(:candidate, account: account) }

  let(:authentication_headers) { auth_headers(user) }

  describe 'GET /v1/users/educations' do
    let!(:educations) { create_list(:education, 3, candidate: candidate, account: account) }

    before do
      Education.reindex
      get '/v1/users/educations', headers: authentication_headers
    end

    it 'returns all educations' do
      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data'].size).to eq(3)
    end
  end

  describe 'POST /v1/users/educations' do
    context 'with IDs' do
      let(:institution) { create(:institution, account: account) }
      let(:study_area) { create(:study_area, account: account) }
      let(:valid_params) do
        {
          education: {
            candidate_id: candidate.id,
            institution_id: institution.id,
            study_area_id: study_area.id
          }
        }
      end

      it 'creates a new education using IDs' do
        expect {
          post '/v1/users/educations', params: valid_params, headers: authentication_headers, as: :json
        }.to change(Education, :count).by(1)
        expect(response).to have_http_status(:created)
        expect(Education.last.institution).to eq(institution)
      end
    end

    context 'with names' do
      let(:valid_params_with_names) do
        {
          education: {
            candidate_id: candidate.id,
            institution_name: 'Nova Faculdade Pelo Nome',
            study_area_name: 'Nova Área Pelo Nome'
          }
        }
      end

      it 'creates a new education and new associations by name' do
        expect {
          post '/v1/users/educations', params: valid_params_with_names, headers: authentication_headers, as: :json
        }.to change(Education, :count).by(1)
         .and change(Institution, :count).by(1)
         .and change(StudyArea, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(Institution.last.name).to eq('Nova Faculdade Pelo Nome')
        expect(StudyArea.last.name).to eq('Nova Área Pelo Nome')
      end
    end
  end

  describe 'PUT /v1/users/educations/:id' do
    let!(:education) { create(:education, candidate: candidate, account: account) }
    let(:new_institution) { create(:institution, name: 'Outra Instituição', account: account) }
    let(:valid_params) do
      {
        education: {
          institution_id: new_institution.id,
          study_area_name: 'Área de Estudo Atualizada'
        }
      }
    end

    it 'updates the education record' do
      expect {
        put "/v1/users/educations/#{education.id}", params: valid_params, headers: authentication_headers, as: :json
      }.to change(StudyArea, :count).by(1) # Creates a new study area

      expect(response).to have_http_status(:ok)
      education.reload
      expect(education.institution).to eq(new_institution)
      expect(education.study_area.name).to eq('Área de Estudo Atualizada')
    end
  end

  describe 'DELETE /v1/users/educations/:id' do
    let!(:education) { create(:education, candidate: candidate, account: account) }

    it 'deletes the education record' do
      expect {
        delete "/v1/users/educations/#{education.id}", headers: authentication_headers
      }.to change(Education, :count).by(-1)
      expect(response).to have_http_status(:ok)
    end
  end
end
