require 'rails_helper'

RSpec.describe V1::Users::AnswersController, type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:headers) { auth_headers(user) }
  let(:evaluation) { create(:evaluation, user: user, account: account) }
  let(:question) { create(:question, evaluation: evaluation) }

  describe 'POST /v1/users/answers' do
    context 'with minimal valid params' do
      let(:params) do
        {
          answer: {
            title: 'My Answer',
            question_id: question.id,
            evaluation_id: evaluation.id,
            choices: [ 'A', 'B' ],
            time_taken: 12
          }
        }
      end

      it 'creates an answer' do
        expect {
          post '/v1/users/answers', params: params.to_json, headers: headers
        }.to change(Answer, :count).by(1)

        expect(response).to have_http_status(:created)
        body = JSON.parse(response.body)
        expect(body['data']['attributes']['title']).to eq('My Answer')
        expect(body['data']['attributes']['question_id']).to eq(question.id)
        expect(body['data']['attributes']['evaluation_id']).to eq(evaluation.id)
        expect(body['data']['attributes']['account_id']).to eq(account.id)
        expect(body['data']['attributes']['user_id']).to eq(user.id)
      end
    end

    context 'with invalid params (missing title but allowed blank -> still ok)' do
      let(:params) do
        {
          answer: {
            question_id: question.id,
            evaluation_id: evaluation.id
          }
        }
      end

      it 'creates even without title since validation allows blank' do
        expect {
          post '/v1/users/answers', params: params.to_json, headers: headers
        }.to change(Answer, :count).by(1)
        expect(response).to have_http_status(:created)
      end
    end
  end

  describe 'GET /v1/users/answers' do
    before do
      create_list(:answer, 2, user: user, account: account, question: question, evaluation: evaluation)
      Answer.reindex
    end

    it 'lists answers' do
      get '/v1/users/answers', headers: headers
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data'].length).to be >= 2
    end
  end

  describe 'PUT /v1/users/answers/:id' do
    let(:answer) { create(:answer, user: user, account: account, question: question, evaluation: evaluation, title: 'Old') }
    let(:params) { { answer: { title: 'Updated Title', time_taken: 33 } } }

    it 'updates the answer' do
      put "/v1/users/answers/#{answer.id}", params: params.to_json, headers: headers
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']['attributes']['title']).to eq('Updated Title')
      expect(body['data']['attributes']['time_taken']).to eq(33)
    end
  end

  describe 'DELETE /v1/users/answers/:id' do
    let!(:answer) { create(:answer, user: user, account: account, question: question, evaluation: evaluation) }

    it 'destroys the answer' do
      expect {
        delete "/v1/users/answers/#{answer.id}", headers: headers
      }.to change(Answer, :count).by(-1)
      expect(response).to have_http_status(:no_content)
    end
  end
end
