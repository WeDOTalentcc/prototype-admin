require 'rails_helper'

RSpec.describe 'V1::Users::DataFiles API', type: :request do
  let!(:user) do
    account = create(:account)
    create(:user, account: account)
  end
  let!(:other_user) { create(:user) }


  let(:authentication_headers) { auth_headers(user) }
  let(:unauthorized_headers) { {} }
  let(:file_upload) do
    Rack::Test::UploadedFile.new(
      Rails.root.join('spec/support/assets/example.pdf'),
      'application/pdf'
    )
  end

  describe 'GET /v1/users/data_files' do
    # Current.user = user
    let!(:user_files) { create_list(:data_file, 3, user: user) }
    let!(:other_user_files) { create_list(:data_file, 2, user: other_user) }

    before do
      Current.user = user
      DataFile.reindex
      get '/v1/users/data_files', headers: authentication_headers
    end

    it 'returns a success status' do
      expect(response).to have_http_status(:ok)
    end

    it 'returns only the data files belonging to the current user' do
      json = JSON.parse(response.body)
      expect(json['data'].size).to eq(3)
      expect(json['data'].map { |d| d['id'].to_i }).to match_array(user_files.map(&:id))
    end
  end

  describe 'GET /v1/users/data_files/:id' do
    let!(:data_file) { create(:data_file, user:) }

    context 'when authenticated' do
      it 'returns the data file' do
        get "/v1/users/data_files/#{data_file.id}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['id'].to_i).to eq(data_file.id)
        expect(json['data']['attributes']['name']).to eq(data_file.name)
      end
    end

    context 'when requesting another user\'s file' do
      let!(:other_file) { create(:data_file, user: other_user) }
      it 'returns a not found status' do
        get "/v1/users/data_files/#{other_file.id}", headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'POST /v1/users/data_files' do
    let(:valid_attributes) do
      {
        data_file: {
          name: 'Curriculo Novo.pdf',
          reference_type: 'Candidate',
          reference_id: 1,
          file: file_upload
        }
      }
    end

    let(:invalid_attributes) do
      {
        data_file: {
          name: '', # nome inválido
          reference_type: 'User',
          reference_id: 1,
          file: file_upload
        }
      }
    end

    context 'with valid parameters' do
      it 'creates a new DataFile' do
        expect {
          post '/v1/users/data_files', params: valid_attributes, headers: authentication_headers
        }.to change(DataFile, :count).by(1)
      end

      it 'returns a created status and the file URL' do
        post '/v1/users/data_files', params: valid_attributes, headers: authentication_headers

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)
        expect(json['message']).to eq('File uploaded successfully')
        expect(json['url']).to include('example.pdf')
      end
    end

    context 'with invalid parameters' do
      it 'does not create a new DataFile' do
        expect {
          post '/v1/users/data_files', params: invalid_attributes, headers: authentication_headers
        }.not_to change(DataFile, :count)
      end

      it 'returns an unprocessable entity status' do
        post '/v1/users/data_files', params: invalid_attributes, headers: authentication_headers
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when avoiding duplicates' do
      let!(:existing_file) { create(:data_file, name: 'Curriculo.pdf', reference_type: 'Candidate', reference_id: 1, user:) }
      let(:duplicate_attributes) do
        {
          data_file: {
            name: 'Curriculo.pdf',
            reference_type: 'Candidate',
            reference_id: 1,
            file_type: 'application/pdf',
            file: file_upload,
            avoid_duplicate: 'true'
          }
        }
      end

      it 'updates the existing file instead of creating a new one' do
         expect {
          post '/v1/users/data_files', params: duplicate_attributes, headers: authentication_headers
        }.not_to change(DataFile, :count)
      end

      it 'returns an ok status with an updated message' do
        post '/v1/users/data_files', params: duplicate_attributes, headers: authentication_headers
        expect(response).to have_http_status(:ok)
        expect(JSON.parse(response.body)['message']).to eq('File updated successfully')
      end
    end
  end

  describe 'PUT /v1/users/data_files/:id' do
    let!(:data_file) { create(:data_file, user:) }
    let(:new_attributes) { { data_file: { name: 'Nome Atualizado.pdf' } } }

    it 'updates the requested data_file' do
      put "/v1/users/data_files/#{data_file.id}",
          params: new_attributes.to_json,
          headers: authentication_headers.merge({ 'Content-Type' => 'application/json' })

      data_file.reload
      expect(data_file.name).to eq('Nome Atualizado.pdf')
      expect(response).to have_http_status(:ok)
    end
  end


  describe 'DELETE /v1/users/data_files/:id' do
    let!(:data_file) { create(:data_file, user:) }

    it 'destroys the requested data_file' do
      expect {
        delete "/v1/users/data_files/#{data_file.id}", headers: authentication_headers
      }.to change(DataFile, :count).by(-1)
    end

    it 'returns a no content status' do
      delete "/v1/users/data_files/#{data_file.id}", headers: authentication_headers
      expect(response).to have_http_status(:no_content)
    end
  end
end
