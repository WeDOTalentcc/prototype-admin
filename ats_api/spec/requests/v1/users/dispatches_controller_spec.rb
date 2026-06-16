require 'rails_helper'

RSpec.describe 'V1::Users::DispatchesController', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:authentication_headers) { auth_headers(user) }

  describe 'POST /v1/users/dispatches' do
    context 'with ids target_type' do
      let!(:candidates) { create_list(:candidate, 2, account: account) }
      let(:payload) do
        {
          dispatch: {
            name: 'Sample Dispatch',
            channel_type: 'email',
            target_type: 'ids',
            candidate_ids: candidates.map(&:id)
          }
        }
      end

      it 'creates dispatch and returns accepted with minimal payload while logging IO' do
        expect {
          post '/v1/users/dispatches', params: payload, headers: authentication_headers
        }.to change(Dispatch, :count).by(1)

        expect(response).to have_http_status(:accepted)
        json = JSON.parse(response.body)
        expect(json.dig('dispatch', 'status')).to eq('pending')
        expect(json.dig('dispatch', 'channel_type')).to eq('email')

        Rails.logger.info("Dispatch create input=#{payload.to_json} output=#{json.to_json}")
      end
    end

    # context 'with invalid ids (empty list)' do
    #   let(:payload) do
    #     {
    #       dispatch: {
    #         name: 'Empty Dispatch',
    #         channel_type: 'email',
    #         target_type: 'ids',
    #         candidate_ids: []
    #       }
    #     }
    #   end

    #   it 'returns unprocessable_entity and logs error payload' do
    #     expect {
    #       post '/v1/users/dispatches', params: payload, headers: headers
    #     }.not_to change(Dispatch, :count)

    #     expect(response).to have_http_status(:unprocessable_entity)
    #     json = JSON.parse(response.body)
    #     Rails.logger.info("Dispatch create failure input=#{payload.to_json} output=#{json.to_json}")
    #     expect(json['errors']).to include('Sem candidatos informados')
    #   end
    # end
  end
end
