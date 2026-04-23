# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::IntentBasedRefinementService do
  let(:account) { create(:account) }
  let(:llm_client) { instance_double(GeminiClient) }
  let(:encoder) { instance_double(Embeddings::Encoder) }
  let(:service) { described_class.new(llm_client: llm_client, encoder: encoder) }

  let(:original_centroid) { Array.new(768) { rand } }
  let(:vectorial_refined) { Array.new(768) { rand } }

  describe "#refine_with_intent" do
    context "when disliked feedbacks are empty" do
      it "returns skipped IntentResult with vectorial embedding" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [],
          disliked_feedbacks: [],
          liked_candidates: []
        )

        expect(result).to be_a(described_class::IntentResult)
        expect(result.embedding).to eq(vectorial_refined)
        expect(result.skipped).to be true
      end
    end

    context "when disliked feedbacks have skill requirements" do
      let(:base_candidate) do
        create(:candidate,
          account: account,
          role_name: "Java Developer",
          data_raw: { "skills" => [ { "name" => "java" }, { "name" => "spring" } ] }
        )
      end

      let(:disliked_candidate) { create(:candidate, account: account) }

      let(:disliked_feedbacks) do
        [ {
          candidate_id: disliked_candidate.id,
          candidate: disliked_candidate,
          reason: "não sabe ruby on rails"
        } ]
      end

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "Senior Ruby on Rails developer with 5+ years experience", "elasticsearch_query": "Java Spring Ruby Rails backend senior", "must_have_skills": ["ruby", "rails"], "nice_to_have_skills": ["java", "spring"], "searchable_attributes": ["ruby", "rails", "senior"], "not_searchable_feedback": []}'
            }
          } ]
        }
      end

      let(:intent_embedding) { Array.new(768) { rand } }

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
        allow(encoder).to receive(:call).and_return(intent_embedding)
      end

      it "extracts intent and blends embeddings" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: []
        )

        expect(result).to be_a(described_class::IntentResult)
        expect(result.embedding).to be_a(Array)
        expect(result.embedding.size).to eq(768)
        expect(result.embedding).not_to eq(vectorial_refined)
        expect(result.skipped).to be false
        expect(result.description).to include("Ruby on Rails")
        expect(result.elasticsearch_query).to include("Java", "Ruby")
        expect(result.must_have_skills).to include("ruby", "rails")
        expect(result.nice_to_have_skills).to include("java", "spring")
        expect(result.searchable_attributes).to include("ruby", "rails")
      end

      it "calls LLM with correct context including skills" do
        service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: []
        )

        expect(llm_client).to have_received(:chat) do |args|
          prompt = args[:messages].last[:content]
          expect(prompt).to include("não sabe ruby on rails")
          expect(prompt).to include(base_candidate.name)
          expect(prompt).to include("java")
          expect(prompt).to include("skills:")
        end
      end

      it "generates embedding from extracted description" do
        service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: []
        )

        expect(encoder).to have_received(:call)
          .with("Senior Ruby on Rails developer with 5+ years experience")
      end

      it "normalizes the blended result" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: []
        )

        magnitude = Math.sqrt(result.embedding.sum { |v| v**2 })
        expect(magnitude).to be_within(0.01).of(1.0)
      end

      it "includes liked candidates skills in context" do
        liked_candidate = create(:candidate,
          account: account,
          role_name: "Ruby Developer",
          data_raw: { "skills" => [ { "name" => "ruby" }, { "name" => "rails" } ] }
        )

        service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: [ liked_candidate ]
        )

        expect(llm_client).to have_received(:chat) do |args|
          prompt = args[:messages].last[:content]
          expect(prompt).to include(liked_candidate.name)
          expect(prompt).to include("ruby")
          expect(prompt).to include("rails")
        end
      end
    end

    context "when LLM call fails" do
      let(:base_candidate) { create(:candidate, account: account) }
      let(:disliked_feedbacks) do
        [ { candidate_id: 1, candidate: base_candidate, reason: "não sabe rails" } ]
      end

      before do
        allow(llm_client).to receive(:chat).and_raise(StandardError.new("API error"))
      end

      it "returns skipped IntentResult as fallback" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: []
        )

        expect(result.embedding).to eq(vectorial_refined)
        expect(result.skipped).to be true
      end

      it "logs error" do
        allow(Rails.logger).to receive(:error)

        service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: []
        )

        expect(Rails.logger).to have_received(:error)
          .with(match(/IntentRefinement.*LLM extraction failed/))
      end
    end

    context "when embedding generation fails" do
      let(:base_candidate) { create(:candidate, account: account) }
      let(:disliked_feedbacks) do
        [ { candidate_id: 1, candidate: base_candidate, reason: "não sabe rails" } ]
      end

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "Ruby developer", "elasticsearch_query": "Ruby developer", "must_have_skills": ["ruby"], "nice_to_have_skills": [], "searchable_attributes": ["ruby"], "not_searchable_feedback": []}'
            }
          } ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
        allow(encoder).to receive(:call).and_raise(StandardError.new("Embedding error"))
      end

      it "returns skipped IntentResult as fallback" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: []
        )

        expect(result.embedding).to eq(vectorial_refined)
        expect(result.skipped).to be true
      end
    end

    context "with language feedback" do
      let(:base_candidate) { create(:candidate, account: account, role_name: "Backend Developer") }

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "Backend developer fluent in English with strong communication skills", "elasticsearch_query": "Backend developer English fluent", "must_have_skills": ["english"], "nice_to_have_skills": [], "searchable_attributes": ["english", "fluent"], "not_searchable_feedback": []}'
            }
          } ]
        }
      end

      let(:intent_embedding) { Array.new(768) { rand } }

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
        allow(encoder).to receive(:call).and_return(intent_embedding)
      end

      it "extracts language requirements as searchable" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: [ { candidate_id: 1, candidate: base_candidate, reason: "não fala inglês" } ],
          liked_candidates: []
        )

        expect(result.skipped).to be false
        expect(result.description).to match(/english|inglês/i)
        expect(result.searchable_attributes).to include("english")
      end
    end

    context "with seniority feedback" do
      let(:base_candidate) { create(:candidate, account: account, role_name: "Software Developer") }

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "Senior software engineer with 8+ years experience and tech lead background", "elasticsearch_query": "Senior software engineer tech lead", "must_have_skills": ["senior"], "nice_to_have_skills": [], "searchable_attributes": ["senior", "tech lead", "8+ years"], "not_searchable_feedback": []}'
            }
          } ]
        }
      end

      let(:intent_embedding) { Array.new(768) { rand } }

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
        allow(encoder).to receive(:call).and_return(intent_embedding)
      end

      it "extracts seniority requirements" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: [
            { candidate_id: 1, candidate: base_candidate, reason: "muito junior" },
            { candidate_id: 2, candidate: base_candidate, reason: "pouca experiência" }
          ],
          liked_candidates: []
        )

        expect(result.skipped).to be false
        expect(result.description).to match(/senior|staff|lead|experienc/i)
      end
    end

    context "with mixed searchable and not_searchable feedback" do
      let(:base_candidate) { create(:candidate, account: account, role_name: "Backend Developer") }

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "Ruby developer fluent in English", "elasticsearch_query": "Ruby Rails English backend", "must_have_skills": ["ruby", "english"], "nice_to_have_skills": [], "searchable_attributes": ["ruby", "english"], "not_searchable_feedback": [{"feedback": "pretens\u00e3o muito alta", "type": "salary"}]}'
            }
          } ]
        }
      end

      let(:intent_embedding) { Array.new(768) { rand } }

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
        allow(encoder).to receive(:call).and_return(intent_embedding)
      end

      it "separates searchable from not_searchable" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: [
            { candidate_id: 1, candidate: base_candidate, reason: "não sabe ruby" },
            { candidate_id: 2, candidate: base_candidate, reason: "pretensão muito alta" },
            { candidate_id: 3, candidate: base_candidate, reason: "não fala inglês" }
          ],
          liked_candidates: []
        )

        expect(result.skipped).to be false
        expect(result.searchable_attributes).to include("ruby", "english")
        expect(result.not_searchable_feedback).to be_a(Array)
        expect(result.not_searchable_feedback.first).to include("feedback" => "pretensão muito alta")
      end
    end

    context "with only not_searchable feedback" do
      let(:base_candidate) { create(:candidate, account: account, role_name: "Java Developer") }

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "", "elasticsearch_query": "", "must_have_skills": [], "nice_to_have_skills": [], "searchable_attributes": [], "not_searchable_feedback": [{"feedback": "pretens\u00e3o fora do budget", "type": "salary"}, {"feedback": "n\u00e3o aceita PJ", "type": "work_model"}]}'
            }
          } ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it "skips intent blending" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: [
            { candidate_id: 1, candidate: base_candidate, reason: "pretensão fora do budget" },
            { candidate_id: 2, candidate: base_candidate, reason: "não aceita PJ" }
          ],
          liked_candidates: []
        )

        expect(result.skipped).to be true
        expect(result.embedding).to eq(vectorial_refined)
        expect(result.not_searchable_feedback.size).to eq(2)
      end

      it "does not call encoder" do
        allow(encoder).to receive(:call)

        service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: [
            { candidate_id: 1, candidate: base_candidate, reason: "pretensão fora do budget" }
          ],
          liked_candidates: []
        )

        expect(encoder).not_to have_received(:call)
      end
    end

    context "with vague subjective feedback" do
      let(:base_candidate) { create(:candidate, account: account, role_name: "Developer") }

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "", "searchable_attributes": [], "not_searchable_feedback": [{"feedback": "não gostei", "type": "subjective"}, {"feedback": "não tem fit", "type": "cultural_fit"}]}'
            }
          } ]
        }
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it "skips intent blending for vague feedback" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: [
            { candidate_id: 1, candidate: base_candidate, reason: "não gostei" },
            { candidate_id: 2, candidate: base_candidate, reason: "não tem fit" }
          ],
          liked_candidates: []
        )

        expect(result.skipped).to be true
        expect(result.embedding).to eq(vectorial_refined)
      end
    end

    context "with leadership feedback" do
      let(:base_candidate) { create(:candidate, account: account, role_name: "Senior Developer") }

      let(:llm_response) do
        {
          "choices" => [ {
            "message" => {
              "content" => '{"ideal_candidate_description": "Tech Lead or Engineering Manager with team leadership experience", "elasticsearch_query": "Tech Lead Engineering Manager leadership", "must_have_skills": ["tech lead", "leadership"], "nice_to_have_skills": [], "searchable_attributes": ["tech lead", "engineering manager", "leadership"], "not_searchable_feedback": []}'
            }
          } ]
        }
      end

      let(:intent_embedding) { Array.new(768) { rand } }

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
        allow(encoder).to receive(:call).and_return(intent_embedding)
      end

      it "extracts leadership requirements" do
        result = service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: [ base_candidate ],
          disliked_feedbacks: [
            { candidate_id: 1, candidate: base_candidate, reason: "nunca foi tech lead" },
            { candidate_id: 2, candidate: base_candidate, reason: "não tem experiência com gestão de time" }
          ],
          liked_candidates: []
        )

        expect(result.skipped).to be false
        expect(result.description).to match(/tech.?lead|management|leadership|gestão/i)
      end
    end
  end

  describe "blending formula" do
    it "uses GAMMA weight of 0.25" do
      expect(described_class::GAMMA).to eq(0.25)
    end

    it "normalizes both vectors before blending" do
      vectorial = Array.new(768) { |i| i.even? ? 1.0 : 0.0 }
      intent = Array.new(768) { |i| i.odd? ? 1.0 : 0.0 }

      allow(llm_client).to receive(:chat).and_return(
        "choices" => [ {
          "message" => { "content" => '{"ideal_candidate_description": "test", "elasticsearch_query": "test", "must_have_skills": ["test"], "nice_to_have_skills": [], "searchable_attributes": ["test"], "not_searchable_feedback": []}' }
        } ]
      )
      allow(encoder).to receive(:call).and_return(intent)

      base_cand = create(:candidate, account: account)
      result = service.refine_with_intent(
        original_centroid: Array.new(768, 1.0),
        vectorial_refined: vectorial,
        base_candidates: [ base_cand ],
        disliked_feedbacks: [ { candidate_id: 1, candidate: base_cand, reason: "test" } ],
        liked_candidates: []
      )

      magnitude = Math.sqrt(result.embedding.sum { |v| v**2 })
      expect(magnitude).to be_within(0.01).of(1.0)
    end

    it "blends in correct direction" do
      vectorial = Array.new(768, 0.0)
      vectorial[0] = 1.0

      intent = Array.new(768, 0.0)
      intent[1] = 1.0

      allow(llm_client).to receive(:chat).and_return(
        "choices" => [ {
          "message" => { "content" => '{"ideal_candidate_description": "test", "elasticsearch_query": "test", "must_have_skills": ["test"], "nice_to_have_skills": [], "searchable_attributes": ["test"], "not_searchable_feedback": []}' }
        } ]
      )
      allow(encoder).to receive(:call).and_return(intent)

      base_cand = create(:candidate, account: account)
      result = service.refine_with_intent(
        original_centroid: Array.new(768, 0.5),
        vectorial_refined: vectorial,
        base_candidates: [ base_cand ],
        disliked_feedbacks: [ { candidate_id: 1, candidate: base_cand, reason: "test" } ],
        liked_candidates: []
      )

      expect(result.embedding[0]).to be > 0.5
      expect(result.embedding[1]).to be > 0.1

      cos_sim_vec = result.embedding[0]
      cos_sim_intent = result.embedding[1]
      expect(cos_sim_vec).to be > cos_sim_intent
    end
  end

  describe "#extract_candidate_skills" do
    it "extracts skills from data_raw" do
      candidate = create(:candidate,
        account: account,
        data_raw: { "skills" => [ { "name" => "ruby" }, { "name" => "rails" }, "python" ] }
      )

      skills = service.send(:extract_candidate_skills, candidate)

      expect(skills).to include("ruby", "rails", "python")
    end

    it "extracts skills from curriculum_text" do
      candidate = create(:candidate,
        account: account,
        curriculum_text: "Senior developer with experience in Ruby on Rails, PostgreSQL, and Docker"
      )

      skills = service.send(:extract_candidate_skills, candidate)

      expect(skills).to include("ruby", "rails", "postgresql", "docker")
    end

    it "limits to 15 skills" do
      candidate = create(:candidate,
        account: account,
        curriculum_text: "ruby rails python java javascript typescript react vue angular node spring django flask express api rest graphql sql postgresql mysql mongodb redis"
      )

      skills = service.send(:extract_candidate_skills, candidate)

      expect(skills.size).to be <= 15
    end

    it "returns unique skills" do
      candidate = create(:candidate,
        account: account,
        data_raw: { "skills" => [ { "name" => "ruby" } ] },
        curriculum_text: "Ruby developer with Ruby on Rails experience"
      )

      skills = service.send(:extract_candidate_skills, candidate)

      expect(skills.count("ruby")).to eq(1)
    end
  end
end
