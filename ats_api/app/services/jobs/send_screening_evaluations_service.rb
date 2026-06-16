# frozen_string_literal: true

module Jobs
  class SendScreeningEvaluationsService
    def self.call(job_id:, account_id: nil, user_id: nil)
      new(job_id: job_id, account_id: account_id, user_id: user_id).call
    end

    def initialize(job_id:, account_id: nil, user_id: nil)
      @job_id = job_id
      @account_id = account_id
      @user_id = user_id
      @sent_count = 0
      @skipped_saturation = 0
      @errors = []
    end

    def call
      return result(success: false, error: "Job not found") unless job
      return result(success: false, error: "Job screening not active") unless job.is_screening_active?
      return result(success: false, error: "Screening send limit date reached") unless job.can_send_screenings?
      return result(success: false, error: "No screening stage configured") unless screening_selective_process
      return result(success: false, error: "No screening evaluation configured") unless screening_evaluation

      log_start
      process_applies
      log_summary
      result(success: true)
    rescue StandardError => e
      @errors << e.message
      Rails.logger.error "❌ [SendScreeningEvaluationsService] job_id=#{job_id} error=#{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      result(success: false, error: e.message)
    end

    private

    attr_reader :job_id, :account_id, :user_id
    attr_accessor :sent_count, :skipped_saturation, :errors

    def job
      @job ||= Job.find_by(id: job_id)
    end

    def screening_selective_process
      @screening_selective_process ||= job
        .selective_processes
        .where(is_deleted: false)
        .where(status: SelectiveProcess.statuses[:screening])
        .order(:position)
        .first
    end

    def screening_evaluation
      @screening_evaluation ||= find_screening_evaluation
    end

    def find_screening_evaluation
      eval_in_sp = Evaluation
        .screening
        .find_by(
          job_id: job_id,
          selective_process_id: screening_selective_process.id,
          is_deleted: false
        )
      return eval_in_sp if eval_in_sp

      screening_sp_ids = job
        .selective_processes
        .where(is_deleted: false, status: SelectiveProcess.statuses[:screening])
        .pluck(:id)

      Evaluation
        .screening
        .find_by(
          job_id: job_id,
          selective_process_id: screening_sp_ids,
          is_deleted: false
        )
    end

    def screening_sp_id
      screening_evaluation&.selective_process_id || screening_selective_process&.id
    end

    def applies_to_process
      return Apply.none unless screening_sp_id

      Apply
        .where(
          job_id: job_id,
          selective_process_id: screening_sp_id,
          is_deleted: false
        )
        .where(
          "NOT EXISTS (
            SELECT 1 FROM evaluation_candidates ec
            WHERE ec.apply_id = applies.id
              AND ec.evaluation_id = ?
              AND ec.is_deleted = false
          )",
          screening_evaluation.id
        )
        .order(created_at: :asc)
    end

    def process_applies
      job.reload
      applies_to_process.find_each do |apply|
        process_apply(apply)
      end
    end

    def process_apply(apply)
      return :skipped if apply.is_screening_sent?

      blocking = saturation_blocking_reason
      if blocking
        self.skipped_saturation += 1
        log_skip(apply: apply, source: blocking[:source], current: blocking[:current], limit: blocking[:limit])
        return :skipped_saturation
      end

      create_evaluation_candidate(apply)
    rescue StandardError => e
      errors << "Apply #{apply.id}: #{e.message}"
      Rails.logger.error "❌ [SendScreeningEvaluationsService] job_id=#{job_id} apply_id=#{apply.id} error=#{e.message}"
      :error
    end

    def can_send_to_apply?(apply)
      saturation_blocking_reason.nil?
    end

    def saturation_blocking_reason
      return nil if job.saturation_overridden_by_limit_date?

      %w[web sourcing].each do |source|
        first_sent_at = first_screening_sent_at_for_source(source)
        limit = job.effective_saturation_limit_for_source(source, first_sent_at: first_sent_at)
        next if limit <= 0

        current = current_sent_count_by_source(source)
        return { source: source, current: current, limit: limit } if current >= limit
      end
      nil
    end

    def first_screening_sent_at_for_source(source)
      scope = EvaluationCandidate
        .joins(:apply)
        .where(
          evaluation_id: screening_evaluation.id,
          is_deleted: false,
          applies: {
            job_id: job_id,
            selective_process_id: screening_sp_id,
            is_deleted: false,
            is_screening_sent: true
          }
        )

      case source
      when "web" then scope.where(applies: { source: %w[web_response web] })
      when "sourcing" then scope.where.not(applies: { source: %w[web_response web] })
      else scope.where.not(applies: { source: %w[web_response web] })
      end.minimum(:created_at)
    end

    def normalize_source(source)
      case source.to_s
      when "web_response", "web" then "web"
      when "sourcing" then "sourcing"
      else "sourcing"
      end
    end

    def current_sent_count_by_source(source)
      scope = Apply
        .where(
          job_id: job_id,
          selective_process_id: screening_sp_id,
          is_deleted: false,
          is_screening_sent: true
        )

      case source
      when "web" then scope.where(source: %w[web_response web])
      when "sourcing" then scope.where.not(source: %w[web_response web])
      else scope.where.not(source: %w[web_response web])
      end.count
    end

    def create_evaluation_candidate(apply)
      resolved_user_id = user_id.presence || job.default_user_id_for_screening(evaluation: screening_evaluation)
      return :error if resolved_user_id.blank?

      ec = EvaluationCandidate.find_or_create_by!(
        apply_id: apply.id,
        evaluation_id: screening_evaluation.id
      ) do |record|
        record.candidate_id = apply.candidate_id
        record.job_id = job_id
        record.user_id = resolved_user_id
        record.account_id = job.account_id
        record.uid = SecureRandom.uuid
        record.candidate_uid = apply.candidate&.uid
      end

      if ec.previously_new_record?
        self.sent_count += 1
        log_sent(apply: apply, source: normalize_source(apply.source))
        :sent
      else
        :skipped_already_sent
      end
    end

    def log_start
      applies_count = applies_to_process.count
      Rails.logger.info "🔄 [SendScreeningEvaluationsService] START job_id=#{job_id} applies_to_process=#{applies_count} screening_sp_id=#{screening_sp_id}"
    end

    def log_skip(apply:, source:, current:, limit:)
      Rails.logger.info(
        "⏸️  [SendScreeningEvaluationsService] SKIP job_id=#{job_id} apply_id=#{apply.id} " \
        "source=#{source} saturation_reached current=#{current} limit=#{limit}"
      )
    end

    def log_sent(apply:, source:)
      Rails.logger.info(
        "✅ [SendScreeningEvaluationsService] SENT job_id=#{job_id} apply_id=#{apply.id} " \
        "source=#{source} channel=#{screening_evaluation.chatbot_channel}"
      )
    end

    def log_summary
      web_sent = current_sent_count_by_source("web")
      sourcing_sent = current_sent_count_by_source("sourcing")
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [SendScreeningEvaluationsService] COMPLETED job_id=#{job_id}"
      Rails.logger.info "   sent_count=#{sent_count} skipped_saturation=#{skipped_saturation}"
      Rails.logger.info "   saturation_counts web=#{web_sent} sourcing=#{sourcing_sent}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def result(success:, error: nil)
      {
        success: success,
        sent_count: sent_count,
        skipped_saturation: skipped_saturation,
        errors: errors
      }.tap { |r| r[:error] = error if error }
    end
  end
end
