# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::LocalSearchJob, "#pagination" do
  subject(:job) { described_class.new }

  let(:account) { instance_double(Account, id: 1, tenant: "test_tenant") }
  let(:user) { instance_double(User, id: 10) }

  let(:sourcing) do
    instance_double(
      Sourcing,
      id: 100,
      user_id: 10,
      parameters: { "limit" => 50 },
      sourced_profiles: sourced_profiles_relation,
      local_results_count: 0,
      global_results_count: 0,
      update!: true
    )
  end

  let(:sourced_profiles_relation) { instance_double(ActiveRecord::Relation) }

  let(:candidates) do
    (1..50).map do |i|
      instance_double(
        Candidate, id: i, name: "Candidate #{i}", email: "c#{i}@example.com",
        phone: "1199900000#{i}", mobile_phone: nil, cpf: nil, date_birth: nil,
        role_name: "Developer", self_introduction: "Dev #{i}", avatar_public_url: nil,
        gender: nil, marital_status: nil, city: "SP", state: "SP", country: "BR",
        remote_work: true, mobility: false, current_company: "Company #{i}",
        position_level: "senior", curriculum_text: "cv text #{i}",
        linkedin_slug: nil, linkedin: nil
      )
    end
  end

  let(:search_result) do
    Candidates::Search::HybridSearchService::Result.new(
      candidates: candidates,
      metadata: { total: 50 },
      explanation: nil,
      search_meta_by_id: candidates.each_with_object({}) { |c, h| h[c.id] = { source: "hybrid", score: 1.0 - (c.id * 0.01) } }
    )
  end

  let(:hybrid_service) { instance_double(Candidates::Search::HybridSearchService) }

  before do
    allow(Account).to receive(:find).with(1).and_return(account)
    allow(User).to receive(:find).with(10).and_return(user)
    allow(Apartment::Tenant).to receive(:switch).with("test_tenant").and_yield
    allow(Sourcing).to receive(:find).with(100).and_return(sourcing)
    allow(SourcingChannel).to receive(:broadcast_to)
    allow(Rails.logger).to receive(:info)
    allow(Rails.logger).to receive(:error)

    allow(Candidates::Search::HybridSearchService).to receive(:new).and_return(hybrid_service)
    allow(hybrid_service).to receive(:search).and_return(search_result)

    allow(sourced_profiles_relation).to receive(:find_by).and_return(nil)
    allow(SourcedProfiles::ProfileMatchingService).to receive_message_chain(:new, :find_duplicate).and_return(nil)
    allow(SourcedProfiles::CandidateEnrichmentService).to receive(:call)

    profile = instance_double(SourcedProfile, id: 50, provider: "local", curriculum_text: "text")
    allow(SourcedProfile).to receive(:new).and_return(profile)
    allow(profile).to receive(:save!)
    allow(SourcedProfileSourcing).to receive(:create!)

    allow(Rails.cache).to receive(:write)
  end

  describe "#execute_candidates_search" do
    it "searches with POOL_SIZE instead of original limit" do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.send(:execute_candidates_search, sourcing, "ruby developer", {}, 50)

      expect(hybrid_service).to have_received(:search).with(
        "ruby developer",
        user_filters: {},
        limit: Candidates::LocalSearchJob::POOL_SIZE,
        debug: true
      )
    end

    it "caches the full pool in Redis" do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.send(:execute_candidates_search, sourcing, "ruby developer", {}, 50)

      expect(Rails.cache).to have_received(:write).with(
        "sourcing_pool:100:local",
        hash_including(
          candidate_ids: candidates.map(&:id),
          total: 50,
          page_size: Candidates::LocalSearchJob::PAGE_SIZE
        ),
        expires_in: Candidates::LocalSearchJob::POOL_TTL
      )
    end

    it "only processes first PAGE_SIZE candidates" do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.send(:execute_candidates_search, sourcing, "ruby developer", {}, 50)

      expect(sourcing).to have_received(:update!).with(
        results_count: Candidates::LocalSearchJob::PAGE_SIZE,
        local_results_count: Candidates::LocalSearchJob::PAGE_SIZE
      )
    end

    it "broadcasts profiles_processing_completed" do
      job.instance_variable_set(:@account, account)
      job.instance_variable_set(:@user, user)
      job.send(:execute_candidates_search, sourcing, "ruby developer", {}, 50)

      expect(SourcingChannel).to have_received(:broadcast_to).with(
        "10_sourcing_100",
        hash_including(type: "profiles_processing_completed")
      )
    end
  end
end
