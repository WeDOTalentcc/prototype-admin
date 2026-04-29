# frozen_string_literal: true

module V1
  module Users
    class EmailTemplatesController < ApplicationController
      before_action :set_email_template, only: %i[show update destroy duplicate]

      def index
        authorize EmailTemplate

        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        params[:where][:is_deleted] = false unless params[:where].key?(:is_deleted)

        perform_search(
          model: EmailTemplate,
          serializer: EmailTemplateSerializer
        )
      end

      def show
        authorize @email_template

        render_success(@email_template, serializer: EmailTemplateSerializer)
      end

      def create
        authorize EmailTemplate

        @email_template = EmailTemplate.new(email_template_params)
        @email_template.account_id = @current_user.account_id
        @email_template.user_id = @current_user.id

        if @email_template.save
          return render_success(@email_template, serializer: EmailTemplateSerializer, status: :created)
        end

        render_error(@email_template)
      end

      def update
        authorize @email_template

        if @email_template.update(email_template_params)
          return render_success(@email_template, serializer: EmailTemplateSerializer)
        end

        render_error(@email_template)
      end

      def destroy
        authorize @email_template

        @email_template.update(is_deleted: true)
        render_success(@email_template, serializer: EmailTemplateSerializer)
      end

      def categories
        authorize EmailTemplate

        render json: {
          categories: EmailTemplate::CATEGORIES
        }
      end

      def tags
        authorize EmailTemplate

        reference_types = Array(params[:reference_types] || params[:reference_type]).map(&:to_s)
        all_tags = EmailTemplate.tag_array
        tags_list = []

        if reference_types.empty?
          all_tags.each_value do |tag_array|
            tags_list.concat(tag_array)
          end
        else
          reference_types.each do |type|
            if all_tags.key?(type.to_sym)
              tags_list.concat(all_tags[type.to_sym])
            end
          end
        end

        render json: {
          data: tags_list.map do |tag|
            {
              attributes: {
                text: tag[:text],
                tag: tag[:tag],
                field: tag[:field]
              }
            }
          end
        }
      end

      def generate_suggestion
        authorize EmailTemplate

        text = params[:text] || params[:modification_text]
        email_template_id = params[:email_template_id] || params[:id]

        extra_params = params[:extra_params] || {}
        extra_params = extra_params.to_h.with_indifferent_access if extra_params.respond_to?(:to_h)
        if params[:reference_types].present? || params[:reference_type].present?
          reference_types = Array(params[:reference_types] || params[:reference_type]).map(&:to_s)
          extra_params[:reference_types] = reference_types
        end
        extra_params[:subject] = params[:subject] if params[:subject].present?
        extra_params[:content] = params[:content] if params[:content].present?
        extra_params[:account_id] = @current_user.account_id if @current_user&.account_id.present?

        if text.blank?
          return render_simple_error("text não pode estar em branco", status: :unprocessable_entity)
        end

        email_template = nil
        if email_template_id.present?
          email_template = EmailTemplate.where(account_id: @current_user.account_id).find_by(id: email_template_id)
          if email_template.nil?
            return render_not_found("Email Template")
          end
          authorize email_template
        end

        suggestion = EmailTemplates::SuggestionService.call(email_template, text, extra_params)

        if suggestion.nil?
          return render_simple_error("Não foi possível gerar a sugestão", status: :internal_server_error)
        end

        render json: {
          data: {
            name: suggestion[:name],
            subject: suggestion[:subject],
            content: suggestion[:content],
            category_id: suggestion[:category_id]
          }
        }, status: :ok
      end

      def duplicate
        authorize @email_template

        duplicated_template = @email_template.dup
        duplicated_template.name = "#{@email_template.name} (cópia)"
        duplicated_template.user_id = @current_user.id
        duplicated_template.account_id = @current_user.account_id
        duplicated_template.is_deleted = false

        if duplicated_template.save
          return render_success(duplicated_template, serializer: EmailTemplateSerializer, status: :created)
        end

        render_error(duplicated_template)
      end

      def render_preview
        authorize EmailTemplate

        content = params[:content]

        if params[:template_id].present?
          template = EmailTemplate.where(account_id: @current_user.account_id).find_by(id: params[:template_id])
          return render_not_found("Email Template") unless template
          authorize template
          content ||= template.content
        end

        return render_simple_error("content é obrigatório", status: :unprocessable_entity) if content.blank?

        context_params = params.permit(context: [ :candidate_id, :job_id ])[:context] || {}
        record = build_render_record(context_params)

        rendered = TagReplacer::Service.call(content, record: record, recruiter_id: @current_user.id)
        missing = rendered.scan(/\{\{[^}]+\}\}/).uniq

        render json: { rendered_text: rendered, missing_variables: missing }, status: :ok
      end

      def render_for_candidate
        authorize EmailTemplate

        template = EmailTemplate.where(account_id: @current_user.account_id).find_by(id: params[:template_id])
        return render_not_found("Email Template") unless template

        candidate = Candidate.find_by(id: params[:candidate_id], account_id: @current_user.account_id)
        return render_not_found("Candidate") unless candidate

        record = { user: @current_user, Candidate: candidate }

        if params[:job_id].present?
          job = Job.find_by(id: params[:job_id], account_id: @current_user.account_id)
          return render_not_found("Job") unless job
          record[:Job] = job
        end

        if params[:apply_id].present?
          apply = Apply.find_by(id: params[:apply_id], is_deleted: false)
          record[:Apply] = apply if apply
        end

        content = template.content
        subject = template.subject

        extra_variables = params[:extra_variables] || {}
        extra_variables.each do |key, value|
          content = content.gsub("{{#{key}}}", value.to_s)
          subject = subject&.gsub("{{#{key}}}", value.to_s)
        end

        rendered_body = TagReplacer::Service.call(content, record: record, recruiter_id: @current_user.id)
        rendered_subject = subject.present? ? TagReplacer::Service.call(subject, record: record, recruiter_id: @current_user.id) : ""

        body_missing = rendered_body.scan(/\{\{[^}]+\}\}/).uniq
        subject_missing = rendered_subject.scan(/\{\{[^}]+\}\}/).uniq
        all_missing = (body_missing + subject_missing).uniq

        variables_used = template.content.scan(/\{\{([^}]+)\}\}/).flatten.uniq - all_missing.map { |v| v.gsub(/[{}]/, "") }

        render json: {
          subject: rendered_subject,
          body: rendered_body,
          body_text: ActionView::Base.full_sanitizer.sanitize(rendered_body),
          variables_used: variables_used,
          variables_missing: all_missing
        }, status: :ok
      end

      def send_email
        authorize EmailTemplate

        send_params = send_email_params

        if send_params[:interview_session_id].present?
          return send_interview_via_unified_template(send_params)
        end

        collections = Array(send_params[:collections])

        return render_simple_error("collections é obrigatório e deve conter pelo menos um item", status: :unprocessable_entity) if collections.empty?

        subject = send_params[:subject]
        content = send_params[:content]

        if send_params[:template_id].present?
          template = EmailTemplate.where(account_id: @current_user.account_id).find_by(id: send_params[:template_id])
          return render_not_found("Email Template") unless template
          authorize template

          subject ||= template.subject
          content ||= template.content
        end

        return render_simple_error("subject é obrigatório", status: :unprocessable_entity) if subject.blank?
        return render_simple_error("content é obrigatório", status: :unprocessable_entity) if content.blank?

        dispatch = Dispatch.create!(
          account_id: @current_user.account_id,
          user_id: @current_user.id,
          channel_type: "microsoft_mail",
          status: :pending,
          name: "Email Template Send - #{Time.current}",
          subject: subject,
          body: content
        )

        message_ids = []
        applies_created = 0

        job = send_params[:job_id].present? ? Job.find_by(id: send_params[:job_id], account_id: @current_user.account_id) : nil

        collections.each do |collection_item|
          email = collection_item[:email] || collection_item["email"]
          next if email.blank?

          entities = {}
          entities[:User] = @current_user
          entities[:Job] = job if job.present?

          if collection_item[:reference_type] == "Candidate"
            entities[:Candidate] = Candidate.find_by(id: collection_item[:reference_id], account_id: @current_user.account_id)
          end
          if collection_item[:reference_type] == "SourcedProfile"
            entities[:SourcedProfile] = SourcedProfile.find_by(id: collection_item[:reference_id], account_id: @current_user.account_id)
          end

          processed_subject = EmailTemplate.replace_tags(subject, entities)
          processed_content = EmailTemplate.replace_tags(content, entities)
          unified_content = build_unified_invite_html(
            send_params: send_params,
            collection_item: collection_item,
            entities: entities,
            original_content: processed_content
          )
          processed_content = unified_content.presence || processed_content
          processed_content = wrap_plain_text_in_html(processed_content) unless html_content?(processed_content)

          unique_recipient_id = compute_numeric_id("#{dispatch.id}:#{email}")
          message = DispatchMessage.create!(
            account_id: @current_user.account_id,
            dispatch_id: dispatch.id,
            recipient_type: "ExternalEmail",
            recipient_id: unique_recipient_id,
            recipient_address: email,
            status: :pending,
            subject: processed_subject,
            body: processed_content
          )
          message_ids << message.id

          if send_params[:job_id].present? && send_params[:selective_process_id].present?
            candidate_id = collection_item[:reference_id] if collection_item[:reference_type] == "Candidate"
            candidate_id = entities[:SourcedProfile].candidate_id if collection_item[:reference_type] == "SourcedProfile"
            if candidate_id.present?
              apply = Apply.find_or_create_apply(
                candidate_id: candidate_id,
                job_id: send_params[:job_id],
                account_id: @current_user.account_id,
                selective_process_id: send_params[:selective_process_id],
                user_id: @current_user.id
              )
              applies_created += 1 if apply&.persisted?
            end
          end
        end

        job_options = {
          "save_to_sent" => true,
          "reply_to" => nil
        }
        message_ids.each do |message_id|
          MsGraphEmailWorker.perform_async(message_id, @current_user.id, job_options)
        end

        render json: {
          ok: true,
          dispatch_id: dispatch.id,
          recipients_count: message_ids.size,
          applies_created: applies_created
        }, status: :accepted
      rescue => error
        Rails.logger.error("Email template send error: #{error.class} #{error.message}")
        Rails.logger.error(error.backtrace&.first(10)&.join("\n"))
        render json: { error: "Falha ao enviar emails" }, status: :unprocessable_entity
      end

      private

      def build_render_record(context_params)
        record = { user: @current_user }
        record[:candidate] = Candidate.find_by(id: context_params[:candidate_id], account_id: @current_user.account_id) if context_params[:candidate_id].present?
        record[:job] = Job.find_by(id: context_params[:job_id], account_id: @current_user.account_id) if context_params[:job_id].present?
        record
      end

      def set_email_template
        @email_template = EmailTemplate.where(account_id: @current_user.account_id).find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Email Template")
      end

      def email_template_params
        params.require(:email_template).permit(
          :name,
          :subject,
          :content,
          :category_id,
          :is_automated,
          :delay_hours,
          :response_deadline_days,
          :trigger_event
        )
      end

      def send_email_params
        params.permit(
          :template_id,
          :subject,
          :content,
          :job_id,
          :selective_process_id,
          :interview_session_id,
          :channel,
          collections: [ :reference_type, :reference_id, :email ]
        )
      end


      def compute_numeric_id(string)
        max_signed_63 = (1 << 63) - 1
        Digest::SHA256.hexdigest(string)[0, 16].to_i(16) & max_signed_63
      end

      def html_content?(content)
        content.to_s.match?(/<(html|body|div|table|p|br\s*\/?)[\s>]/i)
      end

      def build_unified_invite_html(send_params:, collection_item:, entities:, original_content:)
        evaluation_candidate = resolve_evaluation_candidate(send_params, collection_item, entities)
        return nil unless evaluation_candidate

        interview_session = resolve_interview_session(send_params, evaluation_candidate, original_content)
        channels = resolve_invite_channels(send_params, evaluation_candidate, interview_session, original_content)
        return nil if channels.empty?

        interview_sessions = resolve_all_interview_sessions(evaluation_candidate, channels, interview_session)

        service = Evaluations::UnifiedInviteService.new(
          evaluation_candidate: evaluation_candidate,
          user: @current_user,
          channels: channels,
          interview_sessions: interview_sessions
        )
        service.render_body
      rescue StandardError => e
        Rails.logger.error("Email template unified render error: #{e.class} #{e.message}")
        nil
      end

      def resolve_evaluation_candidate(send_params, collection_item, entities)
        candidate_id = extract_candidate_id(collection_item, entities)
        return nil unless candidate_id

        scope = EvaluationCandidate.where(account_id: @current_user.account_id, candidate_id: candidate_id)
        scope = scope.where(job_id: send_params[:job_id]) if send_params[:job_id].present?
        scope.order(created_at: :desc).first
      end

      def extract_candidate_id(collection_item, entities)
        return entities[:Candidate]&.id if entities[:Candidate].present?
        return entities[:SourcedProfile]&.candidate_id if entities[:SourcedProfile].present?

        reference_type = collection_item[:reference_type] || collection_item["reference_type"]
        reference_id = collection_item[:reference_id] || collection_item["reference_id"]
        return reference_id if reference_type == "Candidate"

        if reference_type == "SourcedProfile"
          sourced_profile = SourcedProfile.find_by(id: reference_id, account_id: @current_user.account_id)
          return sourced_profile&.candidate_id
        end

        nil
      end

      def resolve_interview_session(send_params, evaluation_candidate, content)
        if send_params[:interview_session_id].present?
          return InterviewSession.find_by(id: send_params[:interview_session_id], account_id: @current_user.account_id)
        end

        if evaluation_candidate.interview_session_id.present?
          session = InterviewSession.find_by(id: evaluation_candidate.interview_session_id, account_id: @current_user.account_id)
          return session if session
        end

        session_scope = InterviewSession.where(account_id: @current_user.account_id, candidate_id: evaluation_candidate.candidate_id)
        session_scope = session_scope.where(job_id: evaluation_candidate.job_id) if evaluation_candidate.job_id.present?

        hint_channel = normalize_channel_hint(send_params[:channel])
        session_scope = session_scope.where(interview_type: "phone") if hint_channel == :phone
        session_scope = session_scope.where(interview_type: %w[voice video]) if hint_channel == :voice
        session_scope = session_scope.where(status: %w[pending active]) if content.to_s.include?("/interviews/")

        session_scope.order(created_at: :desc).first
      end

      def resolve_invite_channels(send_params, evaluation_candidate, interview_session, content)
        channels = Array(evaluation_candidate.evaluation&.notification_channels).map(&:to_sym)
        hint_channel = normalize_channel_hint(send_params[:channel])
        channels << hint_channel if hint_channel

        if interview_session.present?
          channels << (interview_session.interview_type == "phone" ? :phone : :voice)
        end

        channels << :voice if content.to_s.include?("/interviews/") && channels.exclude?(:phone)
        channels << :internal if content.to_s.match?(/chat|conversa/i)
        channels << :internal if channels.empty? && evaluation_candidate.get_evaluation_candidate_url.present?
        channels.uniq
      end

      def resolve_all_interview_sessions(evaluation_candidate, channels, primary_session)
        voice_phone = channels.select { |c| c.in?([ :voice, :phone ]) }
        return {} if voice_phone.empty?

        sessions = {}
        if primary_session
          key = primary_session.interview_type&.to_sym || :voice
          sessions[key] = primary_session
        end

        voice_phone.each do |channel|
          next if sessions[channel]

          session = InterviewSession.accessible.where(
            account_id: @current_user.account_id,
            evaluation_candidate_id: evaluation_candidate.id,
            interview_type: channel.to_s
          ).order(created_at: :desc).first

          sessions[channel] = session if session
        end
        sessions
      end

      def normalize_channel_hint(channel)
        return nil if channel.blank?

        value = channel.to_s.downcase
        return :internal if %w[internal chat webchat].include?(value)
        return :voice if %w[voice video].include?(value)
        return :phone if %w[phone call ligacao].include?(value)

        nil
      end

      def wrap_plain_text_in_html(text)
        escaped = ERB::Util.html_escape(text)
        body_html = escaped.gsub("\n", "<br>")
        footer_html = ApplicationController.renderer.render(
          partial: "shared/mailer/email_footer",
          locals: { front_url: ENV.fetch("FRONT_URL", "http://localhost:3000") }
        )
        <<~HTML
          <!DOCTYPE html>
          <html lang="pt-BR">
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
          </head>
          <body style="margin: 0; padding: 0; background-color: #f9fafb; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f9fafb;">
              <tr>
                <td align="center" style="padding: 32px 16px;">
                  <table role="presentation" cellpadding="0" cellspacing="0" width="560" style="max-width: 560px; width: 100%;">
                    <tr>
                      <td style="background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden;">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                          <tr>
                            <td style="padding: 28px 32px; font-size: 14px; line-height: 1.7; color: #374151;">
                              #{body_html}
                            </td>
                          </tr>
                        </table>
                        #{footer_html}
                      </td>
                    </tr>
                    <tr>
                      <td align="center" style="padding: 20px 16px 0;">
                        <p style="margin: 0; font-size: 11px; color: #d1d5db; line-height: 1.5;">
                          Este e um email automatico, por favor nao responda.
                        </p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </body>
          </html>
        HTML
      end

      def send_interview_via_unified_template(send_params)
        session = InterviewSession.find_by(id: send_params[:interview_session_id], account_id: @current_user.account_id)
        return render_not_found("InterviewSession") unless session

        evaluation_candidate = session.evaluation_candidate
        return render_simple_error("EvaluationCandidate not found for session", status: :unprocessable_entity) unless evaluation_candidate

        evaluation = session.evaluation
        stored = Array(evaluation&.notification_channels).map(&:to_sym)
        interview_channel = session.interview_type == "phone" ? :phone : :voice
        channels = stored.any? ? (stored | [ interview_channel ]) : [ interview_channel ]

        interview_sessions = resolve_all_interview_sessions(evaluation_candidate, channels, session)

        result = Evaluations::UnifiedInviteService.new(
          evaluation_candidate: evaluation_candidate,
          user: @current_user,
          channels: channels,
          interview_sessions: interview_sessions
        ).call

        if result[:success]
          render json: { ok: true, recipients_count: 1 }, status: :accepted
        else
          render json: { error: result[:error] }, status: :unprocessable_entity
        end
      end
    end
  end
end
