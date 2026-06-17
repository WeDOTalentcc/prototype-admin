# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::LocalSearchJob, '#return_sourced' do
  subject(:job) { described_class.new }

  let(:account) { instance_double(Account, id: 1, tenant: "test_tenant") }
  let(:user) { instance_double(User, id: 1, account: account) }
  let(:sourcing) do
    instance_double(
      Sourcing,
      id: 1,
      user_id: 1,
      parameters: { "limit" => 50 },
      update!: true
    )
  end

  before do
    allow(Account).to receive(:find).and_return(account)
    allow(User).to receive(:find).and_return(user)
    allow(Apartment::Tenant).to receive(:switch).and_yield
    allow(Sourcing).to receive(:find).and_return(sourcing)
    allow(Rails.logger).to receive(:info)
    allow(Rails.logger).to receive(:error)
  end

  describe '#execute_search with return_sourced=true' do
    let(:search_results) do
      instance_double(
        'Searchkick::Results',
        total_count: 5,
        each_with_index: nil
      )
    end

    let(:sps_data) do
      [
        { sourced_profile_id: 101, name: "João Silva" },
        { sourced_profile_id: 102, name: "Maria Santos" }
      ]
    end

    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.instance_variable_set(:@return_sourced, true)

      allow(SourcedProfileSourcings::SearchService).to receive(:call).and_return(search_results)
      allow(search_results).to receive(:each_with_index).and_yield(sps_data[0], 0).and_yield(sps_data[1], 1)
      allow(SourcedProfile).to receive(:find_by).and_return(
        instance_double(SourcedProfile, id: 101),
        instance_double(SourcedProfile, id: 102)
      )
      allow(SourcedProfileSourcing).to receive(:find_or_create_by!).and_return(
        instance_double(SourcedProfileSourcing, id: 201, persisted?: true)
      )
      allow(job).to receive(:broadcast_sourcing_started)
      allow(job).to receive(:broadcast_sourcing_completed)
      allow(job).to receive(:broadcast_sourcing_profiles_found)
    end

    it 'chama SourcedProfileSourcings::SearchService ao invés de HybridSearchService' do
      expect(SourcedProfileSourcings::SearchService).to receive(:call).with(
        hash_including(
          query: "ruby developer",
          account_id: account.id,
          limit: 50
        )
      )

      job.send(:execute_search, sourcing.id, "ruby developer", "{}", "{}")
    end

    it 'não chama HybridSearchService' do
      expect(Candidates::Search::HybridSearchService).not_to receive(:new)

      job.send(:execute_search, sourcing.id, "ruby developer", "{}", "{}")
    end

    it 'processa sourced_profile_sourcings encontrados' do
      expect(SourcedProfile).to receive(:find_by).at_least(:once)

      job.send(:execute_search, sourcing.id, "ruby developer", "{}", "{}")
    end

    it 'cria SourcedProfileSourcing linkando ao novo sourcing' do
      expect(SourcedProfileSourcing).to receive(:find_or_create_by!).with(
        hash_including(
          sourcing_id: sourcing.id,
          account_id: account.id,
          user_id: user.id
        )
      ).at_least(:once)

      job.send(:execute_search, sourcing.id, "ruby developer", "{}", "{}")
    end

    it 'marca search_source como local_sourced' do
      new_sps = instance_double(SourcedProfileSourcing, is_deleted: nil, search_source: nil)

      expect(SourcedProfileSourcing).to receive(:find_or_create_by!).and_yield(new_sps).and_return(
        instance_double(SourcedProfileSourcing, id: 201, persisted?: true)
      )
      expect(new_sps).to receive(:is_deleted=).with(false)
      expect(new_sps).to receive(:search_source=).with("local_sourced")

      job.send(:execute_search, sourcing.id, "ruby", "{}", "{}")
    end

    it 'atualiza results_count do sourcing' do
      expect(sourcing).to receive(:update!).with(hash_including(:results_count)).at_least(:once)

      job.send(:execute_search, sourcing.id, "ruby", "{}", "{}")
    end

    it 'marca sourcing como done' do
      expect(sourcing).to receive(:update!).with(status: "done")

      job.send(:execute_search, sourcing.id, "ruby", "{}", "{}")
    end

    it 'loga que está usando modo SourcedProfileSourcing' do
      job.send(:execute_search, sourcing.id, "ruby", "{}", "{}")

      expect(Rails.logger).to have_received(:info).with(/MODO: Busca em SourcedProfileSourcing/).at_least(:once)
    end
  end

  describe '#execute_search with return_sourced=false' do
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

      allow(Candidates::Search::HybridSearchService).to receive(:new).and_return(hybrid_service)
      allow(hybrid_service).to receive(:search).and_return(search_result)
      allow(job).to receive(:broadcast_sourcing_started)
      allow(job).to receive(:broadcast_sourcing_completed)
      allow(job).to receive(:process_candidates_batch).and_return(0)
      allow(job).to receive(:broadcast_sourcing_profiles_found)
      allow(job).to receive(:broadcast_profiles_processing_completed)
      allow(Rails.cache).to receive(:write)
    end

    it 'usa HybridSearchService (fluxo padrão)' do
      expect(Candidates::Search::HybridSearchService).to receive(:new).with(
        account_id: account.id,
        tenant: account.tenant
      )

      job.send(:execute_search, sourcing.id, "ruby developer", "{}", "{}")
    end

    it 'não chama SourcedProfileSourcings::SearchService' do
      expect(SourcedProfileSourcings::SearchService).not_to receive(:call)

      job.send(:execute_search, sourcing.id, "ruby developer", "{}", "{}")
    end

    it 'processa candidates via process_candidates_batch' do
      expect(job).to receive(:process_candidates_batch)

      job.send(:execute_search, sourcing.id, "ruby", "{}", "{}")
    end
  end

  describe '#build_sourced_profile_sourcings_where' do
    before do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
    end

    it 'extrai city e state dos user_filters' do
      user_filters = { city: "São Paulo", state: "SP", role_name: "Developer" }

      result = job.send(:build_sourced_profile_sourcings_where, user_filters)

      expect(result).to eq({ city: "São Paulo", state: "SP" })
    end

    it 'retorna hash vazio se user_filters vazio' do
      result = job.send(:build_sourced_profile_sourcings_where, {})
      expect(result).to eq({})
    end

    it 'ignora campos que não sejam city ou state' do
      user_filters = { role_name: "Developer", skills: [ "Ruby" ] }

      result = job.send(:build_sourced_profile_sourcings_where, user_filters)

      expect(result).to eq({})
    end
  end
end
