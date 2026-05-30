require "rails_helper"

RSpec.describe Apify::LinkedinSearchExecutorService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:sourcing) { create(:sourcing, account: account, status: "pending") }

  subject(:service) do
    described_class.new(user: user, sourcing: sourcing, params: { query: "Ruby engineer" })
  end

  describe "#call com retry em falhas transitórias" do
    context "quando TimeoutError ocorre nas primeiras tentativas e depois sucede" do
      let(:result_set) { instance_double(Apify::LinkedinSearchService::ResultSet, total_count: 0, run_id: "r1", pages_scraped: 1, has_more?: false) }
      let(:empty_query) { instance_double(Apify::LinkedinSearchService::Query, estimated_cost: 0) }

      before do
        allow(result_set).to receive(:filter_map).and_return([])
        allow(result_set).to receive(:query).and_return(empty_query)
        call_count = 0
        allow_any_instance_of(Apify::LinkedinSearchService).to receive(:search) do
          call_count += 1
          raise Apify::LinkedinSearchService::TimeoutError, "timeout" if call_count < 3
          result_set
        end
        allow(service).to receive(:sleep) # não espera em teste
      end

      it "tenta até MAX_RETRIES vezes antes de suceder" do
        result = service.call
        expect(result[:success]).to be true
      end
    end

    context "quando TimeoutError ocorre em todas as tentativas" do
      before do
        allow_any_instance_of(Apify::LinkedinSearchService).to receive(:search)
          .and_raise(Apify::LinkedinSearchService::TimeoutError, "timeout always")
        allow(service).to receive(:sleep)
      end

      it "esgota MAX_RETRIES e retorna success: false" do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to include("tentativas")
      end

      it "chama LinkedinSearchService exatamente MAX_RETRIES vezes" do
        expect_any_instance_of(Apify::LinkedinSearchService).to receive(:search)
          .exactly(Apify::LinkedinSearchExecutorService::MAX_RETRIES).times
          .and_raise(Apify::LinkedinSearchService::TimeoutError)
        allow(service).to receive(:sleep)
        service.call
      end

      it "atualiza sourcing para status failed" do
        allow(service).to receive(:sleep)
        service.call
        expect(sourcing.reload.status).to eq("failed")
      end
    end

    context "quando RunFailedError ocorre (também retryable)" do
      before do
        allow_any_instance_of(Apify::LinkedinSearchService).to receive(:search)
          .and_raise(Apify::LinkedinSearchService::RunFailedError, "actor run failed")
        allow(service).to receive(:sleep)
      end

      it "retry e depois retorna falha" do
        result = service.call
        expect(result[:success]).to be false
      end
    end

    context "quando RateLimitError ocorre (não retryable — sem retry)" do
      before do
        allow_any_instance_of(Apify::LinkedinSearchService).to receive(:search)
          .and_raise(Apify::LinkedinSearchService::RateLimitError.new("rate limited", retry_after: 1.hour.from_now))
      end

      it "não retenta — retorna imediatamente com mensagem de rate limit" do
        expect_any_instance_of(Apify::LinkedinSearchService).to receive(:search).once
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to include("rate limit")
      end
    end

    context "delay exponencial entre retries" do
      before do
        allow_any_instance_of(Apify::LinkedinSearchService).to receive(:search)
          .and_raise(Apify::LinkedinSearchService::TimeoutError, "t")
      end

      it "usa delay exponencial baseado em RETRY_BASE_DELAY" do
        base = Apify::LinkedinSearchExecutorService::RETRY_BASE_DELAY
        expect(service).to receive(:sleep).with(base).ordered        # attempt 1 → delay 5
        expect(service).to receive(:sleep).with(base * 2).ordered    # attempt 2 → delay 10
        service.call
      end
    end
  end
end
