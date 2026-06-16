require 'rails_helper'

RSpec.describe 'V1::Users::SearchArchetypes API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:other_user) { create(:user) }

  let(:authentication_headers) { auth_headers(user) }
  let(:invalid_authentication_headers) { invalid_auth_headers }
  let(:no_authentication_headers) { no_auth_headers }

  describe 'GET /v1/users/search_archetypes' do
    let!(:user_archetypes) { create_list(:search_archetype, 3, user: user, account: account) }
    let!(:public_archetypes) { create_list(:search_archetype, 2, :public_archetype, account: account) }
    let!(:default_archetypes) { create_list(:search_archetype, 2, :default, account: account) }
    let!(:deleted_archetypes) { create_list(:search_archetype, 1, :deleted, user: user, account: account) }
    let!(:other_account_archetypes) { create_list(:search_archetype, 2, user: other_user, account: other_user.account) }

    before do
      SearchArchetype.reindex
    end

    context 'when authenticated' do
      it 'returns user archetypes, public and defaults' do
        get '/v1/users/search_archetypes', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(7)
      end

      it 'does not return deleted archetypes' do
        get '/v1/users/search_archetypes', headers: authentication_headers

        json = JSON.parse(response.body)
        ids = json['data'].map { |d| d['id'].to_i }
        expect(ids).not_to include(deleted_archetypes.first.id)
      end

      it 'supports search by name' do
        archetype = create(:search_archetype, name: 'Tech Lead Ruby on Rails', user: user, account: account)
        SearchArchetype.reindex

        get '/v1/users/search_archetypes', params: { search: 'ruby' }, headers: authentication_headers

        json = JSON.parse(response.body)
        expect(json['data'].map { |d| d['id'].to_i }).to include(archetype.id)
      end

      it 'filters by seniority' do
        senior = create(:search_archetype, seniority: :senior, user: user, account: account)
        create(:search_archetype, seniority: :junior, user: user, account: account)
        SearchArchetype.reindex

        get '/v1/users/search_archetypes',
            params: { where: { seniority: 'senior' }.to_json },
            headers: authentication_headers

        json = JSON.parse(response.body)
        expect(json['data'].map { |d| d['id'].to_i }).to include(senior.id)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/search_archetypes', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/search_archetypes/defaults' do
    let!(:default_archetypes) { create_list(:search_archetype, 3, :default, account: account) }
    let!(:user_archetypes) { create_list(:search_archetype, 2, user: user, account: account) }

    before do
      SearchArchetype.reindex
    end

    context 'when authenticated' do
      it 'returns only default archetypes' do
        get '/v1/users/search_archetypes/defaults', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)

        json['data'].each do |archetype_data|
          expect(archetype_data['attributes']['is_default']).to eq(true)
        end
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/search_archetypes/defaults', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/search_archetypes/enums' do
    context 'when authenticated' do
      it 'returns enum options with labels' do
        get '/v1/users/search_archetypes/enums', headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json).to have_key('seniorities')
        expect(json).to have_key('work_models')
        expect(json).to have_key('contract_types')

        expect(json['seniorities']).to be_an(Array)
        expect(json['seniorities'].first).to have_key('value')
        expect(json['seniorities'].first).to have_key('label')
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/search_archetypes/enums', headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/search_archetypes/:uid' do
    let!(:archetype) { create(:search_archetype, user: user, account: account) }

    context 'when authenticated' do
      it 'returns the archetype' do
        get "/v1/users/search_archetypes/#{archetype.uid}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)

        expect(json['data']['id']).to eq(archetype.id.to_s)
        expect(json['data']['attributes']['name']).to eq(archetype.name)
        expect(json['data']['attributes']['uid']).to eq(archetype.uid)
      end

      it 'returns 404 for non-existent archetype' do
        get "/v1/users/search_archetypes/#{SecureRandom.uuid}", headers: authentication_headers
        expect(response).to have_http_status(:not_found)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        get "/v1/users/search_archetypes/#{archetype.uid}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/search_archetypes' do
    let(:valid_attributes) do
      {
        archetype: {
          name: 'Tech Lead Python',
          emoji: '🐍',
          description: 'Buscando tech lead experiente',
          query: 'Tech Lead Python Django',
          seniority: 'lead',
          min_experience_years: 8,
          industry: 'Tecnologia',
          location: 'São Paulo, SP',
          work_model: 'remote',
          contract_type: 'clt',
          skills: [ 'Python', 'Django', 'AWS' ],
          tags: [ 'backend', 'cloud' ],
          languages: [ 'Português', 'Inglês' ],
          is_public: false
        }
      }
    end

    let(:invalid_attributes) do
      { archetype: { name: '' } }
    end

    context 'when authenticated with valid attributes' do
      it 'creates a new archetype' do
        post '/v1/users/search_archetypes', params: valid_attributes.to_json, headers: authentication_headers

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['name']).to eq('Tech Lead Python')
        expect(json['data']['attributes']['seniority']).to eq('lead')
        expect(json['data']['attributes']['skills']).to eq([ 'Python', 'Django', 'AWS' ])
      end

      it 'changes archetype count by 1' do
        expect {
          post '/v1/users/search_archetypes', params: valid_attributes.to_json, headers: authentication_headers
        }.to change(SearchArchetype, :count).by(1)
      end

      it 'assigns archetype to current user and account' do
        post '/v1/users/search_archetypes', params: valid_attributes.to_json, headers: authentication_headers

        archetype = SearchArchetype.last
        expect(archetype.user_id).to eq(user.id)
        expect(archetype.account_id).to eq(account.id)
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users/search_archetypes', params: invalid_attributes.to_json, headers: authentication_headers
        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'returns validation errors' do
        post '/v1/users/search_archetypes', params: invalid_attributes.to_json, headers: authentication_headers
        json = JSON.parse(response.body)
        expect(json).to have_key('errors')
      end
    end

    context 'when creating from description with AI' do
      let(:ai_attributes) do
        {
          from_description: true,
          description: 'Busco Tech Lead Python com 8+ anos de experiência'
        }
      end

      it 'calls CreateFromDescriptionService' do
        expect(SearchArchetypes::CreateFromDescriptionService).to receive(:call).with(
          account: account,
          user: user,
          description: 'Busco Tech Lead Python com 8+ anos de experiência'
        ).and_return(create(:search_archetype, :tech_lead_python, user: user, account: account))

        post '/v1/users/search_archetypes', params: ai_attributes.to_json, headers: authentication_headers
        expect(response).to have_http_status(:created)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post '/v1/users/search_archetypes', params: valid_attributes.to_json, headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PATCH /v1/users/search_archetypes/:uid' do
    let!(:archetype) { create(:search_archetype, user: user, account: account, name: 'Original Name') }
    let(:update_attributes) do
      { archetype: { name: 'Updated Name', emoji: '🔥' } }
    end

    context 'when authenticated as owner' do
      it 'updates the archetype' do
        patch "/v1/users/search_archetypes/#{archetype.uid}",
              params: update_attributes.to_json,
              headers: authentication_headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['name']).to eq('Updated Name')
        expect(json['data']['attributes']['emoji']).to eq('🔥')
      end

      it 'persists changes to database' do
        patch "/v1/users/search_archetypes/#{archetype.uid}",
              params: update_attributes.to_json,
              headers: authentication_headers

        archetype.reload
        expect(archetype.name).to eq('Updated Name')
        expect(archetype.emoji).to eq('🔥')
      end
    end

    context 'when authenticated as non-owner' do
      let(:other_user_headers) { auth_headers(other_user) }

      it 'returns forbidden' do
        patch "/v1/users/search_archetypes/#{archetype.uid}",
              params: update_attributes.to_json,
              headers: other_user_headers

        expect(response).to have_http_status(:forbidden)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        patch "/v1/users/search_archetypes/#{archetype.uid}",
              params: update_attributes.to_json,
              headers: no_authentication_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/search_archetypes/:uid' do
    let!(:archetype) { create(:search_archetype, user: user, account: account) }

    context 'when authenticated as owner' do
      it 'soft deletes the archetype' do
        delete "/v1/users/search_archetypes/#{archetype.uid}", headers: authentication_headers

        expect(response).to have_http_status(:ok)
        archetype.reload
        expect(archetype.is_deleted).to eq(true)
      end

      it 'does not destroy the record' do
        expect {
          delete "/v1/users/search_archetypes/#{archetype.uid}", headers: authentication_headers
        }.not_to change(SearchArchetype, :count)
      end
    end

    context 'when authenticated as non-owner' do
      let(:other_user_headers) { auth_headers(other_user) }

      it 'returns forbidden' do
        delete "/v1/users/search_archetypes/#{archetype.uid}", headers: other_user_headers
        expect(response).to have_http_status(:forbidden)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/search_archetypes/#{archetype.uid}", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/search_archetypes/:uid/search' do
    let!(:archetype) { create(:search_archetype, user: user, account: account) }

    context 'when authenticated with sufficient credits' do
      before do
        account.update(pearch_credits: 10)
      end

      it 'executes search and returns sourcing info' do
        allow(SearchArchetypes::ExecuteSearchService).to receive(:call).and_return(
          double(id: 123, uid: 'sourcing-uid', status: 'started')
        )

        post "/v1/users/search_archetypes/#{archetype.uid}/search",
             params: { sources: [ 'local', 'global' ] }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:accepted)
        json = JSON.parse(response.body)

        expect(json['sourcing_id']).to eq(123)
        expect(json['archetype_name']).to eq(archetype.name)
        expect(json['sources']).to eq([ 'local', 'global' ])
      end

      it 'increments usage_count' do
        allow(SearchArchetypes::ExecuteSearchService).to receive(:call).and_return(
          double(id: 123, uid: 'sourcing-uid', status: 'started')
        )

        expect {
          post "/v1/users/search_archetypes/#{archetype.uid}/search",
               params: { sources: [ 'local' ] }.to_json,
               headers: authentication_headers
          archetype.reload
        }.to change { archetype.usage_count }.by(1)
      end
    end

    context 'when authenticated with insufficient credits for global search' do
      before do
        account.update(pearch_credits: 0)
      end

      it 'returns payment required' do
        post "/v1/users/search_archetypes/#{archetype.uid}/search",
             params: { sources: [ 'local', 'global' ] }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:payment_required)
        json = JSON.parse(response.body)
        expect(json['error']).to include('Créditos insuficientes')
      end

      it 'allows local search without credits' do
        allow(SearchArchetypes::ExecuteSearchService).to receive(:call).and_return(
          double(id: 123, uid: 'sourcing-uid', status: 'started')
        )

        post "/v1/users/search_archetypes/#{archetype.uid}/search",
             params: { sources: [ 'local' ] }.to_json,
             headers: authentication_headers

        expect(response).to have_http_status(:accepted)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/search_archetypes/#{archetype.uid}/search",
             params: { sources: [ 'local' ] }.to_json,
             headers: no_authentication_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/search_archetypes/:uid/duplicate' do
    let!(:archetype) { create(:search_archetype, :with_usage, :public_archetype, user: other_user, account: account, name: 'Original') }

    context 'when authenticated' do
      it 'creates a duplicate for current user' do
        post "/v1/users/search_archetypes/#{archetype.uid}/duplicate", headers: authentication_headers

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)

        expect(json['data']['attributes']['name']).to eq('Original (cópia)')
        expect(json['data']['attributes']['user_id']).to eq(user.id)
      end

      it 'resets flags on duplicate' do
        post "/v1/users/search_archetypes/#{archetype.uid}/duplicate", headers: authentication_headers

        json = JSON.parse(response.body)
        expect(json['data']['attributes']['is_default']).to eq(false)
        expect(json['data']['attributes']['is_public']).to eq(false)
        expect(json['data']['attributes']['usage_count']).to eq(0)
      end

      it 'generates new uid for duplicate' do
        post "/v1/users/search_archetypes/#{archetype.uid}/duplicate", headers: authentication_headers

        json = JSON.parse(response.body)
        expect(json['data']['attributes']['uid']).not_to eq(archetype.uid)
      end

      it 'changes archetype count by 1' do
        expect {
          post "/v1/users/search_archetypes/#{archetype.uid}/duplicate", headers: authentication_headers
        }.to change(SearchArchetype, :count).by(1)
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post "/v1/users/search_archetypes/#{archetype.uid}/duplicate", headers: no_authentication_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
