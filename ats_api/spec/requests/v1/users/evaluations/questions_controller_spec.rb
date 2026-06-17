# frozen_string_literal: true

require 'rails_helper'

RSpec.describe "V1::Users::Evaluations::Questions API", type: :request do
  let(:user) { create(:user) }
  let(:evaluation) { create(:evaluation) }
  let(:other_evaluation) { create(:evaluation) }
  let(:headers) { auth_headers(user) }

  let(:valid_attributes) do
    {
      question: {
        title: "Sample Question",
        description: "This is a description",
        response_type: 1
      }
    }
  end

  let(:invalid_attributes) do
    {
      question: {
        title: "",
        response_type: nil
      }
    }
  end

  describe "GET /v1/users/evaluations/:evaluation_id/questions" do
    before do
      Question.reindex
      create_list(:question, 3, evaluation: evaluation)
      create_list(:question, 2, evaluation: other_evaluation)
      Question.reindex
    end

    it "returns all questions for the evaluation" do
      get "/v1/users/evaluations/#{evaluation.id}/questions", headers: headers
      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json["data"].size).to eq(3)
    end
  end

  describe "GET /v1/users/evaluations/:evaluation_id/questions/:id" do
    let!(:question) { create(:question, evaluation: evaluation) }

    it "returns the question" do
      get "/v1/users/evaluations/#{evaluation.id}/questions/#{question.id}", headers: headers
      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data']['attributes']["id"]).to eq(question.id)
      expect(json['data']['attributes']["title"]).to eq(question.title)
    end
  end

  describe "POST /v1/users/evaluations/:evaluation_id/questions" do
    context "with valid attributes" do
      it "creates a new question" do
        expect {
          post "/v1/users/evaluations/#{evaluation.id}/questions", params: valid_attributes.to_json, headers: headers
        }.to change(Question, :count).by(1)

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)
        expect(json["data"]["attributes"]["title"]).to eq("Sample Question")
        expect(json["data"]["attributes"]["evaluation_id"]).to eq(evaluation.id)
      end
    end

    context "with invalid attributes" do
      it "returns unprocessable entity" do
        post "/v1/users/evaluations/#{evaluation.id}/questions", params: invalid_attributes.to_json, headers: headers
        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json["errors"]).to include("Title can't be blank")
      end
    end
  end

  describe "PUT /v1/users/evaluations/:evaluation_id/questions/:id" do
    let!(:question) { create(:question, evaluation: evaluation) }

    it "updates the question" do
      put "/v1/users/evaluations/#{evaluation.id}/questions/#{question.id}",
          params: { question: { title: "Updated Title" } }.to_json,
          headers: headers

      expect(response).to have_http_status(:ok)
      question.reload
      expect(question.title).to eq("Updated Title")
    end
  end

  describe "DELETE /v1/users/evaluations/:evaluation_id/questions/:id" do
    let!(:question) { create(:question, evaluation: evaluation, is_deleted: false) }

    it "soft deletes the question" do
      delete "/v1/users/evaluations/#{evaluation.id}/questions/#{question.id}", headers: headers
      expect(response).to have_http_status(:no_content)
      question.reload
      expect(question.is_deleted).to eq(true)
    end
  end
end
