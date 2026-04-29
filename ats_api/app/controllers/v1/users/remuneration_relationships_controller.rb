module V1
  module Users
    class RemunerationRelationshipsController < ApplicationController
      before_action :set_remuneration_relationship, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        perform_search(
          model: RemunerationRelationship,
          serializer: RemunerationRelationshipSerializer
        )
      end

      def show
        render_success(@remuneration_relationship, serializer: RemunerationRelationshipSerializer)
      end

      def create
        remuneration = build_remuneration_relationship
        return render_error(remuneration, status: :unprocessable_entity) unless remuneration.save

        render_success(remuneration, serializer: RemunerationRelationshipSerializer, status: :created)
      end

      def bulk_upsert
        return render_validation_error unless valid_bulk_params?

        service = RemunerationRelationships::BulkUpsertService.new(
          relationships_params: params[:remuneration_relationships],
          current_user: @current_user
        )

        result = service.call

        return render_bulk_error(result[:errors]) if result[:errors].any?

        render_bulk_success(result)
      end

      def update
        return render_error(@remuneration_relationship) unless @remuneration_relationship.update(remuneration_relationship_params)

        render_success(@remuneration_relationship, serializer: RemunerationRelationshipSerializer)
      end

      def destroy
        @remuneration_relationship.update(is_deleted: true)
        render_success(@remuneration_relationship, serializer: RemunerationRelationshipSerializer)
      end

      def get_currencies
        currencies = ::RemunerationRelationship::CURRENCY_LIST.map { |c| OpenStruct.new(c) }
        render_success(currencies, serializer: CurrencySerializer)
      end

      def get_contract_types
        contract_types = ::RemunerationRelationship::CONTRACT_TYPE_LIST.map { |c| OpenStruct.new(c) }
        render_success(contract_types, serializer: ContractTypeSerializer)
      end

      private

      def build_remuneration_relationship
        RemunerationRelationship.new(
          remuneration_relationship_params.merge(
            account_id: @current_user.account_id,
            user_id: @current_user.id
          )
        )
      end

      def valid_bulk_params?
        params[:remuneration_relationships].is_a?(Array) && params[:remuneration_relationships].any?
      end

      def render_validation_error
        message = params[:remuneration_relationships].is_a?(Array) ?
          "É necessário enviar ao menos uma remuneração" :
          "Parâmetro 'remuneration_relationships' é obrigatório"

        render_simple_error(message, status: :unprocessable_entity)
      end

      def render_bulk_error(errors)
        render json: {
          success: false,
          message: "Erro ao processar remunerações",
          errors: errors
        }, status: :unprocessable_entity
      end

      def render_bulk_success(result)
        render json: {
          success: true,
          message: "Remunerações processadas com sucesso",
          data: {
            created: result[:created].size,
            updated: result[:updated].size,
            total: result[:total],
            relationships: serialize_relationships(result[:created] + result[:updated])
          }
        }, status: :ok
      end

      def serialize_relationships(relationships)
        relationships.map { |r| RemunerationRelationshipSerializer.new(r).as_json }
      end

      def set_remuneration_relationship
        @remuneration_relationship = RemunerationRelationship.find_by(id: params[:id])
        return if @remuneration_relationship

        render_not_found("RemunerationRelationship")
      end

      def ensure_owner
        return if @remuneration_relationship.account_id == @current_user.account_id

        render_simple_error("Não autorizado a realizar esta ação nesta remuneração relationship", status: :forbidden)
      end

      def remuneration_relationship_params
        params.require(:remuneration_relationship).permit(
          :remuneration_id, :account_id, :user_id,
          :reference_type, :reference_id, :is_deleted,
          :currency, :period, :comments, :value, :amount,
          contract_type: []
        )
      end
    end
  end
end
