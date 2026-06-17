# frozen_string_literal: true

require "stringio"

module V1
  module Users
    class SourcingsController < ApplicationController
      include ResourceLoader

      before_action :check_credits, only: [ :create ]
      before_action :set_active_storage_host, only: [ :create, :show ]
      before_action :set_resource, only: %i[show stats update context_for_ai recalculate_stats refine]

      def index
        prepare_index_filters
        results = perform_search(model: Sourcing, serializer: SourcingSerializer, return_results: true)
        records = results[:records]

        ActiveRecord::Associations::Preloader.new(
          records: records, associations: { files_attachments: :blob }
        ).call

        meta = { total: results[:total_count] }
        meta[:where] = global_search_params[:where] if global_search_params[:where].present?
        meta[:search] = params[:search] if params[:search].present?

        render json: SourcingSerializer.new(
          records,
          meta: meta,
          params: { current_user: @current_user }
        ).serializable_hash
      end

      def create
        return render_bad_request("Query parameter or files are required") unless valid_create_params?

        sources = parse_sources
        return render_bad_request("Invalid source. Use 'local', 'global', and/or 'linkedin'") if sources.empty?

        return handle_linkedin_sourcing(sources) if linkedin_parsing_requested?

        sourcing = create_sourcing(sources)
        enqueue_searches(sourcing, sources)
        render_accepted(sourcing)
      end

      def show
        data = SourcingSerializer.new(@sourcing).serializable_hash
        data[:meta] = { pagination: pool_pagination_info(@sourcing) }
        render json: data, status: :ok
      end

      def load_more
        sourcing = current_account.sourcings.find(params[:id])
        page = (params[:page] || 2).to_i
        page_size = if params[:page_size].present?
          params[:page_size].to_i.clamp(1, 100)
        else
          Sourcings::FirstBatchPageSize.for_sourcing(sourcing)
        end

        Candidates::LoadMoreCandidatesJob.perform_async(
          current_account.id,
          @current_user.id,
          sourcing.id,
          page,
          page_size
        )

        render json: {
          sourcing_id: sourcing.id,
          status: "processing",
          page: page,
          page_size: page_size,
          pagination: pool_pagination_info(sourcing)
        }, status: :accepted
      end

      def update
        return render_success(@sourcing, serializer: SourcingSerializer) if @sourcing.update(sourcing_update_params)
        render_error(@sourcing.errors.full_messages.join(", "))
      end

      def stats
        render_success(build_stats_response)
      end

      def context_for_ai
        render_success(build_context_for_ai_response)
      end

      def recalculate_stats
        @sourcing.enqueue_stats_calculation
        render_success({ message: "Stats calculation enqueued", sourcing_id: @sourcing.id })
      end

      def credits
        render_success(credits_service.statistics(
          start_date: parse_date(:start_date),
          end_date: parse_date(:end_date)
        ))
      rescue ArgumentError => e
        render_bad_request("Invalid date format: #{e.message}")
      end

      def search_profiles
        render_success(build_search_profiles_response)
      end

      def find_similar_candidates
        result = Candidates::SimilarCandidatesSearchService.new(
          account: @current_user.account,
          user: @current_user
        ).call(
          candidate_ids: Array(params.require(:candidate_ids)).map(&:to_i),
          job_id: params[:job_id]&.to_i,
          limit: (params[:limit] || 20).to_i.clamp(1, 50),
          threshold: (params[:threshold] || 0.60).to_f.clamp(0.0, 1.0),
          exclude_ids: Array(params[:exclude_ids]).map(&:to_i),
          sources: Array(params[:sources] || [ "local" ]),
          pearch_options: build_pearch_options(params[:pearch_options]),
          skip_cache: ActiveModel::Type::Boolean.new.cast(params[:skip_cache])
        )

        render json: result, status: :ok
      rescue ArgumentError => e
        handle_similar_candidates_error(e)
      rescue ActiveRecord::RecordNotFound => e
        render json: { error: "not_found", message: e.message }, status: :not_found
      end

      def refine
        Rails.logger.warn "[DEPRECATED] POST /sourcings/:id/refine is deprecated. Use POST /sourcings/:id/refinements instead."

        service = Candidates::SimilarCandidates::RefinementService.new(
          account: @current_user.account,
          user: @current_user
        )

        result = service.call(
          sourcing: @sourcing,
          liked_candidate_ids: Array(params[:liked_candidate_ids]).map(&:to_i),
          disliked_feedbacks: parse_disliked_feedbacks,
          sources: Array(params[:sources] || [ "local" ]),
          limit: (params[:limit] || 20).to_i.clamp(1, 50)
        )

        render json: result, status: :ok
      rescue ArgumentError => e
        render json: { error: "invalid_params", message: e.message }, status: :unprocessable_entity
      rescue ActiveRecord::RecordNotFound => e
        render json: { error: "not_found", message: e.message }, status: :not_found
      end


      def history
        render_success(build_history_response)
      end

      def transactions
        render_success(build_transaction_response)
      rescue ArgumentError => e
        render_bad_request("Invalid date format: #{e.message}")
      end

      def move_to_job
        result = Sourcings::MoveToJobService.call(
          sourcing: find_sourcing,
          job_id: params[:job_id],
          candidate_ids: params[:candidate_ids],
          user: @current_user
        )

        return render_bad_request(result.error) unless result.success?

        render json: {
          success: true,
          applies_created: result.applies_created&.size || 0,
          skipped: result.skipped || []
        }, status: :ok
      end

      def create_job
        result = Sourcings::CreateJobService.call(
          sourcing: find_sourcing,
          job_attributes: params[:job],
          candidate_ids: params[:candidate_ids],
          user: @current_user
        )

        return render_bad_request(result.error) unless result.success?

        render json: {
          success: true,
          job_id: result.job.id,
          job: JobSerializer.new(result.job).serializable_hash.dig(:data, :attributes),
          applies_created: result.applies_created || 0
        }, status: :created
      end

      def add_candidate
        sourcing = find_sourcing
        return render json: { error: "Sourcing not found" }, status: :not_found unless sourcing

        sourced_profile = resolve_sourced_profile_for_add(sourcing)
        return if performed?

        existing = SourcedProfileSourcing
                     .where(sourcing_id: sourcing.id, sourced_profile_id: sourced_profile.id, is_deleted: false)
                     .first

        if existing
          render json: { data: serialize_add_relation(existing), meta: { idempotent: true } }, status: :ok
          return
        end

        relation = SourcedProfileSourcing.create!(
          sourcing_id: sourcing.id,
          sourced_profile_id: sourced_profile.id,
          account_id: sourcing.account_id,
          score: params[:score],
          general_comments: params[:notes]
        )

        render json: { data: serialize_add_relation(relation) }, status: :created
      rescue ActiveRecord::RecordInvalid => e
        render json: { error: e.message }, status: :unprocessable_entity
      end

      private

      def resolve_sourced_profile_for_add(sourcing)
        if params[:sourced_profile_id].present?
          sp = @current_user.account.sourced_profiles.active.find_by(id: params[:sourced_profile_id])
          return sp if sp

          render json: { error: "sourced_profile not found" }, status: :not_found
          return nil
        end

        if params[:candidate_id].present?
          candidate = @current_user.account.candidates.find_by(id: params[:candidate_id])
          unless candidate
            render json: { error: "candidate not found" }, status: :not_found
            return nil
          end
          return find_or_create_sourced_profile_from_candidate(candidate, sourcing)
        end

        render json: { error: "candidate_id or sourced_profile_id required" }, status: :unprocessable_entity
        nil
      end

      def find_or_create_sourced_profile_from_candidate(candidate, sourcing)
        existing = candidate.sourced_profile.first
        return existing if existing

        SourcedProfile.create!(
          account_id: sourcing.account_id,
          candidate_id: candidate.id,
          name: candidate.name,
          email: candidate.email
        )
      end

      def serialize_add_relation(relation)
        {
          id: relation.id,
          sourcing_id: relation.sourcing_id,
          sourced_profile_id: relation.sourced_profile_id,
          score: relation.score,
          general_comments: relation.general_comments,
          created_at: relation.created_at
        }
      end

      def find_sourcing
        Sourcing.find_by(id: params[:id], account_id: @current_user.account_id)
      end

      def valid_create_params?
        params[:query].present? || params[:files].present? || params[:file].present?
      end

      def linkedin_parsing_requested?
        params[:is_linkedin_parse] && params[:linkedin_profile_urls].present?
      end

      def prepare_index_filters
        params[:where] = parse_json_param(params[:where]) || {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?
      end

      def build_pearch_options(pearch_params)
        return {} if pearch_params.blank?

        pearch_params = pearch_params.is_a?(String) ? JSON.parse(pearch_params) : pearch_params

        {
          type: pearch_params[:type] || pearch_params["type"] || "pro",
          limit: (pearch_params[:limit] || pearch_params["limit"] || 10).to_i.clamp(1, 30),
          show_emails: ActiveModel::Type::Boolean.new.cast(pearch_params[:show_emails] || pearch_params["show_emails"]),
          show_phone_numbers: ActiveModel::Type::Boolean.new.cast(pearch_params[:show_phone_numbers] || pearch_params["show_phone_numbers"]),
          high_freshness: ActiveModel::Type::Boolean.new.cast(pearch_params[:high_freshness] || pearch_params["high_freshness"]),
          require_emails: ActiveModel::Type::Boolean.new.cast(pearch_params[:require_emails] || pearch_params["require_emails"]),
          require_phone_numbers: ActiveModel::Type::Boolean.new.cast(pearch_params[:require_phone_numbers] || pearch_params["require_phone_numbers"])
        }.compact
      rescue JSON::ParserError
        {}
      end

      def parse_disliked_feedbacks
        return [] unless params[:disliked_feedbacks].present?

        Array(params[:disliked_feedbacks]).map do |df|
          {
            candidate_id: df[:candidate_id].to_i,
            reason: df[:reason].to_s
          }
        end
      end

      def handle_linkedin_sourcing(sources)
        sourcing = build_sourcing(
          sources,
          additional_params: { linkedin_profile_urls: params[:linkedin_profile_urls] }
        )

        Candidates::ProcessLinkedinProfilesJob.perform_async(
          @current_user.account.id,
          sourcing.id,
          params[:linkedin_profile_urls],
          params[:include_email] || false
        )

        render_accepted(sourcing)
      end

      def build_stats_response
        {
          sourcing_stats: @sourcing.stats,
          score_distribution: @sourcing.score_distribution,
          roi_metrics: @sourcing.roi_metrics
        }
      end

      def build_search_profiles_response
        {
          profiles: Pearch::SearchProfiles.all,
          current_balance: @current_user.account.pearch_credits,
          notes: Pearch::SearchProfiles.cost_notes
        }
      end

      def build_history_response
        page = params[:page] || 1
        per_page = params[:per_page] || 30

        results = fetch_sourcing_history(page, per_page)
        sourcings = results[:records] || []
        total_count = results[:total_count] || 0

        {
          history: group_by_date(sourcings),
          pagination: build_pagination(page, per_page, total_count)
        }
      end

      def build_transaction_response
        {
          current_balance: credits_service.current_balance,
          total_consumed: credits_service.total_consumed,
          transactions: fetch_transactions.as_json(only: transaction_fields)
        }
      end


      def create_sourcing(sources)
        sourcing = build_sourcing(sources)
        attach_files_to_sourcing(sourcing) if files_present?
        sourcing.reload
      end

      def build_sourcing(sources, additional_params: {})
        @current_user.account.sourcings.create!(
          user: @current_user,
          uid: SecureRandom.uuid,
          provider: determine_provider(sources),
          query: params[:query].to_s,
          parameters: build_sourcing_parameters(sources, additional_params),
          status: "processing",
          searched_at: Time.current
        )
      end

      def determine_provider(sources)
        sources.size > 1 ? "hybrid" : sources.first
      end

      def build_sourcing_parameters(sources, additional_params)
        filtered_params.merge(
          limit: params[:limit],
          sources: sources
        ).merge(additional_params)
      end

      def enqueue_searches(sourcing, sources)
        sources.each do |source|
          job_params = params.to_unsafe_h.symbolize_keys.merge(source: source)
          Sourcings::JobEnqueuerService.new(
            user: @current_user,
            sourcing: sourcing,
            query: sourcing.query,
            params: job_params
          ).call
        end
      end

      def files_present?
        params[:files].present? || params[:file].present?
      end

      def attach_files_to_sourcing(sourcing)
        files = extract_files_from_params
        return if files.empty?

        log_file_processing(sourcing, files)

        extracted_texts = process_and_attach_files(sourcing, files)
        update_sourcing_query_with_texts(sourcing, extracted_texts) if extracted_texts.any?
      end

      def extract_files_from_params
        files = normalize_files_param(params[:files]) || [ params[:file] ].compact
        files.select { |f| f.is_a?(ActionDispatch::Http::UploadedFile) }
      end

      def normalize_files_param(files_param)
        return nil unless files_param.present?
        return files_param if files_param.is_a?(Array)
        return files_param.to_unsafe_h.values if files_param.respond_to?(:to_unsafe_h)
        return files_param.values if files_param.is_a?(Hash)
        [ files_param ]
      end

      def process_and_attach_files(sourcing, files)
        files.each_with_object([]) do |file, extracted_texts|
          text = safely_extract_text(file)
          extracted_texts << text if text.present?
          sourcing.files.attach(file)
        end
      end

      def safely_extract_text(file)
        return nil unless file.is_a?(ActionDispatch::Http::UploadedFile)

        yomu = Yomu.new(file.tempfile)
        yomu.text
      rescue => e
        log_extraction_error(e)
        nil
      end

      def update_sourcing_query_with_texts(sourcing, extracted_texts)
        combined_text = extracted_texts.join("\n\n")
        new_query = generate_query_from_texts(sourcing.query, combined_text)
        sourcing.update(query: new_query)
        log_query_generation(new_query)
      rescue => e
        log_query_generation_error(e)
        fallback_update_query(sourcing, combined_text)
      end

      def generate_query_from_texts(current_query, combined_text)
        generated = Candidates::SuggestionService.generate_query_from_files(combined_text)
        return merge_queries(current_query, generated) if generated.present?
        merge_queries(current_query, combined_text)
      end

      def merge_queries(current, new_content)
        return new_content if current.blank?
        "#{current}\n\n#{new_content}"
      end

      def fallback_update_query(sourcing, combined_text)
        new_query = merge_queries(sourcing.query, combined_text)
        sourcing.update(query: new_query)
      end


      def fetch_sourcing_history(page, per_page)
        Sourcing.search_default("*",
          where: build_history_where_clause,
          page: page,
          per_page: per_page,
          order: { created_at: :desc }
        )
      end

      def fetch_transactions
        credits_service.transaction_history(
          limit: [ params[:limit]&.to_i || 50, 100 ].min,
          start_date: parse_date(:start_date),
          end_date: parse_date(:end_date)
        )
      end


      def parse_sources
        sources = params[:sources] || params[:source]
        return [ "global" ] if sources.blank?

        normalized = sources.is_a?(Array) ? sources : [ sources ]
        normalized.map(&:to_s).map(&:downcase).uniq & [ "local", "global", "linkedin" ]
      end

      def parse_date(key)
        return nil unless params[key]
        Date.parse(params[key])
      end

      def build_history_where_clause
        where = parse_json_param(params[:where]) || {}
        where = normalize_array_params(where)
        where["is_deleted"] = false if where["is_deleted"].nil?
        where["account_id"] = @current_user.account_id
        where["user_id"] = @current_user.id
        where
      end

      def normalize_array_params(hash)
        return hash unless hash.is_a?(Hash)

        hash.transform_values do |value|
          normalize_array_value(value)
        end
      end

      def normalize_array_value(value)
        return value unless value.is_a?(Hash)
        return value.values if numeric_keys_only?(value)
        normalize_array_params(value)
      end

      def numeric_keys_only?(hash)
        hash.keys.all? { |k| k.to_s.match?(/^\d+$/) }
      end

      def group_by_date(sourcings)
        return [] if sourcings.blank?

        sourcings
          .group_by { |s| s.created_at.to_date }
          .map { |date, items| build_date_group(date, items) }
          .sort_by { |group| group[:date] }
          .reverse
      end

      def build_date_group(date, items)
        {
          date: date,
          count: items.size,
          sourcings: items.map { |s| SourcingSerializer.new(s).serializable_hash }
        }
      end

      def build_pagination(page, per_page, total_count)
        {
          current_page: page.to_i,
          per_page: per_page.to_i,
          total_count: total_count,
          total_pages: (total_count.to_f / per_page.to_i).ceil
        }
      end


      def render_bad_request(error_message)
        render json: { error: error_message }, status: :bad_request
      end

      def render_payment_required(error_message, balance = 0)
        render json: { error: error_message, current_balance: balance }, status: :payment_required
      end

      def render_error(error_message, balance = nil, status_code = :unprocessable_entity)
        render json: { error: error_message, current_balance: balance }.compact, status: status_code
      end

      def render_success(data, status_code = :ok, serializer: nil)
        data = serializer.new(data).serializable_hash if serializer
        render json: data, status: status_code
      end

      def render_accepted(sourcing)
        render json: build_accepted_response(sourcing), status: :accepted
      end

      def build_accepted_response(sourcing)
        {
          sourcing_id: sourcing.id,
          uid: sourcing.uid,
          provider: sourcing.provider,
          sources: sourcing.parameters["sources"],
          status: sourcing.status,
          message: "Subscribe to channel: sourcing_#{sourcing.id}"
        }
      end


      def check_credits
        sources = parse_sources
        return unless sources.include?("global")
        return if @current_user.account.pearch_credits.positive?

        render_payment_required(
          "No credits available for global search. Please contact support to purchase credits.",
          0
        )
      end

      def set_resource
        @sourcing = @current_user.account.sourcings.active.find(params[:id])
      end

      def current_account
        @current_user.account
      end

      def pool_pagination_info(sourcing)
        local_cache = Rails.cache.read("sourcing_pool:#{sourcing.id}:local")
        global_cache = Rails.cache.read("sourcing_pool:#{sourcing.id}:global")

        loaded_count = sourcing.sourced_profile_sourcings.where(is_deleted: false).count

        return default_pagination_info(sourcing, loaded_count) unless local_cache.present? || global_cache.present?

        local_total = local_cache&.dig(:total) || 0
        global_total = global_cache&.dig(:total) || 0
        total = local_total + global_total

        page_size_local = local_cache&.dig(:page_size) || 10
        page_size_global = global_cache&.dig(:page_size) || 10
        page_size = [ page_size_local, page_size_global ].max

        max_source_total = [ local_total, global_total ].max
        total_pages = max_source_total > 0 ? (max_source_total.to_f / page_size).ceil : 1
        current_page = [ (loaded_count.to_f / (page_size * sources_count(sourcing))).ceil, 1 ].max

        {
          current_page: current_page,
          page_size: page_size,
          total_pages: total_pages,
          total_in_pool: total,
          loaded_count: loaded_count,
          has_more: current_page < total_pages,
          pool_available: true,
          pool_expires_at: [ local_cache&.dig(:expires_at), global_cache&.dig(:expires_at) ].compact.min,
          sources: {
            local: local_cache.present? ? { total: local_total, page_size: page_size_local } : nil,
            global: global_cache.present? ? { total: global_total, page_size: page_size_global } : nil
          }.compact
        }
      end

      def sources_count(sourcing)
        (sourcing.parameters["sources"] || [ "local" ]).size
      end

      def default_pagination_info(sourcing, loaded_count)
        {
          current_page: 1,
          page_size: 10,
          total_pages: 1,
          total_in_pool: loaded_count,
          loaded_count: loaded_count,
          has_more: false,
          pool_available: false,
          pool_expires_at: nil
        }
      end

      def set_active_storage_host
        return unless Rails.env.development? || Rails.env.test?
        ActiveStorage::Current.url_options = { host: request.base_url }
      end


      def credits_service
        @credits_service ||= ::Pearch::CreditsService.new(@current_user.account)
      end

      def resource_class
        Sourcing
      end

      def filtered_params
        params.except(:controller, :action, :query, :async, :sourcing_id).to_unsafe_h
      end

      def sourcing_update_params
        params.require(:sourcing).permit(:saved, :notes, :status, :is_deleted)
      end

      def transaction_fields
        [ :id, :transaction_type, :amount, :balance_before, :balance_after,
         :reason, :reference_id, :reference_type, :created_at ]
      end

      def log_file_processing(sourcing, files)
        Rails.logger.info "SourcingsController: Processing #{files.size} file(s) for sourcing #{sourcing.id}"
      end

      def log_extraction_error(error)
        Rails.logger.error "Failed to extract text from file: #{error.message}"
        Rails.logger.error error.backtrace.join("\n")
      end

      def log_query_generation(query)
        Rails.logger.info "Sourcing query generated from files: #{query[0, 100]}..."
      end

      def log_query_generation_error(error)
        Rails.logger.error "Failed to generate query from files: #{error.message}"
        Rails.logger.error error.backtrace.join("\n")
      end

      def build_context_for_ai_response
        page = (params[:page] || 1).to_i
        per_page = (params[:per_page] || 30).to_i
        offset = (page - 1) * per_page

        base_relation = @sourcing.sourced_profile_sourcings
                                .where(is_deleted: false)
                                .includes(:sourced_profile)

        total_count = base_relation.count
        profiles = base_relation.order(score: :desc).offset(offset).limit(per_page)

        {
          sourcing: {
            id: @sourcing.id,
            uid: @sourcing.uid,
            query: @sourcing.query,
            provider: @sourcing.provider,
            status: @sourcing.status,
            results_count: @sourcing.results_count,
            searched_at: @sourcing.searched_at
          },
          aggregated_stats: @sourcing.aggregated_stats.presence || {},
          current_page_data: profiles.map { |sps| serialize_for_ai(sps) },
          pagination: {
            page: page,
            per_page: per_page,
            total_profiles: total_count,
            total_pages: (total_count.to_f / per_page).ceil
          },
          selected_ids: params[:selected_ids] || []
        }
      end

      def serialize_for_ai(sourced_profile_sourcing)
        profile = sourced_profile_sourcing.sourced_profile

        {
          id: sourced_profile_sourcing.id,
          sourced_profile_id: profile.id,
          name: profile.name,
          email: profile.email,
          phone: profile.phone,
          city: profile.city,
          state: profile.state,
          current_company: profile.current_company,
          current_title: profile.current_title,
          total_experience_years: profile.total_experience_years,
          score: sourced_profile_sourcing.score,
          clt_expectation: profile.clt_expectation,
          pj_expectation: profile.pj_expectation,
          remote_work: profile.remote_work,
          mobility: profile.mobility,
          skills: extract_skill_names(profile.skills_data),
          languages: extract_language_names(profile.languages_data),
          has_email: profile.email.present? || profile.has_emails,
          has_phone: profile.phone.present? || profile.has_phone_numbers,
          analysis_summary: sourced_profile_sourcing.analysis&.dig("one_liner")
        }
      end

      def extract_skill_names(skills_data)
        (skills_data || []).map { |s| s.is_a?(Hash) ? s["name"] : s }.compact.first(10)
      end

      def extract_language_names(languages_data)
        (languages_data || []).map { |l| l.is_a?(Hash) ? (l["language"] || l["name"]) : l }.compact
      end

      def handle_similar_candidates_error(error)
        if error.message.start_with?("missing_embeddings:")
          missing_ids = error.message.sub("missing_embeddings:", "").split(",").map(&:to_i)
          render json: {
            error: "missing_embeddings",
            message: "The following candidates do not have embeddings: #{missing_ids}",
            missing_ids: missing_ids
          }, status: :unprocessable_entity
        else
          render json: { error: "invalid_params", message: error.message }, status: :bad_request
        end
      end
    end
  end
end
