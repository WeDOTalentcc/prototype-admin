# frozen_string_literal: true

module V1
  module Evaluations
    class BaseController < ApplicationController
      skip_before_action :authorize_request

      def show
        ec = EvaluationCandidate.find_by(uid: params[:uid], is_deleted: false)
        return render_not_found("EvaluationCandidate") unless ec

        evaluation = ::Evaluation.find_by(id: ec.evaluation_id)
        return render_not_found("Evaluation") unless evaluation

        render_success(evaluation, serializer: EvaluationSerializer)
      end
    end
  end
end
