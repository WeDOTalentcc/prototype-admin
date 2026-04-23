module V1
  module Users
    class OrganizationalPositionsController < ApplicationController
      before_action :set_position, only: %i[show update destroy reporting_chain direct_reports]

      def index
        enforce_limit!
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        params[:where][:is_active] = true unless params[:where].key?(:is_active)

        perform_search(
          model: OrganizationalPosition,
          serializer: OrganizationalPositionSerializer,
          include_aggregators: true
        )
      end

      def show
        render_success(@position, serializer: OrganizationalPositionSerializer)
      end

      def create
        position = OrganizationalPosition.new(position_params)
        position.account_id = @current_user.account_id

        if position.save
          render_success(position, serializer: OrganizationalPositionSerializer, status: :created)
        else
          render_error(position)
        end
      end

      def update
        if @position.update(position_params)
          render_success(@position, serializer: OrganizationalPositionSerializer)
        else
          render_error(@position)
        end
      end

      def destroy
        @position.update(is_active: false)
        render_success(@position, serializer: OrganizationalPositionSerializer)
      end

      def reporting_chain
        render json: {
          reporting_chain: @position.reporting_chain.map do |position|
            {
              id: position.id,
              title: position.title,
              current_holder: position.current_user&.name
            }
          end
        }
      end

      def direct_reports
        reports = @position.direct_reports.includes(:department)
        render json: {
          direct_reports: reports.map do |position|
            {
              id: position.id,
              title: position.title,
              department: position.department.name,
              is_active: position.is_active
            }
          end
        }
      end

      private

      def position_params
        params.require(:organizational_position).permit(
          :title,
          :description,
          :department_id,
          :reports_to_id,
          :level,
          :position_type,
          :is_active
        )
      end

      def set_position
        @position = OrganizationalPosition.where(account_id: @current_user.account_id).find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Posição")
      end

      def enforce_limit!(max = 100)
        limit_value = params[:limit].presence || params[:per_page].presence
        limit_value = limit_value.to_i if limit_value
        limit_value = max if limit_value.blank? || limit_value <= 0 || limit_value > max
        params[:limit] = limit_value
      end
    end
  end
end
