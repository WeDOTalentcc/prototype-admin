# frozen_string_literal: true

module V1
  module Users
    module Jobs
      module Applies
        class AppliesController < ApplicationController
          before_action :set_job

          def approve_collection
            unless params[:select_all_params].present?
              return render_simple_error(
                "select_all_params é obrigatório",
                status: :bad_request
              )
            end

            CollectionJob::AppliesJob::ApproveCollectionJob.perform_later(
              select_all_params.to_h,
              @current_user.id,
              @job.id
            )

            render_success({
              status: "processing",
              message: "As candidaturas estão sendo aprovadas em background",
              job_id: @job.id
            })
          rescue StandardError => e
            Rails.logger.error("[ApproveCollection] #{e.class}: #{e.message}")
            render_simple_error("Erro interno ao processar aprovação", status: :internal_server_error)
          end

          def reject_collection
            unless params[:select_all_params].present?
              return render_simple_error(
                "select_all_params é obrigatório",
                status: :bad_request
              )
            end

            FairnessGuard.audit_bulk_rejection(
              user_id: @current_user.id,
              job_id: @job.id,
              select_all_params: select_all_params
            )

            CollectionJob::AppliesJob::RejectCollectionJob.perform_later(
              select_all_params.to_h,
              @current_user.id,
              @job.id
            )

            fairness_warning = FairnessGuard.bulk_rejection_warning(select_all_params)

            render_success({
              status: "processing",
              message: "As candidaturas estão sendo rejeitadas em background",
              job_id: @job.id,
              fairness_warning: fairness_warning
            }.compact)
          rescue StandardError => e
            Rails.logger.error("[RejectCollection] #{e.class}: #{e.message}")
            render_simple_error("Erro interno ao processar rejeição", status: :internal_server_error)
          end

          def send_reject_feedback
            generate = ActiveModel::Type::Boolean.new.cast(params[:generate])

            if generate
              handle_generate_reject_feedback
            else
              handle_template_reject_feedback
            end
          rescue StandardError => e
            Rails.logger.error("[SendRejectFeedback] #{e.class}: #{e.message}")
            render_simple_error("Erro interno ao processar", status: :internal_server_error)
          end

          # Gate 1: Screening → Interview (bulk approve/reject at screening stage)
          def gate1_approve
            gate_action(from_status: :screening, to_status: :interview, action: :approve)
          end

          def gate1_reject
            gate_action(from_status: :screening, to_status: :rejected, action: :reject)
          end

          # Gate 2: Interview → Hired (bulk approve/reject at interview stage)
          def gate2_approve
            gate_action(from_status: :interview, to_status: :hired, action: :approve)
          end

          def gate2_reject
            gate_action(from_status: :interview, to_status: :rejected, action: :reject)
          end

          private

          def gate_action(from_status:, to_status:, action:)
            apply_ids = params[:apply_ids]
            return render_simple_error("apply_ids é obrigatório", status: :bad_request) unless apply_ids.present?

            from_stages = @job.selective_processes.where(status: from_status)
            target_stage = @job.selective_processes.find_by(status: to_status)

            unless target_stage
              return render_simple_error(
                "Estágio '#{to_status}' não encontrado para esta vaga",
                status: :unprocessable_entity
              )
            end

            applies = Apply.where(id: apply_ids, job_id: @job.id, is_deleted: false, selective_process_id: from_stages.select(:id))

            if applies.empty?
              return render_simple_error(
                "Nenhuma candidatura encontrada no estágio '#{from_status}'",
                status: :unprocessable_entity
              )
            end

            Current.user = @current_user
            Thread.current[:skip_pipeline_broadcast] = true
            results = applies.map do |apply|
              apply.update(selective_process: target_stage)
              { apply_id: apply.id, candidate_id: apply.candidate_id, status: "moved_to_#{to_status}" }
            end

            Apply.broadcast_bulk_pipeline_update(@job.id, results, to_status)

            render_success({
              action: action,
              gate: from_status == :screening ? 1 : 2,
              moved: results.size,
              target_stage: target_stage.name,
              results: results
            })
          rescue StandardError => e
            Rails.logger.error("[GateAction] #{e.class}: #{e.message}")
            render_simple_error("Erro interno ao processar gate action", status: :internal_server_error)
          ensure
            Thread.current[:skip_pipeline_broadcast] = nil
          end

          def handle_generate_reject_feedback
            unless params[:reference_ids].present? || params[:select_all_params].present?
              return render_simple_error(
                "reference_ids ou select_all_params é obrigatório",
                status: :bad_request
              )
            end

            if params[:reference_ids].present? && params[:reference_ids].size > 50
              return render_simple_error(
                "Limite máximo de 50 candidatos por vez",
                status: :bad_request
              )
            end

            payload = build_send_reject_feedback_payload

            CollectionJob::AppliesJob::RejectFeedbackCollectionJob.perform_later(
              payload,
              @current_user.id,
              @job.id
            )

            render_success({
              status: "processing",
              message: "Os feedbacks estão sendo gerados em background",
              job_id: @job.id
            })
          end

          def handle_template_reject_feedback
            unless params[:reference_ids].present?
              return render_simple_error("reference_ids é obrigatório quando generate é false", status: :bad_request)
            end
            unless params[:subject].present?
              return render_simple_error("subject é obrigatório quando generate é false", status: :bad_request)
            end
            unless params[:description].present?
              return render_simple_error("description é obrigatório quando generate é false", status: :bad_request)
            end

            if params[:reference_ids].size > 50
              return render_simple_error("Limite máximo de 50 candidatos por vez", status: :bad_request)
            end

            payload = build_template_reject_feedback_payload

            CollectionJob::AppliesJob::RejectFeedbackCollectionJob.perform_later(
              payload,
              @current_user.id,
              @job.id
            )

            render_success({
              status: "processing",
              message: "Os feedbacks estão sendo criados em background",
              job_id: @job.id
            })
          end

          def build_send_reject_feedback_payload
            if params[:reference_ids].present?
              { reference_ids: params[:reference_ids].first(50) }
            else
              { select_all_params: params[:select_all_params].to_h }
            end
          end

          def build_template_reject_feedback_payload
            {
              reference_ids: params[:reference_ids].first(50),
              template: {
                subject: params[:subject],
                description: params[:description],
                name: params[:name].presence || "Feedback de rejeição"
              }
            }
          end

          def set_job
            @job = Job.find_by!(id: params[:id], account_id: @current_user.account_id)
          end

          def select_all_params
            params.require(:select_all_params).permit!
          end
        end
      end
    end
  end
end
