module RemunerationRelationships
  class BulkUpsertService
    def initialize(relationships_params:, current_user:)
      @relationships_params = relationships_params
      @current_user = current_user
      @results = { created: [], updated: [], errors: [], total: 0 }
    end

    def call
      ActiveRecord::Base.transaction do
        process_relationships
        raise ActiveRecord::Rollback if @results[:errors].any?
      end

      @results
    end

    private

    attr_reader :relationships_params, :current_user, :results

    def process_relationships
      relationships_params.each_with_index do |params, index|
        result = upsert_relationship(params)

        return add_error(index, result[:errors]) unless result[:success]

        result[:created] ? results[:created] << result[:relationship] : results[:updated] << result[:relationship]
        results[:total] += 1
      end
    end

    def upsert_relationship(params)
      return validation_error unless valid_params?(params)

      existing = find_existing_relationship(params)
      existing ? update_relationship(existing, params) : create_relationship(params)
    end

    def valid_params?(params)
      return true if params[:id].present?

      params[:remuneration_id].present? &&
        params[:reference_type].present? &&
        params[:reference_id].present?
    end

    def validation_error
      {
        success: false,
        errors: "Campos obrigatórios: id OU (remuneration_id, reference_type, reference_id)"
      }
    end

    def find_existing_relationship(params)
      return find_by_id(params[:id]) if params[:id].present?

      find_by_unique_keys(params)
    end

    def find_by_id(id)
      RemunerationRelationship.find_by(
        id: id,
        account_id: current_user.account_id,
        is_deleted: false
      )
    end

    def find_by_unique_keys(params)
      RemunerationRelationship.find_by(
        remuneration_id: params[:remuneration_id],
        reference_type: params[:reference_type],
        reference_id: params[:reference_id],
        account_id: current_user.account_id,
        is_deleted: false
      )
    end

    def update_relationship(relationship, params)
      return success_result(relationship, false) if relationship.update(permitted_attributes(params))

      error_result(relationship.errors.full_messages.join(", "))
    end

    def create_relationship(params)
      relationship = RemunerationRelationship.new(permitted_attributes(params).merge(is_deleted: false))
      return success_result(relationship, true) if relationship.save

      error_result(relationship.errors.full_messages.join(", "))
    end

    def permitted_attributes(params)
      attrs = {}
      attrs[:remuneration_id] = params[:remuneration_id] if params[:remuneration_id].present?
      attrs[:reference_type] = params[:reference_type] if params[:reference_type].present?
      attrs[:reference_id] = params[:reference_id] if params[:reference_id].present?
      attrs[:currency] = params[:currency] if params.key?(:currency)
      attrs[:period] = params[:period] if params.key?(:period)
      attrs[:value] = params[:value] if params.key?(:value)
      attrs[:amount] = params[:amount] if params.key?(:amount)
      attrs[:comments] = params[:comments] if params.key?(:comments)
      attrs[:contract_type] = params[:contract_type] if params.key?(:contract_type)
      attrs[:account_id] = current_user.account_id
      attrs[:user_id] = current_user.id
      attrs
    end

    def success_result(relationship, created)
      { success: true, created: created, relationship: relationship }
    end

    def error_result(errors)
      { success: false, errors: errors }
    end

    def add_error(index, errors)
      results[:errors] << { index: index, errors: errors }
    end
  end
end
