# frozen_string_literal: true

require 'rails_helper'

RSpec.describe V1::Users::Evaluations::EvaluationsController, type: :request do
  describe 'POST /v1/users/evaluations/process_ai_response' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, account: account, user: user) }
    let(:evaluation) { create(:evaluation, account: account, user: user, job: job, is_chatbot: true, chatbot_channel: 'whatsapp') }
    let(:candidate) { create(:candidate, account: account, mobile_phone: '+5511999999999') }
    let(:apply) { create(:apply, job: job, candidate: candidate, account: account) }
    let(:evaluation_candidate) { create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, apply: apply, account: account, job: job, user: user) }
    let(:question) { create(:question, evaluation: evaluation, title: 'Test Question', description: 'Describe your experience') }
    let(:message) do
      create(:message,
             account: account,
             reference: candidate,
             content: 'Candidate response',
             entity: Message::ROLE_CANDIDATE,
             status: Message::STATUS_NOT_ANSWERED,
             evaluation: evaluation,
             apply: apply,
             metadata: { 'question_index' => 1, 'question_id' => question.id })
    end

    let(:valid_params) do
      {
        original_payload: {
          account_id: account.id,
          evaluation_candidate_id: evaluation_candidate.id,
          message_id: message.id,
          question_id: question.id,
          candidate_answer: 'Tenho 5 anos de experiência com React...'
        },
        ai_response: {
          score: 0.85,
          is_answer_satisfactory: true,
          feedback_for_recruiter: 'Candidato demonstrou conhecimento sólido...',
          chat_ack: 'Ótimo! ',
          responded: true,
          changed_subject: false,
          response_to_candidate: 'Entendi, obrigado pela resposta detalhada.',
          followup_needed: false,
          followup_question: nil,
          next_question: nil,
          end: false,
          interested_job: true,
          interested_job_msg: nil,
          avoid_answer: false
        },
        chatbot_channel: 'whatsapp'
      }
    end

    let(:headers) do
      token = JsonWebToken.encode_ott(account_id: account.id, user_id: user.id)
      {
        'Authorization' => "Bearer #{token}",
        'Content-Type' => 'application/json'
      }
    end

    before do
      Apartment::Tenant.switch!(account.tenant)
      allow(Meta::WhatsappService).to receive(:send_text_message).and_return(true)
    end

    context 'with valid OTT token and params' do
      it 'returns success' do
        post '/v1/users/evaluations/process_ai_response',
             params: valid_params.to_json,
             headers: headers

        expect(response).to have_http_status(:ok)
        expect(json_response['success']).to be true
      end

      it 'creates an Answer record' do
        expect do
          post '/v1/users/evaluations/process_ai_response',
               params: valid_params.to_json,
               headers: headers
        end.to change(Answer, :count).by(1)
      end

      it 'returns evaluation_candidate_id in response' do
        post '/v1/users/evaluations/process_ai_response',
             params: valid_params.to_json,
             headers: headers

        expect(json_response['data']['evaluation_candidate_id']).to eq(evaluation_candidate.id)
      end
    end

    context 'with invalid token' do
      let(:invalid_headers) do
        {
          'Authorization' => 'Bearer invalid_token',
          'Content-Type' => 'application/json'
        }
      end

      it 'returns unauthorized' do
        post '/v1/users/evaluations/process_ai_response',
             params: valid_params.to_json,
             headers: invalid_headers

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'with missing params' do
      let(:missing_params) do
        {
          ai_response: valid_params[:ai_response]
          # original_payload is missing
        }
      end

      it 'returns bad request' do
        post '/v1/users/evaluations/process_ai_response',
             params: missing_params.to_json,
             headers: headers

        expect(response).to have_http_status(:bad_request).or have_http_status(:unprocessable_entity)
      end
    end

    context 'with non-existent evaluation_candidate' do
      let(:invalid_params) do
        valid_params.deep_merge(
          original_payload: { evaluation_candidate_id: 999999 }
        )
      end

      it 'returns unprocessable_entity' do
        post '/v1/users/evaluations/process_ai_response',
             params: invalid_params.to_json,
             headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json_response['success']).to be false
        expect(json_response['code']).to eq('NOT_FOUND')
      end
    end

    context 'with service token' do
      let(:service_headers) do
        token = JsonWebToken.encode_service_token(account_id: account.id, user_id: user.id)
        {
          'Authorization' => "Bearer #{token}",
          'Content-Type' => 'application/json'
        }
      end

      it 'returns success' do
        post '/v1/users/evaluations/process_ai_response',
             params: valid_params.to_json,
             headers: service_headers

        expect(response).to have_http_status(:ok)
      end
    end
  end

  private

  def json_response
    JSON.parse(response.body)
  end
end
