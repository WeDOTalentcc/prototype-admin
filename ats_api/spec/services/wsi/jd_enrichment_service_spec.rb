# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::JdEnrichmentService do
  subject(:service) { described_class.new(job: job) }

  def stub_job_relationships_for_enrichment(dbl)
    allow(dbl).to receive(:skill_relationships).and_return(instance_double(ActiveRecord::Relation, any?: false))

    behavioral = double("behavioral_skill_rels")
    allow(behavioral).to receive(:where).with(is_deleted: false).and_return(behavioral)
    allow(behavioral).to receive(:includes).with(:behavioral_skill).and_return(behavioral)
    allow(behavioral).to receive(:none?).and_return(true)
    allow(dbl).to receive(:behavioral_skill_relationships).and_return(behavioral)

    remuneration = double("remuneration_rels")
    allow(remuneration).to receive(:where).with(is_deleted: false).and_return(remuneration)
    allow(remuneration).to receive(:includes).with(:remuneration).and_return(remuneration)
    allow(remuneration).to receive(:none?).and_return(true)
    allow(dbl).to receive(:remuneration_relationships).and_return(remuneration)

    benefits = double("benefit_rels")
    allow(benefits).to receive(:where).with(is_deleted: false).and_return(benefits)
    allow(benefits).to receive(:none?).and_return(true)
    allow(dbl).to receive(:benefit_relationships).and_return(benefits)
  end

  let(:quality_score_ok) do
    { "score" => 72, "status" => "good", "dimensions" => [], "evaluated_at" => Time.current.iso8601 }
  end

  let(:quality_score_critical) do
    { "score" => 20, "status" => "critical", "dimensions" => [], "evaluated_at" => Time.current.iso8601 }
  end

  let(:good_description) do
    "Empresa de tecnologia B2B buscando profissional para liderar o squad de backend com Ruby on Rails. " \
    "Trabalhamos com AWS, Docker, Kubernetes, PostgreSQL e Redis. " \
    "Você vai colaborar com times de produto, design e dados para entregar soluções escaláveis. " \
    "Ambiente ágil, autonomia real e foco em qualidade de código e observabilidade."
  end

  let(:good_responsibilities) do
    "Desenvolver e implementar soluções escaláveis com Ruby on Rails e microsserviços. " \
    "Arquitetar sistemas distribuídos na AWS garantindo alta disponibilidade. " \
    "Liderar revisões de código e definir padrões técnicos com o time. " \
    "Construir e manter pipelines de CI/CD com GitHub Actions e Docker. " \
    "Monitorar sistemas em produção e coordenar resposta a incidentes críticos. " \
    "Analisar e priorizar backlog técnico em colaboração com produto e design."
  end

  let(:llm_response_payload) do
    {
      "quality_report" => {
        "score_total" => 78,
        "nivel" => "bom",
        "resumo_executivo" => "JD de boa qualidade com skills específicas e responsabilidades mensuráveis.",
        "dimensoes" => [],
        "problemas_criticos" => [],
        "avisos" => [ "Setor não informado" ],
        "compliance_flags" => {
          "fairness_issues_found" => false,
          "fairness_issues" => [],
          "fields_missing" => [ "setor" ]
        },
        "ready_for_processing" => true
      },
      "enriched_jd" => {
        "titulo_padronizado" => "Engenheiro(a) de Software Sênior",
        "senioridade_confirmada" => "Sênior",
        "about_role" => "Papel de liderança técnica no squad de backend.",
        "responsabilidades" => [ "Desenvolver soluções escaláveis", "Arquitetar sistemas" ],
        "skills_obrigatorias" => [
          { "skill" => "Ruby on Rails", "contexto" => "framework principal" },
          { "skill" => "AWS EC2", "contexto" => "infraestrutura" },
          { "skill" => "Docker", "contexto" => "containerização" },
          { "skill" => "Kubernetes", "contexto" => "orquestração" },
          { "skill" => "PostgreSQL", "contexto" => "banco relacional" },
          { "skill" => "Redis", "contexto" => "cache" },
          { "skill" => "GitHub Actions", "contexto" => "CI/CD" },
          { "skill" => "REST APIs", "contexto" => "integração" },
          { "skill" => "Observabilidade", "contexto" => "monitoramento" }
        ],
        "skills_desejaveis" => [ "Terraform", "Kafka" ],
        "competencias_comportamentais" => [
          { "competencia" => "Liderança técnica", "contexto" => "guiar decisões do time", "trait_big_five" => "extraversion" },
          { "competencia" => "Organização", "contexto" => "priorização de backlog", "trait_big_five" => "conscientiousness" },
          { "competencia" => "Adaptabilidade", "contexto" => "ambiente ágil", "trait_big_five" => "openness" },
          { "competencia" => "Colaboração", "contexto" => "trabalho cross-funcional", "trait_big_five" => "agreeableness" },
          { "competencia" => "Resiliência", "contexto" => "resposta a incidentes", "trait_big_five" => "stability" }
        ],
        "context_signals" => {
          "nivel_autonomia" => "alto",
          "nivel_inovacao" => "medio",
          "nivel_pressao" => "medio",
          "nivel_colaboracao" => "alto"
        },
        "alteracoes_realizadas" => [],
        "fairness_corrections" => []
      }
    }.to_json
  end

  let(:gemini_response) do
    { "choices" => [ { "message" => { "content" => llm_response_payload } } ] }
  end

  let(:gemini_client) { instance_double(GeminiClient) }

  let(:job) do
    instance_double(
      Job,
      id:               1,
      title:            "Engenheiro de Software Sênior",
      description:      good_description,
      responsibilities: good_responsibilities,
      seniority:        2,
      sector:           nil,
      jd_quality_score: quality_score_ok
    ).tap do |dbl|
      allow(dbl).to receive(:try).with(:is_remote).and_return(false)
      stub_job_relationships_for_enrichment(dbl)
      allow(dbl).to receive(:update_column)
    end
  end

  before do
    allow(GeminiClient).to receive(:new).and_return(gemini_client)
    allow(gemini_client).to receive(:chat).and_return(gemini_response)
  end

  describe "#call" do
    context "when quality score is sufficient (>= 30)" do
      it "returns success: true" do
        result = service.call
        expect(result[:success]).to be true
      end

      it "returns lia_job_description without persisting on the job" do
        expect(job).not_to receive(:update_column)
        result = service.call
        expect(result[:lia_job_description]).to include(
          "status" => "pending_review",
          "enriched_jd" => be_a(Hash),
          "quality_report" => be_a(Hash)
        )
      end

      it "calls LLM with temperature 0.3" do
        expect(gemini_client).to receive(:chat).with(
          hash_including(temperature: 0.3, max_tokens: described_class::MAX_TOKENS)
        ).and_return(gemini_response)
        service.call
      end

      it "sets status to pending_review in the returned payload" do
        result = service.call
        expect(result[:lia_job_description]["status"]).to eq("pending_review")
      end

      it "enriched_jd contains at least 5 competencias_comportamentais each with trait_big_five" do
        result = service.call
        competencias = result[:lia_job_description].dig("enriched_jd", "competencias_comportamentais")
        expect(competencias.length).to be >= 5
        expect(competencias).to all(include("trait_big_five"))
      end

      it "enriched_jd contains at least 9 skills_obrigatorias" do
        result = service.call
        skills = result[:lia_job_description].dig("enriched_jd", "skills_obrigatorias")
        expect(skills.length).to be >= 9
      end

      it "includes method_version in the payload" do
        result = service.call
        expect(result[:lia_job_description]["method_version"]).to eq("wsi_f1c_v1")
      end

      context "when job has no jd_quality_score stored but override is passed" do
        let(:job) do
          instance_double(
            Job,
            id:               1,
            title:            "Engenheiro de Software Sênior",
            description:      good_description,
            responsibilities: good_responsibilities,
            seniority:        2,
            sector:           nil,
            jd_quality_score: nil
          ).tap do |dbl|
            allow(dbl).to receive(:try).with(:is_remote).and_return(false)
            stub_job_relationships_for_enrichment(dbl)
          end
        end

        subject(:service) { described_class.new(job: job, jd_quality_score: quality_score_ok) }

        it "uses override and succeeds" do
          result = service.call
          expect(result[:success]).to be true
          expect(result[:lia_job_description]["status"]).to eq("pending_review")
        end
      end
    end

    context "when quality score is missing" do
      let(:job) do
        instance_double(Job, id: 2, jd_quality_score: nil).tap do |dbl|
          allow(dbl).to receive(:update_column)
        end
      end

      it "returns failure without calling LLM" do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("jd_quality_score_missing")
        expect(gemini_client).not_to have_received(:chat)
      end
    end

    context "when quality score < 30 (critical)" do
      let(:job) do
        instance_double(
          Job,
          id:               3,
          title:            "Dev",
          description:      "Curta desc.",
          responsibilities: "Tarefas.",
          seniority:        nil,
          sector:           nil,
          jd_quality_score: quality_score_critical
        ).tap do |dbl|
          allow(dbl).to receive(:try).with(:is_remote).and_return(nil)
          stub_job_relationships_for_enrichment(dbl)
          allow(dbl).to receive(:update_column)
        end
      end

      it "returns failure with jd_quality_below_threshold" do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("jd_quality_below_threshold")
      end

      it "does not invoke the LLM" do
        service.call
        expect(gemini_client).not_to have_received(:chat)
      end
    end

    context "when JD has fewer than 50 useful words" do
      let(:job) do
        instance_double(
          Job,
          id:               4,
          title:            "Dev",
          description:      "Curta.",
          responsibilities: "Fazer.",
          seniority:        nil,
          sector:           nil,
          jd_quality_score: quality_score_ok
        ).tap do |dbl|
          allow(dbl).to receive(:try).with(:is_remote).and_return(nil)
          stub_job_relationships_for_enrichment(dbl)
          allow(dbl).to receive(:update_column)
        end
      end

      it "returns failure with jd_too_short" do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("jd_too_short")
      end
    end

    context "when LLM returns invalid JSON" do
      let(:bad_response) { { "choices" => [ { "message" => { "content" => "not json {{}}" } } ] } }

      before { allow(gemini_client).to receive(:chat).and_return(bad_response) }

      it "returns failure with invalid_llm_response" do
        result = service.call
        expect(result[:success]).to be false
        expect(result[:error]).to eq("invalid_llm_response")
      end

      it "does not persist anything on the job" do
        expect(job).not_to receive(:update_column)
        service.call
      end
    end
  end
end
