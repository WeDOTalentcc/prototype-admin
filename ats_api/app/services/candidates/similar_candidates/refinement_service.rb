# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class RefinementService
      DEFAULT_LIMIT = 20
      DEFAULT_THRESHOLD = 0.60

      def initialize(account:, user:)
        @account = account
        @user = user
      end

      def call(sourcing:, liked_candidate_ids: [], disliked_feedbacks: [], sources: [ "local" ], limit: DEFAULT_LIMIT, use_intent_refinement: true)
        start_time = Process.clock_gettime(Process::CLOCK_MONOTONIC)

        validate!(sourcing, liked_candidate_ids, disliked_feedbacks)

        context = load_sourcing_context(sourcing)

        save_feedbacks(sourcing, liked_candidate_ids, disliked_feedbacks, context[:job_id])

        refinement_result = refine_embedding(
          original_centroid: context[:original_embedding],
          liked_ids: liked_candidate_ids,
          disliked_ids: disliked_feedbacks.map { |d| d[:candidate_id] },
          disliked_feedbacks: disliked_feedbacks,
          base_candidates: context[:base_candidates],
          use_intent: use_intent_refinement
        )

        refined_embedding = refinement_result[:embedding]
        intent_result = refinement_result[:intent_result]

        feedback_analysis = analyze_feedback(
          context: context,
          liked_ids: liked_candidate_ids,
          disliked_feedbacks: disliked_feedbacks
        )

        all_exclude_ids = build_exclude_ids(
          context: context,
          sourcing: sourcing,
          disliked_ids: disliked_feedbacks.map { |d| d[:candidate_id] }
        )

        new_results = HybridSearchService.new(account_id: @account.id).search(
          embedding: refined_embedding,
          intent_result: intent_result,
          exclude_ids: all_exclude_ids,
          limit: limit,
          threshold: context[:threshold]
        )

        updated_existing = recompute_existing_similarities(
          sourcing: sourcing,
          refined_embedding: refined_embedding,
          disliked_ids: disliked_feedbacks.map { |d| d[:candidate_id] }
        )

        new_enriched = process_new_results(
          results: new_results,
          base_candidates: context[:base_candidates],
          sourcing: sourcing
        )

        duration = duration_ms(start_time)

        update_sourcing_metadata(
          sourcing: sourcing,
          new_count: new_enriched.size,
          duration: duration,
          feedback_analysis: feedback_analysis
        )

        build_response(
          sourcing: sourcing,
          existing_candidates: updated_existing,
          new_candidates: new_enriched,
          feedback_analysis: feedback_analysis,
          intent_result: intent_result,
          duration: duration
        )
      end

      private

      def validate!(sourcing, liked_ids, disliked_feedbacks)
        unless sourcing.parameters&.dig("search_type") == "similarity"
          raise ArgumentError, "Sourcing #{sourcing.id} is not a similarity search"
        end

        if liked_ids.empty? && disliked_feedbacks.empty?
          raise ArgumentError, "At least 1 like or 1 dislike is required"
        end

        sourcing_candidate_ids = SourcedProfileSourcing
          .where(sourcing_id: sourcing.id, is_deleted: false)
          .joins(:sourced_profile)
          .pluck("sourced_profiles.candidate_id")
          .compact

        all_feedback_ids = liked_ids + disliked_feedbacks.map { |d| d[:candidate_id] }
        invalid = all_feedback_ids - sourcing_candidate_ids

        if invalid.any?
          raise ArgumentError, "Candidates #{invalid} do not belong to Sourcing #{sourcing.id}"
        end

        disliked_feedbacks.each do |df|
          if df[:reason].blank?
            raise ArgumentError, "Reason is required for dislike of candidate #{df[:candidate_id]}"
          end
        end
      end

      def load_sourcing_context(sourcing)
        base_candidate_ids = sourcing.parameters["base_candidate_ids"]
        job_id = sourcing.parameters["job_id"]
        threshold = sourcing.search_metadata&.dig("threshold") || DEFAULT_THRESHOLD

        base_candidates = Candidate.where(id: base_candidate_ids, account_id: @account.id)
        original_embedding = compute_centroid(base_candidate_ids)

        {
          base_candidate_ids: base_candidate_ids,
          base_candidates: base_candidates,
          job_id: job_id,
          threshold: threshold,
          original_embedding: original_embedding
        }
      end

      def compute_centroid(candidate_ids)
        vectors = Embedding
          .where(reference_type: "Candidate", reference_id: candidate_ids)
          .pluck(:embedding)

        return nil if vectors.empty?
        return vectors.first if vectors.size == 1

        dims = vectors.first.size
        centroid = Array.new(dims, 0.0)
        vectors.each { |vec| vec.each_with_index { |v, i| centroid[i] += v } }
        centroid.map { |v| v / vectors.size }
      end

      def save_feedbacks(sourcing, liked_ids, disliked_feedbacks, job_id)
        liked_ids.each do |candidate_id|
          create_feedback(
            sourcing: sourcing,
            candidate_id: candidate_id,
            feedback_type: "like",
            reason: nil,
            job_id: job_id
          )
        end

        disliked_feedbacks.each do |df|
          create_feedback(
            sourcing: sourcing,
            candidate_id: df[:candidate_id],
            feedback_type: "dislike",
            reason: df[:reason],
            job_id: job_id
          )
        end
      end

      def create_feedback(sourcing:, candidate_id:, feedback_type:, reason:, job_id:)
        existing = CandidateFeedback.find_by(
          sourcing_id: sourcing.id,
          candidate_id: candidate_id,
          user_id: @user.id
        )

        if existing
          existing.update!(
            feedback_type: feedback_type,
            reason: reason
          )
        else
          sps = SourcedProfileSourcing
            .joins(:sourced_profile)
            .find_by(
              sourcing_id: sourcing.id,
              "sourced_profiles.candidate_id": candidate_id,
              is_deleted: false
            )

          candidate = Candidate.find_by(id: candidate_id, account_id: @account.id)

          CandidateFeedback.create!(
            sourcing_id: sourcing.id,
            candidate_id: candidate_id,
            user_id: @user.id,
            account_id: @account.id,
            job_id: job_id,
            feedback_type: feedback_type,
            reason: reason,
            sourced_profile_sourcing_id: sps&.id,
            candidate_score_snapshot: {
              role_name: candidate&.role_name,
              current_company: candidate&.current_company,
              position_level: candidate&.position_level,
              city: candidate&.city,
              state: candidate&.state
            },
            search_query_snapshot: {
              sourcing_query: sourcing.query,
              refinement: true
            }
          )
        end
      end

      def refine_embedding(original_centroid:, liked_ids:, disliked_ids:, disliked_feedbacks: [], base_candidates: [], use_intent: true)
        vectorial_service = EmbeddingRefinementService.new(original_centroid: original_centroid)
        vectorial_refined = vectorial_service.refine(liked_ids: liked_ids, disliked_ids: disliked_ids)

        return { embedding: vectorial_refined, intent_result: nil } unless use_intent && disliked_feedbacks.any?

        liked_candidates = Candidate.where(id: liked_ids, account_id: @account.id)

        intent_service = IntentBasedRefinementService.new
        intent_result = intent_service.refine_with_intent(
          original_centroid: original_centroid,
          vectorial_refined: vectorial_refined,
          base_candidates: base_candidates,
          disliked_feedbacks: disliked_feedbacks,
          liked_candidates: liked_candidates
        )

        { embedding: intent_result.embedding, intent_result: intent_result }
      end

      def analyze_feedback(context:, liked_ids:, disliked_feedbacks:)
        return nil if disliked_feedbacks.size < 2

        liked_candidates = Candidate.where(id: liked_ids, account_id: @account.id)
        dislikes_with_candidates = disliked_feedbacks.map do |df|
          {
            candidate: Candidate.find_by(id: df[:candidate_id], account_id: @account.id),
            reason: df[:reason]
          }
        end

        FeedbackAnalyzerService.new.analyze(
          base_candidates: context[:base_candidates],
          liked_candidates: liked_candidates,
          dislike_feedbacks: dislikes_with_candidates
        )
      end

      def build_exclude_ids(context:, sourcing:, disliked_ids:)
        ids = context[:base_candidate_ids].dup
        ids += disliked_ids

        if context[:job_id].present?
          ids += Apply.where(job_id: context[:job_id], is_deleted: false).pluck(:candidate_id)
        end

        existing_candidate_ids = SourcedProfileSourcing
          .where(sourcing_id: sourcing.id, is_deleted: false)
          .joins(:sourced_profile)
          .pluck("sourced_profiles.candidate_id")
          .compact

        ids += existing_candidate_ids
        ids.uniq
      end

      def recompute_existing_similarities(sourcing:, refined_embedding:, disliked_ids:)
        existing_sps = SourcedProfileSourcing
          .where(sourcing_id: sourcing.id, is_deleted: false)
          .joins(:sourced_profile)
          .includes(:sourced_profile)

        existing_sps.filter_map do |sps|
          candidate_id = sps.sourced_profile.candidate_id
          next unless candidate_id
          next if disliked_ids.include?(candidate_id)

          embedding_record = Embedding.find_by(
            reference_type: "Candidate",
            reference_id: candidate_id
          )
          next unless embedding_record

          new_distance = cosine_distance(refined_embedding, embedding_record.embedding)
          new_similarity = (1.0 - new_distance).clamp(0.0, 1.0)
          new_similarity_pct = (new_similarity * 100).round(1)

          old_similarity_pct = sps.similarity_score

          if old_similarity_pct != new_similarity_pct
            sps.update_column(:similarity_score, new_similarity_pct)
            sps.update_column(:search_score, new_similarity)
          end

          {
            candidate_id: candidate_id,
            sourced_profile_id: sps.sourced_profile_id,
            name: sps.sourced_profile.name,
            role_name: sps.sourced_profile.role_name,
            current_company: sps.sourced_profile.current_company,
            location: [ sps.sourced_profile.city, sps.sourced_profile.state ].compact.join(", "),
            similarity_score: new_similarity_pct,
            previous_similarity_score: old_similarity_pct,
            ai_score: sps.score,
            status: "existing",
            score_changed: old_similarity_pct != new_similarity_pct
          }
        end
      end

      def cosine_distance(vec_a, vec_b)
        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0

        vec_a.each_with_index do |a, i|
          b = vec_b[i].to_f
          dot += a * b
          norm_a += a * a
          norm_b += b * b
        end

        return 1.0 if norm_a.zero? || norm_b.zero?

        similarity = dot / (Math.sqrt(norm_a) * Math.sqrt(norm_b))
        1.0 - similarity.clamp(-1.0, 1.0)
      end

      def process_new_results(results:, base_candidates:, sourcing:)
        return [] if results.empty?

        candidates = Candidate.where(id: results.map { |r| r[:candidate_id] }).index_by(&:id)

        results.filter_map do |result|
          candidate = candidates[result[:candidate_id]]
          next unless candidate

          profile = create_or_link_sourced_profile(candidate, sourcing, result[:similarity])
          shared = extract_shared_signals(base_candidates, candidate)

          {
            candidate_id: candidate.id,
            sourced_profile_id: profile.id,
            name: candidate.name,
            role_name: candidate.role_name,
            current_company: candidate.current_company,
            location: [ candidate.city, candidate.state ].compact.join(", "),
            similarity_score: (result[:similarity] * 100).round(1),
            shared_signals: shared,
            source: result[:source]&.to_s,
            ai_score: nil,
            status: "new"
          }
        end
      end

      def create_or_link_sourced_profile(candidate, sourcing, similarity_score)
        existing_profile = SourcedProfile.find_by(
          account_id: @account.id,
          candidate_id: candidate.id,
          is_deleted: false
        )

        profile = existing_profile || build_sourced_profile(candidate, sourcing)
        profile.save! if profile.new_record?

        SourcedProfileSourcing.create!(
          sourced_profile: profile,
          sourcing: sourcing,
          account_id: @account.id,
          user_id: @user.id,
          search_source: "similarity_refined",
          search_score: similarity_score,
          similarity_score: (similarity_score * 100).round(1),
          ai_metadata: {
            search_type: "similar_candidates_refined",
            similarity_percentage: (similarity_score * 100).round(1),
            refinement_round: current_refinement_round(sourcing)
          }
        )

        profile
      end

      def build_sourced_profile(candidate, sourcing)
        profile = SourcedProfile.new(
          sourcing: sourcing,
          account_id: @account.id,
          candidate: candidate,
          provider: "local",
          external_id: "similar_refined_#{sourcing.id}_#{candidate.id}",
          status: "new",
          name: candidate.name,
          email: candidate.email,
          phone: candidate.phone || candidate.mobile_phone,
          cpf: candidate.cpf,
          date_birth: candidate.date_birth,
          gender: candidate.gender,
          marital_status: candidate.marital_status,
          role_name: candidate.role_name,
          position_level: candidate.position_level,
          current_company: candidate.current_company,
          city: candidate.city,
          state: candidate.state,
          country: candidate.country,
          linkedin: candidate.linkedin,
          linkedin_slug: candidate.linkedin_slug,
          github: candidate.github,
          portfolio: candidate.portfolio,
          curriculum_text: candidate.curriculum_text,
          self_introduction: candidate.self_introduction,
          clt_expectation: candidate.clt_expectation,
          pj_expectation: candidate.pj_expectation,
          freelance_expectation: candidate.freelance_expectation,
          current_salary: candidate.current_salary,
          desired_salary: candidate.desired_salary,
          remote_work: candidate.remote_work,
          mobility: candidate.mobility,
          secondary_email: candidate.secondary_email,
          mobile_phone: candidate.mobile_phone,
          secondary_phone: candidate.secondary_phone,
          has_emails: candidate.email.present?,
          has_phone_numbers: (candidate.phone || candidate.mobile_phone).present?,
          location: [ candidate.city, candidate.state ].compact.join(", "),
          title: candidate.role_name,
          summary: candidate.self_introduction
        )

        begin
          SourcedProfiles::CandidateEnrichmentService.call(profile, candidate)
        rescue StandardError => e
          Rails.logger.error("[RefinementService] CandidateEnrichmentService failed: #{e.message}")
        end

        profile
      end

      def extract_shared_signals(base_candidates, similar_candidate)
        base_tokens = base_candidates.flat_map { |c| tokenize(c.curriculum_text) }.uniq
        similar_tokens = tokenize(similar_candidate.curriculum_text)
        (base_tokens & similar_tokens).sort_by { |t| -t.length }.first(8)
      end

      def tokenize(text)
        return [] if text.blank?

        text.downcase
            .gsub(/[^a-záàâãéèêíïóôõöúçñ0-9\s+#.]/i, " ")
            .split(/\s+/)
            .reject { |t| t.length < 3 || stopwords.include?(t) }
            .uniq
      end

      def stopwords
        @stopwords ||= Set.new(%w[
          que para com por uma como mais sobre entre quando muito desde onde esta
          sao tem sido pode sua seu seus suas anos experiencia profissional
          trabalho empresa area tambem ainda sendo foram fazer apos
          das dos nos nas pelo pela pelos pelas esse essa esses essas
          este esta estes estas isso isto aqui ali aquele aquela the and
        ])
      end

      def update_sourcing_metadata(sourcing:, new_count:, duration:, feedback_analysis:)
        current_meta = sourcing.search_metadata || {}
        refinements = current_meta["refinements"] || []

        refinements << {
          round: refinements.size + 1,
          timestamp: Time.current.iso8601,
          new_candidates_found: new_count,
          duration_ms: duration,
          feedback_analysis: feedback_analysis&.slice(:desired_profile, :rejection_patterns)
        }

        sourcing.update!(
          results_count: sourcing.results_count + new_count,
          local_results_count: (sourcing.local_results_count || 0) + new_count,
          processed_count: (sourcing.processed_count || 0) + new_count,
          search_metadata: current_meta.merge(
            "refinements" => refinements,
            "last_refined_at" => Time.current.iso8601,
            "total_refinement_rounds" => refinements.size
          )
        )
      end

      def current_refinement_round(sourcing)
        refinements = sourcing.search_metadata&.dig("refinements")
        (refinements&.size || 0) + 1
      end

      def build_response(sourcing:, existing_candidates:, new_candidates:, feedback_analysis:, intent_result:, duration:)
        all_candidates = (existing_candidates + new_candidates)
          .sort_by { |c| -(c[:similarity_score] || 0) }

        {
          sourcing_id: sourcing.id,
          sourcing_uid: sourcing.uid,
          search_type: "similarity_refined",
          refinement_round: current_refinement_round(sourcing) - 1,
          candidates: all_candidates,
          summary: {
            total: all_candidates.size,
            existing_updated: existing_candidates.size,
            new_found: new_candidates.size,
            scores_changed: existing_candidates.count { |c| c[:score_changed] }
          },
          feedback_analysis: feedback_analysis ? {
            desired_profile: feedback_analysis[:desired_profile],
            rejection_patterns: feedback_analysis[:rejection_patterns],
            positive_patterns: feedback_analysis[:positive_patterns],
            explanation: feedback_analysis[:explanation]
          } : nil,
          intent_analysis: build_intent_analysis(intent_result),
          metadata: {
            duration_ms: duration,
            embedding_model: Llm::ClientFactory.embedding_model,
            refinement_method: search_method(intent_result),
            alpha: EmbeddingRefinementService::ALPHA,
            beta: EmbeddingRefinementService::BETA,
            gamma: IntentBasedRefinementService::GAMMA
          }
        }
      end

      def build_intent_analysis(intent_result)
        return nil unless intent_result

        {
          applied: !intent_result.skipped,
          description: intent_result.description,
          elasticsearch_query: intent_result.elasticsearch_query,
          must_have_skills: intent_result.must_have_skills,
          nice_to_have_skills: intent_result.nice_to_have_skills,
          searchable_attributes: intent_result.searchable_attributes,
          not_searchable_feedback: intent_result.not_searchable_feedback,
          hybrid_search: intent_result.elasticsearch_query.present?
        }
      end

      def search_method(intent_result)
        return "centroid_adjustment" unless intent_result
        return "centroid_adjustment_with_intent" if intent_result.skipped || intent_result.elasticsearch_query.blank?

        "hybrid_rrf"
      end

      def duration_ms(start_time)
        ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start_time) * 1000).round(1)
      end
    end
  end
end
