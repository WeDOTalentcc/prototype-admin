module SourcedProfiles
  class AiAnalysisJob < ApplicationJob
    queue_as :ai_analysis

    # Gemini pode ter rate limit/timeout — garantir retries em falhas transitórias
    sidekiq_options retry: 10

    def perform(account_id, sourced_profile_id, sourcing_id = nil)
      return if Rails.env.test?

      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)
      Current.account = account

      profile = SourcedProfile.find_by(id: sourced_profile_id)
      unless profile
        Rails.logger.warn "⚠️ [AiAnalysisJob] Profile #{sourced_profile_id} not found"
        return
      end

      curriculum = profile.curriculum_text.presence || profile.candidate&.curriculum_text.presence
      if curriculum.blank?
        Rails.logger.warn "⚠️ [AiAnalysisJob] Skipping profile #{profile.id} - no curriculum_text"
        handle_skipped_profile(sourced_profile_id, sourcing_id, profile, "no_curriculum")
        return
      end

      sourcing = sourcing_id ? Sourcing.find_by(id: sourcing_id) : profile.sourcings.order(created_at: :desc).first
      unless sourcing
        Rails.logger.warn "⚠️ [AiAnalysisJob] No sourcing found for profile #{profile.id}"
        return
      end

      Current.user = sourcing.user

      sourced_profile_sourcing = SourcedProfileSourcing.find_by(sourced_profile_id: profile.id, sourcing_id: sourcing.id)
      unless sourced_profile_sourcing
        Rails.logger.warn "⚠️ [AiAnalysisJob] SourcedProfileSourcing not found for profile #{profile.id}, sourcing #{sourcing.id}"
        return
      end

      query = sourcing.query || profile.sourcing&.query
      result = analyzer.call(profile: profile, query: query, sourcing: sourcing)

      if result[:status] == :ok
        handle_success(sourced_profile_sourcing, profile, result)
      end
      handle_skip(profile, result) if result[:status] == :skipped
      handle_error(profile, result) if result[:status] != :ok && result[:status] != :skipped
    rescue => e
      Rails.logger.error "❌ [SourcedProfiles::AiAnalysisJob] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise # Re-raise para Sidekiq fazer retry
    end

    private

    def analyzer
      @analyzer ||= SourcedProfiles::ProfileAnalyzer.new
    end

    def enrich_profile_with_ai_data(sourced_profile_sourcing)
      enrichment_service = SourcedProfiles::AiEnrichmentService.new(sourced_profile_sourcing)
      enrichment_service.enrich!
      Rails.logger.info "✨ [AiAnalysisJob] Enriched profile #{sourced_profile_sourcing.sourced_profile_id} with AI data"
    rescue => e
      Rails.logger.error "⚠️  [AiAnalysisJob] Enrichment failed for profile #{sourced_profile_sourcing.sourced_profile_id}: #{e.message}"
    end

    def handle_success(sourced_profile_sourcing, profile, result)
      metadata = result[:metadata] || {}
      insights = result[:insights] || {}

      sourced_profile_sourcing.update!(
        score: result[:score],
        analysis: insights.is_a?(Hash) ? insights : {},
        ai_metadata: metadata
      )

      enrich_profile_with_ai_data(sourced_profile_sourcing)

      maybe_auto_add_to_job(sourced_profile_sourcing)

      progress = Sourcings::SourcingProgressCounts.call(sourced_profile_sourcing.sourcing)
      update_sourcing_progress(sourced_profile_sourcing.sourcing, broadcast_progress: false, precomputed: progress)
      Sourcings::ProfileAnalyzedBroadcast.call(
        sourcing: sourced_profile_sourcing.sourcing,
        sourced_profile_sourcing: sourced_profile_sourcing,
        progress: progress
      )
    end

    def handle_skip(profile, result)
      Rails.logger.warn "⚠️ [AiAnalysisJob] Skipped profile #{profile.id}: #{result[:error]}"
    end

    def handle_skipped_profile(profile_id, sourcing_id, profile, reason)
      return unless sourcing_id

      sourcing = Sourcing.find_by(id: sourcing_id)
      return unless sourcing

      # Atualizar progresso mesmo quando skipado
      update_sourcing_progress(sourcing)

      progress = Sourcings::SourcingProgressCounts.call(sourcing)

      # Notificar frontend sobre o skip
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "profile_skipped",
          profile_id: profile_id,
          sourcing_id: sourcing_id,
          reason: reason,
          message: skip_message(reason),
          processed: progress[:processed],
          total: progress[:total],
          percentage: progress[:percentage]
        }
      )

      Rails.logger.info "🟡 [AiAnalysisJob] Broadcasted skip notification for profile #{profile_id}"
    end

    def skip_message(reason)
      case reason
      when "no_curriculum"
        "Perfil sem currículo disponível para análise"
      else
        "Perfil pulado na análise"
      end
    end

    def handle_error(profile, result)
      Rails.logger.error "❌ [AiAnalysisJob] Error analyzing profile #{profile.id}: #{result[:error]}"
    end

    def maybe_auto_add_to_job(sourced_profile_sourcing)
      sourcing = sourced_profile_sourcing.sourcing
      auto_add_job_id = sourcing.parameters&.dig("auto_add_job_id")
      return unless auto_add_job_id.present?

      min_score = sourcing.parameters&.dig("min_score_threshold")&.to_f || 70.0
      return unless sourced_profile_sourcing.score.to_f >= min_score

      Jobs::AutoAddCandidateService.call(
        sourced_profile_sourcing: sourced_profile_sourcing,
        job_id: auto_add_job_id,
        account: Current.account,
        user: sourcing.user
      )
    rescue => e
      Rails.logger.error "❌ [AiAnalysisJob] AutoAdd failed for sps #{sourced_profile_sourcing.id}: #{e.message}"
    end

    def update_sourcing_progress(sourcing, broadcast_progress: true, precomputed: nil)
      return unless sourcing

      progress = precomputed || Sourcings::SourcingProgressCounts.call(sourcing)

      if broadcast_progress
        SourcingChannel.broadcast_to(
          "#{sourcing.user_id}_sourcing_#{sourcing.id}",
          {
            type: "sourcing_progress",
            sourcing_id: sourcing.id,
            processed: progress[:processed],
            total: progress[:total],
            percentage: progress[:percentage],
            local_count: sourcing.local_results_count,
            global_count: sourcing.global_results_count
          }
        )
        Rails.logger.info "📊 [AiAnalysisJob] AI Analysis Progress: #{progress[:processed]}/#{progress[:total]} (#{progress[:percentage]}%)"
      end

      # Se todas as análises foram concluídas, enviar sinal de conclusão
      if progress[:processed] >= progress[:total] && progress[:total] > 0
        broadcast_ai_analysis_completed(sourcing, progress[:processed], progress[:total])
      end
    rescue => e
      Rails.logger.error "❌ [AiAnalysisJob] Failed to update progress: #{e.message}"
    end

    def broadcast_ai_analysis_completed(sourcing, processed, total)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "profiles_processing_completed",
          sourcing_id: sourcing.id,
          total_profiles: processed,
          profiles_analyzed: processed,
          profiles_skipped: total - processed,
          phase: "ai_analysis_completed",
          timestamp: Time.current.iso8601
        }
      )
      Rails.logger.info "✅ [AiAnalysisJob] AI analysis queue completed - #{processed}/#{total} profiles analyzed"

      update_auto_source_metadata_if_needed(sourcing)

      sleep(0.1)
      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_fully_completed",
          sourcing_id: sourcing.id,
          processed: processed,
          total: total,
          percentage: 100,
          total_analyzed: processed,
          total_expected: total,
          local_count: sourcing.local_results_count,
          global_count: sourcing.global_results_count,
          success: true,
          message: "#{processed} candidatos analisados",
          timestamp: Time.current.iso8601
        }
      )
      Rails.logger.info "✅ [AiAnalysisJob] Sourcing fully completed - All queues processed"
    end

    def update_auto_source_metadata_if_needed(sourcing)
      auto_add_job_id = sourcing.parameters&.dig("auto_add_job_id")
      return unless auto_add_job_id.present?

      job = Job.find_by(id: auto_add_job_id)
      return unless job

      added_count = Apply
        .joins(candidate: { sourced_profile: :sourced_profile_sourcings })
        .where(job_id: job.id, sourced_profile_sourcings: { sourcing_id: sourcing.id })
        .distinct
        .count

      Rails.logger.info "📊 [AiAnalysisJob] Auto Source: #{added_count} candidates added to job #{job.id}"

      ::Jobs::AutoSourceMetadataUpdateService.call(
        job: job,
        sourcing: sourcing,
        added_count: added_count
      )
    rescue => e
      Rails.logger.error "❌ [AiAnalysisJob] Failed to update auto source metadata: #{e.message}"
    end
  end
end
