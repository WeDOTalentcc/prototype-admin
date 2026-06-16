# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::QuestionRetryCoordinator do
  let(:invalid) { "short text" }

  it "returns needs_manual_review after max_attempts failures" do
    attempts = []
    result = described_class.call(max_attempts: 3) do |_attempt, _err|
      attempts << 1
      invalid
    end

    expect(result[:needs_manual_review]).to be true
    expect(result[:generation_attempts]).to eq(3)
    expect(attempts.size).to eq(3)
  end

  it "returns success on first valid text" do
    good = <<~TXT.strip
      Descreva uma situação profissional em que você teve que organizar várias entregas simultâneas com prazo
      apertado e qualidade em risco. Como você priorizou o trabalho, quais decisões tomou em equipe e qual foi
      o resultado mensurável alcançado no projeto naquele período?
    TXT

    result = described_class.call(max_attempts: 3) { |_a, _e| good }
    expect(result[:success]).to be true
    expect(result[:needs_manual_review]).to be false
    expect(result[:generation_attempts]).to eq(1)
  end
end
