# frozen_string_literal: true

require "rails_helper"

RSpec.describe Evaluations::AiFeedbackService do
  describe ".call" do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, user: user, account: account) }
    let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
    let(:candidate) { create(:candidate, account: account) }
    let(:evaluation_candidate) do
      create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: candidate,
        account: account,
        user: user,
        job: job,
        score: 8.2,
        wsi_classification: "High",
        wsi_level: "Proficient"
      )
    end
    let(:question) do
      create(
        :question,
        evaluation: evaluation,
        title: "Conhecimento técnico",
        competence_type: "technical",
        bloom_level: "analyze",
        dreyfus_target: 4,
        ocean_trait: "conscientiousness"
      )
    end
    let!(:answer) do
      create(
        :answer,
        question: question,
        evaluation: evaluation,
        candidate: candidate,
        account: account,
        user: user,
        job: job,
        description: "Situação: desafio contábil. Ação: implementei melhoria. Resultado: redução de 30%.",
        final_skill_score: 4.1,
        analysis_data: {
          bloom: { score: 4, level: "analyze" },
          dreyfus: { score: 4, level: "proficient" },
          big_five: { o: 3.9, c: 4.4, e: 3.2, a: 3.8, n: 2.9 },
          cbi_star: {
            situation: "desafio contábil",
            task: "reduzir atrasos",
            action: "automatizei lançamentos",
            result: "redução de 30%",
            completeness_score: 4.5
          },
          scoring: {
            self_declaration_score: 4.0,
            context_score: 4.3,
            final_skill_score: 4.1,
            penalties_total: 0.0,
            bonuses_total: 0.3
          }
        },
        comments_response: { score: 0.82, feedback_for_recruiter: "boa resposta" }
      )
    end

    before do
      allow_any_instance_of(GeminiClient).to receive(:chat).and_return(
        {
          "choices" => [
            {
              "message" => {
                "content" => {
                  wsi_score: 1.0,
                  wsi_classification: "Low",
                  wsi_level: "Novice",
                  dreyfus_level: 1,
                  skills_analysis: [],
                  behavioral_analysis: {},
                  full_analysis: "texto",
                  summary: "resumo",
                  strengths: [],
                  weaknesses: [],
                  recommendation: "NOT_RECOMMENDED",
                  recommendation_justification: "x",
                  next_steps: "y",
                  approval_criteria: {}
                }.to_json
              }
            }
          ]
        }
      )
    end

    it "uses deterministic scores as source of truth" do
      result = described_class.call(evaluation_candidate: evaluation_candidate)

      expect(result[:wsi_score]).to eq(8.2)
      expect(result[:wsi_classification]).to eq("Excellent")
      expect(result[:wsi_level]).to eq("Proficient")
      expect(result[:dreyfus_level]).to eq(4)
      expect(result[:skills_analysis]).to be_present
      expect(result[:status]).to eq("success")
      expect(result[:wsi_macro_distribution]).to eq(
        Evaluations::WsiDimensionScores.new(evaluation_candidate: evaluation_candidate).macro_distribution_weights
      )
    end

    it "attaches GapAnalyzer severity to weaknesses without changing the LLM prompt contract" do
      result = described_class.call(evaluation_candidate: evaluation_candidate)

      expect(result[:weaknesses]).to be_a(Array)
      expect(result[:weaknesses].first).to include(
        "text" => be_a(String),
        "severity" => "MEDIO"
      )
    end

    it "replaces JSON schema placeholder summary with an excerpt from full_analysis" do
      placeholder = described_class::SUMMARY_JSON_PLACEHOLDER
      allow_any_instance_of(GeminiClient).to receive(:chat).and_return(
        {
          "choices" => [
            {
              "message" => {
                "content" => {
                  full_analysis: "Candidata excepcional com domínio completo de arquitetura. Demonstra liderança técnica " \
                    "consistente. Altamente recomendada para posições sênior.",
                  summary: placeholder,
                  strengths: [],
                  weaknesses: [],
                  recommendation: "APPROVED",
                  recommendation_justification: "ok",
                  next_steps: "next"
                }.to_json
              }
            }
          ]
        }
      )

      result = described_class.call(evaluation_candidate: evaluation_candidate)

      expect(result[:summary]).to include("Candidata excepcional")
      expect(result[:summary]).not_to eq(placeholder)
    end

    it "uses full_analysis excerpt when summary is blank" do
      allow_any_instance_of(GeminiClient).to receive(:chat).and_return(
        {
          "choices" => [
            {
              "message" => {
                "content" => {
                  full_analysis: "Primeiro parágrafo narrativo. Segundo parágrafo com detalhes.",
                  summary: "",
                  strengths: [],
                  weaknesses: [],
                  recommendation: "APPROVED",
                  recommendation_justification: "ok",
                  next_steps: "next"
                }.to_json
              }
            }
          ]
        }
      )

      result = described_class.call(evaluation_candidate: evaluation_candidate)

      expect(result[:summary]).to include("Primeiro parágrafo narrativo")
    end
  end
end
