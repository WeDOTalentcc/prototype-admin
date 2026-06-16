# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::LocalSearchJob, '#has_phone and #has_email_or_phone filters' do
  subject(:job) { described_class.new }

  let(:account) { instance_double(Account, id: 1, tenant: "test_tenant") }
  let(:user) { instance_double(User, id: 1, account: account) }

  let(:sourcing_with_has_phone) do
    instance_double(
      Sourcing,
      id: 1,
      user_id: 1,
      parameters: { "limit" => 50, "has_phone" => true },
      update!: true
    )
  end

  let(:sourcing_with_has_email_or_phone) do
    instance_double(
      Sourcing,
      id: 2,
      user_id: 1,
      parameters: { "limit" => 50, "has_email_or_phone" => true },
      update!: true
    )
  end

  let(:sourcing_without_filters) do
    instance_double(
      Sourcing,
      id: 3,
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

  describe '#apply_has_phone_filter' do
    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
    end

    context 'quando has_phone: true está presente' do
      let(:user_filters) { { city: "São Paulo" } }
      let(:sourcing_params) { { "has_phone" => true } }

      it 'adiciona has_phone_numbers: true aos filtros' do
        result = job.send(:apply_has_phone_filter, user_filters, sourcing_params)

        expect(result).to include(has_phone_numbers: true)
        expect(result[:city]).to eq("São Paulo")
      end

      it 'loga que está aplicando o filtro' do
        expect(Rails.logger).to receive(:info).with(/Aplicando filtro has_phone=true/)

        job.send(:apply_has_phone_filter, user_filters, sourcing_params)
      end
    end

    context 'quando has_phone não está presente' do
      let(:user_filters) { { city: "São Paulo" } }
      let(:sourcing_params) { { "limit" => 50 } }

      it 'não adiciona filtro has_phone_numbers' do
        result = job.send(:apply_has_phone_filter, user_filters, sourcing_params)

        expect(result).not_to have_key(:has_phone_numbers)
        expect(result[:city]).to eq("São Paulo")
      end
    end

    context 'quando has_phone: false' do
      let(:user_filters) { { city: "São Paulo" } }
      let(:sourcing_params) { { "has_phone" => false } }

      it 'não adiciona filtro has_phone_numbers' do
        result = job.send(:apply_has_phone_filter, user_filters, sourcing_params)

        expect(result).not_to have_key(:has_phone_numbers)
      end
    end
  end

  describe '#apply_has_email_or_phone_filter' do
    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
    end

    context 'quando has_email_or_phone: true está presente' do
      let(:user_filters) { { city: "Rio de Janeiro" } }
      let(:sourcing_params) { { "has_email_or_phone" => true } }

      it 'adiciona has_contact: true aos filtros' do
        result = job.send(:apply_has_email_or_phone_filter, user_filters, sourcing_params)

        expect(result).to include(has_contact: true)
        expect(result[:city]).to eq("Rio de Janeiro")
      end

      it 'loga que está aplicando o filtro' do
        expect(Rails.logger).to receive(:info).with(/Aplicando filtro has_email_or_phone=true/)

        job.send(:apply_has_email_or_phone_filter, user_filters, sourcing_params)
      end
    end

    context 'quando has_email_or_phone não está presente' do
      let(:user_filters) { { city: "Rio de Janeiro" } }
      let(:sourcing_params) { { "limit" => 50 } }

      it 'não adiciona filtro has_contact' do
        result = job.send(:apply_has_email_or_phone_filter, user_filters, sourcing_params)

        expect(result).not_to have_key(:has_contact)
        expect(result[:city]).to eq("Rio de Janeiro")
      end
    end
  end

  describe '#execute_search com has_phone filter' do
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

      allow(Sourcing).to receive(:find).with(1).and_return(sourcing_with_has_phone)
      allow(Sourcing).to receive(:find).with(2).and_return(sourcing_with_has_email_or_phone)
      allow(Candidates::Search::HybridSearchService).to receive(:new).and_return(hybrid_service)
      allow(hybrid_service).to receive(:search).and_return(search_result)
      allow(job).to receive(:broadcast_sourcing_started)
      allow(job).to receive(:broadcast_sourcing_completed)
      allow(job).to receive(:process_candidates_batch).and_return(0)
      allow(job).to receive(:broadcast_sourcing_profiles_found)
      allow(job).to receive(:broadcast_profiles_processing_completed)
      allow(Rails.cache).to receive(:write)
    end

    context 'quando has_phone: true está no sourcing' do
      it 'passa has_phone_numbers: true para HybridSearchService' do
        expect(hybrid_service).to receive(:search).with(
          "desenvolvedor ruby",
          user_filters: hash_including(has_phone_numbers: true),
          limit: Candidates::LocalSearchJob::POOL_SIZE,
          debug: true
        )

        job.send(:execute_search, 1, "desenvolvedor ruby", "{}", "{}")
      end
    end

    context 'quando has_email_or_phone: true está no sourcing' do
      it 'passa has_contact: true para HybridSearchService' do
        expect(hybrid_service).to receive(:search).with(
          "python developer",
          user_filters: hash_including(has_contact: true),
          limit: Candidates::LocalSearchJob::POOL_SIZE,
          debug: true
        )

        job.send(:execute_search, 2, "python developer", "{}", "{}")
      end
    end
  end

  describe 'return_sourced com has_phone filters' do
    let(:search_results) do
      instance_double('Searchkick::Results', total_count: 5, each_with_index: nil)
    end

    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.instance_variable_set(:@return_sourced, true)

      allow(Sourcing).to receive(:find).with(1).and_return(sourcing_with_has_phone)
      allow(Sourcing).to receive(:find).with(2).and_return(sourcing_with_has_email_or_phone)
      allow(SourcedProfileSourcings::SearchService).to receive(:call).and_return(search_results)
      allow(job).to receive(:broadcast_sourcing_started)
      allow(job).to receive(:broadcast_sourcing_completed)
      allow(job).to receive(:process_sourced_profile_sourcings)
    end

    it 'passa has_phone_numbers: true para SourcedProfileSourcings::SearchService' do
      expect(SourcedProfileSourcings::SearchService).to receive(:call) do |args|
        expect(args[:where]).to include(has_phone_numbers: true)
        expect(args[:query]).to eq("java")
        expect(args[:account_id]).to eq(account.id)
        search_results
      end

      job.send(:execute_search, 1, "java", "{}", "{}")
    end

    it 'passa has_contact: true para SourcedProfileSourcings::SearchService' do
      expect(SourcedProfileSourcings::SearchService).to receive(:call) do |args|
        expect(args[:where]).to include(has_contact: true)
        expect(args[:query]).to eq("javascript")
        expect(args[:account_id]).to eq(account.id)
        search_results
      end

      job.send(:execute_search, 2, "javascript", "{}", "{}")
    end
  end
end
