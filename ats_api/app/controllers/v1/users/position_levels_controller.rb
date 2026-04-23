# frozen_string_literal: true

module V1
  module Users
    class PositionLevelsController < ApplicationController
      def index
        term = params[:term] || params[:q] || ""

        term = "" if term == "*"

        query = Candidate
          .where(account_id: @current_user.account_id)
          .where(is_deleted: [ false, nil ])
          .where.not(position_level: [ nil, "" ])
          .distinct
          .order("position_level ASC")

        if term.present?
          query = query.where("position_level ILIKE ?", "%#{term}%")
        end

        position_levels = query.limit(30).pluck(:position_level).uniq

        render json: {
          data: position_levels.map { |position_level|
            {
              attributes: {
                name: position_level,
                position_level: position_level
              }
            }
          }
        }, status: :ok
      end
    end
  end
end
