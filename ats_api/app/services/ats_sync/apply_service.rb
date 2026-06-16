# frozen_string_literal: true

module AtsSync
  class ApplyService < BaseService
    def self.sync(apply)
      new(apply).sync
    end

    private

    def ats_provider
      "questt"
    end

    def execute_sync(payload)
      is_update = apply_exists_in_ats?

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [ApplyService] Execute Sync"
      Rails.logger.info "   Apply ID: #{record.id}"
      Rails.logger.info "   Apply external_id: #{record.external_id.inspect}"
      Rails.logger.info "   Candidate ID: #{record.candidate_id} (external_id: #{record.candidate.external_id.inspect})"
      Rails.logger.info "   Job ID: #{record.job_id}"
      Rails.logger.info "      - external_id: #{record.job.external_id.inspect}"
      Rails.logger.info "      - provider: #{record.job.provider.inspect}"
      Rails.logger.info "      - provider_job_id: #{record.job.provider_job_id.inspect}"
      Rails.logger.info "      - effective_provider_job_id: #{effective_provider_job_id.inspect} #{effective_provider_job_id == record.job.external_id ? '(using external_id)' : '(using provider_job_id)'}"
      Rails.logger.info "   SelectiveProcess ID: #{record.selective_process_id} (external_id: #{record.selective_process&.external_id.inspect})"
      Rails.logger.info "   Action: #{is_update ? 'UPDATE' : 'CREATE'}"
      Rails.logger.info "   "
      Rails.logger.info "   📦 Payload References:"
      Rails.logger.info "      - wedo_candidate_id: #{payload[:references][:wedo_candidate_id]}"
      Rails.logger.info "      - wedo_job_id: #{payload[:references][:wedo_job_id]}"
      Rails.logger.info "      - wedo_apply_id: #{payload[:references][:wedo_apply_id]}"
      Rails.logger.info "   "
      Rails.logger.info "   📦 Payload ATS References:"
      Rails.logger.info "      - ats_candidate_id: #{payload[:ats_references][:ats_candidate_id].inspect}"
      Rails.logger.info "      - ats_job_id: #{payload[:ats_references][:ats_job_id].inspect}"
      Rails.logger.info "      - ats_apply_id: #{payload[:ats_references][:ats_apply_id].inspect}"
      Rails.logger.info "      - ats_selective_process_id: #{payload[:ats_references][:ats_selective_process_id].inspect}"
      Rails.logger.info "   "
      Rails.logger.info "   📦 Payload Job Info:"
      Rails.logger.info "      - provider_job_id: #{payload[:provider_job_id].inspect}"
      Rails.logger.info "   "
      Rails.logger.info "   📄 Full Payload JSON (first 2000 chars):"
      payload_json = JSON.pretty_generate(payload.as_json)
      Rails.logger.info payload_json[0..2000]
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      return client.update_apply(payload) if is_update

      client.create_apply(payload)
    end

    def apply_exists_in_ats?
      record.candidate.external_id.present? && record.job.external_id.present?
    end

    def validate_required_data
      return "candidate not found" if record.candidate.blank?
      return "job not found" if record.job.blank?
      return "selective_process not found" if record.selective_process.blank?
      return "account not found" if record.account.blank?
      return "candidate name missing" if record.candidate.name.blank?
      return "job external_id missing (job_id=#{record.job_id})" if record.job.external_id.blank?
      return "selective_process external_id missing (sp_id=#{record.selective_process_id})" if record.selective_process.external_id.blank?

      nil
    end

    def build_payload
      {
        action: apply_exists_in_ats? ? "update_apply" : "create_apply",
        provider: ats_provider,
        account_id: record.job.account_id,
        provider_job_id: effective_provider_job_id,
        references: build_references,
        ats_references: build_ats_references,
        candidate: build_candidate_data,
        experiences: build_experiences,
        educations: build_educations,
        skills: build_skills,
        languages: build_languages,
        apply: build_apply_data
      }
    end

    def build_references
      {
        wedo_candidate_id: record.candidate_id,
        wedo_job_id: record.job_id,
        wedo_apply_id: record.id
      }
    end

    def build_ats_references
      ats_refs = {
        ats_candidate_id: record.candidate.external_id,
        ats_job_id: record.job.external_id,
        ats_apply_id: record.external_id,
        ats_selective_process_id: record.selective_process&.external_id
      }

      if ats_refs[:ats_apply_id].blank? && apply_exists_in_ats?
        Rails.logger.warn "⚠️  [ApplyService] UPDATE requested but ats_apply_id is nil (Apply##{record.id})"
      end

      ats_refs
    end

    def build_candidate_data
      candidate_service.send(:build_candidate_data)
    end

    def build_experiences
      candidate_service.send(:build_experiences)
    end

    def build_educations
      candidate_service.send(:build_educations)
    end

    def build_skills
      candidate_service.send(:build_skills)
    end

    def build_languages
      candidate_service.send(:build_languages)
    end

    def build_apply_data
      {
        source: "wedotalent",
        applied_at: record.created_at,
        status: record.selective_process_status,
        is_deleted: record.is_deleted
      }
    end

    def effective_provider_job_id
      # Use provider_job_id if present, otherwise fallback to external_id
      record.job.provider_job_id.presence || record.job.external_id
    end

    def candidate_service
      @candidate_service ||= CandidateService.new(record.candidate)
    end

    def save_ats_ids(ats_ids)
      return unless ats_ids.present?

      save_candidate_ids(ats_ids)
      save_apply_ids(ats_ids)
    end

    def save_candidate_ids(ats_ids)
      return unless ats_ids["candidate_id"] && record.candidate

      record.candidate.update_columns(
        external_id: ats_ids["candidate_id"],
        external_provider: "questt"
      )
    end

    def save_apply_ids(ats_ids)
      updates = {}

      if ats_ids["apply_id"]
        updates[:external_id] = ats_ids["apply_id"]
        updates[:external_provider] = "questt"
      end

      record.update_columns(updates) if updates.any?
    end
  end
end
