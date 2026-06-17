module V1
  module Users
    class MaritalStatusesController < ApplicationController
      def index
        marital_statuses = Candidate::MARITAL_STATUS.map { |status| OpenStruct.new(status) }
        render_success(marital_statuses, serializer: MaritalStatusSerializer)
      end
    end
  end
end
