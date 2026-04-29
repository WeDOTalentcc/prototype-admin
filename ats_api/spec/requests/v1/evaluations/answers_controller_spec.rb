require 'rails_helper'

RSpec.describe V1::Evaluations::AnswersController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user) }
  let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:apply) { create(:apply, account: account, job: job, candidate: candidate) }
  let(:evaluation_candidate) { create(:evaluation_candidate, account: account, user: user, evaluation: evaluation, candidate: candidate, apply: apply) }

  describe 'Answers public CRUD' do
    let(:base_path) { "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}/answers" }

    it 'creates, shows, lists, updates and destroys an answer scoped by uid' do
      # Create
      payload = {
        answer: {
          title: 'Hello',
          question_id: create(:question, evaluation: evaluation).id,
          time_taken: 12,
          choices: [ 'A', 'B' ]
        }
      }
      post base_path, params: payload.to_json, headers: { 'Content-Type' => 'application/json' }
      expect(response).to have_http_status(:created)
      body = JSON.parse(response.body)
      id = body['data']['id']
      expect(body['data']['attributes']['title']).to eq('Hello')
      expect(body['data']['attributes']['evaluation_id']).to eq(evaluation.id)
      expect(body['data']['attributes']['candidate_id']).to eq(candidate.id)

      # Show
      get "#{base_path}/#{id}"
      expect(response).to have_http_status(:ok)

      # Index
      get base_path
      expect(response).to have_http_status(:ok)
      list = JSON.parse(response.body)
      expect(list['data'].any? { |r| r['id'] == id }).to be(true)

      # Update
      put "#{base_path}/#{id}", params: { answer: { title: 'Updated' } }.to_json, headers: { 'Content-Type' => 'application/json' }
      expect(response).to have_http_status(:ok)
      updated = JSON.parse(response.body)
      expect(updated['data']['attributes']['title']).to eq('Updated')

      # Destroy
      delete "#{base_path}/#{id}"
      expect(response).to have_http_status(:no_content)
      expect(Answer.where(id: id)).to be_empty
    end

    it 'returns 401 for invalid uid' do
      get "/v1/evaluations/#{account.uid}/invalid/answers"
      expect(response).to have_http_status(:unauthorized)
    end

    it 'returns 403 when changing description after submit' do
      question = create(:question, evaluation: evaluation)
      allow(Evaluations::ScoreCalculatorService).to receive(:call).and_return(
        double(success?: true, analysis_data: {}, final_skill_score: 3.0, error: nil)
      )
      allow(Evaluations::EvaluationAggregateService).to receive(:call)

      post base_path, params: {
        answer: {
          title: 'T',
          question_id: question.id,
          description: 'first answer'
        }
      }.to_json, headers: { 'Content-Type' => 'application/json' }
      expect(response).to have_http_status(:created)
      id = JSON.parse(response.body)['data']['id']

      put "#{base_path}/#{id}", params: { answer: { description: 'changed' } }.to_json, headers: { 'Content-Type' => 'application/json' }
      expect(response).to have_http_status(:forbidden)
    end

    it 'persists nested comments_response (score) for strong params' do
      technical_q = create(:question, evaluation: evaluation, competence_type: "technical")
      allow(Evaluations::ScoreCalculatorService).to receive(:call).and_return(
        double(success?: true, analysis_data: {}, final_skill_score: 5.0, error: nil)
      )
      allow(Evaluations::EvaluationAggregateService).to receive(:call)

      post base_path, params: {
        answer: {
          title: 'T',
          question_id: technical_q.id,
          description: 'text',
          comments_response: { score: 4, feedback_for_recruiter: 'ok' }
        }
      }.to_json, headers: { 'Content-Type' => 'application/json' }
      expect(response).to have_http_status(:created)
      id = JSON.parse(response.body)['data']['id']
      get "#{base_path}/#{id}"
      expect(response).to have_http_status(:ok)
      attrs = JSON.parse(response.body)['data']['attributes']
      expect(attrs['comments_response']['score'].to_f).to eq(4.0)
    end

    it 'persists self_declaration_score and eligibility for WSI' do
      technical_q = create(:question, evaluation: evaluation, competence_type: "technical")
      elig_q = create(:question, evaluation: evaluation, competence_type: "eligibility")

      post base_path, params: {
        answer: {
          title: 'T',
          question_id: technical_q.id,
          description: 'text',
          self_declaration_score: 3
        }
      }.to_json, headers: { 'Content-Type' => 'application/json' }
      expect(response).to have_http_status(:created)
      attrs = JSON.parse(response.body)['data']['attributes']
      expect(attrs['self_declaration_score']).to eq(3)

      allow(Evaluations::ScoreCalculatorService).to receive(:call)
      allow(Evaluations::EvaluationAggregateService).to receive(:call)
      post base_path, params: {
        answer: {
          title: 'E',
          question_id: elig_q.id,
          description: 'yes',
          eligibility_answer: false
        }
      }.to_json, headers: { 'Content-Type' => 'application/json' }
      expect(response).to have_http_status(:created)
      expect(JSON.parse(response.body)['data']['attributes']['eligibility_answer']).to be false
    end
  end
end
