# frozen_string_literal: true

module V1
  module Users
    module Scheduling
      class LinksController < ApplicationController
        wrap_parameters :scheduling_link
        before_action :set_link, only: %i[show update destroy]

        def index
          service = ::Scheduling::LinkService.new(user: @current_user)
          links = service.list(filter_params)
          render_success(links, serializer: SchedulingLinkSerializer)
        end

        def show
          render_success(@link, serializer: SchedulingLinkSerializer)
        end

        def create
          service = ::Scheduling::LinkService.new(user: @current_user)
          result = service.create(link_params)

          if result.success?
            render_success(result.data, serializer: SchedulingLinkSerializer, status: :created)
          else
            render json: { errors: result.errors }, status: :unprocessable_entity
          end
        end

        def update
          service = ::Scheduling::LinkService.new(user: @current_user)
          result = service.update(@link, link_params)

          if result.success?
            render_success(result.data, serializer: SchedulingLinkSerializer)
          else
            render json: { errors: result.errors }, status: :unprocessable_entity
          end
        end

        def destroy
          service = ::Scheduling::LinkService.new(user: @current_user)
          result = service.cancel(@link)

          if result.success?
            render_success(result.data, serializer: SchedulingLinkSerializer)
          else
            render json: { errors: result.errors }, status: :unprocessable_entity
          end
        end

        private

        def set_link
          @link = SchedulingLink.find_by!(id: params[:id], account_id: @current_user.account_id)
        rescue ActiveRecord::RecordNotFound
          render_not_found("SchedulingLink")
        end

        def link_params
          params.require(:scheduling_link).permit(
            :duration_minutes, :interview_type, :platform, :location,
            :subject, :message, :expires_at, :apply_id, :candidate_id, :job_id,
            slots: %i[start_time end_time],
            channels: []
          )
        end

        def filter_params
          params.permit(:status, :job_id, :apply_id)
        end
      end
    end
  end
end
