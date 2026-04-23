# frozen_string_literal: true

module V1
  module Users
    class BenefitRelationshipsController < ApplicationController
      include ResourceLoader

      def index
        authorize BenefitRelationship
        perform_search(
          model: BenefitRelationship,
          serializer: BenefitRelationshipSerializer
        )
      end

      def show
        render_success(@benefit_relationship, serializer: BenefitRelationshipSerializer)
      end

      def create
        authorize BenefitRelationship
        ActiveRecord::Base.transaction do
          benefit = process_benefit
          return if benefit == false

          relationship_params = benefit_relationship_params.except(:benefit_attributes)
          relationship_params[:benefit_id] = benefit.id if benefit.present? && benefit.persisted?

          @benefit_relationship = BenefitRelationship.new(relationship_params)

          if @benefit_relationship.save
            render_success(@benefit_relationship, serializer: BenefitRelationshipSerializer, status: :created)
          else
            render_error(@benefit_relationship)
            raise ActiveRecord::Rollback
          end
        end
      end

      def update
        authorize @benefit_relationship
        ActiveRecord::Base.transaction do
          benefit = process_benefit

          return if benefit == false

          relationship_params = benefit_relationship_params.except(:benefit_attributes)
          relationship_params[:benefit_id] = benefit.id if benefit.present? && benefit.persisted?

          if @benefit_relationship.update(relationship_params)
            render_success(@benefit_relationship, serializer: BenefitRelationshipSerializer)
          else
            render_error(@benefit_relationship)
            raise ActiveRecord::Rollback
          end
        end
      end

      def destroy
        authorize @benefit_relationship
        @benefit_relationship.destroy
        render_success(@benefit_relationship, serializer: BenefitRelationshipSerializer)
      end

      def create_collection
        authorize BenefitRelationship
        return render_error("No benefit_relationships provided") unless benefit_relationship_collection_params.present?
        benefit_relationship_collection_params.each do |benefit_relationship|
          BenefitRelationship.create(benefit_relationship)
        end
      end

      def bulk_upsert
        return render_validation_error unless valid_bulk_params?

        service = BenefitRelationships::BulkUpsertService.new(
          relationships_params: params[:benefit_relationships],
          current_user: @current_user
        )

        result = service.call

        return render_bulk_error(result[:errors]) if result[:errors].any?

        render_bulk_success(result)
      end

      private

      def benefit_relationship_params
        params.require(:benefit_relationship).permit(
          :benefit_id,
          :name,
          :reference_type,
          :reference_id,
          :is_deleted,
          :is_possible_extend_to_dependents,
          :is_per_day,
          :days_of_month,
          :enable_value_editing,
          :type_description,
          :description,
          :is_company,
          :details,
          :is_extendable_to_dependents,
          :dependents_count,
          :category,
          :provider,
          :value,
          :eligibility,
          :waiting_days,
          :is_active,
          :highlight,
          :required,
          :has_discount,
          types: [],
          benefit_attributes: [
            :id,
            :name,
            :is_deleted,
            :is_possible_extend_to_dependents,
            :is_per_day,
            :days_of_month,
            :enable_value_editing,
            :category,
            types: []
          ]
        )
      end

      def benefit_relationship_collection_params
        params.require(:benefit_relationships).map do |benefit_relationship|
          benefit_relationship.permit(
            :benefit_id,
            :name,
            :reference_type,
            :reference_id,
            :is_deleted,
            :is_possible_extend_to_dependents,
            :is_per_day,
            :days_of_month,
            :enable_value_editing,
            :type_description,
            :description,
            :is_company,
            :details,
            :is_extendable_to_dependents,
            :dependents_count,
            types: []
          )
        end
      end

      def valid_bulk_params?
        params[:benefit_relationships].is_a?(Array) && params[:benefit_relationships].any?
      end

      def render_validation_error
        message = params[:benefit_relationships].is_a?(Array) ?
          "É necessário enviar ao menos um benefit_relationship" :
          "Parâmetro 'benefit_relationships' é obrigatório"

        render_simple_error(message, status: :unprocessable_entity)
      end

      def render_bulk_error(errors)
        render json: {
          success: false,
          message: "Erro ao processar benefit_relationships",
          errors: errors
        }, status: :unprocessable_entity
      end

      def render_bulk_success(result)
        render json: {
          success: true,
          message: "Benefit relationships processados com sucesso",
          data: {
            created: result[:created].size,
            updated: result[:updated].size,
            deleted: result[:deleted].size,
            total: result[:total],
            relationships: serialize_relationships(result[:created] + result[:updated] + result[:deleted])
          }
        }, status: :ok
      end

      def serialize_relationships(relationships)
        relationships.map { |r| BenefitRelationshipSerializer.new(r).as_json }
      end

      def process_benefit
        benefit_attrs = benefit_relationship_params[:benefit_attributes]

        if benefit_attrs.blank?
          benefit_id = benefit_relationship_params[:benefit_id]
          if benefit_id.present?
            begin
              return Benefit.find(benefit_id)
            rescue ActiveRecord::RecordNotFound
              render_simple_error("Benefit com id #{benefit_id} não encontrado", status: :not_found)
              return false
            end
          end
          return nil
        end

        if benefit_attrs[:id].present?
          begin
            benefit = Benefit.find(benefit_attrs[:id])
            authorize benefit, :update?

            if benefit.update(benefit_attrs.except(:id))
              benefit
            else
              render_error(benefit)
              false
            end
          rescue ActiveRecord::RecordNotFound
            render_simple_error("Benefit com id #{benefit_attrs[:id]} não encontrado", status: :not_found)
            false
          end
        else
          authorize Benefit, :create?
          benefit = Benefit.new(benefit_attrs)

          if benefit.save
            benefit
          else
            render_error(benefit)
            false
          end
        end
      end
    end
  end
end
