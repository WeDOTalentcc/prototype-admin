# frozen_string_literal: true

module V1
  module Users
    class JobUsersController < ApplicationController
      before_action :set_job_user, only: %i[show update destroy]

      def index
        perform_search(
          model: JobUser,
          serializer: JobUserSerializer,
          compact: params[:compact]&.split(",") || []
        )
      end

      def show
        render_success(@job_user, serializer: JobUserSerializer, serializer_params: { current_user: @current_user })
      end

      def create
        @job_user = JobUser.new(job_user_params.merge(account_id: @current_user.account_id))

        if @job_user.save
          return render_success(@job_user, serializer: JobUserSerializer, serializer_params: { current_user: @current_user }, status: :created)
        end
        render_error(@job_user, status: :unprocessable_entity)
      end

      def update
        if @job_user.update(job_user_params)
          render_success(@job_user, serializer: JobUserSerializer, serializer_params: { current_user: @current_user })
        else
          render_error(@job_user)
        end
      end

      def destroy
        @job_user.destroy
        render_success(@job_user, serializer: JobUserSerializer, serializer_params: { current_user: @current_user })
      end

      private

      def set_job_user
        @job_user = JobUser.include_base.find_by(id: params[:id])
        render_not_found("JobUser") unless @job_user
      end

      def job_user_params
        params.require(:job_user).permit(
          :user_id,
          :job_id,
          :person_function,
          :split
        )
      end
    end
  end
end
