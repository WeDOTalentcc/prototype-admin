# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::JdQualityScoreService do
  subject(:service) { described_class.new(job: job) }

  let(:full_responsibilities) do
    "Desenvolver e implementar soluções de software escaláveis utilizando Ruby on Rails. " \
    "Colaborar com equipes de produto e design para definir requisitos técnicos claros e mensuráveis. " \
    "Garantir a qualidade do código através de testes automatizados, code review e documentação técnica. " \
    "Arquitetar e estruturar microsserviços resilientes na plataforma AWS com foco em disponibilidade. " \
    "Liderar tecnicamente os sprints da equipe, analisando e priorizando backlog com o time de produto. " \
    "Monitorar a saúde dos sistemas em produção, coordenar incidentes e propor melhorias de observabilidade. " \
    "Construir e manter pipelines de CI/CD com GitHub Actions, Docker e Kubernetes para entregas contínuas."
  end

  let(:full_description) do
    "Empresa de tecnologia B2B buscando profissional para liderar o squad de backend. " \
    "Ambiente ágil com foco em qualidade, utilizando python, ruby, rails, docker, kubernetes, postgres, redis, aws. " \
    "Você vai trabalhar com um time multidisciplinar e colaborar diretamente com o time de produto e design. " \
    "Valorizamos autonomia, aprendizado contínuo e impacto real nas decisões técnicas da plataforma."
  end

  let(:job) do
    instance_double(
      Job,
      title:               "Engenheiro de Software Sênior",
      description:         full_description,
      responsibilities:    full_responsibilities,
      responsibilities?:   true,
      seniority:           2, # Sênior (index 2 = "Sênior" em Job::SENIORITY)
      sector:              "Tecnologia",
      segment:             nil,
      career_page_name:    "WeDo Talent",
      try:                 nil
    ).tap do |dbl|
      allow(dbl).to receive(:try).with(:skill_relationships).and_return(nil)
      allow(dbl).to receive(:try).with(:company).and_return(nil)
      allow(dbl).to receive(:respond_to?).with(:competence_relationships).and_return(false)
      allow(dbl).to receive(:update_column)
    end
  end

  describe "#call with persist: false" do
    it "does not write jd_quality_score to the job" do
      expect(job).not_to receive(:update_column)
      described_class.call(job: job, persist: false)
    end

    it "returns jd_quality_score payload in the result" do
      result = described_class.call(job: job, persist: false)
      expect(result[:jd_quality_score]).to include(
        "score" => be_a(Integer),
        "status" => be_a(String),
        "dimensions" => be_a(Array),
        "evaluated_at" => be_a(String)
      )
    end
  end

  describe "#call" do
    it "returns a hash with score, status, dimensions and jd_quality_score" do
      result = service.call
      expect(result).to include(:success, :score, :status, :dimensions, :jd_quality_score)
      expect(result[:success]).to be true
    end

    it "returns score between 0 and 100" do
      result = service.call
      expect(result[:score]).to be_between(0, 100)
    end

    it "returns 9 dimensions" do
      result = service.call
      expect(result[:dimensions].length).to eq(9)
    end

    it "persists jd_quality_score on the job" do
      expect(job).to receive(:update_column).with(:jd_quality_score, hash_including("score", "status", "dimensions"))
      service.call
    end

    context "with a rich, complete JD" do
      it "returns score >= 50 (adequate or better)" do
        result = service.call
        expect(result[:score]).to be >= 50
      end
    end
  end

  describe "dimension: density" do
    context "when total words < 150" do
      let(:job) do
        instance_double(
          Job,
          title: "Dev",
          description: "Curta descrição.",
          responsibilities: "Executar tarefas.",
          seniority: nil,
          sector: nil, segment: nil, career_page_name: nil
        ).tap do |dbl|
          allow(dbl).to receive(:try).and_return(nil)
          allow(dbl).to receive(:respond_to?).with(:competence_relationships).and_return(false)
          allow(dbl).to receive(:update_column)
        end
      end

      it "density dimension scores 0" do
        result = service.call
        density = result[:dimensions].find { |d| d["dimension"] == "density" }
        expect(density["score"]).to eq(0)
        expect(density["status"]).to eq("critico")
      end
    end

    context "when total words >= 150" do
      it "density dimension scores 5" do
        result = service.call
        density = result[:dimensions].find { |d| d["dimension"] == "density" }
        expect(density["score"]).to eq(5)
        expect(density["status"]).to eq("ok")
      end
    end
  end

  describe "dimension: inclusive_language" do
    context "when description contains gender markers" do
      let(:job) do
        instance_double(
          Job,
          title:            "Analista",
          description:      "O candidato ideal deve ser jovem e dinâmico, com boa aparência.",
          responsibilities: full_responsibilities,
          seniority:        1,
          sector:           nil, segment: nil, career_page_name: nil
        ).tap do |dbl|
          allow(dbl).to receive(:try).and_return(nil)
          allow(dbl).to receive(:respond_to?).with(:competence_relationships).and_return(false)
          allow(dbl).to receive(:update_column)
        end
      end

      it "inclusive_language dimension scores 0 with status critico" do
        result = service.call
        dim = result[:dimensions].find { |d| d["dimension"] == "inclusive_language" }
        expect(dim["score"]).to eq(0)
        expect(dim["status"]).to eq("critico")
      end
    end

    context "when description uses neutral language" do
      it "inclusive_language dimension scores 10" do
        result = service.call
        dim = result[:dimensions].find { |d| d["dimension"] == "inclusive_language" }
        expect(dim["score"]).to eq(10)
        expect(dim["status"]).to eq("ok")
      end
    end
  end

  describe "dimension: responsibilities" do
    context "when responsibilities has < 40 words and < 2 action verbs" do
      let(:job) do
        instance_double(
          Job,
          title:            "Dev",
          description:      "Tech company.",
          responsibilities: "Fazer tarefas.",
          seniority:        nil,
          sector:           nil, segment: nil, career_page_name: nil
        ).tap do |dbl|
          allow(dbl).to receive(:try).and_return(nil)
          allow(dbl).to receive(:respond_to?).with(:competence_relationships).and_return(false)
          allow(dbl).to receive(:update_column)
        end
      end

      it "responsibilities dimension scores 0" do
        result = service.call
        dim = result[:dimensions].find { |d| d["dimension"] == "responsibilities" }
        expect(dim["score"]).to eq(0)
      end
    end

    context "when responsibilities is minimal but description contains the full JD body" do
      let(:job) do
        instance_double(
          Job,
          title:            "Engenheiro de Software Sênior",
          description:      "#{full_description}\n\n#{full_responsibilities}",
          responsibilities: "Ver descrição acima.",
          seniority:        2,
          sector:           "Tecnologia",
          segment:          nil,
          career_page_name: "WeDo Talent"
        ).tap do |dbl|
          allow(dbl).to receive(:try).with(:skill_relationships).and_return(nil)
          allow(dbl).to receive(:try).with(:company).and_return(nil)
          allow(dbl).to receive(:respond_to?).with(:competence_relationships).and_return(false)
          allow(dbl).to receive(:update_column)
        end
      end

      it "uses description plus responsibilities for word and verb counts" do
        result = service.call
        dim = result[:dimensions].find { |d| d["dimension"] == "responsibilities" }
        expect(dim["score"]).to eq(15)
      end
    end
  end

  describe "status classification" do
    it "classifies score < 30 as critical" do
      allow(service).to receive(:evaluate_all_dimensions).and_return(
        Array.new(9) { { "score" => 0, "max_score" => 15, "status" => "critico", "finding" => "", "dimension" => "x" } }
      )
      result = service.call
      expect(result[:status]).to eq(:critical)
    end

    it "classifies score 50..69 as adequate" do
      allow(service).to receive(:evaluate_all_dimensions).and_return([
        { "score" => 10, "max_score" => 10, "status" => "ok", "finding" => "", "dimension" => "title_clarity" },
        { "score" => 15, "max_score" => 15, "status" => "ok", "finding" => "", "dimension" => "responsibilities" },
        { "score" => 10, "max_score" => 15, "status" => "ok", "finding" => "", "dimension" => "technical_skills" },
        { "score" => 10, "max_score" => 10, "status" => "ok", "finding" => "", "dimension" => "behavioral_competencies" },
        { "score" => 0,  "max_score" => 15, "status" => "critico", "finding" => "", "dimension" => "seniority_consistency" },
        { "score" => 0,  "max_score" => 10, "status" => "aviso",   "finding" => "", "dimension" => "no_contradictions" },
        { "score" => 0,  "max_score" => 10, "status" => "aviso",   "finding" => "", "dimension" => "organizational_context" },
        { "score" => 10, "max_score" => 10, "status" => "ok",      "finding" => "", "dimension" => "inclusive_language" },
        { "score" => 5,  "max_score" => 5,  "status" => "ok",      "finding" => "", "dimension" => "density" }
      ])
      result = service.call
      expect(result[:score]).to eq(60)
      expect(result[:status]).to eq(:adequate)
    end

    it "classifies score >= 85 as excellent" do
      allow(service).to receive(:evaluate_all_dimensions).and_return(
        Array.new(9) { { "score" => 15, "max_score" => 15, "status" => "ok", "finding" => "", "dimension" => "x" } }
      )
      result = service.call
      expect(result[:status]).to eq(:excellent)
    end
  end
end
