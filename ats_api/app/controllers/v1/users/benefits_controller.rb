# frozen_string_literal: true

module V1
  module Users
    class BenefitsController < ApplicationController
      include ResourceLoader

      def index
        authorize Benefit
        perform_search(
          model: Benefit,
          serializer: BenefitSerializer
        )
      end

      def show
        render_success(@benefit, serializer: BenefitSerializer)
      end

      def create
        authorize Benefit
        @benefit = Benefit.new(benefit_params)
        if @benefit.save
          render_success(@benefit, serializer: BenefitSerializer, status: :created)
        else
          render_error(@benefit)
        end
      end

      def update
        authorize @benefit
        if @benefit.update(benefit_params)
          render_success(@benefit, serializer: BenefitSerializer)
        else
          render_error(@benefit)
        end
      end

      def destroy
        authorize @benefit
        @benefit.destroy
        render_success(@benefit, serializer: BenefitSerializer)
      end

      def grouped_by_category
        authorize Benefit
        benefits = Benefit.where(is_deleted: [ false, nil ]).order(:name)
        grouped = benefits.group_by(&:category).transform_values do |items|
          items.map { |b| BenefitSerializer.new(b).serializable_hash[:data][:attributes] }
        end
        render json: { data: grouped }
      end

      private

      def benefit_params
        params.require(:benefit).permit(:name, :category, :is_deleted, :is_possible_extend_to_dependents, :is_per_day, :days_of_month, :enable_value_editing, types: [])
      end
    end
  end
end
