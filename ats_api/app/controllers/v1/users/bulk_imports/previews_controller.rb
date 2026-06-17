require "csv"

module V1
  module Users
    module BulkImports
      class PreviewsController < ApplicationController
        ALLOWED_ENTITIES = %w[candidates jobs applies].freeze

        before_action :validate_entity_type

        def create
          data_file = DataFile.find(preview_params[:data_file_id])
          return render_error("Arquivo não encontrado.", :not_found) unless data_file.file.attached?

          file_headers = extract_headers_from(data_file)
          target_fields = target_fields_service.call

          suggested_mapping = RecruitAgentService.map_csv_headers(
            csv_headers: file_headers,
            target_fields: target_fields,
            entity_name: params[:entity_type].singularize
          )

          render json: {
            data_file_id: data_file.id,
            csv_headers: file_headers,
            target_fields: target_fields,
            suggested_mapping: suggested_mapping
          }, status: :ok
        end

        private

        def preview_params
          params.require(:preview).permit(:data_file_id)
        end

        def extract_headers_from(data_file)
          data_file.file.open do |file|
            CSV.read(file.path, headers: true, encoding: "bom|utf-8").headers
          end
        end

        def render_error(message, status)
          render json: { errors: [ { title: message } ] }, status: status
        end

        def target_fields_service
          service_class_name = "BulkImports::#{params[:entity_type].camelize}Service"
          service_class_name.constantize
        end

        def validate_entity_type
          return if ALLOWED_ENTITIES.include?(params[:entity_type])

          render_error("Tipo de importação '#{params[:entity_type]}' não é válido.", :bad_request)
        end
      end
    end
  end
end
