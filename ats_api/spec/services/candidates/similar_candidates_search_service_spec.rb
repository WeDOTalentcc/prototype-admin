# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidatesSearchService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:service) { described_class.new(account: account, user: user) }

  let(:base_candidate) do
    create(:candidate, account: account, name: "Ana Costa", role_name: "Senior Ruby Developer",
           current_company: "Nubank", curriculum_text: "ruby rails postgresql microservices fintech")
  end

  let(:similar_candidate) do
    create(:candidate, account: account, name: "Pedro Lima", role_name: "Tech Lead Ruby",
           current_company: "iFood", curriculum_text: "ruby rails redis microservices backend")
  end

  let(:distant_candidate) do
    create(:candidate, account: account, name: "Maria Santos", role_name: "Marketing Manager",
           current_company: "Magazine Luiza", curriculum_text: "marketing digital campaigns branding")
  end

  let(:base_embedding_vector) { Array.new(768) { 0.5 } }
  let(:similar_embedding_vector) { Array.new(768) { 0.48 } }
  let(:distant_embedding_vector) { Array.new(768) { -0.3 } }

  before do
    allow_any_instance_of(Candidate).to receive(:sync_vector_after_commit)
    allow_any_instance_of(SourcedProfileSourcing).to receive(:enqueue_ai_analysis)
    allow_any_instance_of(SourcedProfileSourcing).to receive(:enqueue_stats_recalculation)
  end

  describe "#call" do
    context "with valid single candidate" do
      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:similar_emb) { create(:embedding, reference: similar_candidate, embedding: similar_embedding_vector) }
      let!(:distant_emb) { create(:embedding, reference: distant_candidate, embedding: distant_embedding_vector) }

      it "returns similar candidates ordered by similarity" do
        result = service.call(candidate_ids: [ base_candidate.id ])

        expect(result[:search_type]).to eq("similarity")
        expect(result[:mode]).to eq("local")
        expect(result[:base_candidates].size).to eq(1)
        expect(result[:base_candidates].first[:id]).to eq(base_candidate.id)
        expect(result[:similar_candidates]).to be_an(Array)
      end

      it "creates a sourcing record" do
        expect {
          service.call(candidate_ids: [ base_candidate.id ])
        }.to change(Sourcing, :count).by(1)

        sourcing = Sourcing.last
        expect(sourcing.provider).to eq("local")
        expect(sourcing.query).to include("Similar to")
        expect(sourcing.parameters["search_type"]).to eq("similarity")
        expect(sourcing.parameters["base_candidate_ids"]).to eq([ base_candidate.id ])
        expect(sourcing.status).to eq("done")
      end

      it "creates sourced profiles and sourced profile sourcings" do
        result = service.call(candidate_ids: [ base_candidate.id ])
        found_count = result[:similar_candidates].size

        next if found_count.zero?

        expect(SourcedProfileSourcing.where(search_source: "similarity").count).to eq(found_count)
      end

      it "excludes the base candidate from results" do
        result = service.call(candidate_ids: [ base_candidate.id ])

        candidate_ids_in_results = result[:similar_candidates].map { |c| c[:candidate_id] }
        expect(candidate_ids_in_results).not_to include(base_candidate.id)
      end

      it "includes similarity score as percentage" do
        result = service.call(candidate_ids: [ base_candidate.id ])

        next if result[:similar_candidates].empty?

        result[:similar_candidates].each do |sc|
          expect(sc[:similarity_score]).to be_a(Float)
          expect(sc[:similarity_score]).to be_between(0, 100)
        end
      end

      it "includes shared signals" do
        result = service.call(candidate_ids: [ base_candidate.id ])

        next if result[:similar_candidates].empty?

        result[:similar_candidates].each do |sc|
          expect(sc[:shared_signals]).to be_an(Array)
        end
      end

      it "includes metadata with search info" do
        result = service.call(candidate_ids: [ base_candidate.id ])

        expect(result[:metadata][:embedding_model]).to eq("gemini-embedding-001")
        expect(result[:metadata][:search_method]).to eq("single")
        expect(result[:metadata][:base_count]).to eq(1)
        expect(result[:metadata][:duration_ms]).to be_a(Float)
      end
    end

    context "with multiple base candidates (centroid)" do
      let(:second_base) do
        create(:candidate, account: account, name: "Bruno Alves", role_name: "Senior Dev",
               curriculum_text: "ruby rails api backend")
      end
      let(:second_embedding_vector) { Array.new(768) { 0.52 } }

      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:second_emb) { create(:embedding, reference: second_base, embedding: second_embedding_vector) }
      let!(:similar_emb) { create(:embedding, reference: similar_candidate, embedding: similar_embedding_vector) }

      it "uses centroid method for multiple candidates" do
        result = service.call(candidate_ids: [ base_candidate.id, second_base.id ])

        expect(result[:metadata][:search_method]).to eq("centroid")
        expect(result[:metadata][:base_count]).to eq(2)
        expect(result[:base_candidates].size).to eq(2)
      end

      it "creates sourcing with multi-candidate query" do
        service.call(candidate_ids: [ base_candidate.id, second_base.id ])

        sourcing = Sourcing.last
        expect(sourcing.query).to include("2 candidates")
        expect(sourcing.parameters["method"]).to eq("centroid")
      end
    end

    context "with job_id filter" do
      let(:job) { create(:job, account: account) }
      let(:selective_process) { create(:selective_process, job: job, account: account) }
      let(:applied_candidate) do
        create(:candidate, account: account, name: "Candidato Aplicado",
               curriculum_text: "ruby rails devops")
      end

      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:applied_emb) { create(:embedding, reference: applied_candidate, embedding: Array.new(768) { 0.49 }) }
      let!(:similar_emb) { create(:embedding, reference: similar_candidate, embedding: similar_embedding_vector) }

      before do
        create(:apply, candidate: applied_candidate, job: job, selective_process: selective_process, account: account)
      end

      it "excludes candidates already applied to the job" do
        result = service.call(candidate_ids: [ base_candidate.id ], job_id: job.id)

        candidate_ids_in_results = result[:similar_candidates].map { |c| c[:candidate_id] }
        expect(candidate_ids_in_results).not_to include(applied_candidate.id)
      end

      it "reports excluded count" do
        result = service.call(candidate_ids: [ base_candidate.id ], job_id: job.id)

        expect(result[:excluded_count]).to be >= 1
      end
    end

    context "with exclude_ids" do
      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:similar_emb) { create(:embedding, reference: similar_candidate, embedding: similar_embedding_vector) }

      it "excludes specified candidate IDs" do
        result = service.call(
          candidate_ids: [ base_candidate.id ],
          exclude_ids: [ similar_candidate.id ]
        )

        candidate_ids_in_results = result[:similar_candidates].map { |c| c[:candidate_id] }
        expect(candidate_ids_in_results).not_to include(similar_candidate.id)
      end
    end

    context "with threshold filter" do
      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:similar_emb) { create(:embedding, reference: similar_candidate, embedding: similar_embedding_vector) }

      it "returns fewer results with higher threshold" do
        low_result = service.call(candidate_ids: [ base_candidate.id ], threshold: 0.30)
        high_result = service.call(candidate_ids: [ base_candidate.id ], threshold: 0.99)

        expect(high_result[:total]).to be <= low_result[:total]
      end
    end

    context "when candidate has no embedding" do
      it "raises error with missing IDs" do
        expect {
          service.call(candidate_ids: [ base_candidate.id ])
        }.to raise_error(ArgumentError, /missing_embeddings/)
      end
    end

    context "when candidate does not exist" do
      it "raises RecordNotFound" do
        expect {
          service.call(candidate_ids: [ 999_999 ])
        }.to raise_error(ActiveRecord::RecordNotFound)
      end
    end

    context "when no results above threshold" do
      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:distant_emb) { create(:embedding, reference: distant_candidate, embedding: distant_embedding_vector) }

      it "returns empty results without creating sourcing" do
        result = service.call(candidate_ids: [ base_candidate.id ], threshold: 0.999)

        expect(result[:similar_candidates]).to be_empty
        expect(result[:total]).to eq(0)
        expect(result[:sourcing_id]).to be_nil
      end
    end

    context "when sourced profile already exists for candidate" do
      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:similar_emb) { create(:embedding, reference: similar_candidate, embedding: similar_embedding_vector) }

      let!(:existing_profile) do
        create(:sourced_profile, account: account, candidate: similar_candidate,
               provider: "local", name: similar_candidate.name)
      end

      it "reuses existing sourced profile instead of creating new" do
        result = service.call(candidate_ids: [ base_candidate.id ])

        next if result[:similar_candidates].empty?

        similar_entry = result[:similar_candidates].find { |c| c[:candidate_id] == similar_candidate.id }
        next unless similar_entry

        expect(similar_entry[:sourced_profile_id]).to eq(existing_profile.id)
      end
    end

    context "with invalid params" do
      it "raises error when candidate_ids is empty" do
        expect {
          service.call(candidate_ids: [])
        }.to raise_error(ArgumentError, /candidate_ids/)
      end

      it "raises error when more than 10 candidates" do
        expect {
          service.call(candidate_ids: Array.new(11, 1))
        }.to raise_error(ArgumentError, /candidate_ids/)
      end

      it "raises error when limit is out of range" do
        create(:embedding, reference: base_candidate, embedding: base_embedding_vector)

        expect {
          service.call(candidate_ids: [ base_candidate.id ], limit: 0)
        }.to raise_error(ArgumentError, /limit/)
      end

      it "raises error when threshold is out of range" do
        create(:embedding, reference: base_candidate, embedding: base_embedding_vector)

        expect {
          service.call(candidate_ids: [ base_candidate.id ], threshold: 1.5)
        }.to raise_error(ArgumentError, /threshold/)
      end

      it "raises error when sources is not an array" do
        create(:embedding, reference: base_candidate, embedding: base_embedding_vector)

        expect {
          service.call(candidate_ids: [ base_candidate.id ], sources: "local")
        }.to raise_error(ArgumentError, /sources must be an array/)
      end

      it "raises error when sources contains invalid value" do
        create(:embedding, reference: base_candidate, embedding: base_embedding_vector)

        expect {
          service.call(candidate_ids: [ base_candidate.id ], sources: [ "invalid" ])
        }.to raise_error(ArgumentError, /sources must be an array/)
      end

      it "raises error when sources is empty" do
        create(:embedding, reference: base_candidate, embedding: base_embedding_vector)

        expect {
          service.call(candidate_ids: [ base_candidate.id ], sources: [])
        }.to raise_error(ArgumentError, /sources cannot be empty/)
      end
    end

    context "with sources parameter" do
      let!(:base_emb) { create(:embedding, reference: base_candidate, embedding: base_embedding_vector) }
      let!(:similar_emb) { create(:embedding, reference: similar_candidate, embedding: similar_embedding_vector) }

      let(:global_strategy) { instance_double(Candidates::SimilarCandidates::GlobalSearchStrategy) }
      let(:global_result) do
        {
          results: [
            {
              docid: "pearch-123",
              name: "Carlos Souza",
              title: "Senior Developer",
              current_company: "Remote Company",
              location: "Remote",
              pearch_score: 4,
              expertise: [ "Ruby", "Rails" ],
              insights: { score: 85 },
              profile_data: {
                "first_name" => "Carlos",
                "last_name" => "Souza",
                "title" => "Senior Developer",
                "linkedin_slug" => "carlos-souza",
                "location" => "Remote",
                "expertise" => [ "Ruby", "Rails" ],
                "experiences" => [],
                "educations" => []
              }
            }
          ],
          credits_used: 50,
          synthesis: { query: "ruby developer", explanation: "Senior Ruby developers" }
        }
      end

      before do
        allow(Candidates::SimilarCandidates::GlobalSearchStrategy).to receive(:new).and_return(global_strategy)
        allow(global_strategy).to receive(:search).and_return(global_result)
      end

      context "when sources includes only local" do
        it "runs only local search" do
          result = service.call(candidate_ids: [ base_candidate.id ], sources: [ "local" ])

          expect(result[:mode]).to eq("local")
          expect(result[:similar_candidates][:local]).to be_an(Array)
          expect(result[:similar_candidates][:global]).to be_empty
          expect(result[:local_count]).to be >= 0
          expect(result[:global_count]).to eq(0)
        end

        it "does not call global strategy" do
          service.call(candidate_ids: [ base_candidate.id ], sources: [ "local" ])

          expect(Candidates::SimilarCandidates::GlobalSearchStrategy).not_to have_received(:new)
        end
      end

      context "when sources includes only global" do
        let(:account_with_credits) { create(:account, pearch_credits: 500) }
        let(:user_with_credits) { create(:user, account: account_with_credits) }
        let(:service_with_credits) { described_class.new(account: account_with_credits, user: user_with_credits) }

        it "runs only global search" do
          result = service_with_credits.call(candidate_ids: [ base_candidate.id ], sources: [ "global" ])

          expect(result[:mode]).to eq("pearch")
          expect(result[:similar_candidates][:local]).to be_empty
          expect(result[:similar_candidates][:global]).to be_an(Array)
          expect(result[:local_count]).to eq(0)
          expect(result[:global_count]).to be >= 0
        end

        it "creates sourcing with pearch provider" do
          service_with_credits.call(candidate_ids: [ base_candidate.id ], sources: [ "global" ])

          sourcing = Sourcing.last
          expect(sourcing.provider).to eq("pearch")
          expect(sourcing.global_results_count).to be >= 0
          expect(sourcing.local_results_count).to eq(0)
        end
      end

      context "when sources includes both local and global (hybrid)" do
        let(:account_with_credits) { create(:account, pearch_credits: 500) }
        let(:user_with_credits) { create(:user, account: account_with_credits) }
        let(:service_with_credits) { described_class.new(account: account_with_credits, user: user_with_credits) }

        it "runs both searches" do
          result = service_with_credits.call(
            candidate_ids: [ base_candidate.id ],
            sources: [ "local", "global" ]
          )

          expect(result[:mode]).to eq("hybrid")
          expect(result[:similar_candidates][:local]).to be_an(Array)
          expect(result[:similar_candidates][:global]).to be_an(Array)
          expect(result[:total]).to eq(result[:local_count] + result[:global_count])
        end

        it "creates sourcing with hybrid provider" do
          service_with_credits.call(
            candidate_ids: [ base_candidate.id ],
            sources: [ "local", "global" ]
          )

          sourcing = Sourcing.last
          expect(sourcing.provider).to eq("hybrid")
          expect(sourcing.local_results_count).to be >= 0
          expect(sourcing.global_results_count).to be >= 0
          expect(sourcing.credits_used).to be_present
        end

        it "marks global results with source field" do
          result = service_with_credits.call(
            candidate_ids: [ base_candidate.id ],
            sources: [ "local", "global" ]
          )

          if result[:similar_candidates][:global].any?
            global_result = result[:similar_candidates][:global].first
            expect(global_result[:source]).to eq("global")
            expect(global_result[:docid]).to be_present
          end

          if result[:similar_candidates][:local].any?
            local_result = result[:similar_candidates][:local].first
            expect(local_result[:source]).to eq("local")
            expect(local_result[:candidate_id]).to be_present
          end
        end

        it "creates sourced profiles for global results" do
          result = service_with_credits.call(
            candidate_ids: [ base_candidate.id ],
            sources: [ "local", "global" ]
          )

          if result[:similar_candidates][:global].any?
            global_result = result[:similar_candidates][:global].first
            profile = SourcedProfile.find(global_result[:sourced_profile_id])

            expect(profile.provider).to eq("pearch")
            expect(profile.external_id).to eq(global_result[:docid])
          end
        end
      end

      context "when global search fails gracefully" do
        before do
          allow(global_strategy).to receive(:search).and_return(
            { results: [], error: "insufficient_credits", error_message: "insufficient_credits:100:50" }
          )
        end

        it "returns local results with warning" do
          result = service.call(
            candidate_ids: [ base_candidate.id ],
            sources: [ "local", "global" ]
          )

          expect(result[:similar_candidates][:local]).to be_an(Array)
          expect(result[:similar_candidates][:global]).to be_empty
          expect(result[:warnings]).to be_present
          expect(result[:warnings].first).to include("Insufficient Pearch credits")
        end
      end

      context "with pearch_options" do
        let(:account_with_credits) { create(:account, pearch_credits: 500) }
        let(:user_with_credits) { create(:user, account: account_with_credits) }
        let(:service_with_credits) { described_class.new(account: account_with_credits, user: user_with_credits) }

        it "passes pearch options to global strategy" do
          pearch_options = { type: "pro", limit: 15, show_emails: true }

          service_with_credits.call(
            candidate_ids: [ base_candidate.id ],
            sources: [ "global" ],
            pearch_options: pearch_options
          )

          expect(global_strategy).to have_received(:search) do |**args|
            expect(args[:pearch_options]).to eq(pearch_options)
          end
        end
      end
    end
  end
end
