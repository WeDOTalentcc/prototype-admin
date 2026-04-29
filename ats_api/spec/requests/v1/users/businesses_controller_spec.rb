# spec/requests/v1/users/businesses_spec.rb
require 'rails_helper'

RSpec.describe "V1::Businesses API", type: :request do
  let!(:super_admin) { create(:user, roles: [ :super_admin ]) }
  let!(:regular_user) { create(:user, roles: [ :admin ]) }

  let!(:user_business) { create(:business, account: regular_user.account) }
  let!(:other_businesses) { create_list(:business, 2) }

  before do
    Business.reindex
  end

  describe 'GET /v1/users/businesses' do
    context 'when user is a super_admin' do
      it 'returns a list of all businesses' do
        get '/v1/users/businesses', headers: auth_headers(super_admin)

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
      end
    end

    context 'when user is a regular user' do
      it 'returns only their own business' do
        get '/v1/users/businesses', headers: auth_headers(regular_user)

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(1)
        expect(json['data'][0]['id']).to eq(user_business.id.to_s)
      end
    end

    context 'when user is not authenticated' do
      it 'returns unauthorized' do
        get '/v1/users/businesses', headers: {}
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end


  describe 'PUT /v1/users/businesses/:id' do
    let(:new_attributes) { { business: { name: 'Updated Business Name' } } }

    context 'when a regular user updates their own business' do
      it 'updates the business successfully' do
        put "/v1/users/businesses/#{user_business.id}", params: new_attributes.to_json, headers: auth_headers(regular_user)

        user_business.reload
        expect(response).to have_http_status(:ok)
        expect(user_business.name).to eq('Updated Business Name')
      end
    end

    context "when a regular user tries to update another business" do
      let(:other_business_id) { other_businesses.first.id }

      it 'returns a forbidden status' do
        put "/v1/users/businesses/#{other_business_id}", params: new_attributes.to_json, headers: auth_headers(regular_user)
        expect(response).to have_http_status(:forbidden)
      end
    end

    context 'when a super_admin updates any business' do
      let(:other_business_id) { other_businesses.first.id }

      it 'updates the business successfully' do
        put "/v1/users/businesses/#{other_business_id}", params: new_attributes.to_json, headers: auth_headers(super_admin)
        expect(response).to have_http_status(:ok)
      end
    end
  end
end
