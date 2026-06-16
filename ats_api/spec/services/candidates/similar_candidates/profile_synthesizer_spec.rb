# frozen_string_literal: true

require "rails_helper"

RSpec.describe Candidates::SimilarCandidates::ProfileSynthesizer do
  let(:llm_client) { instance_double(GeminiClient) }
  let(:service) { described_class.new(llm_client: llm_client) }

  describe "#call" do
    context "when base_candidates is blank" do
      it "returns default synthesis" do
        result = service.call([])

        expect(result[:query]).to eq("experienced professional")
        expect(result[:custom_filters][:locations]).to include("Brasil")
        expect(result[:synthesis_method]).to eq("fallback")
      end
    end

    context "with valid base candidates" do
      let(:candidate1) do
        instance_double(
          Candidate,
          name: "João Silva",
          role_name: "Senior Ruby Developer",
          current_company: "Tech Corp",
          city: "São Paulo",
          state: "SP",
          position_level: "senior",
          curriculum_text: "Experienced Ruby on Rails developer with microservices expertise",
          self_introduction: "Passionate about clean code",
          experiences: [
            { "title" => "Tech Lead", "company" => "Tech Corp", "start_date" => "2020-01", "end_date" => nil }
          ],
          educations: [
            { "degree" => "Bachelor", "field_of_study" => "Computer Science", "school" => "USP" }
          ]
        )
      end

      let(:candidate2) do
        instance_double(
          Candidate,
          name: "Maria Santos",
          role_name: "Ruby Developer",
          current_company: "StartupXYZ",
          city: "São Paulo",
          state: "SP",
          position_level: "mid",
          curriculum_text: "Ruby developer focused on backend development and APIs",
          self_introduction: nil,
          experiences: [],
          educations: []
        )
      end

      let(:llm_response) do
        {
          "query" => "senior ruby rails developer backend microservices",
          "custom_filters" => {
            "locations" => [ "São Paulo, SP" ],
            "keywords" => [ "Ruby", "Rails", "PostgreSQL", "Redis" ],
            "titles" => [ "Senior Developer", "Tech Lead" ],
            "min_total_experience_years" => 5
          },
          "explanation" => "Senior backend developers specialized in Ruby/Rails"
        }.to_json
      end

      before do
        allow(llm_client).to receive(:chat).and_return(llm_response)
      end

      it "calls LLM with profiles context" do
        service.call([ candidate1, candidate2 ])

        expect(llm_client).to have_received(:chat) do |args|
          expect(args[:model]).to include("gemini")
          expect(args[:messages].size).to eq(2)
          expect(args[:messages][0][:role]).to eq("system")
          expect(args[:messages][1][:role]).to eq("user")
          expect(args[:messages][1][:content]).to include("João Silva")
          expect(args[:messages][1][:content]).to include("Maria Santos")
          expect(args[:response_format]).to eq({ type: "json_object" })
        end
      end

      it "returns synthesized query and filters" do
        result = service.call([ candidate1, candidate2 ])

        expect(result[:query]).to eq("senior ruby rails developer backend microservices")
        expect(result[:custom_filters][:locations]).to eq([ "São Paulo, SP" ])
        expect(result[:custom_filters][:keywords]).to include("Ruby", "Rails")
        expect(result[:custom_filters][:min_total_experience_years]).to eq(5)
        expect(result[:explanation]).to include("Senior backend")
        expect(result[:synthesis_method]).to eq("llm")
      end

      it "normalizes custom filters correctly" do
        result = service.call([ candidate1 ])

        expect(result[:custom_filters]).to be_a(Hash)
        expect(result[:custom_filters][:keywords]).to be_an(Array)
        expect(result[:custom_filters][:keywords].size).to be <= 10
      end
    end

    context "when LLM times out" do
      let(:candidate) do
        instance_double(
          Candidate,
          name: "Test",
          role_name: "Developer",
          current_company: "Corp",
          city: nil,
          state: nil,
          position_level: nil,
          curriculum_text: "Test",
          self_introduction: nil,
          experiences: [],
          educations: []
        )
      end

      before do
        allow(llm_client).to receive(:chat).and_raise(Timeout::Error)
      end

      it "returns default synthesis" do
        result = service.call([ candidate ])

        expect(result[:synthesis_method]).to eq("fallback")
        expect(result[:query]).to eq("experienced professional")
      end
    end

    context "when LLM returns invalid JSON" do
      let(:candidate) do
        instance_double(
          Candidate,
          name: "Test",
          role_name: "Developer",
          current_company: "Corp",
          city: nil,
          state: nil,
          position_level: nil,
          curriculum_text: "Test",
          self_introduction: nil,
          experiences: [],
          educations: []
        )
      end

      before do
        allow(llm_client).to receive(:chat).and_return("invalid json {")
      end

      it "returns default synthesis" do
        result = service.call([ candidate ])

        expect(result[:synthesis_method]).to eq("fallback")
      end
    end

    context "when LLM returns incomplete response" do
      let(:candidate) do
        instance_double(
          Candidate,
          name: "Test",
          role_name: "Developer",
          current_company: "Corp",
          city: nil,
          state: nil,
          position_level: nil,
          curriculum_text: "Test",
          self_introduction: nil,
          experiences: [],
          educations: []
        )
      end

      before do
        allow(llm_client).to receive(:chat).and_return({ "custom_filters" => {} }.to_json)
      end

      it "uses fallback query" do
        result = service.call([ candidate ])

        expect(result[:query]).to include("Developer")
        expect(result[:synthesis_method]).to eq("llm")
      end
    end
  end
end
