module V1
  module Users
    class CitiesController < ApplicationController
      before_action :set_city, only: [ :show, :update, :destroy ]

      def index
        perform_search(model: City, serializer: CitySerializer)
      end

      def show
        render_success(@city, serializer: CitySerializer)
      end

      def create
        @city = City.new(city_params)
        if @city.save
          return render_success(@city, serializer: CitySerializer, status: :created)
        end
        render_error(@city, status: :unprocessable_entity)
      end

      def update
        if @city.update(city_params)
          return render_success(@city, serializer: CitySerializer)
        end
        render_error(@city, status: :unprocessable_entity)
      end

      def destroy
        @city.destroy
        render_success(@city, serializer: CitySerializer)
      end

      private

      def set_city
        @city = City.find_by(id: params[:id])
        render_not_found("City") unless @city
      end

      def city_params
        params.require(:city).permit(:name, :state_id, :country_id)
      end
    end
  end
end
