require "rails_helper"

RSpec.describe Sourcings::CreateJobService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:sourcing) { create(:sourcing, account: account) }
  let(:candidates) { create_list(:candidate, 2, account: account) }
  let(:candidate_ids) { candidates.map(&:id) }
  let(:job_attrs) { { title: "Engenheiro Ruby", account_id: account.id } }

  subject(:service) do
    described_class.new(
      sourcing: sourcing,
      job_attributes: job_attrs,
      candidate_ids: candidate_ids,
      user: user
    )
  end

  describe "#call" do
    context "sucesso — cria job e applies" do
      it "retorna success? true com job criado" do
        result = service.call
        expect(result.success?).to be true
        expect(result.job).to be_persisted
      end
    end

    context "quando MoveToJobService levanta BulkApplyError" do
      before do
        allow(Sourcings::MoveToJobService).to receive(:call)
          .and_raise(Sourcings::MoveToJobService::BulkApplyError, "Falha ao adicionar candidato 42")
      end

      it "retorna success? false com mensagem clara" do
        result = service.call
        expect(result.success?).to be false
        expect(result.error).to include("Falha ao adicionar candidato")
      end

      it "nao persiste o Job — rollback completo" do
        expect { service.call }.not_to change(Job, :count)
      end
    end

    context "quando MoveToJobService retorna Result(success?: false)" do
      before do
        allow(Sourcings::MoveToJobService).to receive(:call)
          .and_return(Sourcings::MoveToJobService::Result.new(success?: false, error: "candidate_ids required"))
      end

      it "retorna success? false" do
        result = service.call
        expect(result.success?).to be false
      end

      it "nao persiste o Job — Rollback acionado" do
        expect { service.call }.not_to change(Job, :count)
      end
    end

    context "sem title" do
      let(:job_attrs) { { title: "" } }

      it "retorna erro antes de tocar o DB" do
        result = service.call
        expect(result.success?).to be false
        expect(result.error).to include("obrigatório")
        expect(Job.count).to eq(0)
      end
    end
  end
end
