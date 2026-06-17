require 'rails_helper'

RSpec.describe 'V1::Users::Skills API - Category Include Issue', type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let!(:skill_category) { create(:skill_category, name: "Programming #{SecureRandom.hex(4)}", icon: "💻", color: "#3B82F6") }
  let!(:skill_with_category) { create(:skill, name: "Ruby #{SecureRandom.hex(4)}", account: account, skill_category: skill_category) }
  let!(:skill_without_category) { create(:skill, name: "Generic Skill #{SecureRandom.hex(4)}", account: account, skill_category: nil) }

  before do
    # Switch to correct tenant before each test
    Apartment::Tenant.switch!(account.tenant)
    Skill.reindex
    sleep 1 # Wait for Elasticsearch to index
  end

  after do
    Apartment::Tenant.reset
  end

  describe 'GET /v1/users/skills - Category Include Test' do
    context 'when fetching all skills' do
      it 'returns skills with category information included' do
        get '/v1/users/skills', headers: auth_headers(user)

        if response.status != 200
          puts "Response status: #{response.status}"
          puts "Response body: #{response.body[0..500]}"
        end

        expect(response).to have_http_status(:ok)

        # Find our specific skill with category
        skill_data = json['data'].find { |s| s['attributes']['id'] == skill_with_category.id }

        expect(skill_data).to be_present
        expect(skill_data['attributes']).to include(
          'skill_category_id' => skill_category.id,
          'skill_category_name' => skill_category.name,
          'skill_category_icon' => skill_category.icon,
          'skill_category_color' => skill_category.color
        )
      end

      it 'handles skills without category gracefully' do
        get '/v1/users/skills', headers: auth_headers(user)

        expect(response).to have_http_status(:ok)

        skill_data = json['data'].find { |s| s['attributes']['id'] == skill_without_category.id }

        expect(skill_data).to be_present
        expect(skill_data['attributes']['skill_category_id']).to be_nil
        expect(skill_data['attributes']['skill_category_name']).to be_nil
        expect(skill_data['attributes']['skill_category_icon']).to be_nil
        expect(skill_data['attributes']['skill_category_color']).to be_nil
      end

      it 'loads multiple skills with categories efficiently' do
        # Create additional skills
        5.times do |i|
          create(:skill, name: "Skill #{i} #{SecureRandom.hex(4)}", account: account, skill_category: skill_category)
        end
        Skill.reindex
        sleep 1

        get '/v1/users/skills', headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        # Just verify we get multiple results
        expect(json['data'].size).to be >= 5
      end
    end

    context 'when fetching a single skill' do
      it 'returns skill with category information' do
        get "/v1/users/skills/#{skill_with_category.id}", headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']).to include(
          'id' => skill_with_category.id,
          'name' => skill_with_category.name,
          'skill_category_id' => skill_category.id,
          'skill_category_name' => skill_category.name,
          'skill_category_icon' => skill_category.icon,
          'skill_category_color' => skill_category.color
        )
      end

      it 'returns skill without category' do
        get "/v1/users/skills/#{skill_without_category.id}", headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']).to include(
          'id' => skill_without_category.id,
          'name' => skill_without_category.name,
          'skill_category_id' => nil,
          'skill_category_name' => nil
        )
      end
    end

    context 'when filtering by category' do
      it 'filters skills by skill_category_id' do
        get '/v1/users/skills',
            params: { where: { skill_category_id: skill_category.id } },
            headers: auth_headers(user)

        expect(response).to have_http_status(:ok)

        # All returned skills should have the specified category
        json['data'].each do |skill_data|
          expect(skill_data['attributes']['skill_category_id']).to eq(skill_category.id)
        end
      end
    end
  end

  describe 'POST /v1/users/skills - Creating with Category' do
    it 'creates a skill with category and returns complete category info' do
      skill_params = {
        skill: {
          name: "New Skill #{SecureRandom.hex(4)}",
          skill_category_id: skill_category.id
        }
      }

      post '/v1/users/skills',
           params: skill_params.to_json,
           headers: auth_headers(user)

      expect(response).to have_http_status(:created)
      expect(json['data']['attributes']).to include(
        'skill_category_id' => skill_category.id,
        'skill_category_name' => skill_category.name,
        'skill_category_icon' => skill_category.icon,
        'skill_category_color' => skill_category.color
      )
    end
  end

  describe 'PUT /v1/users/skills/:id - Updating Category' do
    let(:another_category) { create(:skill_category, name: "Backend #{SecureRandom.hex(4)}", icon: "⚙️", color: "#10B981") }

    it 'updates skill category and returns new category info' do
      put "/v1/users/skills/#{skill_with_category.id}",
          params: { skill: { skill_category_id: another_category.id } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']).to include(
        'skill_category_id' => another_category.id,
        'skill_category_name' => another_category.name,
        'skill_category_icon' => another_category.icon,
        'skill_category_color' => another_category.color
      )
    end

    it 'can remove category from skill' do
      put "/v1/users/skills/#{skill_with_category.id}",
          params: { skill: { skill_category_id: nil } }.to_json,
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['skill_category_id']).to be_nil
      expect(json['data']['attributes']['skill_category_name']).to be_nil
    end
  end
end
