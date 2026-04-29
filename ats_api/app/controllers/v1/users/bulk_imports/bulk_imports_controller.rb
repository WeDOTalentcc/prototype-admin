
module V1
  module Users
    module BulkImports
      class BulkImportsController < ApplicationController
        ALLOWED_ENTITIES = [ "candidates", "jobs", "applies" ].freeze

        before_action :validate_entity_type

        def create
          BulkImportJob.perform_later(
            entity_type: params[:entity_type],
            data_file_id: import_params[:data_file_id],
            mapping: import_params[:mapping].to_h,
            user_id: @current_user.id,
            account_id: @current_user.account_id
          )

          render json: { message: "A importação de #{params[:entity_type]} foi iniciada com sucesso." }, status: :accepted
        end

        private

        def validate_entity_type
          return if ALLOWED_ENTITIES.include?(params[:entity_type])

          render json: { error: "Tipo de importação inválido: #{params[:entity_type]}" }, status: :bad_request
        end

        def import_params
          params.require(:data).permit(:data_file_id, mapping: {})
        end
      end
    end
  end
end
