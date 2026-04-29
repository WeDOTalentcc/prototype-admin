# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Jobs::ExportService do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let!(:job) { create(:job, user: user, account: account, title: "Developer Senior") }

  before do
    JobStatus.create_default_statuses
    job.update!(job_status: JobStatus.find_by(name: "Ativa"))
  end

  describe '#call' do
    context 'CSV format' do
      it 'generates a CSV file' do
        result = described_class.new(job: job, format: "csv").call

        expect(result[:success]).to be true
        expect(result[:content_type]).to eq("text/csv")
        expect(result[:filename]).to include("vaga_#{job.id}")
        expect(result[:content]).to include("Developer Senior")
        expect(result[:content]).to include("INFORMAÇÕES BÁSICAS")
      end

      it 'includes skills in CSV' do
        skill = Skill.create!(name: "Ruby", account: account)
        SkillRelationship.create!(
          skill: skill,
          reference_type: "Job",
          reference_id: job.id,
          account: account
        )

        result = described_class.new(job: job, format: "csv").call

        expect(result[:content]).to include("Ruby")
      end
    end

    context 'PDF format' do
      it 'generates a PDF file' do
        result = described_class.new(job: job, format: "pdf").call

        expect(result[:success]).to be true
        expect(result[:content_type]).to eq("application/pdf")
        expect(result[:filename]).to include(".pdf")
        expect(result[:content]).to be_present
      end
    end

    context 'invalid format' do
      it 'returns error' do
        result = described_class.new(job: job, format: "xml").call

        expect(result[:success]).to be false
        expect(result[:error]).to include("Formato inválido")
      end
    end
  end
end
