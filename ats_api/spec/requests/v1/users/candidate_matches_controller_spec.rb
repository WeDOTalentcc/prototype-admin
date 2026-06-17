# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::CandidateMatches API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }

  describe 'POST /v1/users/candidates/match_by_text' do
    let(:fake_embedding) { Array.new(768) { rand(-1.0..1.0) } }

    before do
      allow_any_instance_of(Embeddings::Encoder).to receive(:call).and_return(fake_embedding)
    end

    context 'when authenticated' do
      context 'with valid text' do
        let(:params) { { text: 'Senior Ruby developer with 5 years experience' } }

        before do
          allow(Embedding).to receive_message_chain(:for_candidates, :nearest_neighbors).and_return([])
        end

        it 'returns ok with empty results' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text', params: params.to_json, headers: auth_headers(user)
          end

          expect(response).to have_http_status(:ok)
        end

        it 'returns expected meta structure' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text', params: params.to_json, headers: auth_headers(user)
          end

          expect(json['meta']).to include('total', 'page', 'per_page')
        end
      end

      context 'with missing text' do
        it 'returns bad_request' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text', params: { text: '' }.to_json, headers: auth_headers(user)
          end

          expect(response).to have_http_status(:bad_request)
        end
      end

      context 'with text too short' do
        before do
          allow(Embedding).to receive_message_chain(:for_candidates, :nearest_neighbors).and_return([])
        end

        it 'returns unprocessable_entity' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text', params: { text: 'short' }.to_json, headers: auth_headers(user)
          end

          expect(response).to have_http_status(:unprocessable_entity)
        end
      end

      context 'with pagination params' do
        let(:params) { { text: 'Senior Ruby developer with experience', page: 2, per_page: 10 } }

        before do
          allow(Embedding).to receive_message_chain(:for_candidates, :nearest_neighbors).and_return([])
        end

        it 'respects pagination params' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text', params: params.to_json, headers: auth_headers(user)
          end

          expect(response).to have_http_status(:ok)
          expect(json['meta']['page']).to eq(2)
          expect(json['meta']['per_page']).to eq(10)
        end
      end

      context 'with score filter params' do
        let(:params) { { text: 'Senior Ruby developer with experience', min_score: 0.5, max_score: 0.9 } }

        before do
          allow(Embedding).to receive_message_chain(:for_candidates, :nearest_neighbors).and_return([])
        end

        it 'accepts score filters' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text', params: params.to_json, headers: auth_headers(user)
          end

          expect(response).to have_http_status(:ok)
          expect(json['meta']['min_score']).to eq(0.5)
          expect(json['meta']['max_score']).to eq(0.9)
        end
      end

      context 'when embedding generation fails' do
        before do
          allow_any_instance_of(Embeddings::Encoder).to receive(:call).and_return(nil)
        end

        it 'returns unprocessable_entity' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text',
                 params: { text: 'Senior Ruby developer with experience' }.to_json,
                 headers: auth_headers(user)
          end

          expect(response).to have_http_status(:unprocessable_entity)
        end
      end

      context 'with top_k param' do
        let(:params) { { text: 'Senior Ruby developer with experience', top_k: 100 } }

        before do
          allow(Embedding).to receive_message_chain(:for_candidates, :nearest_neighbors).and_return([])
        end

        it 'accepts top_k param' do
          Apartment::Tenant.switch!(account.tenant) do
            post '/v1/users/candidates/match_by_text', params: params.to_json, headers: auth_headers(user)
          end

          expect(response).to have_http_status(:ok)
        end
      end
    end

    context 'when not authenticated' do
      it 'returns unauthorized' do
        post '/v1/users/candidates/match_by_text',
             params: { text: 'test query' }.to_json,
             headers: no_auth_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
