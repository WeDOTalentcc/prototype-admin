module BenefitRelationships
  class BulkUpsertService
    def initialize(relationships_params:, current_user:)
      @relationships_params = relationships_params
      @current_user = current_user
      @results = { created: [], updated: [], deleted: [], errors: [], total: 0 }
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

        case result[:action]
        when :created
          results[:created] << result[:relationship]
        when :updated
          results[:updated] << result[:relationship]
        when :deleted
          results[:deleted] << result[:relationship]
        end
        results[:total] += 1
      end
    end

    def upsert_relationship(params)
      return validation_error unless valid_params?(params)

      if params[:is_deleted] == true || params["is_deleted"] == true
        return delete_relationship(params)
      end

      if params[:benefit_relationship_id].present? || params["benefit_relationship_id"].present?
        return update_relationship(params)
      end

      create_relationship(params)
    end

    def valid_params?(params)
      params[:benefit_id].present? || params["benefit_id"].present? ||
        (params[:reference_type].present? || params["reference_type"].present?) &&
        (params[:reference_id].present? || params["reference_id"].present?)
    end

    def validation_error
      {
        success: false,
        errors: "Campos obrigatórios: benefit_id OU (reference_type, reference_id)"
      }
    end

    def find_relationship_by_id(id)
      BenefitRelationship.find_by(id: id, is_deleted: false)
    end

    def find_relationship_for_delete(id)
      BenefitRelationship.find_by(id: id)
    end

    def delete_relationship(params)
      id = params[:benefit_relationship_id] || params["benefit_relationship_id"]
      return error_result("benefit_relationship_id é obrigatório para deletar") unless id.present?

      relationship = find_relationship_for_delete(id)
      return error_result("BenefitRelationship não encontrado") unless relationship

      return success_result(relationship, :deleted) if relationship.is_deleted?

      if relationship.update(is_deleted: true)
        success_result(relationship, :deleted)
      else
        error_result(relationship.errors.full_messages.join(", "))
      end
    end

    def update_relationship(params)
      id = params[:benefit_relationship_id] || params["benefit_relationship_id"]
      relationship = find_relationship_by_id(id)
      return error_result("BenefitRelationship não encontrado") unless relationship

      if relationship.update(permitted_attributes(params))
        success_result(relationship, :updated)
      else
        error_result(relationship.errors.full_messages.join(", "))
      end
    end

    def create_relationship(params)
      relationship = BenefitRelationship.new(permitted_attributes(params).merge(is_deleted: false))

      if relationship.name.blank? && relationship.benefit_id.present?
        benefit = Benefit.find_by(id: relationship.benefit_id)
        relationship.name = benefit&.name || "Benefit Relationship #{Time.current.to_i}"
      elsif relationship.name.blank?
        relationship.name = "Benefit Relationship #{Time.current.to_i}"
      end

      if relationship.save
        success_result(relationship, :created)
      else
        error_result(relationship.errors.full_messages.join(", "))
      end
    end

    def permitted_attributes(params)
      attrs = {}
      attrs[:benefit_id] = params[:benefit_id] || params["benefit_id"] if params[:benefit_id].present? || params["benefit_id"].present?
      attrs[:reference_type] = params[:reference_type] || params["reference_type"] if params[:reference_type].present? || params["reference_type"].present?
      attrs[:reference_id] = params[:reference_id] || params["reference_id"] if params[:reference_id].present? || params["reference_id"].present?
      attrs[:type_description] = params[:type_description] || params["type_description"] if params.key?(:type_description) || params.key?("type_description")
      attrs[:value] = params[:value] || params["value"] if params.key?(:value) || params.key?("value")
      attrs[:details] = params[:details] || params["details"] if params.key?(:details) || params.key?("details")
      attrs[:is_per_day] = params[:is_per_day] || params["is_per_day"] if params.key?(:is_per_day) || params.key?("is_per_day")
      attrs[:days_of_month] = params[:days_of_month] || params["days_of_month"] if params.key?(:days_of_month) || params.key?("days_of_month")
      attrs
    end

    def success_result(relationship, action)
      { success: true, action: action, relationship: relationship }
    end

    def error_result(errors)
      { success: false, errors: errors }
    end

    def add_error(index, errors)
      results[:errors] << { index: index, errors: errors }
    end
  end
end
