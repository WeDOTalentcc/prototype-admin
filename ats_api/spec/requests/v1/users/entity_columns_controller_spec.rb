# frozen_string_literal: true

require 'rails_helper'

RSpec.describe V1::Users::EntityColumnsController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe 'GET /v1/users/entity_columns' do
    let!(:public_column) { create(:entity_column, :public, account: account) }
    let!(:private_column) { create(:entity_column, user: user, account: account) }
    let!(:other_user_column) { create(:entity_column, user: create(:user), account: account) }

    before do
      EntityColumn.reindex(refresh: true)
    end

    it 'returns accessible entity columns' do
      get '/v1/users/entity_columns', headers: headers

      expect(response).to have_http_status(:ok)

      response_data = JSON.parse(response.body)
      entity_columns = response_data['data']

      expect(entity_columns.length).to eq(3)

      returned_ids = entity_columns.map { |ec| ec['id'].to_i }
      expect(returned_ids).to include(public_column.id, private_column.id)
    end

    it 'filters out deleted entity columns by default' do
      deleted_column = create(:entity_column, :public, account: account, is_deleted: true)
      get '/v1/users/entity_columns', headers: headers

      expect(response).to have_http_status(:ok)

      response_data = JSON.parse(response.body)
      p response_data['data']
      entity_columns = response_data['data']
      returned_ids = entity_columns.map { |ec| ec['id'].to_i }

      expect(returned_ids).not_to include(deleted_column.id)
    end
  end

  describe 'GET /v1/users/entity_columns_structure/:entity' do
    it 'returns structure for supported entity' do
      get '/v1/users/entity_columns_structure/candidate', headers: headers

      expect(response).to have_http_status(:ok)

      response_data = JSON.parse(response.body)
      expect(response_data).to have_key('entity_column')
    end

    it 'returns 404 for unsupported entity' do
      get '/v1/users/entity_columns_structure/invalid_entity', headers: headers

      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /v1/users/entity_columns/:entity' do
    let(:valid_params) do
      {
        entity_columns: {
          entity: 'candidate',
          columns_view: [
            { field: 'name', sortable: true, width: 200 },
            { field: 'email', sortable: false, width: 150 }
          ]
        }
      }
    end

    it 'creates or updates entity column configuration' do
      post '/v1/users/entity_columns/candidate', params: valid_params.to_json, headers: headers

      expect(response).to have_http_status(:ok)

      entity_column = EntityColumn.find_by(
        entity: 'candidate',
        user_id: user.id,
        account_id: account.id,
        requested: 'default'
      )

      expect(entity_column).to be_present

      expected_columns = valid_params[:entity_columns][:columns_view].map do |col|
        col.except(:field).stringify_keys
      end
    end


    it 'handles custom requested parameter' do
      post '/v1/users/entity_columns/candidate/custom', params: valid_params.to_json, headers: headers

      expect(response).to have_http_status(:ok)

      entity_column = EntityColumn.find_by(
        entity: 'candidate',
        user_id: user.id,
        account_id: account.id,
        requested: 'custom'
      )

      expect(entity_column).to be_present
    end

    it 'returns 200 without entity_columns params' do
      post '/v1/users/entity_columns/candidate', headers: headers

      expect(response).to have_http_status(:ok)
    end
  end

  describe 'POST /v1/users/entity_columns/' do
    let(:view_params) do
      {
        entity_columns: {
          entity: 'candidate',
          label: 'My Custom View',
          is_public: false,
          requested: 'jobs',
          is_main: false,
          is_views: true,
          columns_view: [
            { field: 'name', sortable: true, width: 200 }
          ]
        }
      }
    end

    it 'creates a new view' do
      post '/v1/users/entity_columns/', params: view_params.to_json, headers: headers

      expect(response).to have_http_status(:created)

      response_data = JSON.parse(response.body)

      expect(response_data['entity_column']['label']).to eq('My Custom View')
      expect(response_data['entity_column']['is_views']).to be_truthy
      expect(response_data['entity_column']['is_main']).to be_falsey
    end

    it 'requires label for views' do
      view_params[:entity_columns].delete(:label)

      post '/v1/users/entity_columns/', params: view_params.to_json, headers: headers

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end

  describe 'PUT /v1/users/entity_columns/update_view' do
    let!(:main_column) do
      create(:entity_column, :main,
        entity: 'candidate',
        user: user,
        account: account,
        requested: 'default'
      )
    end

    let(:update_params) do
      {
        entity: 'candidate',
        entity_columns: {
          columns_view: [
            { field: 'name', sortable: false, width: 300 }
          ]
        }
      }
    end

    it 'updates main column view' do
      put '/v1/users/entity_columns/update_view', params: update_params.to_json, headers: headers

      expect(response).to have_http_status(:ok)

      main_column.reload
      columns_view = main_column.columns_view
      expect(columns_view.first['width']).to eq(300)
    end
  end
end
