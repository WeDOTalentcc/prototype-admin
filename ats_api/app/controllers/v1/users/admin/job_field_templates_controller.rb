# frozen_string_literal: true

module V1
  module Users
    module Admin
      class JobFieldTemplatesController < Admin::ApplicationController
        before_action :set_job_field_template, only: [ :show, :update, :destroy ]

        def index
          params[:where] ||= {}
          params[:where][:account_id] = @current_user.account_id
          params[:order] ||= { is_default: "desc", created_at: "desc" }

          perform_search(
            model: JobFieldTemplate,
            serializer: JobFieldTemplateSerializer
          )
        end

        def show
          render_success(@template, serializer: JobFieldTemplateSerializer)
        end

        def create
          @template = JobFieldTemplate.new(template_params.merge(account_id: @current_user.account_id))

          if @template.save
            return render_success(@template, serializer: JobFieldTemplateSerializer, status: :created)
          end

          render_error(@template, status: :unprocessable_entity)
        end

        def update
          if @template.update(template_params)
            return render_success(@template, serializer: JobFieldTemplateSerializer)
          end

          render_error(@template, status: :unprocessable_entity)
        end

        def destroy
          @template.destroy
          render_success(@template, serializer: JobFieldTemplateSerializer)
        end

        def default_fields
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
          params.require(:job_field_template).permit(:name, :is_default, fields: [])
        end
      end
    end
  end
end
