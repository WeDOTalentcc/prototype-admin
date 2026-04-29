module V1
  module Users
    class SearchArchetypesController < ApplicationController
      include ResourceLoader

      before_action :authorize_request
      before_action :set_resource, only: %i[show update destroy search duplicate]

      def index
        prepare_search_params
        apply_visibility_filter

        perform_search(
          model: SearchArchetype,
          serializer: SearchArchetypeSerializer
        )
      end

      def defaults
        prepare_defaults_params

        perform_search(
          model: SearchArchetype,
          serializer: SearchArchetypeSerializer
        )
      end

      def show
        render_resource(@archetype)
      end

      def create
        archetype = build_archetype
        render_resource(archetype, status: :created)
      rescue ActiveRecord::RecordInvalid => e
        render_validation_error(e)
      rescue StandardError => e
        render_server_error(e)
      end

      def update
        authorize_edit!

        return render_resource(@archetype) if @archetype.update(archetype_params)
        render_validation_error(@archetype)
      end

      def destroy
        authorize_edit!
        @archetype.update!(is_deleted: true)
        render_resource(@archetype)
      end

      def search
        sources = Array(params[:sources] || [ "local", "global" ])
        check_credits!(sources)

        sourcing = @archetype.execute_search!(user: @current_user, sources: sources)
        render_search_response(sourcing, sources)
      end

      def duplicate
        new_archetype = @archetype.duplicate_for(@current_user)
        new_archetype.account = @current_user.account
        new_archetype.save!

        render_resource(new_archetype, status: :created)
      end

      def enums
        render json: {
          seniorities: enum_options(SearchArchetype::SENIORITY_LABELS),
          work_models: enum_options(SearchArchetype::WORK_MODEL_LABELS),
          contract_types: enum_options(SearchArchetype::CONTRACT_TYPE_LABELS)
        }
      end

      private

      def set_resource
        @archetype = SearchArchetype
          .where(account_id: @current_user.account_id, is_deleted: false)
          .find_by!(uid: params[:id])
      end

      def resource_class
        SearchArchetype
      end

      def prepare_search_params
        params[:where] = parse_json_param(params[:where]) || {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?
        params[:where]["account_id"] = @current_user.account_id
      end

      def prepare_defaults_params
        params[:where] = {
          is_deleted: false,
          is_default: true,
          account_id: @current_user.account_id
        }
        params[:order] = { usage_count: :desc }
      end

      def apply_visibility_filter
        params[:where][:_or] = [
          { user_id: @current_user.id },
          { is_public: true },
          { is_default: true, user_id: nil }
        ]
      end

      def build_archetype
        return create_from_description if params[:from_description].present?
        return create_from_job if params[:from_job_id].present?
        create_manual
      end

      def create_from_description
        SearchArchetypes::CreateFromDescriptionService.call(
          account: @current_user.account,
          user: @current_user,
          description: params[:description]
        )
      end

      def create_from_job
        job = @current_user.account.jobs.find(params[:from_job_id])
        SearchArchetypes::CreateFromJobService.call(
          account: @current_user.account,
          user: @current_user,
          job: job
        )
      end

      def create_manual
        @current_user.account.search_archetypes.create!(
          archetype_params.merge(user: @current_user)
        )
      end

      def archetype_params
        params.require(:search_archetype).permit(
          :name, :emoji, :description, :query,
          :seniority, :min_experience_years, :industry,
          :location, :work_model, :contract_type, :is_public,
          skills: [], tags: [], languages: [],
          local_filters: {}, global_filters: {}
        )
      end

      def authorize_edit!
        return if @archetype.user_id == @current_user.id
        return if @archetype.user_id.nil? && @current_user.is_admin

        render_forbidden
      end

      def check_credits!(sources)
        return unless sources.map(&:to_s).include?("global")
        return if @current_user.account.pearch_credits.positive?

        render_payment_required
      end

      def render_resource(resource, status: :ok)
        data = SearchArchetypeSerializer.new(resource, params: { current_user: @current_user }).serializable_hash
        render json: data, status: status
      end

      def render_search_response(sourcing, sources)
        render json: {
          sourcing_id: sourcing.id,
          uid: sourcing.uid,
          archetype_id: @archetype.id,
          archetype_name: @archetype.name,
          sources: sources,
          status: sourcing.status,
          message: "Subscribe to channel: sourcing_#{sourcing.id}"
        }, status: :accepted
      end

      def render_validation_error(error)
        message = error.is_a?(ActiveRecord::RecordInvalid) ? error.message : error.errors.full_messages
        render json: { errors: Array(message) }, status: :unprocessable_entity
      end

      def render_server_error(error)
        Rails.logger.error("SearchArchetype error: #{error.message}")
        render json: { error: error.message }, status: :internal_server_error
      end

      def render_forbidden
        render json: { error: "Sem permissão para editar este arquétipo" }, status: :forbidden
      end

      def render_payment_required
        render json: { error: "Créditos insuficientes", current_balance: 0 }, status: :payment_required
      end

      def enum_options(labels)
        labels.map { |k, v| { value: k, label: v } }
      end
    end
  end
end
