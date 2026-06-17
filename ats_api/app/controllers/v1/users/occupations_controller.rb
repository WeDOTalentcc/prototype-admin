module V1
  module Users
    class OccupationsController < ApplicationController
      before_action :set_occupation, only: [ :show, :update, :destroy ]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: Occupation,
          serializer: OccupationSerializer
        )
      end

      def show
        render_success(@occupation, serializer: OccupationSerializer)
      end

      def create
        @occupation = Occupation.new(occupation_params.merge(
          account_id: @current_user.account_id,
          user_id: @current_user.id
        ))

        if @occupation.save
          render_success(@occupation, serializer: OccupationSerializer, status: :created)
        else
          render_error(@occupation, status: :unprocessable_entity)
        end
      end

      def update
        if @occupation.update(occupation_params)
          render_success(@occupation, serializer: OccupationSerializer)
        else
          render_error(@occupation)
        end
      end

      def destroy
        @occupation.update(is_deleted: true)
        if @occupation.save
          render_success(@occupation, serializer: OccupationSerializer)
        else
          render_error(@occupation)
        end
      end

      private

      def set_occupation
        @occupation = Occupation.find_by(id: params[:id])
        render_not_found("Occupation") unless @occupation
      end

      def occupation_params
        params.require(:occupation).permit(:name, :description, :user_id, :account_id)
      end
    end
  end
end
