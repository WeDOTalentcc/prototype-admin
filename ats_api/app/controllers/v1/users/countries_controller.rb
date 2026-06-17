# app/controllers/v1/users/countries_controller.rb
module V1
  module Users
    class CountriesController < ApplicationController
      def index
        perform_search(model: Country, serializer: CountrySerializer)
      end

      def show
        country = Country.find_by(id: params[:id])
        return render_not_found("Country") unless country

        render_success(country, serializer: CountrySerializer)
      end
    end
  end
end
