# app/services/candidates/search/simple_query_detector.rb
#
# Detecta o tipo de query para decidir qual estratégia de busca usar:
# - Query simples: pula QueryAnalyzer, busca direta no ES
# - Query complexa: usa QueryAnalyzer + HyDE
# - Currículo: usa extração de perfil + busca por similaridade

module Candidates
  module Search
    class SimpleQueryDetector
      # Padrões que indicam query SIMPLES (não precisa de LLM)
      SIMPLE_PATTERNS = [
        /^\w+$/i,
        /^[\w\s\.\-]{1,60}$/,
        /^\w+\s+(junior|jr|pleno|pl|senior|sr|lead|tech\s*lead)$/i,
        /^(dev|desenvolvedor|developer|programador|engenheiro|engineer|analista)\s+\w+/i
      ].freeze

      # Padrões que indicam query COMPLEXA (precisa de análise)
      COMPLEX_INDICATORS = [
        /\d+\s*(anos?|years?|meses|months)/i,
        /\b(e|ou|and|or|com|with|sem|without)\b/i,
        /[,;]/,
        /(experiência|experience|conhecimento|knowledge|habilidade|skill)/i,
        /\b(não|never|exceto|except|apenas|only)\b/i,
        /(formação|graduação|pós|mestrado|doutorado|mba)/i,
        /(salário|pretensão|remuneração|clt|pj)/i
      ].freeze

      # Indicadores de CURRÍCULO completo
      RESUME_INDICATORS = [
        /(experiência\s+profissional|professional\s+experience)/i,
        /(formação\s+acadêmica|education|academic)/i,
        /(objetivo|resumo|summary|profile)/i,
        /\b(19|20)\d{2}\s*[-–—]\s*(19|20)?\d{0,4}\b/,
        /@\w+\.(com|br|org|net)/,
        /linkedin\.com/i,
        /github\.com/i
      ].freeze

      # Indicadores de JOB DESCRIPTION
      JD_INDICATORS = [
        /\b(requisitos|requirements|qualifica[çc][õo]es)\b/i,
        /\b(responsabilidades|responsibilities|atribui[çc][õo]es)\b/i,
        /\b(desej[aá]vel|nice.?to.?have|diferencial)\b/i,
        /\b(vaga|position|oportunidade|job)\s+(de|for|para)/i,
        /\b(oferecemos|we.?offer|benef[íi]cios)\b/i,
        /\b(contrata[çc][ãa]o|hiring|recrutamento)\b/i,
        /\b(candidato\s+ideal|ideal\s+candidate)\b/i,
        /\b(perfil|profile)\s+(desejado|buscado)/i
      ].freeze

      class << self
        # Retorna :simple, :complex, :resume, ou :job_description
        def detect(query)
          return :simple if query.blank? || query.to_s.strip == "*"

          return :job_description if job_description?(query)
          return :resume if resume?(query)
          return :complex if complex_indicators?(query)

          :simple
        end

        def simple?(query)
          detect(query) == :simple
        end

        def complex?(query)
          detect(query) == :complex
        end

        def resume?(query)
          return false if query.blank?

          q = query.to_s
          checks = [
            q.length > 500,
            word_count(q) > 50,
            RESUME_INDICATORS.count { |p| q.match?(p) } >= 2,
            has_multiple_proper_nouns?(q),
            has_date_ranges?(q)
          ]

          checks.count(true) >= 2
        end

        def job_description?(query)
          return false if query.blank?
          return false if query.length < 200

          q = query.to_s

          jd_score = JD_INDICATORS.count { |p| q.match?(p) }
          resume_score = RESUME_INDICATORS.count { |p| q.match?(p) }

          return true if jd_score >= 3
          return true if jd_score > resume_score && jd_score >= 2

          has_jd_structure?(q)
        end

        private

        def complex_indicators?(query)
          return false if query.blank?

          COMPLEX_INDICATORS.any? { |pattern| query.to_s.match?(pattern) }
        end

        def word_count(query)
          query.to_s.split(/\s+/).reject(&:blank?).size
        end

        def has_multiple_proper_nouns?(query)
          proper_nouns = query.scan(/\b[A-Z][a-záéíóúâêîôûãõç]+(?:\s+[A-Z][a-záéíóúâêîôûãõç]+)*\b/)
          proper_nouns.size > 3
        end

        def has_date_ranges?(query)
          date_patterns = [
            /\b(19|20)\d{2}\s*[-–—]\s*(19|20)?\d{2,4}\b/,
            /\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|atual|present)/i
          ]

          date_patterns.any? { |p| query.match?(p) }
        end

        def has_jd_structure?(text)
          sections = [
            /requisitos|requirements|qualifica/i,
            /responsabilidades|responsibilities/i,
            /sobre\s+(a\s+)?(empresa|vaga)|about\s+(the\s+)?(company|role)/i
          ]

          sections.count { |s| text.match?(s) } >= 2
        end
      end
    end
  end
end
