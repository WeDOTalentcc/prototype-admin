# frozen_string_literal: true

require 'rails_helper'

RSpec.describe TagReplacer::Service do
  let(:candidate) { double("Candidate", name: "Maria Silva", email: "maria@test.com", first_name: "Maria") }
  let(:user) { double("User", name: "João Recruiter", email: "joao@test.com") }
  let(:record) { { candidate: candidate, user: user } }

  describe ".call" do
    it "replaces simple attribute tags" do
      result = described_class.call(
        "Hello {{candidate_name}}, your email is {{candidate_email}}",
        record: record
      )
      expect(result).to eq("Hello Maria Silva, your email is maria@test.com")
    end

    it "replaces same tag multiple times (cache)" do
      result = described_class.call(
        "{{candidate_name}}, reinforcing: {{candidate_name}}",
        record: record
      )
      expect(result).to eq("Maria Silva, reinforcing: Maria Silva")
    end

    it "returns '-' for missing entity" do
      result = described_class.call(
        "Job: {{job_title}}",
        record: { candidate: candidate }
      )
      expect(result).to eq("Job: -")
    end

    it "maintains unknown tags in text when resolver fails and no fallback" do
      result = described_class.call(
        "Unknown tag: {{invalid_tag}}",
        record: record
      )
      expect(result).to include("{{invalid_tag}}")
    end

    it "returns empty string for blank input" do
      expect(described_class.call("", record: record)).to eq("")
      expect(described_class.call(nil, record: record)).to eq("")
    end

    it "supports legacy Portuguese tags" do
      result = described_class.call(
        "Olá {{nome_do_candidato}}, seu e-mail é {{email_do_candidato}}",
        record: record
      )
      expect(result).to eq("Olá Maria Silva, seu e-mail é maria@test.com")
    end

    it "replaces multiple entity tags" do
      result = described_class.call(
        "Candidate: {{candidate_name}}, Recruiter: {{user_name}}",
        record: record
      )
      expect(result).to eq("Candidate: Maria Silva, Recruiter: João Recruiter")
    end
  end
end
