# frozen_string_literal: true

module V1
  module Users
    class LanguageRelationshipsController < ApplicationController
      include ResourceLoader

      def levels
        render json: LanguageLevelSerializer.serialize(LanguageRelationship::LEVELS), status: :ok
      end

      def index
        authorize LanguageRelationship
        perform_search(
          model: LanguageRelationship,
          serializer: LanguageRelationshipSerializer
        )
      end

      def show
        render_success(@language_relationship, serializer: LanguageRelationshipSerializer)
      end

      def create
        authorize LanguageRelationship
        @language_relationship = LanguageRelationship.new(language_relationship_params)
        if @language_relationship.save
          render_success(@language_relationship, serializer: LanguageRelationshipSerializer, status: :created)
        else
          render_error(@language_relationship)
        end
      end

      def update
        authorize @language_relationship
        if @language_relationship.update(language_relationship_params)
          render_success(@language_relationship, serializer: LanguageRelationshipSerializer)
        else
          render_error(@language_relationship)
        end
      end

      def destroy
        authorize @language_relationship
        @language_relationship.destroy
        render_success(@language_relationship, serializer: LanguageRelationshipSerializer)
      end

      private

      def language_relationship_params
        params.require(:language_relationship).permit(:language_id, :reference_type, :reference_id, :min_value, :max_value, :priority, :level, :is_required)
      end
    end
  end
end
