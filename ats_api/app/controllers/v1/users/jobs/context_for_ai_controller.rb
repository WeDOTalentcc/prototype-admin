# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class ContextForAiController < ApplicationController
        before_action :set_job

        def show
          tier = (params[:tier] || 1).to_i
          data = tier >= 2 ? build_tier2 : build_tier1

          render json: { success: true, data: data }, status: :ok
        end

        private

        def set_job
          @job = Job.include_base.where(is_deleted: false).find_by(id: params[:id])
          return render_not_found("Job") unless @job
          render_simple_error("Not authorized", status: :forbidden) unless @job.account_id == @current_user.account_id
        end

        def build_tier1
          {
            job: serialize_job,
            pipeline_summary: @job.selection_process_summary
          }
        end

        def build_tier2
          build_tier1.merge(
            analytics: fetch_analytics,
            recent_activity: fetch_recent_activity
          )
        end

        def serialize_job
          missing = @job.make_missing_fields

          {
            id: @job.id,
            title: @job.title,
            description: @job.description,
            city: @job.city,
            state: @job.state,
            country: @job.country,
            workplace_type_text: @job.workplace_type_text,
            seniority_text: seniority_text,
            employment_type_text: employment_type_text,
            priority_text: priority_text,
            urgency_level_text: urgency_level_text,
            is_active: @job.is_active,
            is_archived: @job.is_archived,
            is_urgent: @job.is_urgent,
            is_deleted: @job.is_deleted,
            disabilities: @job.disabilities,
            published_date: @job.published_date,
            application_deadline: @job.application_deadline,
            screening_deadline: @job.screening_deadline,
            shortlist_deadline: @job.shortlist_deadline,
            closing_deadline: @job.closing_deadline,
            job_status_name: @job.try(:job_status) || @job.job_status&.name,
            job_status_color: @job.try(:job_status_color),
            user_name: @job.try(:user_name) || @job.user&.name,
            user_email: @job.try(:user_email) || @job.user&.email,
            company_name: @job.try(:company_name) || @job.company&.name,
            department_name: @job.try(:department_name) || @job.department&.name,
            team_name: @job.try(:team_name),
            hiring_manager_name: @job.try(:hiring_manager_name) || @job.hiring_manager&.name,
            hiring_manager_email: @job.try(:hiring_manager_email) || @job.hiring_manager&.email,
            reports_to_position_title: @job.try(:reports_to_position_title),
            salary_from: @job.salary_from,
            salary_to: @job.salary_to,
            salary_currency: @job.try(:salary_currency),
            salary_period: @job.try(:salary_period),
            salary_contract_type: @job.try(:salary_contract_type),
            commission_from: @job.try(:commission_from),
            commission_to: @job.try(:commission_to),
            bonus_from: @job.try(:bonus_from),
            bonus_to: @job.try(:bonus_to),
            skills: skill_names,
            benefits: benefit_names,
            responsibilities: @job.responsibilities,
            reason_for_pause: @job.reason_for_pause,
            provider: @job.provider,
            sector: @job.sector,
            segment: @job.segment,
            cached_applies_count: @job.try(:cached_applies_count).to_i,
            completeness_percentage: @job.completeness_percentage,
            is_ready_for_publication: @job.is_ready_for_publication?,
            missing_fields: missing.map { |f| f[:field] },
            missing_fields_count: missing.size,
            created_at: @job.created_at,
            updated_at: @job.updated_at
          }
        end

        def skill_names
          SkillRelationship.where(reference_type: "Job", reference_id: @job.id, is_deleted: false)
                           .joins("JOIN skills ON skills.id = skill_relationships.skill_id")
                           .pluck("skills.name")
        end

        def benefit_names
          @job.benefits.pluck(:name)
        rescue StandardError
          []
        end

        def fetch_analytics
          ::Jobs::AnalyticsService.new(job: @job, force_refresh: false).call
        rescue StandardError => e
          Rails.logger.error "[ContextForAi] Analytics failed for Job##{@job.id}: #{e.message}"
          {}
        end

        def fetch_recent_activity
          @job.applies
              .where(is_deleted: false)
              .includes(:candidate, :selective_process)
              .order(updated_at: :desc)
              .limit(10)
              .map do |apply|
            {
              candidate_name: apply.candidate&.name,
              selective_process: apply.selective_process&.name,
              updated_at: apply.updated_at
            }
          end
        rescue StandardError => e
          Rails.logger.error "[ContextForAi] Activity failed for Job##{@job.id}: #{e.message}"
          []
        end

        def seniority_text
          idx = @job.seniority
          idx.nil? ? "Nao informado" : (Job::SENIORITY[idx] || "Nao informado")
        end

        def employment_type_text
          idx = @job.employment_type
          idx.nil? ? "Nao informado" : (Job::EMPLOYMENT_TYPES[idx] || "Nao informado")
        end

        def priority_text
          Job::PRIORITY.find { |p| p["id"] == @job.priority }&.dig("name") || "Nao informado"
        end

        def urgency_level_text
          Job::URGENCY_LEVEL.find { |u| u["id"] == @job.urgency_level }&.dig("name") || "Nao informado"
        end
      end
    end
  end
end
