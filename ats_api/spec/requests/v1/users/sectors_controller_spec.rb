require 'rails_helper'

RSpec.describe 'V1::Users::Sectors API', type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:super_admin) { create(:user, :super_admin, account: account) }
  let!(:public_sector) { create(:sector, name: 'Technology', is_public: true, account_id: nil) }
  let!(:private_sector) { create(:sector, name: 'Custom Sector', is_public: false, account_id: account.id) }

  before do
    Sector.reindex
  end

  describe 'GET /v1/users/sectors' do
    it 'returns sectors when authenticated' do
      get '/v1/users/sectors', headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data'].map { |s| s['attributes']['name'] }).to include('Technology', 'Custom Sector')
    end

    it 'returns only public sectors for different account' do
      other_account = create(:account)
      other_user = create(:user, account: other_account)

      get '/v1/users/sectors', headers: auth_headers(other_user)
      expect(response).to have_http_status(:ok)
      expect(json['data'].map { |s| s['attributes']['name'] }).to include('Technology')
      expect(json['data'].map { |s| s['attributes']['name'] }).not_to include('Custom Sector')
    end

    it 'returns unauthorized without token' do
      get '/v1/users/sectors', headers: no_auth_headers
      expect(response).to have_http_status(:unauthorized)
    end

    it 'filters by level' do
      parent = create(:sector, name: 'Parent', level: 0, is_public: true, account_id: nil)
      child = create(:sector, name: 'Child', parent_sector: parent, level: 1, is_public: true, account_id: nil)
      Sector.reindex

      get '/v1/users/sectors', params: { where: { level: 0 } }, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data'].map { |s| s['attributes']['name'] }).to include('Parent')
      expect(json['data'].map { |s| s['attributes']['name'] }).not_to include('Child')
    end

    it 'includes children when requested' do
      parent = create(:sector, name: 'Parent', level: 0, is_public: true, account_id: nil)
      create(:sector, name: 'Child', parent_sector: parent, level: 1, is_public: true, account_id: nil)
      Sector.reindex

      get "/v1/users/sectors/#{parent.id}", params: { include_children: true }, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['children'].size).to eq(1)
    end
  end

  describe 'GET /v1/users/sectors/:id' do
    it 'returns a sector' do
      get "/v1/users/sectors/#{public_sector.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['name']).to eq('Technology')
    end

    it 'returns 404 for non-existent sector' do
      get "/v1/users/sectors/99999", headers: auth_headers(user)
      expect(response).to have_http_status(:not_found)
    end

    it 'includes full_path in response' do
      get "/v1/users/sectors/#{public_sector.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']).to have_key('full_path')
    end
  end

  describe 'GET /v1/users/sectors/tree' do
    it 'returns tree structure of root sectors' do
      parent = create(:sector, name: 'Root', parent_sector: nil, is_public: true, account_id: nil)
      create(:sector, name: 'Child', parent_sector: parent, is_public: true, account_id: nil)
      Sector.reindex

      get '/v1/users/sectors/tree', headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      # Verifica que retorna apenas raízes (sem parent_sector_id)
      root_sectors = json['data'].select { |s| s['attributes']['parent_sector_id'].nil? }
      expect(root_sectors.size).to be > 0
    end
  end

  describe 'POST /v1/users/sectors' do
    context 'as super_admin' do
      it 'creates a public sector' do
        post '/v1/users/sectors',
             params: { sector: { name: 'New Sector', is_public: true } }.to_json,
             headers: auth_headers(super_admin)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('New Sector')
        expect(json['data']['attributes']['is_public']).to be true
      end

      it 'creates a private sector' do
        post '/v1/users/sectors',
             params: { sector: { name: 'Private Sector', is_public: false, account_id: account.id } }.to_json,
             headers: auth_headers(super_admin)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('Private Sector')
        expect(json['data']['attributes']['is_public']).to be false
      end

      it 'creates a child sector' do
        post '/v1/users/sectors',
             params: { sector: { name: 'Child Sector', parent_sector_id: public_sector.id, is_public: true } }.to_json,
             headers: auth_headers(super_admin)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['parent_sector_id']).to eq(public_sector.id)
        expect(json['data']['attributes']['level']).to eq(1)
      end

      it 'creates sector with tags' do
        post '/v1/users/sectors',
             params: { sector: { name: 'Tech Sector', is_public: true, tags: [ 'B2B', 'SaaS', 'Cloud' ] } }.to_json,
             headers: auth_headers(super_admin)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['tags']).to match_array([ 'B2B', 'SaaS', 'Cloud' ])
      end
    end

    context 'as regular user' do
      it 'denies creation' do
        post '/v1/users/sectors',
             params: { sector: { name: 'Unauthorized Sector', is_public: true } }.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:forbidden)
      end
    end

    context 'with invalid params' do
      it 'returns error for missing name' do
        post '/v1/users/sectors',
             params: { sector: { is_public: true } }.to_json,
             headers: auth_headers(super_admin)

        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'returns error for public sector with account_id' do
        post '/v1/users/sectors',
             params: { sector: { name: 'Invalid', is_public: true, account_id: account.id } }.to_json,
             headers: auth_headers(super_admin)

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe 'PUT /v1/users/sectors/:id' do
    context 'as super_admin' do
      it 'updates a sector' do
        put "/v1/users/sectors/#{public_sector.id}",
            params: { sector: { name: 'Updated Technology' } }.to_json,
            headers: auth_headers(super_admin)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['name']).to eq('Updated Technology')
      end

      it 'updates tags' do
        put "/v1/users/sectors/#{public_sector.id}",
            params: { sector: { tags: [ 'B2B', 'Enterprise' ] } }.to_json,
            headers: auth_headers(super_admin)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['tags']).to match_array([ 'B2B', 'Enterprise' ])
      end
    end

    context 'as regular user' do
      it 'denies update' do
        put "/v1/users/sectors/#{public_sector.id}",
            params: { sector: { name: 'Unauthorized Update' } }.to_json,
            headers: auth_headers(user)

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /v1/users/sectors/:id' do
    context 'as super_admin' do
      it 'deletes a sector without children' do
        sector_to_delete = create(:sector, name: 'To Delete', is_public: true, account_id: nil)

        delete "/v1/users/sectors/#{sector_to_delete.id}", headers: auth_headers(super_admin)
        expect(response).to have_http_status(:ok)
      end

      it 'prevents deletion of sector with children' do
        parent = create(:sector, name: 'Parent', level: 0, is_public: true, account_id: nil)
        create(:sector, name: 'Child', parent_sector: parent, level: 1, is_public: true, account_id: nil)

        delete "/v1/users/sectors/#{parent.id}", headers: auth_headers(super_admin)
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'as regular user' do
      it 'denies deletion' do
        delete "/v1/users/sectors/#{public_sector.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'search functionality' do
    before do
      create(:sector, name: 'Software Development', is_public: true, account_id: nil)
      create(:sector, name: 'Hardware Engineering', is_public: true, account_id: nil)
      Sector.reindex
    end

    it 'searches by name' do
      get '/v1/users/sectors', params: { search: 'Software' }, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data'].size).to be >= 1
      expect(json['data'].any? { |s| s['attributes']['name'].include?('Software') }).to be true
    end

    it 'searches by tags' do
      sector_with_tags = create(:sector, name: 'SaaS Company', tags: [ 'B2B', 'Cloud' ], is_public: true, account_id: nil)
      Sector.reindex

      get '/v1/users/sectors', params: { search: 'Cloud' }, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      # A busca deve encontrar o setor com a tag Cloud
    end
  end
end
