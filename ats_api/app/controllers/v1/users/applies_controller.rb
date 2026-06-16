# frozen_string_literal: true

module V1
  module Users
    class AppliesController < ApplicationController
      include ResourceLoader
      include Pinnable
      include AtsSyncable

      def stats
        start_date = params[:start_date]&.to_date || 30.days.ago.to_date
        end_date = params[:end_date]&.to_date || Date.current

        cache_key = "applies_stats:#{@current_user.account_id}:#{params[:job_id]}:#{params[:user_id]}:#{start_date}:#{end_date}"
        data = Rails.cache.fetch(cache_key, expires_in: 10.minutes) do
          ::Applies::StatsService.new(
            start_date: start_date,
            end_date: end_date,
            job_id: params[:job_id],
            user_id: params[:user_id]
          ).call
        end

        render json: data, status: :ok
      end

      def aging
        query = ::Applies::AgingQuery.new(
          days: (params[:days] || 3).to_i,
          status: params[:status],
          job_id: params[:job_id]
        )

        page = (params[:page] || 1).to_i
        per_page = [ (params[:per_page] || 30).to_i, 30 ].min

        results = query.call
        total = results.count("applies.id")
        records = results.offset((page - 1) * per_page).limit(per_page)

        severity_counts = query.severity_counts
        stage_counts = query.stage_counts

        render json: AgingApplySerializer.new(
          records,
          meta: {
            total: total,
            page: page,
            per_page: per_page,
            by_severity: severity_counts,
            by_stage: stage_counts
          }
        ).serializable_hash, status: :ok
      end

      def timeline
        apply = Apply.includes(:candidate, :job, :selective_process).find_by(id: params[:id])
        return render_not_found("Apply") unless apply

        data = Applies::TimelineService.new(apply: apply).call
        render json: data, status: :ok
      end

      def index
        new_params = search_with_pin
        new_params[:where][:is_deleted] = false unless new_params[:where].key?(:is_deleted)
        perform_search(
          model: Apply,
          serializer: ApplySerializer,
          search_with_pin: new_params,
          compact: params[:compact]&.split(",") || []
        )
      end

      def show
        render_success(@apply, serializer: ApplySerializer, serializer_params: { current_user: @current_user })
      end

      def create
        params_hash = apply_params
        account_id = params_hash[:account_id] || @current_user.account_id

        resolve_external_ids!(params_hash, account_id)
        return unless validate_required_fields!(params_hash)

        @apply = create_or_find_apply(params_hash, account_id)
        return render_apply_error unless @apply&.persisted?

        sync_apply_to_ats(@apply)
        @apply = Apply.include_base.find(@apply.id)
        render_success(@apply, serializer: ApplySerializer, serializer_params: { current_user: @current_user }, status: :created)
      rescue ActionController::ParameterMissing, StandardError => e
        render_error({ errors: [ e.message ] }, status: :unprocessable_entity)
      end

      def update
        params_to_update = inject_pin_and_confidential(apply_params, @apply)
        return render_error(@apply) unless @apply.update(params_to_update)

        sync_and_render_apply
      end

      def destroy
        status = @apply.selective_process_status.presence || "Deletado"
        return render_error(@apply) unless @apply.update(is_deleted: true, selective_process_status: status)

        sync_and_render_apply
      end

      def create_collection
        return process_select_all_collection if params[:select_all_params].present?

        collection_data = get_collections_data
        return render_simple_error("collections parameter is required", status: :bad_request) unless collection_data

        process_list_collection(collection_data)
      end

      def update_collection
        CollectionJob::AppliesJob::UpdateCollectionJob.perform_now(select_all_params, @current_user.id, apply_params)
        render_success({ message: "As aplicações estão sendo atualizadas" })
      end

      def delete_collection
        CollectionJob::AppliesJob::DeleteCollectionJob.perform_later(select_all_params, @current_user.id, apply_params)
        render_success({ message: "As aplicações estão sendo deletadas" })
      end

      private

      def apply_params
        params[:apply] ||= {}
        enrich_params_with_process_status
        params.require(:apply).permit(
          :candidate_id, :job_id, :selective_process_id, :is_deleted, :account_id, :selective_process_status,
          :pin, :confidential,
          :external_candidate_id, :external_job_id, :external_id, :updated_at,
          :sub_status, :reason_for_reject, :reason_code, :reason_category, :internal_comment,
          :is_screening_sent, :source
        )
      end

      def select_all_params
        params.require(:select_all_params).permit!
      end

      def apply_collection_params
        return nil unless params[:apply_collection]
        params.require(:apply_collection).permit(
          :job_id, :selective_process_id, :selective_process_status,
          collections: %i[candidate_id job_id selective_process_id selective_process_status reference_type reference_id]
        )
      end

      def get_collections_data
        return { collections: params.permit(collections: %i[reference_type reference_id candidate_id])[:collections] } if params[:collections].present?
        return apply_collection_params if params[:apply_collection]&.dig(:collections).present?

        nil
      end

      def get_apply_data
        return apply_params if params[:apply].present?
        return {} unless params[:apply_collection]&.dig(:apply).present?

        apply_data = params.require(:apply_collection).require(:apply).permit(
          :job_id, :selective_process_id, :selective_process_status
        )
        enrich_apply_data_with_status(apply_data)
      end

      def extract_candidate_id_from_collection(collection_item)
        return collection_item[:candidate_id] if collection_item[:candidate_id].present?
        return nil unless collection_item[:reference_type].present? && collection_item[:reference_id].present?

        case collection_item[:reference_type]
        when "SourcedProfileSourcing"
          extract_from_sourced_profile_sourcing(collection_item[:reference_id])
        when "SourcedProfile"
          extract_from_sourced_profile(collection_item[:reference_id])
        when "Candidate"
          collection_item[:reference_id]
        when "Apply"
          Apply.find_by(id: collection_item[:reference_id])&.candidate_id
        end
      end

      def extract_from_sourced_profile_sourcing(reference_id)
        sourced_profile_sourcing = SourcedProfileSourcing.find_by(id: reference_id)
        return nil unless sourced_profile_sourcing

        sourced_profile = sourced_profile_sourcing.sourced_profile
        return nil unless sourced_profile

        queue_conversion_if_needed(sourced_profile)
        sourced_profile.candidate_id
      end

      def extract_from_sourced_profile(reference_id)
        sourced_profile = SourcedProfile.find_by(id: reference_id)
        return nil unless sourced_profile

        queue_conversion_if_needed(sourced_profile)
        sourced_profile.reload.candidate_id
      end

      def queue_conversion_if_needed(sourced_profile)
        return if sourced_profile.candidate_id.present?

        ::SourcedProfiles::ConvertToCandidateJob.perform_later(
          [ sourced_profile.id ],
          @current_user.account_id
        )
      end

      def resolve_external_ids!(params_hash, account_id)
        resolve_external_candidate_id!(params_hash, account_id) if params_hash[:candidate_id].blank?
        resolve_external_job_id!(params_hash, account_id) if params_hash[:job_id].blank?
      end

      def resolve_external_candidate_id!(params_hash, account_id)
        return unless params[:apply][:external_candidate_id].present?

        candidate = Candidate.find_by(external_id: params[:apply][:external_candidate_id], account_id: account_id)
        return render_error({ errors: [ "candidate não encontrado para external_candidate_id=#{params[:apply][:external_candidate_id]}" ] }, status: :unprocessable_entity) unless candidate

        params_hash[:candidate_id] = candidate.id
      end

      def resolve_external_job_id!(params_hash, account_id)
        return unless params[:apply][:external_job_id].present?

        job = Job.find_by(external_id: params[:apply][:external_job_id], account_id: account_id)
        return render_error({ errors: [ "job não encontrado para external_job_id=#{params[:apply][:external_job_id]}" ] }, status: :unprocessable_entity) unless job

        params_hash[:job_id] = job.id
      end

      def validate_required_fields!(params_hash)
        return true if params_hash[:candidate_id].present? && params_hash[:job_id].present?

        render_error({ errors: [ "candidate_id e job_id são obrigatórios" ] }, status: :unprocessable_entity)
        false
      end

      def create_or_find_apply(params_hash, account_id)
        Apply.find_or_create_apply(
          candidate_id: params_hash[:candidate_id],
          job_id: params_hash[:job_id],
          account_id: account_id,
          selective_process_id: params_hash[:selective_process_id],
          selective_process_status: params_hash[:selective_process_status],
          user_id: @current_user.id,
          source: params_hash[:source]
        )
      end

      def render_apply_error
        render_error(@apply || { errors: [ "Não foi possível criar o apply" ] }, status: :unprocessable_entity)
      end

      def enrich_apply_data_with_status(apply_data)
        return apply_data if apply_data[:selective_process_status].present? || apply_data[:selective_process_id].blank?

        selective_process = SelectiveProcess.find_by(id: apply_data[:selective_process_id])
        apply_data[:selective_process_status] = selective_process.status if selective_process
        apply_data
      end

      def enrich_params_with_process_status
        return if params[:apply][:selective_process_status].present? || params[:apply][:selective_process_id].blank?

        selective_process = SelectiveProcess.find_by(id: params[:apply][:selective_process_id])
        params[:apply][:selective_process_status] = selective_process.status if selective_process
      end

      def sync_and_render_apply
        sync_apply_to_ats(@apply)
        @apply = Apply.include_base.find(@apply.id)
        render_success(@apply, serializer: ApplySerializer, serializer_params: { current_user: @current_user })
      end

      def process_select_all_collection
        CollectionJob::AppliesJob::CreateCollectionJob.perform_later(
          select_all_params.to_h,
          @current_user.id,
          apply_params
        )
        render_success({ status: "processing" })
      end

      def process_list_collection(collection_data)
        apply_data = get_apply_data

        CollectionJob::AppliesJob::CreateCollectionFromListJob.perform_later(
          collection_data,
          @current_user.id,
          apply_data
        )

        render_success({
          status: "processing",
          message: "#{collection_data[:collections].size} aplicações estão sendo processadas em background"
        })
      end
    end
  end
end
