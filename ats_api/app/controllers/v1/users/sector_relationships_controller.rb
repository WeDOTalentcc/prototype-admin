# frozen_string_literal: true

module V1
  module Users
    class SectorRelationshipsController < ApplicationController
      before_action :set_sector_relationship, only: [ :show, :update, :destroy ]

      def index
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id
        params[:where][:is_deleted] = false unless params[:where].key?(:is_deleted)

        perform_search(
          model: SectorRelationship,
          serializer: SectorRelationshipSerializer
        )
      end

      def show
        render_success(@sector_relationship, serializer: SectorRelationshipSerializer)
      end

      def create
        @sector_relationship = SectorRelationship.new(sector_relationship_params)
        @sector_relationship.account_id = @current_user.account_id

        if @sector_relationship.save
          render_success(
            @sector_relationship,
            serializer: SectorRelationshipSerializer,
            status: :created
          )
        else
          render_error(
            @sector_relationship.errors.full_messages.join(", "),
            status: :unprocessable_entity
          )
        end
      end

      def update
        if @sector_relationship.update(sector_relationship_params)
          render_success(@sector_relationship, serializer: SectorRelationshipSerializer)
        else
          render_error(
            @sector_relationship.errors.full_messages.join(", "),
            status: :unprocessable_entity
          )
        end
      end

      def destroy
        @sector_relationship.update(is_deleted: true)
        render_success(@sector_relationship, serializer: SectorRelationshipSerializer)
      end

      private

      def set_sector_relationship
        @sector_relationship = SectorRelationship
          .where(account_id: @current_user.account_id)
          .find(params[:id])
      end

      def sector_relationship_params
        params.require(:sector_relationship).permit(
          :sector_id,
          :sector_name,
          :reference_type,
          :reference_id,
          :is_deleted,
        )
      end
    end
  end
end
