# frozen_string_literal: true

module Wsi
  class JdQualityScoreService
    THRESHOLDS = {
      critical:    0..29,
      insufficient: 30..49,
      adequate:    50..69,
      good:        70..84,
      excellent:   85..100
    }.freeze

    JUNIOR_VERBS    = %w[executar implementar desenvolver codificar testar apoiar realizar].freeze
    SENIOR_VERBS    = %w[liderar arquitetar definir estratégia estruturar gerenciar coordenar].freeze
    ACTION_VERBS    = %w[desenvolver implementar criar gerenciar coordenar liderar definir analisar
                         estruturar executar otimizar garantir assegurar estabelecer construir
                         projetar entregar colaborar suportar realizar manter monitorar].freeze

    GENDER_MARKERS = /\b(?:ele|ela|dele|dela|homem|mulher|masculino|feminino|nativo)\b|
                      o\ candidato\ ideal|a\ candidata\ ideal|jovem\ e\ dinâmico|
                      boa\ aparência|apresentação\ pessoal|estado\ civil|native\ speaker|
                      recém-formado|bairros\ nobres|escola\ particular|
                      universidades\ de\ primeira\ linha|faculdade\ de\ ponta/ix.freeze

    CONTRADICTION_PAIRS = [
      [ /autonom\w+/i, /aprovação em tudo|micro.?gest\w+/i ],
      [ /trabalho independente/i, /supervisão constante/i ],
      [ /ambiente ágil/i, /processos rígidos|burocraci\w+/i ]
    ].freeze

    def initialize(job:, persist: true)
      @job    = job
      @persist = persist
    end

    def self.call(job:, persist: true)
      new(job: job, persist: persist).call
    end

    def call
      dimensions = evaluate_all_dimensions
      score      = dimensions.sum { |d| d["score"].to_i }.clamp(0, 100)
      status     = classify(score)

      result = {
        "score"        => score,
        "status"       => status.to_s,
        "dimensions"   => dimensions,
        "evaluated_at" => Time.current.iso8601
      }

      @job.update_column(:jd_quality_score, result) if @persist

      { success: true, score: score, status: status, dimensions: dimensions, jd_quality_score: result }
    end

    private

    attr_reader :job

    def evaluate_all_dimensions
      [
        evaluate_title_clarity,
        evaluate_responsibilities,
        evaluate_technical_skills,
        evaluate_behavioral_competencies,
        evaluate_seniority_consistency,
        evaluate_no_contradictions,
        evaluate_organizational_context,
        evaluate_inclusive_language,
        evaluate_density
      ]
    end

    # Dimensão 1 — Clareza do título (peso 10)
    # Verifica se o título contém indicador de senioridade ou área técnica identificável
    def evaluate_title_clarity
      title    = job.title.to_s.strip
      seniority_labels = %w[júnior junior pleno sênior senior especialista lead gerente diretor
                            estágio estagiário trainee principal]
      has_seniority = seniority_labels.any? { |s| title.downcase.include?(s) } || job.seniority.present?
      has_area      = title.split.length >= 3 || title.match?(/\w{3,}/)

      score = if has_seniority && has_area then 10
      elsif has_seniority || has_area then 5
      else 0
      end

      build_dimension("title_clarity", score, 10,
                       has_seniority && has_area ? "ok" : "aviso",
                       "Título: #{title.presence || "(vazio)"}")
    end

    # Dimensão 2 — Responsabilidades (peso 15)
    # Verifica ≥ 80 palavras e ≥ 5 verbos de ação no conteúdo da vaga (description + responsibilities).
    # Só usar responsibilities isolado penaliza JDs onde o recrutador escreveu tudo em description.
    def evaluate_responsibilities
      text        = [ job.description, job.responsibilities ].compact_blank.join(" ").strip
      word_count  = text.split.length
      verb_count  = ACTION_VERBS.count { |v| text.downcase.include?(v) }

      score = if word_count >= 80 && verb_count >= 5 then 15
      elsif word_count >= 40 && verb_count >= 2 then 7
      else 0
      end

      build_dimension("responsibilities", score, 15,
                       score == 15 ? "ok" : (score == 7 ? "aviso" : "critico"),
                       "#{word_count} palavras, #{verb_count} verbos de ação detectados")
    end

    # Dimensão 3 — Skills técnicas (peso 15)
    # Verifica ≥ 3 skills associadas ao job
    def evaluate_technical_skills
      skills = job.try(:skill_relationships)&.count.to_i

      # Fallback: contar menções a tecnologias no texto da descrição
      if skills < 3
        tech_pattern = /\b(python|ruby|rails|java|javascript|typescript|react|vue|angular|node|
                           aws|azure|gcp|docker|kubernetes|sql|postgres|mysql|mongodb|redis|
                           git|linux|api|rest|graphql|kafka|spark|terraform|ci.?cd)\b/ix
        skills = [ skills, job.description.to_s.scan(tech_pattern).length ].max
      end

      score = if skills >= 5 then 15
      elsif skills >= 3 then 10
      elsif skills >= 1 then 5
      else 0
      end

      build_dimension("technical_skills", score, 15,
                       score >= 10 ? "ok" : (score > 0 ? "aviso" : "critico"),
                       "#{skills} skill(s) técnica(s) identificadas")
    end

    # Dimensão 4 — Competências comportamentais (peso 10)
    # Verifica ≥ 2 competências comportamentais com contexto
    def evaluate_behavioral_competencies
      text  = "#{job.description} #{job.responsibilities}".downcase
      behavioral_keywords = %w[comunicação liderança colaboração adaptabilidade resiliência
                                proatividade criatividade autonomia empatia negociação
                                pensamento crítico inteligência emocional trabalho em equipe
                                relacionamento interpessoal gestão de conflitos]

      count = behavioral_keywords.count { |kw| text.include?(kw) }

      # Tenta contar via relacionamentos de competências se disponível
      if job.respond_to?(:competence_relationships)
        count = [ count, job.competence_relationships.count ].max
      end

      score = if count >= 4 then 10
      elsif count >= 2 then 6
      else 0
      end

      build_dimension("behavioral_competencies", score, 10,
                       count >= 2 ? "ok" : "critico",
                       "#{count} competência(s) comportamental(is) identificadas")
    end

    # Dimensão 5 — Consistência senioridade (peso 15)
    # Verifica se os verbos do texto são compatíveis com o nível declarado
    def evaluate_seniority_consistency
      return build_dimension("seniority_consistency", 7, 15, "aviso", "Senioridade não declarada") unless job.seniority.present?

      text        = "#{job.description} #{job.responsibilities}".downcase
      seniority   = Job::SENIORITY[job.seniority].to_s.downcase

      senior_levels   = %w[sênior senior especialista lead gerente diretor]
      junior_levels   = %w[júnior junior pleno estágio estagiário trainee]

      is_senior = senior_levels.any? { |s| seniority.include?(s) }
      is_junior = junior_levels.any? { |s| seniority.include?(s) }

      senior_verb_count = SENIOR_VERBS.count { |v| text.include?(v) }
      junior_verb_count = JUNIOR_VERBS.count { |v| text.include?(v) }

      consistent = if is_senior
                     senior_verb_count >= 2
      elsif is_junior
                     junior_verb_count >= 2 || senior_verb_count == 0
      else
                     true # pleno — aceita ambos
      end

      score = consistent ? 15 : 5
      build_dimension("seniority_consistency", score, 15,
                       consistent ? "ok" : "aviso",
                       "Nível #{seniority}: #{senior_verb_count} verbos sênior, #{junior_verb_count} verbos júnior")
    end

    # Dimensão 6 — Ausência de inconsistências (peso 10)
    # Detecta pares contraditórios como "autonomia + aprovação em tudo"
    def evaluate_no_contradictions
      text = "#{job.description} #{job.responsibilities}"
      contradictions = CONTRADICTION_PAIRS.select { |a, b| text.match?(a) && text.match?(b) }

      score = contradictions.empty? ? 10 : 0
      build_dimension("no_contradictions", score, 10,
                       contradictions.empty? ? "ok" : "aviso",
                       contradictions.empty? ? "Sem inconsistências detectadas" : "#{contradictions.length} inconsistência(s) detectada(s)")
    end

    # Dimensão 7 — Contexto organizacional (peso 10)
    # Verifica presença de empresa, setor ou tamanho de time
    def evaluate_organizational_context
      has_company  = job.try(:company).present? || job.career_page_name.present?
      has_sector   = job.sector.present? || job.segment.present?
      has_teamsize = job.description.to_s.match?(/time de \d+|equipe de \d+|\d+ pessoas|\d+ membros/i)

      signals = [ has_company, has_sector, has_teamsize ].count(true)
      score   = signals >= 1 ? 10 : 0

      build_dimension("organizational_context", score, 10,
                       score == 10 ? "ok" : "aviso",
                       "#{signals} sinal(is) de contexto organizacional: empresa=#{has_company}, setor=#{has_sector}, time=#{has_teamsize}")
    end

    # Dimensão 8 — Linguagem inclusiva (peso 10)
    # Verifica ausência de marcadores de gênero/origem/idade
    def evaluate_inclusive_language
      text    = "#{job.title} #{job.description} #{job.responsibilities}"
      matches = text.scan(GENDER_MARKERS).flatten.uniq

      score = matches.empty? ? 10 : 0
      build_dimension("inclusive_language", score, 10,
                       matches.empty? ? "ok" : "critico",
                       matches.empty? ? "Linguagem inclusiva" : "Marcadores encontrados: #{matches.join(", ")}")
    end

    # Dimensão 9 — Densidade total (peso 5)
    # Verifica ≥ 150 palavras no total do JD
    def evaluate_density
      total_words = [ job.title, job.description, job.responsibilities ]
                      .map { |f| f.to_s.split.length }
                      .sum

      score = total_words >= 150 ? 5 : 0
      build_dimension("density", score, 5,
                       total_words >= 150 ? "ok" : "critico",
                       "#{total_words} palavras totais (mínimo 150)")
    end

    def classify(score)
      THRESHOLDS.find { |_status, range| range.include?(score) }&.first || :critical
    end

    def build_dimension(name, score, max_score, status, finding)
      { "dimension" => name, "score" => score, "max_score" => max_score,
        "status" => status, "finding" => finding }
    end
  end
end
