require "rails_helper"

RSpec.describe Emails::Delivery::StrategyResolver do
  let(:dispatch) { instance_double("Dispatch", provider: "ms_graph", account_id: 1) }
  let(:delivery_args) do
    { to: "candidate@example.com", subject: "Vaga", body: "<p>Olá</p>", message: double("msg") }
  end

  describe ".deliver_with_fallback" do
    context "quando ms_graph entrega com sucesso" do
      before do
        allow_any_instance_of(Emails::Delivery::MsGraphStrategy).to receive(:deliver)
          .and_return({ success: true, provider: "ms_graph" })
      end

      it "retorna resultado do provider primário" do
        result = described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
        expect(result[:success]).to be true
        expect(result[:provider]).to eq("ms_graph")
        expect(result[:fallback_used]).to be_nil
      end

      it "nao chama MailgunStrategy" do
        expect_any_instance_of(Emails::Delivery::MailgunStrategy).not_to receive(:deliver)
        described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
      end
    end

    context "quando ms_graph falha e mailgun sucede" do
      before do
        allow_any_instance_of(Emails::Delivery::MsGraphStrategy).to receive(:deliver)
          .and_raise(Emails::ProviderUnavailable, "MS Graph indisponivel")
        allow_any_instance_of(Emails::Delivery::MailgunStrategy).to receive(:deliver)
          .and_return({ success: true, provider: "mailgun" })
      end

      it "retorna resultado do fallback com fallback_used: true" do
        result = described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
        expect(result[:success]).to be true
        expect(result[:fallback_used]).to be true
        expect(result[:fallback_provider]).to eq("mailgun")
      end

      it "inclui mensagem do erro primario no resultado" do
        result = described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
        expect(result[:primary_error]).to include("MS Graph")
      end
    end

    context "quando ms_graph falha e mailgun tambem falha" do
      before do
        allow_any_instance_of(Emails::Delivery::MsGraphStrategy).to receive(:deliver)
          .and_raise(Emails::ProviderUnavailable, "MS Graph down")
        allow_any_instance_of(Emails::Delivery::MailgunStrategy).to receive(:deliver)
          .and_raise(StandardError, "Mailgun também falhou")
      end

      it "re-raise o erro primario (nao o do fallback)" do
        expect {
          described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
        }.to raise_error(Emails::ProviderUnavailable, "MS Graph down")
      end
    end

    context "quando provider nao tem fallback configurado (mailgun)" do
      let(:dispatch) { instance_double("Dispatch", provider: "mailgun", account_id: 1) }

      before do
        allow_any_instance_of(Emails::Delivery::MailgunStrategy).to receive(:deliver)
          .and_raise(StandardError, "Mailgun error sem fallback")
      end

      it "re-raise o erro sem tentar fallback" do
        expect {
          described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
        }.to raise_error(StandardError, "Mailgun error sem fallback")
      end

      it "nao chama MsGraphStrategy como fallback" do
        expect_any_instance_of(Emails::Delivery::MsGraphStrategy).not_to receive(:deliver)
        begin
          described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
        rescue StandardError
        end
      end
    end

    context "com provider desconhecido" do
      let(:dispatch) { instance_double("Dispatch", provider: "carrier_pigeon", account_id: 1) }

      it "levanta ArgumentError" do
        expect {
          described_class.deliver_with_fallback(dispatch: dispatch, **delivery_args)
        }.to raise_error(ArgumentError, /Unknown provider/)
      end
    end
  end

  describe ".for (retro-compatibilidade)" do
    it "retorna instancia de MsGraphStrategy para ms_graph" do
      expect(described_class.for(dispatch)).to be_a(Emails::Delivery::MsGraphStrategy)
    end

    it "levanta ArgumentError para provider desconhecido" do
      bad_dispatch = instance_double("Dispatch", provider: "unknown")
      expect { described_class.for(bad_dispatch) }.to raise_error(ArgumentError)
    end
  end
end
