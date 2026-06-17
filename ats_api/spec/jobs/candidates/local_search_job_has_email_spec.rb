# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::LocalSearchJob, '#has_email filter' do
  subject(:job) { described_class.new }

  let(:account) { instance_double(Account, id: 1, tenant: "test_tenant") }
  let(:user) { instance_double(User, id: 1, account: account) }
  let(:sourcing_with_has_email) do
    instance_double(
      Sourcing,
      id: 1,
      user_id: 1,
      parameters: { "limit" => 50, "has_email" => true },
      update!: true
    )
  end
  let(:sourcing_without_has_email) do
    instance_double(
      Sourcing,
      id: 2,
      user_id: 1,
      parameters: { "limit" => 50 },
      update!: true
    )
  end

  before do
    allow(Account).to receive(:find).and_return(account)
    allow(User).to receive(:find).and_return(user)
    allow(Apartment::Tenant).to receive(:switch).and_yield
    allow(Rails.logger).to receive(:info)
    allow(Rails.logger).to receive(:error)
  end

  describe '#apply_has_email_filter' do
    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
    end

    context 'quando has_email: true está presente' do
      let(:user_filters) { { city: "São Paulo" } }
      let(:sourcing_params) { { "has_email" => true } }

      it 'adiciona has_emails: true aos filtros' do
        result = job.send(:apply_has_email_filter, user_filters, sourcing_params)

        expect(result).to include(has_emails: true)
        expect(result[:city]).to eq("São Paulo")
      end

      it 'loga que está aplicando o filtro' do
        expect(Rails.logger).to receive(:info).with(/Aplicando filtro has_email=true/)

        job.send(:apply_has_email_filter, user_filters, sourcing_params)
      end
    end

    context 'quando has_email não está presente' do
      let(:user_filters) { { city: "São Paulo" } }
      let(:sourcing_params) { { "limit" => 50 } }

      it 'não adiciona filtro has_emails' do
        result = job.send(:apply_has_email_filter, user_filters, sourcing_params)

        expect(result).not_to have_key(:has_emails)
        expect(result[:city]).to eq("São Paulo")
      end

      it 'não loga "Aplicando filtro"' do
        expect(Rails.logger).not_to receive(:info).with(/Aplicando filtro has_email=true/)

        job.send(:apply_has_email_filter, user_filters, sourcing_params)
      end
    end

    context 'quando has_email: false' do
      let(:user_filters) { { city: "São Paulo" } }
      let(:sourcing_params) { { "has_email" => false } }

      it 'não adiciona filtro has_emails' do
        result = job.send(:apply_has_email_filter, user_filters, sourcing_params)

        expect(result).not_to have_key(:has_emails)
      end
    end
  end

  describe '#execute_search com has_email filter' do
    let(:hybrid_service) { instance_double(Candidates::Search::HybridSearchService) }
    let(:search_result) do
      instance_double(
        'SearchResult',
        candidates: [],
        metadata: {},
        explanation: {},
        search_meta_by_id: {}
      )
    end

    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.instance_variable_set(:@return_sourced, false)

      allow(Sourcing).to receive(:find).with(1).and_return(sourcing_with_has_email)
      allow(Sourcing).to receive(:find).with(2).and_return(sourcing_without_has_email)
      allow(Candidates::Search::HybridSearchService).to receive(:new).and_return(hybrid_service)
      allow(hybrid_service).to receive(:search).and_return(search_result)
      allow(job).to receive(:broadcast_sourcing_started)
      allow(job).to receive(:broadcast_sourcing_completed)
      allow(job).to receive(:process_candidates_batch).and_return(0)
      allow(job).to receive(:broadcast_sourcing_profiles_found)
      allow(job).to receive(:broadcast_profiles_processing_completed)
      allow(Rails.cache).to receive(:write)
    end

    context 'quando has_email: true está no sourcing' do
      it 'passa has_emails: true para HybridSearchService' do
        expect(hybrid_service).to receive(:search).with(
          "ruby developer",
          user_filters: hash_including(has_emails: true),
          limit: Candidates::LocalSearchJob::POOL_SIZE,
          debug: true
        )

        job.send(:execute_search, 1, "ruby developer", "{}", "{}")
      end
    end

    context 'quando has_email não está no sourcing' do
      it 'não passa has_emails para HybridSearchService' do
        expect(hybrid_service).to receive(:search) do |query, **options|
          expect(query).to eq("ruby developer")
          expect(options[:user_filters]).not_to have_key(:has_emails)
          expect(options[:limit]).to eq(Candidates::LocalSearchJob::POOL_SIZE)
          expect(options[:debug]).to be true
          search_result
        end

        job.send(:execute_search, 2, "ruby developer", "{}", "{}")
      end
    end
  end

  describe 'return_sourced com has_email filter' do
    let(:search_results) do
      instance_double('Searchkick::Results', total_count: 5, each_with_index: nil)
    end

    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.instance_variable_set(:@return_sourced, true)

      allow(Sourcing).to receive(:find).with(1).and_return(sourcing_with_has_email)
      allow(SourcedProfileSourcings::SearchService).to receive(:call).and_return(search_results)
      allow(job).to receive(:broadcast_sourcing_started)
      allow(job).to receive(:broadcast_sourcing_completed)
      allow(job).to receive(:process_sourced_profile_sourcings)
    end

    it 'passa has_emails: true para SourcedProfileSourcings::SearchService' do
      expect(SourcedProfileSourcings::SearchService).to receive(:call) do |args|
        expect(args[:where]).to include(has_emails: true)
        expect(args[:query]).to eq("ruby")
        expect(args[:account_id]).to eq(account.id)
        search_results
      end

      job.send(:execute_search, 1, "ruby", "{}", "{}")
    end
  end
end
