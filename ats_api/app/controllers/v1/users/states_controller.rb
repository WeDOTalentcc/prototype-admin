# app/controllers/v1/users/states_controller.rb
module V1
  module Users
    class StatesController < ApplicationController
      before_action :set_state, only: [ :show, :update, :destroy ]

      def index
        if params[:country_id].present?
          country = Country.find_by(id: params[:country_id])
          return render_not_found("Country") unless country

          states = country.states
          return perform_search(collection: states, serializer: StateSerializer)
        end

        perform_search(model: State, serializer: StateSerializer)
      end

      def show
        render_success(@state, serializer: StateSerializer)
      end

      def create
        @state = State.new(state_params)

        if @state.save
          return render_success(@state, serializer: StateSerializer, status: :created)
        end
        render_error(@state, status: :unprocessable_entity)
      end

      def update
        if @state.update(state_params)
          return render_success(@state, serializer: StateSerializer)
        end
        render_error(@state, status: :unprocessable_entity)
      end

      def destroy
        @state.destroy
        render_success(@state, serializer: StateSerializer)
      end

      private

      def set_state
        @state = State.find_by(id: params[:id])
        render_not_found("State") unless @state
      end

      def state_params
        params.require(:state).permit(:name, :country_id)
      end
    end
  end
end
