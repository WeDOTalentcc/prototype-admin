# frozen_string_literal: true

module V1
  module Users
    class JobsController < ApplicationController
      before_action :authorize_request
      before_action :set_job, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        perform_search(
          model: Job,
          serializer: JobSerializer
        )
      end

      def show
        render_success(@job, serializer: JobSerializer)
      end

      def create
        @job = @current_user.jobs.build(job_params.merge(account_id: @current_user.account_id))

        if @job.save
          return render_success(@job, serializer: JobSerializer, status: :created)
        end
        render_error(@job, status: :unprocessable_entity)
      end

      def update
        @job.update(job_params) ? render_success(@job, serializer: JobSerializer) : render_error(@job)
      end

      def destroy
        @job.destroy
        render_no_content
      end

      private

      def set_job
        @job = Job.find_by(id: params[:id])
        render_not_found("Job") unless @job
      end

      def ensure_owner
        return if @job.user_id == @current_user.id
        render_simple_error("Não autorizado a realizar esta ação neste job", status: :forbidden)
      end

      def job_params
        params.require(:job).permit(
          :title, :description, :user_id, :account_id,
          :status, :department, :employment_type, :seniority_level, :priority, :urgency_level,
          :salary_range, :bonus_range,
          :deadline_screening, :deadline_shortlist, :deadline_closing,
          :manager, :manager_email, :recruiter, :recruiter_email, :created_by, :organizational_structure,
          :published_linkedin, :published_website, :published_indeed,
          :linkedin_post_id, :indeed_job_id, :last_published_at,
          :is_confidential, :is_affirmative, :affirmative_criteria_primary,
          :affirmative_criteria_secondary, :affirmative_description,
          :affirmative_document_required,
          :visibility, :masked_company_name, :exclude_from_sync, :public_slug,
          :budget, :budget_used,
          :approval_status, :approval_requested_at, :approval_requested_by,
          :approved_by, :approved_at, :rejection_reason,
          :whatsapp_template_type, :fork_uuid,
          technical_requirements: [], behavioral_competencies: [],
          screening_questions: [], interview_stages: [], languages: [],
          benefits: [], affirmative_document_types: [], access_list: [], tags: []
        )
      end
    end
  end
end
