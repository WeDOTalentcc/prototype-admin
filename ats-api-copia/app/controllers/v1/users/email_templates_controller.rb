# frozen_string_literal: true

module V1
  module Users
    class EmailTemplatesController < ApplicationController
      before_action :authorize_request
      before_action :require_manager!, only: %i[create update destroy]
      before_action :set_email_template, only: %i[show update destroy]

      def index
        perform_search(
          model: EmailTemplate,
          serializer: EmailTemplateSerializer
        )
      end

      def show
        render_success(@email_template, serializer: EmailTemplateSerializer)
      end

      def create
        @email_template = EmailTemplate.new(email_template_params.merge(account_id: @current_user.account_id))

        if @email_template.save
          return render_success(@email_template, serializer: EmailTemplateSerializer, status: :created)
        end
        render_error(@email_template, status: :unprocessable_entity)
      end

      def update
        @email_template.update(email_template_params) ? render_success(@email_template, serializer: EmailTemplateSerializer) : render_error(@email_template)
      end

      def destroy
        @email_template.destroy
        render_no_content
      end

      private

      def set_email_template
        @email_template = EmailTemplate.find_by(id: params[:id])
        render_not_found("EmailTemplate") unless @email_template
      end

      def email_template_params
        params.require(:email_template).permit(
          :company_id, :name, :subject, :body_html, :body_text, :category,
          :channel, :trigger_type, :variables, :language, :is_active,
          :is_system_template, :visibility
        )
      end
    end
  end
end
