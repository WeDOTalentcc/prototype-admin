# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::TextSearchService do
  let(:account) { create(:account) }
  let(:service) { described_class.new(account_id: account.id) }

  describe "#search" do
    context "when query is blank" do
      it "returns empty array" do
        expect(service.search(query: "", exclude_ids: [])).to eq([])
        expect(service.search(query: nil, exclude_ids: [])).to eq([])
      end
    end

    context "when Searchkick raises error" do
      before do
        allow(Candidate).to receive(:search).and_raise(Searchkick::Error.new("connection failed"))
      end

      it "returns empty array" do
        expect(service.search(query: "ruby rails", exclude_ids: [])).to eq([])
      end

      it "logs error" do
        allow(Rails.logger).to receive(:error)

        service.search(query: "ruby rails", exclude_ids: [])

        expect(Rails.logger).to have_received(:error)
          .with(match(/TextSearch.*Searchkick error/))
      end
    end

    context "when unexpected error occurs" do
      before do
        allow(Candidate).to receive(:search).and_raise(StandardError.new("unexpected"))
      end

      it "returns empty array gracefully" do
        expect(service.search(query: "ruby rails", exclude_ids: [])).to eq([])
      end
    end
  end
end
