# frozen_string_literal: true

module V1
  module Users
    class EntityColumnsController < ApplicationController
      include AuthorizableResource

      before_action :set_entity_column, only: %i[show update]
      before_action :set_entity_context, only: %i[create update_view destroy]

      def index
        authorize EntityColumn
        skip_policy_scope

        perform_search(
          model: EntityColumn,
          serializer: EntityColumnSerializer
        )
      end

      def show
        render_success(@entity_column, serializer: EntityColumnSerializer)
      end

      def show_structure
        entity_name = params[:entity]&.singularize&.downcase
        return render_not_found("Entity not supported") unless EntityColumnService::Structure.supported_entity?(entity_name)

        structure = EntityColumnService::Structure.entity_columns(entity_name, "structure")
        return render_not_found("Structure not found") unless structure

        render json: { entity_column: structure }
      end

      def create
        entity_name = params[:entity]&.singularize
        return render_error_message("Entity is required") if entity_name.blank?

        @entity_column = EntityColumn.find_or_create_by_entity(
          entity_name,
          @current_user.id,
          requested: params[:requested] || "default",
          shortlist_id: @shortlist_id,
          job_id: @job_id,
          account_id: @current_user.account_id
        )

        return render_success(@entity_column, serializer: EntityColumnSerializer) unless params[:entity_columns]

        if @entity_column.update(entity_columns_params)
          return render_success(@entity_column, serializer: EntityColumnSerializer)
        end

        render_error(@entity_column)
      end

      def update
        if @entity_column.update(entity_columns_params)
          render_success(@entity_column, serializer: EntityColumnSerializer)
        else
          render_error(@entity_column)
        end
      end

      def create_view
        return render_error_message("Label is required for views") if view_params[:label].blank?

        @entity_column = @current_user.entity_columns.build(view_params)
        @entity_column.account = @current_user.account
        @entity_column.is_views = true
        @entity_column.is_main = false

        if @entity_column.save
          return render_success(@entity_column, serializer: EntityColumnSerializer, status: :created)
        end
        render_error(@entity_column, status: :unprocessable_entity)
      end

       def update_view
        entity_params = entity_columns_params

        entity_columns = EntityColumn.where(entity: params[:entity].singularize.downcase, user_id: @current_user.id,
                                            is_main: true, requested: entity_params[:requested] || "default").first
        entity_columns.update(entity_params)
        render_success(entity_columns, serializer: EntityColumnSerializer)
      end

      def save_view
        entity_params = entity_columns_params
        return render_error_message("Label is required for views") if entity_params[:label].blank?
        entity_params[:user_id] = @current_user.id
        entity_params[:entity] = entity_params[:entity].singularize

        entity_column = EntityColumn.create(
          label: entity_params[:label],
          entity: entity_params[:entity].downcase,
          user_id: entity_params[:user_id],
          columns_view: entity_params[:columns_view],
          requested: entity_params[:requested],
          is_main: entity_params[:is_main],
          is_views: entity_params[:is_views],
          is_public: entity_params[:is_public]
        )

        render json: { entity_column: }, status: :created
      end

      def destroy
        if @entity_column.destroy
          return head :no_content
        end
        render_error(@entity_column)
      end

      def destroy_by_entity
        entity_column = EntityColumn.where(entity: params[:entity].singularize.downcase, user_id: @current_user.id).last
        if entity_column
          if entity_column.destroy
            return head :no_content
          end
        end
        render_not_found("Entity column not found")
      end

      def delete_view
        view_column = @current_user.entity_columns.view_columns.find(params[:id])

        if view_column.destroy
          head :no_content
        end
        render_error(view_column)
      rescue ActiveRecord::RecordNotFound
        render_not_found("View not found")
      end

      private

      def set_entity_column
        @entity_column = EntityColumn.find(params[:id])
        authorize @entity_column
      rescue ActiveRecord::RecordNotFound
        render_not_found("Entity column not found")
      rescue Pundit::NotAuthorizedError
        render_forbidden
      end

      def set_entity_context
        @shortlist_id = extract_shortlist_id
        @job_id = extract_job_id
      end

      def extract_shortlist_id
        return params[:entity_columns][:shortlist_id] if params[:entity_columns]&.key?(:shortlist_id)
        params[:shortlist_id]
      end

      def extract_job_id
        return params[:entity_columns][:job_id] if params[:entity_columns]&.key?(:job_id)
        params[:job_id]
      end

      def accessible_columns_scope
        {
          _or: [
            { is_public: true },
            { _and: [ { user_id: @current_user.id }, { is_public: false } ] }
          ],
          account_id: @current_user.account_id
        }
      end

      def current_user_main_columns
        @current_user.entity_columns.main_columns
      end

      def current_user_view_columns
        @current_user.entity_columns.view_columns
      end

      def entity_columns_params
        params.require(:entity_columns).permit(
          :entity, :label, :shortlist_id, :requested, :is_main, :is_views,
          :is_public, :job_id,
          business_ids: [],
          columns_view: column_view_attributes,
          columns_all: column_view_attributes
        )
      end

      def view_params
        params.require(:entity_columns).permit(
          :entity, :label, :requested, :is_public,
          business_ids: [],
          columns_view: column_view_attributes
        ).tap do |permitted|
          permitted[:entity] = permitted[:entity]&.singularize&.downcase
        end
      end

      def column_view_attributes
        [
          :field, :search_url, :field_response_text, :field_response_value, :search_entity,
          :update_key, :date_key, :edit_url, :number, :value, :value_name, :text, :sortable,
          :type, :width, :filter, :format_to_save, :component, :preview_component,
          :list, :order, :update_field, :update_url, :object_key, :delete_url,
          :field_sub_filter, :update_entity, :field_url, :separator, :sortable_field,
          :mask, :entity_key, :job_id, :avoid_list,
          { default_values: %i[id name description] }
        ]
      end
    end
  end
end
