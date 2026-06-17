# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::GlobalSearchStrategy do
  let(:account) { create(:account, pearch_credits: 500) }
  let(:user) { create(:user, account: account) }
  let(:strategy) { described_class.new(account: account, user: user) }

  let(:base_candidate) do
    create(:candidate,
      account: account,
      name: "João Silva",
      role_name: "Senior Ruby Developer",
      current_company: "Tech Corp",
      city: "São Paulo",
      state: "SP"
    )
  end

  let(:pearch_search_service) { instance_double(Pearch::SearchService) }
  let(:profile_synthesizer) { instance_double(Candidates::SimilarCandidates::ProfileSynthesizer) }

  let(:synthesis) do
    {
      query: "senior ruby developer backend microservices",
      custom_filters: {
        locations: [ "São Paulo, SP" ],
        keywords: [ "Ruby", "Rails" ],
        titles: [ "Senior Developer" ],
        min_total_experience_years: 5
      },
      explanation: "Senior Ruby developers"
    }
  end

  let(:pearch_response) do
    {
      "uuid" => "search-123",
      "thread_id" => "thread-456",
      "status" => "completed",
      "duration" => 2.5,
      "credits_used" => 50,
      "credits_remaining" => 450,
      "search_results" => [
        {
          "docid" => "pedro-lima-123",
          "score" => 4,
          "profile" => {
            "first_name" => "Pedro",
            "last_name" => "Lima",
            "title" => "Tech Lead",
            "summary" => "Experienced developer",
            "linkedin_slug" => "pedro-lima",
            "location" => "São Paulo, SP, Brazil",
            "total_experience_years" => 8,
            "expertise" => [ "Ruby", "Rails" ],
            "has_emails" => true,
            "has_phone_numbers" => false,
            "experiences" => [
              { "company" => "iFood", "title" => "Tech Lead", "start_date" => "2022-01", "end_date" => nil }
            ]
          },
          "insights" => {
            "score" => 85,
            "explanation" => "Strong match"
          }
        }
      ]
    }
  end

  before do
    allow(Candidates::SimilarCandidates::ProfileSynthesizer).to receive(:new).and_return(profile_synthesizer)
    allow(profile_synthesizer).to receive(:call).and_return(synthesis)
    allow(Pearch::SearchService).to receive(:new).and_return(pearch_search_service)
    allow(pearch_search_service).to receive(:search).and_return(pearch_response)
  end

  describe "#search" do
    context "with valid base candidates and sufficient credits" do
      it "synthesizes profile" do
        strategy.search(base_candidates: [ base_candidate ])

        expect(profile_synthesizer).to have_received(:call).with([ base_candidate ])
      end

      it "calls Pearch API with correct params" do
        strategy.search(base_candidates: [ base_candidate ], pearch_options: { type: "pro", limit: 10 })

        expect(pearch_search_service).to have_received(:search) do |**args|
          expect(args[:query]).to eq(synthesis[:query])
          expect(args[:type]).to eq("pro")
          expect(args[:limit]).to eq(10)
          expect(args[:insights]).to be true
          expect(args[:profile_scoring]).to be true
          expect(args[:custom_filters]).to eq(synthesis[:custom_filters])
        end
      end

      it "includes exclude_docids in blacklist" do
        strategy.search(
          base_candidates: [ base_candidate ],
          exclude_docids: [ "existing-1", "existing-2" ]
        )

        expect(pearch_search_service).to have_received(:search) do |**args|
          expect(args[:docid_blacklist]).to include("existing-1", "existing-2")
        end
      end

      it "returns normalized results" do
        result = strategy.search(base_candidates: [ base_candidate ])

        expect(result[:results]).to be_an(Array)
        expect(result[:results].size).to eq(1)

        first_result = result[:results].first
        expect(first_result[:docid]).to eq("pedro-lima-123")
        expect(first_result[:name]).to eq("Pedro Lima")
        expect(first_result[:title]).to eq("Tech Lead")
        expect(first_result[:current_company]).to eq("iFood")
        expect(first_result[:pearch_score]).to eq(4)
        expect(first_result[:expertise]).to include("Ruby", "Rails")
      end

      it "returns synthesis and credits info" do
        result = strategy.search(base_candidates: [ base_candidate ])

        expect(result[:synthesis]).to eq(synthesis)
        expect(result[:credits_used]).to eq(50)
        expect(result[:credits_remaining]).to eq(450)
      end
    end

    context "with pearch options" do
      it "passes show_emails option" do
        strategy.search(
          base_candidates: [ base_candidate ],
          pearch_options: { show_emails: true }
        )

        expect(pearch_search_service).to have_received(:search) do |**args|
          expect(args[:reveal_emails]).to be true
        end
      end

      it "passes show_phone_numbers option" do
        strategy.search(
          base_candidates: [ base_candidate ],
          pearch_options: { show_phone_numbers: true }
        )

        expect(pearch_search_service).to have_received(:search) do |**args|
          expect(args[:reveal_phones]).to be true
        end
      end

      it "defaults to pro type with limit 10" do
        strategy.search(base_candidates: [ base_candidate ], pearch_options: {})

        expect(pearch_search_service).to have_received(:search) do |**args|
          expect(args[:type]).to eq("pro")
          expect(args[:limit]).to eq(10)
        end
      end
    end

    context "with insufficient credits" do
      let(:account) { create(:account, pearch_credits: 10) }

      it "raises InsufficientCreditsError and returns empty result" do
        result = strategy.search(
          base_candidates: [ base_candidate ],
          pearch_options: { type: "pro", limit: 10 }
        )

        expect(result[:results]).to be_empty
        expect(result[:error]).to eq("insufficient_credits")
        expect(result[:error_message]).to include("insufficient_credits")
      end
    end

    context "when base candidates is empty" do
      it "returns empty result with error" do
        result = strategy.search(base_candidates: [])

        expect(result[:results]).to be_empty
        expect(result[:error]).to eq("No base candidates provided")
      end
    end

    context "when Pearch API fails" do
      before do
        allow(pearch_search_service).to receive(:search).and_raise(StandardError.new("API Error"))
      end

      it "returns empty result with error" do
        result = strategy.search(base_candidates: [ base_candidate ])

        expect(result[:results]).to be_empty
        expect(result[:error]).to eq("search_failed")
        expect(result[:error_message]).to include("API Error")
      end
    end

    context "cost estimation" do
      it "estimates pro search cost correctly" do
        allow(pearch_search_service).to receive(:search)

        strategy.search(
          base_candidates: [ base_candidate ],
          pearch_options: { type: "pro", limit: 10 }
        )

        expect(pearch_search_service).to have_received(:search)
      end

      it "includes email reveal cost" do
        allow(pearch_search_service).to receive(:search)

        strategy.search(
          base_candidates: [ base_candidate ],
          pearch_options: { type: "pro", limit: 10, show_emails: true }
        )

        expect(pearch_search_service).to have_received(:search)
      end
    end
  end
end
