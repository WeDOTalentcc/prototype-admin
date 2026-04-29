# frozen_string_literal: true

module CollectionJob
  module AppliesJob
    class RejectFeedbackCollectionJob < ApplicationJob
      include PhoneNormalizable

      MAX_APPLIES = 50

      queue_as :default
      sidekiq_options retry: 2

      def perform(params, user_id, job_id)
        user = User.find(user_id)
        account = user.account
        Current.user = user
        Apartment::Tenant.switch!(account.tenant)

        params = params.to_h.with_indifferent_access
        use_template = params[:template].present?

        applies = resolve_applies(params, job_id)
        return broadcast_error(user_id, "Nenhuma candidatura encontrada") if applies.empty?

        total_count = applies.size
        results = []
        processed = 0

        applies.each_with_index do |apply, index|
          result = use_template ? create_feedback_from_template(apply, params[:template], user_id) : generate_feedback_for_apply(apply)
          results << result
          processed += 1

          percent = ((index + 1) * 100.0 / total_count).round
          CollectionChannel.broadcast_to("#{user_id}_collection", {
            action: "send_reject_feedback",
            status: "loading",
            percent: percent,
            message: "Processando: #{processed}/#{total_count} feedbacks #{use_template ? 'criados' : 'gerados'}"
          })
        end

        CollectionChannel.broadcast_to("#{user_id}_collection", {
          action: "send_reject_feedback",
          status: "completed",
          percent: 100,
          total: total_count,
          results: results,
          message: "#{total_count} feedbacks #{use_template ? 'criados' : 'gerados'} com sucesso"
        })
      rescue => e
        Rails.logger.error "❌ [RejectFeedbackCollectionJob] Erro: #{e.message}"
        broadcast_error(user_id, "Erro ao processar: #{e.message}")
        raise
      end

      private

      def resolve_applies(params, job_id)
        params = params.to_h.with_indifferent_access

        if params[:reference_ids].present?
          Apply.where(id: params[:reference_ids], job_id: job_id, is_deleted: false).limit(MAX_APPLIES)
        elsif params[:select_all_params].present?
          select_all_params = params[:select_all_params].to_h.with_indifferent_access
          applies = Apply.where(job_id: job_id, is_deleted: false)
          applies = apply_filters(applies, select_all_params)
          applies.limit(MAX_APPLIES)
        else
          Apply.none
        end
      end

      def apply_filters(applies, select_all_params)
        if select_all_params[:reference_ids].present?
          applies = applies.where(id: select_all_params[:reference_ids])
        end

        if select_all_params[:where].present?
          select_all_params[:where].each { |key, value| applies = applies.where(key => value) }
        end

        if select_all_params[:filter].present?
          select_all_params[:filter].each do |field_name, field_value|
            next unless Apply.column_names.include?(field_name.to_s)

            if field_value.is_a?(Array) || field_value.is_a?(Integer) || field_value.is_a?(Hash)
              applies = applies.where(field_name => field_value)
            elsif field_value.present?
              applies = applies.where(Apply.arel_table[field_name].matches("%#{Apply.sanitize_sql_like(field_value.to_s)}%"))
            end
          end
        end

        applies = applies.where.not(id: select_all_params[:except_ids]) if select_all_params[:except_ids].present?
        applies = applies.order(select_all_params[:order]) if select_all_params[:order].present?
        applies
      end

      def create_feedback_from_template(apply, template, user_id)
        record = {
          candidate: apply.candidate,
          job: apply.job,
          user: User.find_by(id: user_id)
        }
        description = TagReplacer::Service.call(template[:description].to_s, record: record, recruiter_id: user_id)
        subject = TagReplacer::Service.call(template[:subject].to_s, record: record, recruiter_id: user_id)
        name = TagReplacer::Service.call((template[:name] || "Feedback de rejeição").to_s, record: record, recruiter_id: user_id)

        feedback = create_feedback_record_from_template(apply, description: description, subject: subject, name: name)
        {
          apply_id: apply.id,
          candidate_id: apply.candidate_id,
          candidate_name: apply.candidate&.name,
          feedback_id: feedback&.id,
          feedback_text: description,
          tone: "neutral",
          development_areas: []
        }
      rescue => e
        Rails.logger.error "❌ [RejectFeedbackCollectionJob] Erro apply #{apply.id}: #{e.message}"
        {
          apply_id: apply.id,
          candidate_id: apply.candidate_id,
          candidate_name: apply.candidate&.name,
          feedback_text: nil,
          tone: "neutral",
          development_areas: [],
          error: e.message
        }
      end

      def generate_feedback_for_apply(apply)
        result = Candidates::RejectFeedbackGeneratorService.call(apply: apply)
        feedback = create_feedback_record(apply, result)
        {
          apply_id: apply.id,
          candidate_id: apply.candidate_id,
          candidate_name: apply.candidate&.name,
          feedback_id: feedback&.id,
          **result
        }
      rescue => e
        Rails.logger.error "❌ [RejectFeedbackCollectionJob] Erro apply #{apply.id}: #{e.message}"
        {
          apply_id: apply.id,
          candidate_id: apply.candidate_id,
          candidate_name: apply.candidate&.name,
          feedback_text: nil,
          tone: "neutral",
          development_areas: [],
          error: e.message
        }
      end

      def create_feedback_record_from_template(apply, description:, subject:, name:)
        return nil if description.blank?

        feedback = Feedback.create!(
          account_id: apply.account_id,
          job_id: apply.job_id,
          selective_process_id: apply.selective_process_id,
          apply_id: apply.id,
          title: subject,
          description: description,
          name: name,
          additional_text: { tone: "neutral", development_areas: [] }.to_json
        )
        send_feedback_email(apply, feedback)
        feedback
      rescue => e
        Rails.logger.error "❌ [RejectFeedbackCollectionJob] Falha ao criar Feedback (apply #{apply.id}): #{e.message}"
        nil
      end

      def create_feedback_record(apply, result)
        return nil if result[:feedback_text].blank?

        feedback = Feedback.create!(
          account_id: apply.account_id,
          job_id: apply.job_id,
          selective_process_id: apply.selective_process_id,
          apply_id: apply.id,
          title: "Feedback de rejeição - #{apply.candidate&.name || 'Candidato'}",
          description: result[:feedback_text].to_s,
          name: apply.candidate&.name || "Feedback gerado",
          additional_text: { tone: result[:tone], development_areas: result[:development_areas] }.to_json
        )
        send_feedback_email(apply, feedback)
        feedback
      rescue => e
        Rails.logger.error "❌ [RejectFeedbackCollectionJob] Falha ao criar Feedback (apply #{apply.id}): #{e.message}"
        nil
      end

      def send_feedback_email(apply, feedback)
        candidate = apply.candidate
        return unless candidate

        phone = normalize_phone(candidate.mobile_phone)
        try_whatsapp = phone.present? && Meta::WhatsappService.send_allowed?(phone)

        whatsapp_ok = false
        if try_whatsapp
          begin
            response = send_feedback_via_whatsapp(phone, apply, feedback)
            whatsapp_ok = response&.success?
          rescue => e
            Rails.logger.warn "📵 [RejectFeedbackCollectionJob] WhatsApp exceção (apply #{apply.id}): #{e.message} - fallback para e-mail"
          end
          unless whatsapp_ok
            Rails.logger.warn "📵 [RejectFeedbackCollectionJob] WhatsApp falhou (apply #{apply.id}), fallback para e-mail"
          end
        end

        send_feedback_via_email(apply, feedback) unless whatsapp_ok
      rescue => e
        Rails.logger.error "❌ [RejectFeedbackCollectionJob] Falha ao enviar feedback (apply #{apply.id}): #{e.message}"
      end

      def send_feedback_via_whatsapp(phone, apply, feedback)
        job_title = sanitize_whatsapp_param(apply.job&.title.to_s, default: "Vaga")
        feedback_content = sanitize_whatsapp_param(feedback.description.to_s, default: "Feedback de rejeição")
        components = [ {
          type: "body",
          parameters: [
            { type: "text", text: job_title },
            { type: "text", text: feedback_content }
          ]
        } ]
        Meta::WhatsappService.send_message_by_template(phone, "feedback_reprovados", "pt_BR", components)
      end

      def sanitize_whatsapp_param(text, default: "Feedback de rejeição")
        result = text
          .to_s
          .gsub(/[\r\n\t]+/, " ")
          .gsub(/ {5,}/, "    ")
          .strip
        result.presence || default
      end

      def send_feedback_via_email(apply, feedback)
        return unless apply.candidate&.email.present?

        RejectFeedbackMailer.feedback_to_candidate(
          candidate: apply.candidate,
          feedback: feedback,
          job: apply.job
        ).deliver_later
      rescue => e
        Rails.logger.error "❌ [RejectFeedbackCollectionJob] Falha ao enviar e-mail (apply #{apply.id}): #{e.message}"
      end

      def broadcast_error(user_id, message)
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          action: "send_reject_feedback",
          status: "error",
          message: message
        })
      end
    end
  end
end
