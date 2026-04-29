# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::QuestionPromptBuilder do
  let(:base_params) do
    {
      skill_name: "Python",
      seniority_label: "Senior",
      dreyfus_level: 4,
      dreyfus_label: "Proficiente",
      bloom_level: 5,
      bloom_label: "Avaliar",
      company_context: "Fintech",
      responsibilities_excerpt: "APIs e integrações"
    }
  end

  describe "#technical_prompt_parts" do
    subject(:parts) { described_class.new(**base_params, skill_rare_or_proprietary: false).technical_prompt_parts }

    it "uses temperature 0.7 and max_tokens 200" do
      expect(parts[:temperature]).to eq(0.7)
      expect(parts[:max_tokens]).to eq(200)
    end

    it "includes explicit PROIBIDO block for rubric leakage in generated question text" do
      expect(parts[:system]).to include("PROIBIDO — FORMATO")
      expect(parts[:system]).to include("critérios de avaliação")
    end

    it "includes SKILL_APPROXIMATED rule when skill is rare" do
      parts_rare = described_class.new(**base_params, skill_rare_or_proprietary: true).technical_prompt_parts
      expect(parts_rare[:system]).to include("[SKILL_APPROXIMATED:")
    end
  end

  describe "#behavioral_prompt_parts" do
    subject(:parts) do
      described_class.new(
        **base_params,
        trait_name: "conscientiousness",
        trait_label: "Conscienciosidade",
        rank_position: 1,
        total_traits_selected: 3,
        evidence_list: "Prazos e qualidade",
        activation_scenario: "Múltiplas responsabilidades",
        previous_questions_list: []
      ).behavioral_prompt_parts
    end

    it "uses temperature 0.75 and max_tokens 250" do
      expect(parts[:temperature]).to eq(0.75)
      expect(parts[:max_tokens]).to eq(250)
    end

    it "includes DEI rules for agreeableness, stability, extraversion" do
      text = parts[:system]
      expect(text).to include("CONFLITO PROFISSIONAL")
      expect(text).to include("pressão PROFISSIONAL")
      expect(text).to include("CONTEXTO PROFISSIONAL")
    end

    it "forbids gendered job titles in instructions" do
      expect(parts[:system]).to include('PROIBIDO: "o funcionário"')
      expect(parts[:system]).to include('"ele/ela"')
    end
  end

  describe ".parse_technical_llm_output" do
    it "strips SKILL_APPROXIMATED prefix and flags metadata" do
      raw = <<~TEXT.strip
        [SKILL_APPROXIMATED: integração de sistemas]
        Descreva um projeto em que você integrou sistemas legados com APIs modernas. O que você fez e qual foi o impacto?
      TEXT

      parsed = described_class.parse_technical_llm_output(raw)
      expect(parsed[:skill_approximated]).to be true
      expect(parsed[:approximated_domain]).to eq("integração de sistemas")
      expect(parsed[:question]).not_to start_with("[SKILL_APPROXIMATED")
    end
  end
end
