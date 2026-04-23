module V1
  module Users
    module Jobs
      class OrganizationalStructuresController < ApplicationController
        before_action :set_job

        def show
          validator = OrganizationalStructureValidator.new(@job).validate
          render json: response_payload(@job.organizational_structure, validator)
        end

        def create
          process_payload(:created)
        end

        def update
          process_payload(:ok)
        end

        private

        def process_payload(success_status)
          payload = structure_params
          return render_error_message("organizational_data obrigatório") if payload.blank?

          result = OrganizationalStructureBuilderService.new(@job, payload).build
          validator = OrganizationalStructureValidator.new(@job.reload).validate

          status = result[:success] ? success_status : :unprocessable_entity
          render json: response_payload(result[:structure], validator).merge(
            success: result[:success],
            changes: result[:changes],
            errors: result[:errors],
            job_id: @job.id
          ), status: status
        end

        def structure_params
          params.require(:organizational_data).permit(
            department: %i[name parent],
            hiring_manager: %i[name title email],
            team: [
              :name,
              :size,
              :description,
              { composition: [ :role, :count, :description ] }
            ],
            reports_to: %i[position name],
            team_composition: [ :role, :count, :description ]
          ).to_h
        rescue ActionController::ParameterMissing
          {}
        end

        def set_job
          @job = Job.where(account_id: @current_user.account_id, is_deleted: false).find(params[:job_id])
        rescue ActiveRecord::RecordNotFound
          render_not_found("Job")
        end

        def response_payload(structure, validator)
          {
            structure: structure,
            complete: validator[:complete],
            suggestions: validator[:suggestions],
            warnings: validator[:warnings],
            completion_percentage: validator[:completion_percentage],
            job_id: params[:job_id]
          }
        end
      end
    end
  end
end
