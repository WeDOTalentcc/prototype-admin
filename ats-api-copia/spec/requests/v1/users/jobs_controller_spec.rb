# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Jobs API', type: :request do
  let(:user) { create(:user) }
  let(:other_user) { create(:user) }

  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token', 'Content-Type' => 'application/json' } }
  let(:no_auth_headers) { { 'Content-Type' => 'application/json' } }

  def jwt_encode(payload, exp = 24.hours.from_now)
    payload[:exp] = exp.to_i
    JWT.encode(payload, Rails.application.secret_key_base)
  end

  describe 'GET /v1/users/jobs' do
    before do
      Current.user = user
      create_list(:job, 3, user: user)
      create_list(:job, 2, user: other_user)
      Job.reindex
    end

    context 'quando autenticado' do
      it 'retorna TODOS os jobs no sistema' do
        get '/v1/users/jobs', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(5)
      end
    end

    context 'quando não autenticado' do
      it 'retorna não autorizado' do
        get '/v1/users/jobs', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'com token inválido' do
      it 'retorna não autorizado' do
        get '/v1/users/jobs', headers: invalid_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/jobs/:id' do
    let!(:job) { create(:job, user: user) }
    let!(:other_job) { create(:job, user: other_user) }

    context 'quando autenticado e acessando seu próprio job' do
      it 'retorna o job' do
        get "/v1/users/jobs/#{job.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['id']).to eq(job.id)
        expect(json['title']).to eq(job.title)
      end
    end

    context 'quando autenticado e acessando job de outro usuário' do
      it 'retorna o job' do
        get "/v1/users/jobs/#{other_job.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['id']).to eq(other_job.id)
        expect(json['title']).to eq(other_job.title)
      end
    end

    context 'quando não autenticado' do
      it 'retorna não autorizado' do
        get "/v1/users/jobs/#{job.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/jobs' do
    let(:valid_attributes) { { job: { title: 'New Job', description: 'Description', user_id: user.id, account_id: user.account.id } } }
    let(:invalid_attributes) { { job: { title: '', description: 'Description' } } }

    context 'quando autenticado com atributos válidos' do
      it 'cria um novo job associado ao usuário' do
        expect do
          post '/v1/users/jobs', params: valid_attributes.to_json, headers: auth_headers(user)
        end.to change(Job, :count).by(1)

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)
        expect(json['title']).to eq('New Job')
        expect(json['user_id']).to eq(user.id)
      end
    end

    context 'quando autenticado com atributos inválidos' do
      it 'retorna entidade não processável' do
        post '/v1/users/jobs', params: invalid_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to include("Title can't be blank")
      end
    end

    context 'quando não autenticado' do
      it 'retorna não autorizado' do
        post '/v1/users/jobs', params: valid_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/jobs/:id' do
    let!(:job) { create(:job, user: user) }
    let!(:other_job) { create(:job, user: other_user) }
    let(:new_attributes) { { job: { title: 'Updated Title' } } }

    context 'quando autenticado e atualizando seu próprio job' do
      it 'atualiza o job' do
        put "/v1/users/jobs/#{job.id}", params: new_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        job.reload
        expect(job.title).to eq('Updated Title')
      end
    end

    context 'quando autenticado e atualizando job de outro usuário' do
      it 'retorna proibido' do
        put "/v1/users/jobs/#{other_job.id}", params: new_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden)
      end
    end

    context 'quando não autenticado' do
      it 'retorna não autorizado' do
        put "/v1/users/jobs/#{job.id}", params: new_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/jobs/:id' do
    let!(:job) { create(:job, user: user) }

    context 'quando autenticado deletando seu job' do
      it 'deleta o job' do
        expect do
          delete "/v1/users/jobs/#{job.id}", headers: auth_headers(user)
        end.to change(Job, :count).by(-1)
        expect(response).to have_http_status(:no_content)
      end
    end

    context 'quando não autenticado' do
      it 'retorna não autorizado' do
        delete "/v1/users/jobs/#{job.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
