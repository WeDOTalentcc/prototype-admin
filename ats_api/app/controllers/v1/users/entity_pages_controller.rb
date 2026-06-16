# frozen_string_literal: true

module V1
  module Users
    class EntityPagesController < ApplicationController
      before_action :set_entity_page, only: %i[show update destroy]

      def index
        entity_pages = EntityPage.for_user(@current_user.id)
        render_success(entity_pages, serializer: EntityPageSerializer)
      end

      def show
        render_success(@entity_page, serializer: EntityPageSerializer)
      end

      def create
        entity_page = EntityPage.upsert_page(@current_user, entity_page_params)
        return render_error(entity_page) unless entity_page.persisted?

        render_success(entity_page, serializer: EntityPageSerializer, status: :created)
      end

      def update
        return render_error(@entity_page) unless @entity_page.update(entity_page_params)

        render_success(@entity_page, serializer: EntityPageSerializer)
      end

      def destroy
        @entity_page.destroy
        head :no_content
      end

      def destroy_all
        EntityPage.where(user_id: @current_user.id).delete_all
        head :no_content
      end

      private

      def set_entity_page
        @entity_page = EntityPage.find_by(id: params[:id], user_id: @current_user.id, account_id: @current_user.account_id)
        render_not_found("EntityPage") unless @entity_page
      end

      def entity_page_params
        permitted = params.require(:entity_page).permit(
          :entity, :type_view, :link, :custom_entity, :job_id, :label, :icon
        )
        permitted[:pages] = sanitize_pages(params[:entity_page][:pages]) if params[:entity_page].key?(:pages)
        permitted
      end

      def sanitize_pages(value)
        return value if value.nil? || value.is_a?(Hash)
        return value.to_unsafe_h if value.is_a?(ActionController::Parameters)

        value
      end
    end
  end
end
