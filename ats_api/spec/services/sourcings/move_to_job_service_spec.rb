require "rails_helper"

RSpec.describe Sourcings::MoveToJobService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account) }
  let(:sourcing) { create(:sourcing, account: account) }
  let(:candidates) { create_list(:candidate, 3, account: account) }
  let(:candidate_ids) { candidates.map(&:id) }

  subject(:service) do
    described_class.new(
      sourcing: sourcing,
      job_id: job.id,
      candidate_ids: candidate_ids,
      user: user
    )
  end

  describe "#call" do
    context "quando todos os candidatos são válidos" do
      it "cria applies para todos os candidatos" do
        expect { service.call }.to change(Apply, :count).by(3)
      end

      it "retorna success? true" do
        result = service.call
        expect(result.success?).to be true
        expect(result.applies_created.size).to eq(3)
      end

      it "pula candidatos já adicionados à vaga" do
        Apply.create!(candidate_id: candidates.first.id, job_id: job.id, account_id: account.id, user_id: user.id, source: "talent_pool")
        result = service.call
        expect(result.applies_created.size).to eq(2)
        expect(result.skipped).to include(candidates.first.id)
      end
    end

    context "quando um create! falha no meio da lista" do
      before do
        call_count = 0
        allow(Apply).to receive(:create!).and_wrap_original do |original, **args|
          call_count += 1
          raise ActiveRecord::RecordInvalid.new(Apply.new) if call_count == 2
          original.call(**args)
        end
      end

      it "faz rollback de todos os applies criados antes da falha" do
        expect { service.call }.not_to change(Apply, :count)
      end

      it "retorna success? false com mensagem de erro" do
        result = service.call
        expect(result.success?).to be false
        expect(result.error).to match(/Falha ao adicionar candidato/)
      end
    end

    context "com parâmetros inválidos" do
      it "retorna erro quando candidate_ids está vazio" do
        svc = described_class.new(sourcing: sourcing, job_id: job.id, candidate_ids: [], user: user)
        result = svc.call
        expect(result.success?).to be false
        expect(result.error).to eq("candidate_ids required")
      end

      it "retorna erro quando job não pertence à account" do
        other_job = create(:job)
        svc = described_class.new(sourcing: sourcing, job_id: other_job.id, candidate_ids: candidate_ids, user: user)
        result = svc.call
        expect(result.success?).to be false
        expect(result.error).to eq("job not found")
      end
    end
  end
end
