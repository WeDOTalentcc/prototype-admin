module V1
  module Users
    class GendersController < ApplicationController
      def index
        genders = Candidate::GENDER.map { |gender| OpenStruct.new(gender) }
        render_success(genders, serializer: GenderSerializer)
      end
    end
  end
end
