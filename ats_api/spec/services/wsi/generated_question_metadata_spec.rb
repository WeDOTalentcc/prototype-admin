# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::GeneratedQuestionMetadata do
  describe ".build" do
    it "includes base flags and skill_name from LLM" do
      meta = described_class.build({
        skill_name: "Python",
        title: "Fallback title",
        expected_signals: [ "métrica clara", " decisão justificada " ]
      })
      expect(meta["reviewed_by_recruiter"]).to be(false)
      expect(meta["needs_manual_review"]).to be(false)
      expect(meta["generation_attempts"]).to eq(0)
      expect(meta["skill_name"]).to eq("Python")
      expect(meta["expected_signals"]).to eq([ "métrica clara", "decisão justificada" ])
    end

    it "falls back skill_name to title when skill_name is blank and no other anchor" do
      meta = described_class.build({ title: "Liderança técnica", expected_signals: [ "sinal" ] })
      expect(meta["skill_name"]).to eq("Liderança técnica")
    end

    it "uses Portuguese OCEAN label for behavioral when skill_name is blank" do
      meta = described_class.build({
        competence_type: "behavioral",
        ocean_trait: "conscientiousness",
        title: "Título longo da pergunta"
      })
      expect(meta["skill_name"]).to eq("Conscienciosidade")
    end

    it "matches anchor skill from title/description when technical and skill_name is blank" do
      meta = described_class.build(
        {
          competence_type: "technical",
          title: "Experiência com Ruby em APIs",
          description: "Detalhe"
        },
        anchor_skills: [ "Python", "Ruby on Rails", "Ruby" ]
      )
      expect(meta["skill_name"]).to eq("Ruby")
    end

    it "omits expected_signals when empty" do
      meta = described_class.build({ title: "T", skill_name: "X", expected_signals: [] })
      expect(meta).not_to have_key("expected_signals")
    end
  end
end
