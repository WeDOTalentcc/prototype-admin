# frozen_string_literal: true

module V1
  module Users
    class JobFieldTemplatesController < ApplicationController
      before_action :set_job_field_template, only: [ :show, :update, :destroy ]

      def index
        authorize JobFieldTemplate

        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        params[:order] ||= { is_default: "desc", created_at: "desc" }

        perform_search(
          model: JobFieldTemplate,
          serializer: JobFieldTemplateSerializer
        )
      end

      def show
        authorize @template
        render_success(@template, serializer: JobFieldTemplateSerializer)
      end

      def create
        authorize JobFieldTemplate

        @template = JobFieldTemplate.new(template_params.merge(account_id: @current_user.account_id))

        if @template.save
          return render_success(@template, serializer: JobFieldTemplateSerializer, status: :created)
        end

        render_error(@template, status: :unprocessable_entity)
      end

      def update
        authorize @template

        if @template.update(template_params)
          return render_success(@template, serializer: JobFieldTemplateSerializer)
        end

        render_error(@template, status: :unprocessable_entity)
      end

      def destroy
        authorize @template

        @template.destroy
        render_success(@template, serializer: JobFieldTemplateSerializer)
      end

      def default_fields
        authorize JobFieldTemplate, :default_fields?

        render json: {
          data: {
            type: "default_fields",
            attributes: {
              fields: JobFieldTemplate.default_fields
            }
          }
        }
      end

      private

      def set_job_field_template
        @template = JobFieldTemplate.for_account(@current_user.account_id)
                                   .find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render json: { error: "Template não encontrado" }, status: :not_found
      end

      def template_params
        params.require(:job_field_template).permit(
          :name,
          :is_default,
          fields: [
            :label,
            :category,
            :priority,
            :field_name,
            :is_required,
            :job_journey_position
          ]
        )
      end
    end
  end
end
