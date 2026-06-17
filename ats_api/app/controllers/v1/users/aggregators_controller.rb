# frozen_string_literal: true

module V1
  module Users
    class AggregatorsController < ApplicationController
      def index
        entity_class = get_entity_class_from_param
        return render_entity_not_found unless entity_class

        search_params = build_search_params
        results = entity_class.search_default(
          "*",
          search_params.merge(per_page: 0, force_aggregators: true),
          1,
          false,
          false,
          true
        )

        aggregators = process_aggregators(results[:aggs], entity_class)
        render json: {
          entity: params[:entity],
          aggregators: aggregators
        }
      end

      private

      def process_aggregators(aggs, entity_class)
        return aggs unless aggs.is_a?(Hash)

        if entity_class.name == "Candidate"
          Candidates::FacetPostProcessor.call(aggs, @current_user)
        else
          aggs
        end
      end

      def build_search_params
        if request.post?
          params.permit(
            where: {},
            filter: {},
            order: {},
            aggs: {}
          ).to_h.symbolize_keys
        else
          global_search_params
        end
      end

      def get_entity_class_from_param
        entity_name = params[:entity]
        return nil unless entity_name.present?

        class_name = entity_name.singularize.camelize

        klass = class_name.safe_constantize
        return nil unless klass && klass < ApplicationRecord && klass.ancestors.include?(Searchable)

        klass
      end

      def render_entity_not_found
        render json: {
          error: "Entity '#{params[:entity]}' not found or not searchable"
        }, status: :not_found
      end
    end
  end
end
