# frozen_string_literal: true

module V1
  module Users
    class LanguagesController < ApplicationController
      include ResourceLoader

      def index
        authorize Language
        perform_search(
          model: Language,
          serializer: LanguageSerializer
        )
      end

      def show
        render_success(@language, serializer: LanguageSerializer)
      end

      def create
        authorize Language
        @language = Language.new(language_params)
        @language.save ? render_success(@language, serializer: LanguageSerializer, status: :created) : render_error(@language)
      end

      def update
        authorize @language
        @language.update(language_params) ? render_success(@language, serializer: LanguageSerializer) : render_error(@language)
      end

      def destroy
        authorize @language
        @language.destroy
        render_success(@language, serializer: LanguageSerializer)
      end

      private

      def language_params
        params.require(:language).permit(:name, :acronym, :name_ptbr)
      end
    end
  end
end
