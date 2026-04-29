
module V1
  module Users
    class CandidateImportsController < ApplicationController
      def create
        data_file_ids = candidate_import_params[:data_file_ids]
        CandidateImportJob.perform_later(data_file_ids: data_file_ids, user_id: @current_user.id)
        render_success({
          message: "Importação iniciada com sucesso",
          data_files: DataFile.where(id: data_file_ids)
        }, status: :accepted)
      end

      def candidate_import_params
        params.require(:candidate_import).permit(data_file_ids: [])
      end
    end
  end
end
