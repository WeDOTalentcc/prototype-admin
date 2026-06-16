module V1
  module Users
    class JobJourneysController < ApplicationController
      before_action :set_job_journey, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id if params[:where][:account_id].nil?
        params[:where][:job_id] = nil unless params[:where][:job_id].present?
        perform_search(
          model: JobJourney,
          serializer: JobJourneySerializer
        )
      end

      def show
        render_success(@job_journey, serializer: JobJourneySerializer)
      end

      def create
        @job_journey = JobJourney.new(job_journey_params.merge(
          account_id: @current_user.account_id
        ))

        if @job_journey.save
          return render_success(@job_journey, serializer: JobJourneySerializer, status: :created)
        end
        render_error(@job_journey, status: :unprocessable_entity)
      end

      def update
        @job_journey.update(job_journey_params) ? render_success(@job_journey, serializer: JobJourneySerializer) : render_error(@job_journey)
      end

      def update_positions
        journeys_params = params.require(:job_journeys)
        journeys_params.each do |journey_param|
          job_journey = JobJourney.find_by(id: journey_param[:id], account_id: @current_user.account_id)
          next unless job_journey
          job_journey.update(position: journey_param[:position])
        end
        render json: { message: "Posição atualizada com sucesso!" }, status: :ok
      end

      def destroy
        @job_journey.destroy
        head :no_content
      end

      private

      def set_job_journey
        @job_journey = JobJourney.find_by(id: params[:id], account_id: @current_user.account_id)
        render_not_found("JobJourney") unless @job_journey
      end

      def ensure_owner
        return if @job_journey.account_id == @current_user.account_id
        render_simple_error("Não autorizado a realizar esta ação nesta jornada", status: :forbidden)
      end

      def job_journey_params
        params.require(:job_journey).permit(:name, :description, :position, :active, :required, :job_id)
      end
    end
  end
end
