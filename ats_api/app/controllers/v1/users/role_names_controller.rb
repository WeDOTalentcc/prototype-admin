# frozen_string_literal: true

module V1
  module Users
    class RoleNamesController < ApplicationController
      def index
        term = params[:term] || params[:q] || ""

        term = "" if term == "*"

        query = Candidate
          .where(account_id: @current_user.account_id)
          .where(is_deleted: [ false, nil ])
          .where.not(role_name: [ nil, "" ])
          .distinct
          .order("role_name ASC")

        if term.present?
          query = query.where("role_name ILIKE ?", "%#{term}%")
        end

        role_names = query.limit(30).pluck(:role_name).uniq

        render json: {
          data: role_names.map { |role_name|
            {
              attributes: {
                name: role_name,
                role_name: role_name
              }
            }
          }
        }, status: :ok
      end

      def suggestions
        role_names_text = params[:role_names] || params[:text] || ""

        if role_names_text.blank?
          return render json: { data: [] }, status: :ok
        end

        suggestions = Candidates::SuggestionService.suggest_role_names(role_names_text)

        render json: {
          data: suggestions
        }, status: :ok
      end
    end
  end
end
