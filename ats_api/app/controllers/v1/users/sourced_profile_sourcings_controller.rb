# frozen_string_literal: true

module V1
  module Users
    class SourcedProfileSourcingsController < ApplicationController
      include ResourceLoader
      include Pinnable

      before_action :set_resource, only: %i[show update destroy similar_candidates]

      def index
        params[:where] = parse_json_param(params[:where])
        params[:where] ||= {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?
        perform_search(
          model: SourcedProfileSourcing,
          serializer: SourcedProfileSourcingSerializer,
          search_with_pin: search_with_pin,
          compact: params[:compact]&.split(",") || []
        )
      end

      def load_more
        trigger_load_more
        render json: { success: true }
      end

      def show
        render_success(@sourced_profile_sourcing, serializer: SourcedProfileSourcingSerializer)
      end

      def create
        @sourced_profile_sourcing = SourcedProfileSourcing.new(
          sourced_profile_sourcing_params.merge(
            account_id: @current_user.account_id,
            user_id: @current_user.id
          )
        )

        if @sourced_profile_sourcing.save
          return render_success(
            @sourced_profile_sourcing,
            serializer: SourcedProfileSourcingSerializer,
            status: :created
          )
        end
        render_error(@sourced_profile_sourcing, status: :unprocessable_entity)
      end

      def update
        if @sourced_profile_sourcing.update(sourced_profile_sourcing_params)
          render_success(@sourced_profile_sourcing, serializer: SourcedProfileSourcingSerializer)
        else
          render_error(@sourced_profile_sourcing)
        end
      end

      def destroy
        @sourced_profile_sourcing.update(is_deleted: true)
        render_success(@sourced_profile_sourcing, serializer: SourcedProfileSourcingSerializer)
      end

      def similar_candidates
        matcher = Matching::CandidatesForSourcedProfileSourcing.new(
          @sourced_profile_sourcing.id,
          top_k: top_k_param,
          account_id: @current_user.account_id,
          filters: filters_param,
          page: page_param,
          per_page: per_page_param,
          min_score: min_score_param,
          max_score: max_score_param
        )

        result = matcher.call
        records = result[:records] || []

        fields = params[:compact]&.split(",") || []
        meta = result[:meta] || {}

        return render_compact_response(records, fields, meta) if fields.any?

        render_success(
          records,
          serializer: JobCandidateMatchSerializer,
          meta: meta,
          serializer_params: { includes: includes_param, current_user: @current_user }
        )
      rescue ActiveRecord::RecordNotFound
        render_not_found("SourcedProfileSourcing")
      rescue StandardError => e
        render_simple_error(e.message, status: :unprocessable_entity)
      end

      private

      def set_resource
        @sourced_profile_sourcing = @current_user.account.sourced_profile_sourcings.active.find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("SourcedProfileSourcing")
      end

      def trigger_load_more
        sourcing_id = (params.dig(:where, "sourcing_id") || params.dig(:where, :sourcing_id))&.to_i
        return unless sourcing_id

        page = (params[:page] || 1).to_i
        return unless page > 1

        sourcing = @current_user.account.sourcings.find_by(id: sourcing_id)
        return unless sourcing

        per_page = (params[:limit] || 200).to_i
        required_count = page * per_page

        existing_count = @current_user.account.sourced_profile_sourcings
          .where(sourcing_id: sourcing.id, is_deleted: false)
          .count

        if existing_count >= required_count
          Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          Rails.logger.info "✅ [AutoTriggerLoadMore] SKIP - Already have enough candidates"
          Rails.logger.info "   Sourcing: #{sourcing.id} | Page: #{page} | Per Page: #{per_page}"
          Rails.logger.info "   Required: #{required_count} | Existing: #{existing_count}"
          Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          return
        end

        lock_key = "load_more_lock:#{sourcing.id}:#{page}"
        return if Rails.cache.read(lock_key)

        has_global_source = sourcing.parameters&.dig("sources")&.include?("global")
        has_local_source = sourcing.parameters&.dig("sources")&.include?("local")

        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Rails.logger.info "🔄 [AutoTriggerLoadMore] Enqueuing LoadMoreCandidatesJob"
        Rails.logger.info "   Sourcing: #{sourcing.id} | Page: #{page} | Per Page: #{per_page}"
        Rails.logger.info "   Required: #{required_count} | Existing: #{existing_count} | Missing: #{required_count - existing_count}"
        Rails.logger.info "   Sources: local=#{has_local_source} | global=#{has_global_source}"
        Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        Rails.cache.write(lock_key, true, expires_in: 5.minutes)

        Candidates::LoadMoreCandidatesJob.perform_async(
          @current_user.account_id,
          @current_user.id,
          sourcing.id,
          page,
          Sourcings::FirstBatchPageSize.for_sourcing(sourcing)
        )
      rescue => e
        Rails.logger.error "[SourcedProfileSourcingsController] auto_trigger_load_more error: #{e.message}"
      end

      def resource_class
        SourcedProfileSourcing
      end

      def sourced_profile_sourcing_params
        params.require(:sourced_profile_sourcing).permit(
          :sourced_profile_id,
          :sourcing_id,
          :analysis,
          :score,
          :saved
        )
      end

      def top_k_param
        value = params[:top_k].to_i
        return 500 if value <= 0
        [ value, 2000 ].min
      end

      def page_param
        [ params[:page].to_i, 1 ].max
      end

      def per_page_param
        value = params[:per_page].to_i
        return 30 if value <= 0
        [ value, 100 ].min
      end

      def limit_params
        value = (params[:per_page] || params[:limit]).to_i
        return 30 if value <= 0
        [value, 100].min
      end

      def min_score_param
        value = params[:min_score].to_f
        return 0.0 if value < 0
        [ value, 1.0 ].min
      end

      def max_score_param
        value = params[:max_score].to_f
        return 1.0 if value <= 0 || value > 1.0
        value
      end

      def filters_param
        return {} unless params[:filters]
        params[:filters].is_a?(Hash) ? params[:filters] : {}
      end

      def includes_param
        raw = params[:include] || params[:includes]
        return [] if raw.blank?
        raw.is_a?(String) ? raw.split(",").map(&:strip) : Array(raw)
      end

      def render_compact_response(records, fields, meta)
        data = records.map do |record|
          record.as_json(methods: [ :score ]).slice(*fields.map(&:strip).map(&:to_s))
        end

        render json: {
          data: data,
          meta: meta
        }
      end
    end
  end
end
