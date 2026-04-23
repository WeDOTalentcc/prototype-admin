# frozen_string_literal: true

require "digest"

module CollectionJob
  module EvaluationCandidatesJob
    class CreateCollectionJob < ApplicationJob
      queue_as :default
      sidekiq_options retry: false

      MAX_BATCH_SIZE = 50
      PAGE_SIZE = 30
      EXPIRATION_DAYS = 7
      INVITE_SUBJECT = "Você foi convidado(a) para uma avaliação"

      QUESTION_COPY_ATTRIBUTES = %w[
        title description details number_retakers time response_type position
        selective_process_id choices expected_response is_required
        parent_question_id value_father extra_params competence_type
        bloom_level dreyfus_target ocean_trait wsi_reviewed wsi_metadata
      ].freeze

      EVALUATION_COPY_ATTRIBUTES = %w[
        selective_process_id status position sub_status description time
        is_chatbot ai_enabled report_date notification_enabled
        notification_type notification_days notification_hour is_screening
      ].freeze

      def perform(select_all_params, user_id, evaluation_candidate_collection_params)
        @user = User.find(user_id)
        @account = @user.account
        @ec_params = evaluation_candidate_collection_params
        Current.user = @user

        Apartment::Tenant.switch!(@account.tenant)
        process_collection(select_all_params)
      rescue StandardError => e
        Rails.logger.error "[CreateCollectionJob] Error: #{e.message}"
        Rails.logger.error e.backtrace.first(10).join("\n")
        broadcast_error(e.message)
        raise
      end

      private

      attr_reader :user, :account, :ec_params

      def process_collection(select_all_params)
        first_result = CollectionService.call(select_all_params, 1)
        total_count = first_result[:total_count]

        return if Rails.env.production? && total_count > 1
        return broadcast_limit_exceeded if total_count > MAX_BATCH_SIZE

        @job = Job.find(ec_params[:job_id])
        return unless @job

        @evaluation = find_or_create_evaluation

        result = process_records(select_all_params, total_count)
        broadcast_completed(result[:ids], result[:errors])
      end

      def find_or_create_evaluation
        existing = Evaluation.find_by(
          parent_evaluation_id: ec_params[:evaluation_id],
          is_deleted: false,
          job_id: @job.id
        )
        return existing if existing

        parent = Evaluation.find_by(id: ec_params[:evaluation_id], is_deleted: false)
        return parent unless parent

        clone = clone_evaluation(parent)
        clone_questions(parent, clone) if clone
        clone || parent
      end

      def clone_evaluation(source)
        attrs = source.attributes.slice(*EVALUATION_COPY_ATTRIBUTES)
        Evaluation.create(
          **attrs.symbolize_keys,
          name: "#{source.name} - #{Time.current.strftime('%d/%m/%Y %H:%M')}",
          job_id: ec_params[:job_id],
          user_id: user.id,
          account_id: account.id,
          is_main: false,
          uid: SecureRandom.uuid,
          chatbot_channel: source.respond_to?(:chatbot_channel) ? source.chatbot_channel : nil,
          notification_channels: source.notification_channels,
          parent_evaluation_id: source.id
        )
      end

      def clone_questions(source_evaluation, target_evaluation)
        Question.where(evaluation_id: source_evaluation.id, is_deleted: false).find_each do |question|
          attrs = question.attributes.slice(*QUESTION_COPY_ATTRIBUTES)
          Question.create(**attrs.symbolize_keys, evaluation_id: target_evaluation.id)
        end
      end

      def process_records(select_all_params, total_count)
        page = 1
        total_pages = (total_count / PAGE_SIZE) + 1
        count = 0
        errors = []
        ids = []

        while page <= total_pages
          CollectionService.call(select_all_params, page)[:records].each do |record|
            next if record.is_deleted

            count += 1
            sleep(0.2)
            broadcast_progress(count, total_count, errors)

            evaluation_candidate, resend = find_or_create_evaluation_candidate(record, errors)
            next unless evaluation_candidate

            ids << evaluation_candidate.id
            send_notification(record, evaluation_candidate, resend)
          end
          page += 1
        end

        { ids: ids, errors: errors }
      end

      def find_or_create_evaluation_candidate(record, errors)
        existing = EvaluationCandidate.find_by(apply_id: record.id, evaluation_id: @evaluation.id)

        if existing
          reset_evaluation_candidate(existing)
          return [ existing, true ]
        end

        candidate = EvaluationCandidate.create(
          candidate_id: record.candidate_id,
          evaluation_id: @evaluation.id,
          apply_id: record.id,
          job_id: ec_params[:job_id],
          date_expiration: EXPIRATION_DAYS.days.from_now,
          user_id: user.id,
          account_id: account.id,
          notification_channels: resolved_notification_channels
        )

        if candidate.errors.any?
          errors << "ID: #{record.id} | #{record.name} | #{record.email} - Erro ao criar evaluation candidate"
          return [ nil, false ]
        end

        [ candidate, false ]
      end

      def reset_evaluation_candidate(evaluation_candidate)
        evaluation_candidate.update(
          date_expiration: EXPIRATION_DAYS.days.from_now,
          completed: false,
          score: 0.0,
          ai_feedback: nil,
          evaluation_summary: nil,
          date_view: nil,
          session_status: nil,
          timeout_count: 0,
          retry_attempts: 0,
          last_timeout_at: nil,
          last_reminder_at: nil,
          last_question_index: nil,
          declined_at: nil,
          declined_reason: nil
        )
      end

      def send_notification(_record, evaluation_candidate, resend)
        if resend && @evaluation.respond_to?(:whatsapp_chatbot?) && @evaluation.whatsapp_chatbot?
          evaluation_candidate.send(:trigger_whatsapp_chatbot_start)
        end

        channels = notification_channels
        return if channels.empty?

        interview_sessions = build_interview_sessions(evaluation_candidate, channels)

        Evaluations::UnifiedInviteService.new(
          evaluation_candidate: evaluation_candidate,
          user: user,
          channels: channels,
          interview_sessions: interview_sessions
        ).call
      end

      def build_interview_sessions(evaluation_candidate, channels)
        InterviewSession.bulk_find_or_create_for_channels(
          evaluation_candidate: evaluation_candidate,
          channels: channels,
          created_by: user
        )
      end

      def resolved_notification_channels
        from_params = Array(ec_params[:notification_channels])
        return from_params if from_params.any?

        from_eval = Array(@evaluation.notification_channels)
        return from_eval if from_eval.any?

        from_job = Array(@job&.notification_channels)
        return from_job if from_job.any?

        @evaluation.internal_chatbot? ? [ "internal" ] : []
      end

      def notification_channels
        resolved_notification_channels.map(&:to_sym)
      end

      def broadcast_progress(count, total, errors)
        EvaluationCandidateCollectionChannel.broadcast_to(
          "#{user.id}_collection",
          { status: "loading", percent: (count * 100 / total).round(2), errors: errors }
        )
      end

      def broadcast_completed(ids, errors)
        sleep(0.3)
        EvaluationCandidateCollectionChannel.broadcast_to(
          "#{user.id}_collection",
          { status: "completed", percent: 100, sent_evaluation_candidate_ids: ids, errors: errors }
        )
      end

      def broadcast_error(message)
        EvaluationCandidateCollectionChannel.broadcast_to(
          "#{user.id}_collection",
          { status: "error", percent: 100, errors: [ "Erro ao processar envio de provas: #{message}" ] }
        )
      end

      def broadcast_limit_exceeded
        EvaluationCandidateCollectionChannel.broadcast_to(
          "#{user.id}_collection",
          { status: "completed", percent: 100, errors: [ "Total de registros maior que #{MAX_BATCH_SIZE} - Processamento interrompido" ] }
        )
      end
    end
  end
end
