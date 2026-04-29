module Candidates
  module Search
    class Reranker
      # Pesos simples e diretos - sem complicação
      SIGNALS = {
        rich_content: { threshold: 0.8, weight: 0.15 },
        good_content: { threshold: 0.6, weight: 0.10 },
        basic_content: { threshold: 0.4, weight: 0.05 },
        has_contact: { weight: 0.05 },
        is_recent: { weight: 0.03 }
      }.freeze

      PENALTY_EMPTY = -0.20

      class << self
        def apply(ranked_candidates, limit: Configuration.final_limit, custom_boost_config: nil)
          candidate_ids = ranked_candidates.first(limit * 2).map(&:id)
          candidates_data = load_candidates_data(candidate_ids)

          ranked_candidates.first(limit * 2).map do |ranked|
            data = candidates_data[ranked.id] || {}
            boost_result = calculate_boost(data, custom_boost_config)

            RerankedCandidate.new(
              id: ranked.id,
              rrf_score: ranked.final_score,
              contributions: ranked.contributions,
              boost: boost_result[:total],
              boost_breakdown: boost_result[:breakdown],
              final_score: ranked.final_score * (1 + boost_result[:total]),
              completeness: data[:content_quality]
            )
          end.sort_by { |c| -c.final_score }
        end

        private

        def load_candidates_data(ids)
          return {} if ids.empty?

          Candidate
            .where(id: ids)
            .pluck(:id, :email, :phone, :mobile_phone, :curriculum_text, :updated_at)
            .to_h do |id, email, phone, mobile, curriculum, updated|
              recent_threshold = 90.days.ago
              [ id, {
                has_contact: email.present? || phone.present? || mobile.present?,
                content_quality: calculate_content_quality(curriculum),
                is_recent: updated && updated > recent_threshold,
                curriculum_text: curriculum.to_s.downcase
              } ]
            end
        end

        def calculate_content_quality(text)
          return 0.0 if text.blank?

          len = text.length
          return 1.0 if len > 2000
          return 0.8 if len > 1000
          return 0.6 if len > 500
          return 0.4 if len > 200
          0.2
        end

        def calculate_boost(data, custom_config)
          breakdown = {}
          total = 0.0

          # Candidato vazio = penaliza
          if data[:content_quality] < 0.2 && !data[:has_contact]
            return { total: PENALTY_EMPTY, breakdown: { empty: PENALTY_EMPTY } }
          end

          # Content quality (principal)
          quality = data[:content_quality]
          SIGNALS.each do |key, config|
            next unless key.to_s.end_with?("_content")
            next unless quality >= config[:threshold]

            breakdown[key] = config[:weight]
            total += config[:weight]
            break
          end

          # Sinais simples
          total += apply_signal(:has_contact, data[:has_contact], breakdown)
          total += apply_signal(:is_recent, data[:is_recent], breakdown)

          # Custom boost (JD matching)
          total += apply_custom_boost(data, custom_config, breakdown) if custom_config

          { total: total.round(4), breakdown: breakdown }
        end

        def apply_signal(key, condition, breakdown)
          return 0.0 unless condition
          weight = SIGNALS[key][:weight]
          breakdown[key] = weight
          weight
        end

        def apply_custom_boost(data, config, breakdown)
          return 0.0 unless config[:required_skill_match]

          skills = config[:required_skill_match][:skills]
          return 0.0 if skills.blank?

          curriculum = data[:curriculum_text]
          matched = skills.count { |s| curriculum.include?(s.downcase) }
          return 0.0 if matched.zero?

          boost = config[:required_skill_match][:weight] * (matched.to_f / skills.size)
          breakdown[:skill_match] = boost.round(4)
          boost
        end
      end
    end

    class RerankedCandidate
      attr_reader :id, :rrf_score, :contributions, :boost, :boost_breakdown,
                  :final_score, :completeness

      def initialize(id:, rrf_score:, contributions:, boost:, boost_breakdown:,
                     final_score:, completeness:)
        @id = id
        @rrf_score = rrf_score
        @contributions = contributions
        @boost = boost
        @boost_breakdown = boost_breakdown
        @final_score = final_score
        @completeness = completeness
      end

      def to_h
        {
          id: id,
          rrf_score: rrf_score.round(6),
          boost: boost,
          boost_breakdown: boost_breakdown,
          final_score: final_score.round(6),
          completeness: completeness
        }
      end
    end
  end
end
