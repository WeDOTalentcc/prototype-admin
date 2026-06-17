# frozen_string_literal: true

module V1
  module Users
    module Lia
      class ProfileAnalysesController < ApplicationController
        def by_candidate
          candidate = find_candidate
          result = ::Candidates::ProfileAnalysesService.call(
            candidate: candidate,
            account_id: @current_user.account_id
          )
          render json: result, status: :ok
        end

        private

        def find_candidate
          Candidate.find_by(id: params[:candidate_id], account_id: @current_user.account_id)
        end
      end
    end
  end
end
