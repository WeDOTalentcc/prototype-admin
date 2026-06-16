# frozen_string_literal: true

module V1
  module Users
    module Evaluations
      class EvaluationsController < ApplicationController
        before_action :set_evaluation, only: %i[show update destroy dashboard_stats]
        before_action :ensure_owner, only: %i[update destroy]

        def index
          perform_search(
            model: Evaluation,
            serializer: EvaluationSerializer,
          )
        end

        def show
          render_success(@evaluation, serializer: EvaluationSerializer)
        end

        def create
          @evaluation = Evaluation.create(evaluation_params.merge(user_id: @current_user.id, account_id: @current_user.account_id))

          return render_error(@evaluation, status: :unprocessable_entity) unless @evaluation.save

          @evaluation.generate_questions_from_template(params[:template_id]) if params[:template_id].present?
          render_success(@evaluation, serializer: EvaluationSerializer, status: :created)
        end

        def update
          @evaluation.update(evaluation_params) ? render_success(@evaluation, serializer: EvaluationSerializer) : render_error(@evaluation)
        end

        def destroy
          @evaluation.update(is_deleted: true)
          render_success(@evaluation, serializer: EvaluationSerializer)
        end

        def dashboard_stats
          stats = @evaluation.calculate_dashboard_stats
          render json: { data: stats }, status: :ok
        rescue StandardError => e
          render_simple_error("Erro ao calcular estatísticas: #{e.message}", status: :internal_server_error)
        end

        def generate_report
          return render_simple_error("Parâmetros inválidos", status: :bad_request) if params[:evaluation_id].blank? || params[:job_id].blank?

          report = EvaluationReportService.call(evaluation_id: params[:evaluation_id], job_id: params[:job_id])
          render json: { report: report.data }, status: :ok
        rescue StandardError => e
          render_simple_error("Erro ao gerar relatório: #{e.message}", status: :internal_server_error)
        end

        def process_ai_response
          Rails.logger.info("[EvaluationsController#process_ai_response] Received AI response")

          result = EvaluationAiResponseService.new(
            original_payload: ai_response_params[:original_payload],
            ai_response: ai_response_params[:ai_response],
            chatbot_channel: ai_response_params[:chatbot_channel]
          ).call

          return render_ai_success(result.data) if result.success?

          render_ai_error(result.error, :unprocessable_entity)
        rescue ActionController::ParameterMissing => e
          render_ai_error("Parâmetros obrigatórios ausentes: #{e.param}", :bad_request, "MISSING_PARAMS")
        rescue StandardError => e
          log_unexpected_error(e)
          render_ai_error("Erro interno ao processar resposta", :internal_server_error, "INTERNAL_ERROR")
        end

        private

        def set_evaluation
          @evaluation = Evaluation.find_by(id: params[:id])
          render_not_found("Evaluation") unless @evaluation
        end

        def ensure_owner
          return if @evaluation.user_id == @current_user.id
          return if @evaluation.account_id == @current_user.account_id

          render_simple_error("Not authorized to access this evaluation", status: :forbidden)
        end

        def evaluation_params
          params.require(:evaluation).permit(
            :name, :job_id, :selective_process_id, :user_id, :account_id,
            :status, :position, :sub_status, :description, :is_main, :time,
            :uid, :is_chatbot, :ai_enabled, :report_date, :chatbot_channel,
            :is_trigger, :notification_enabled, :notification_type, :notification_hour,
            :approved_selective_process_id, :rejected_selective_process_id,
            :is_screening, :introduction_details,
            notification_days: [],
            notification_channels: []
          )
        end

        def ai_response_params
          params.permit(
            :chatbot_channel,
            original_payload: %i[account_id evaluation_candidate_id message_id question_id candidate_answer chatbot_channel],
            ai_response: [
              :score, :is_answer_satisfactory, :feedback_for_recruiter, :chat_ack,
              :responded, :changed_subject, :response_to_candidate, :followup_needed,
              :followup_question, :end, :interested_job, :interested_job_msg, :avoid_answer,
              :is_issue_report, :issue_description,
              { next_question: %i[id title text], evaluation_details: {} }
            ]
          )
        end

        def render_ai_success(data)
          Rails.logger.info("[EvaluationsController#process_ai_response] Success: #{data}")
          render json: { success: true, message: "Resposta processada com sucesso", data: data }, status: :ok
        end

        def render_ai_error(message, status, code = nil)
          Rails.logger.error("[EvaluationsController#process_ai_response] Error: #{message}")
          render json: { success: false, error: message, code: code || error_code_for(message) }, status: status
        end

        def error_code_for(message)
          return "NOT_FOUND" if message&.match?(/couldn't find|not found/i)
          return "TENANT_ERROR" if message&.include?("tenant")

          "PROCESSING_ERROR"
        end

        def log_unexpected_error(error)
          Rails.logger.error("[EvaluationsController#process_ai_response] Unexpected error: #{error.class.name} - #{error.message}")
          Rails.logger.error(error.backtrace.first(10).join("\n"))
        end
      end
    end
  end
end
