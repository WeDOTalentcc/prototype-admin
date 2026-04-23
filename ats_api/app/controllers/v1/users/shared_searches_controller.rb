# frozen_string_literal: true

module V1
  module Users
    class SharedSearchesController < ApplicationController
      include ResourceLoader

      before_action :set_resource, only: %i[resend]

      def index
        perform_search(
          model: SharedSearch,
          serializer: SharedSearchSerializer,
          search_with_pin: search_with_pin.merge(
            where: {
              user_id: @current_user.id,
              account_id: @current_user.account_id,
              is_deleted: false
            }
          )
        )
      end

      def show
        render_success(@shared_search, serializer: SharedSearchSerializer)
      end

      def create
        @shared_search = build_shared_search

        if @shared_search.save
          SharedSearches::DispatchNotificationService.call(@shared_search)
          return render_success(@shared_search, serializer: SharedSearchSerializer, status: :created)
        end

        render_error(@shared_search, status: :unprocessable_entity)
      end

      def update
        return render_success(@shared_search, serializer: SharedSearchSerializer) if @shared_search.update(shared_search_params)

        render_error(@shared_search, status: :unprocessable_entity)
      end

      def destroy
        @shared_search.update(is_deleted: true)
        render_no_content
      end

      def resend
        emails = Array(params[:emails]).compact.reject(&:blank?)
        return render json: { error: "emails é obrigatório" }, status: :unprocessable_entity if emails.empty?

        @shared_search.add_emails(emails)
        SharedSearches::DispatchNotificationService.call(@shared_search, emails: emails)

        render json: { success: true, dispatched_to: emails }
      end

      private

      def build_shared_search
        SharedSearch.new(shared_search_params.merge(
          user_id: @current_user.id,
          account_id: @current_user.account_id
        ))
      end

      def shared_search_params
        params
          .require(:shared_search)
          .permit(:title, :description, :query, :expires_at,
                  candidate_ids: [], shared_with_emails: [])
      end
    end
  end
end
