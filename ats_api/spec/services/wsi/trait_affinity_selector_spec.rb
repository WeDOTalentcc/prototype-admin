# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::TraitAffinitySelector do
  let(:competencies) do
    [
      { "competencia" => "Comunicação", "trait_big_five" => "extraversion" },
      { "competencia" => "Organização", "trait_big_five" => "conscientiousness" },
      { "competencia" => "Colaboração", "trait_big_five" => "agreeableness" }
    ]
  end

  it "selects competency whose trait_big_five matches target trait" do
    result = described_class.new(
      target_trait: "conscientiousness",
      behavioral_competencies: competencies,
      used_indices: []
    ).call

    expect(result[:name]).to eq("Organização")
    expect(result[:index]).to eq(1)
  end

  it "uses positional fallback when no trait match" do
    result = described_class.new(
      target_trait: "openness",
      behavioral_competencies: competencies,
      used_indices: []
    ).call

    expect(result[:index]).to eq(0)
    expect(result[:name]).to eq("Comunicação")
  end

  it "skips used indices then falls back to next available" do
    result = described_class.new(
      target_trait: "conscientiousness",
      behavioral_competencies: competencies,
      used_indices: [ 1 ]
    ).call

    expect(result[:index]).to eq(0)
  end

  it "returns last-resort first index when all used" do
    result = described_class.new(
      target_trait: "conscientiousness",
      behavioral_competencies: competencies,
      used_indices: [ 0, 1, 2 ]
    ).call

    expect(result[:index]).to eq(0)
  end

  it "normalizes neuroticism to stability for matching" do
    list = [
      { "name" => "Resiliência", "trait_big_five" => "stability" }
    ]
    result = described_class.new(
      target_trait: "neuroticism",
      behavioral_competencies: list,
      used_indices: []
    ).call

    expect(result[:name]).to eq("Resiliência")
  end
end
