# frozen_string_literal: true

module V1
  module Users
    class CandidatesController < ApplicationController
      include ResourceLoader
      include Pinnable
      include Favoritable
      include Hideable
      include AtsSyncable

      before_action :set_resource, only: %i[show update destroy get_calculated_remunerations get_calculated_benefits communications]

      def index
        params[:where] = parse_json_param(params[:where]) || {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?
        params[:where]["is_hidden"] = false if params[:where]["is_hidden"].nil?
        normalize_candidate_filters!

        perform_search(
          model: Candidate,
          serializer: CandidateSerializer,
          search_with_pin: search_with_pin,
          compact: params[:compact]&.split(",") || []
        )
      end

      def show
        render_success(@candidate, serializer: CandidateSerializer, serializer_params: serializer_params)
      end

      def create
        @candidate = Candidate.new(candidate_params)
        attach_avatar if avatar_present?

        if @candidate.save
          sync_candidate_to_ats(@candidate)
          return render_success(@candidate, serializer: CandidateSerializer, serializer_params: serializer_params, status: :created)
        end

        render_error(@candidate, status: :unprocessable_entity)
      end

     def update
        attach_avatar if avatar_present?

        params_to_update = build_update_params

        @candidate.update(favorite_user_ids: @candidate.favorite_user_ids | [ @current_user.id ]) if params_to_update[:favorite] == true
        @candidate.update(favorite_user_ids: @candidate.favorite_user_ids - [ @current_user.id ]) if params_to_update[:favorite] == false

        @candidate.update(hide_user_ids: (@candidate.hide_user_ids || []) | [ @current_user.id ]) if params_to_update[:hide] == true
        @candidate.update(hide_user_ids: (@candidate.hide_user_ids || []) - [ @current_user.id ]) if params_to_update[:hide] == false

        return render_error(@candidate) unless @candidate.update(params_to_update.except(:favorite, :hide))

        sync_candidate_to_ats(@candidate)
        render_success(@candidate, serializer: CandidateSerializer, serializer_params: serializer_params)
      end

      def destroy
        @candidate.update(is_deleted: true)
        render_success(@candidate, serializer: CandidateSerializer, serializer_params: serializer_params)
      end

      def get_calculated_remunerations
        return render json: { error: "Candidate not found" }, status: :not_found unless @candidate

        remunerations = fetch_remunerations(@candidate)
        calculated_remunerations, sub_total = build_calculated_remunerations(remunerations)

        calculated_remunerations << build_subtotal_remuneration(sub_total, remunerations.first&.currency)

        render json: { calculated_remunerations: calculated_remunerations }, status: :ok
      end

      def get_calculated_benefits
        return render json: { error: "Candidate not found" }, status: :not_found unless @candidate

        benefits = fetch_benefits(@candidate)
        calculated_benefits, sub_total = build_calculated_benefits(benefits)

        calculated_benefits << { name: "Subtotal Benefícios", value: sub_total, type: "subtotal" }
        render json: { calculated_benefits: calculated_benefits }, status: :ok
      end

      def stats
        start_date = params[:start_date]&.to_date || 30.days.ago.to_date
        end_date = params[:end_date]&.to_date || Date.current

        cache_key = "candidates_stats:#{@current_user.account_id}:#{params[:source]}:#{start_date}:#{end_date}"
        data = Rails.cache.fetch(cache_key, expires_in: 30.minutes) do
          Candidates::StatsService.new(
            start_date: start_date,
            end_date: end_date,
            source: params[:source]
          ).call
        end

        render json: data, status: :ok
      end

      # GET /v1/users/candidates/search_hints
      # Composite: Searchkick facets (same as aggregators/candidates) + curated YAML hints for the bar.
      # Params: optional q (filter hints), categories (comma: job_titles,skills), same where/order as aggregators.
      def search_hints
        params[:search] ||= "*"
        search_bundle = global_search_params.merge(per_page: 0, force_aggregators: true)

        results = Candidate.search_default(
          "*",
          search_bundle,
          1,
          false,
          false,
          true
        )

        facets = Candidates::FacetPostProcessor.call(results[:aggs], @current_user)

        categories = params[:categories].to_s.split(",").map(&:strip).reject(&:blank?)
        hints = Taxonomy::CandidateCatalog.hints_for(q: params[:q], categories: categories)

        render json: {
          entity: "candidates",
          facets: facets,
          hints: hints,
          meta: {
            catalog_version: Taxonomy::CandidateCatalog.version,
            facet_fields: Candidate.agg_search_array.keys.map(&:to_s)
          }
        }, status: :ok
      end

      def communications
        data = Candidates::CommunicationsService.new(candidate: @candidate).call
        render json: data, status: :ok
      end

      def get_suggestions
        text = params[:text] || params[:query] || ""
        result = Candidates::SuggestionService.call(text, business_city: nil, business_state: nil)

        return render json: suggestion_response(result), status: :ok if result

        render json: default_suggestion_response, status: :ok
      end

      def prompt_search
        params[:where] = parse_json_param(params[:where])
        params[:where] ||= {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?

        filter = parse_json_param(params[:filter]) if params[:filter].present?
        order = parse_json_param(params[:order]) if params[:order].present?

        sourcing = Candidates::PromptSearchSourcingService.call(
          user: @current_user,
          account: @current_user.account,
          search: params[:search],
          where: params[:where],
          filter: filter || {},
          order: order || {}
        )

        render_success(sourcing, serializer: SourcingSerializer)
      rescue => e
        Rails.logger.error("PromptSearch failed: #{e.message}\n#{e.backtrace.join("\n")}")
        render json: { error: e.message }, status: :internal_server_error
      end

      def upload_resume
        return render_missing_resume_error unless resume_provided?

        result = Candidates::ResumeUploadService.call(
          user: @current_user,
          account: @current_user.account,
          resume_file: params[:resume_file],
          resume_text: params[:resume_text],
          ai_provider: ai_provider
        )

        if result.success?
          render_success(result.candidate, serializer: CandidateSerializer)
        else
          render json: { error: result.error }, status: :unprocessable_entity
        end
      rescue => e
        Rails.logger.error("ResumeUpload failed: #{e.message}\n#{e.backtrace.join("\n")}")
        render json: { error: e.message }, status: :internal_server_error
      end

      def generate_query
        filters = extract_and_sanitize_filters
        query = Candidates::SuggestionService.generate_query_from_filters(filters)

        render json: { query: query }, status: :ok
      rescue => e
        Rails.logger.error("GenerateQuery failed: #{e.message}\n#{e.backtrace.join("\n")}")
        render json: { error: e.message, query: "" }, status: :internal_server_error
      end

      def resume_provided?
        params[:resume_file].present? || params[:resume_text].present?
      end

      def render_missing_resume_error
        render json: { error: "resume_file ou resume_text é obrigatório" }, status: :unprocessable_entity
      end

      def ai_provider
        @ai_provider ||= params[:ai_provider] || "gemini"
      end

      def enqueue_file_processing
        candidate = create_candidate_with_file

        Candidates::ResumeParserJob.perform_async(
          "user_id" => @current_user.id,
          "candidate_id" => candidate.id,
          "account_id" => @current_user.account_id,
          "additional_data" => params[:additional_data],
          "ai_provider" => ai_provider
        )
      end

      def enqueue_text_processing
        Candidates::ResumeParserJob.perform_async(
          "user_id" => @current_user.id,
          "account_id" => @current_user.account_id,
          "resume_text" => params[:resume_text],
          "additional_data" => params[:additional_data],
          "ai_provider" => ai_provider
        )
      end

      def create_candidate_with_file
        candidate = Candidate.create!(
          account_id: @current_user.account_id,
          name: candidate_name
        )

        candidate.curriculum_pdf.attach(params[:resume_file])
        candidate
      end

      def candidate_name
        params[:additional_data]&.dig(:name) || "Candidato Importado"
      end

      private

      def normalize_candidate_filters!
        w = params[:where]

        normalize_range_filter!(w, "created_at")
        normalize_range_filter!(w, "updated_at")

        salary_range = {}
        salary_range[:gte] = w.delete("min_salary").to_f if w["min_salary"].present?
        salary_range[:lte] = w.delete("max_salary").to_f if w["max_salary"].present?
        w["max_salary_expectation"] = salary_range if salary_range.present?

        if w["selective_process_status"].present?
          w["selective_process_statuses"] = w.delete("selective_process_status")
        end

        normalize_pipeline_filter!(w, "shortlisted")
        normalize_pipeline_filter!(w, "placed")

        w.delete("placed_company")
      end

      def normalize_range_filter!(where_hash, field)
        range = {}
        gte_key = "#{field}_gte"
        lte_key = "#{field}_lte"

        range[:gte] = where_hash.delete(gte_key) if where_hash[gte_key].present?
        range[:lte] = where_hash.delete(lte_key) if where_hash[lte_key].present?
        where_hash[field] = range if range.present?
      end

      def normalize_pipeline_filter!(where_hash, prefix)
        normalize_range_filter!(where_hash, "#{prefix}_at")
        singular_key = "#{prefix}_job_id"
        return unless where_hash[singular_key].present?

        where_hash["#{prefix}_job_ids"] = [ where_hash.delete(singular_key) ]
      end

      def serializer_params
        { includes: params[:includes], current_user: @current_user }
      end

      def avatar_present?
        params.dig(:candidate, :avatar).present?
      end

      def attach_avatar
        @candidate.avatar.attach(params[:candidate][:avatar])
      end

      def build_update_params
        inject_pin_and_confidential(candidate_params, @candidate)
      end

      def build_calculated_benefits(benefits)
        sub_total = 0.0
        calculated = benefits.each_with_object([]) do |benefit, list|
          annual_value = calculate_benefit_annual_value(benefit)
          sub_total += annual_value

          list << {
            name: benefit.name,
            description: benefit.description,
            days_of_month: benefit.days_of_month.to_i,
            types: benefit.types,
            is_per_day: benefit.is_per_day,
            annual_value: annual_value
          }
        end

        [ calculated, sub_total ]
      end

      def calculate_benefit_annual_value(benefit)
        return 0.0 unless benefit.types.include?("value")

        value = benefit.description.to_f
        return value * benefit.days_of_month.to_i * 12 if benefit.is_per_day

        value * 12
      end

      def fetch_remunerations(candidate)
        RemunerationRelationship.where(reference_type: "Candidate", reference_id: candidate.id, is_deleted: false)
      end

      def fetch_benefits(candidate)
        BenefitRelationship.where(reference_type: "Candidate", reference_id: candidate.id, is_deleted: false)
      end

      def find_candidate
        Candidate.find_by(id: params[:id], account_id: @current_user&.account_id)
      end

      def build_subtotal_remuneration(sub_total, currency)
        {
          name: "Subtotal Remuneração",
          value: sub_total,
          type: "subtotal",
          currency: currency || "BRL"
        }
      end

      def suggestion_response(result)
        {
          suggestion: result[:suggestion],
          attributes: result[:attributes] || {}
        }
      end

      def default_suggestion_response
        {
          suggestion: nil,
          attributes: {
            role_name: [],
            experience_type: [],
            location: [],
            sector: [],
            skills: [],
            quality_score: 0
          }
        }
      end

      def parsed_filter
        return {} unless params[:filter].present?
        parse_json_param(params[:filter]) || {}
      end

      def parsed_order
        return {} unless params[:order].present?
        parse_json_param(params[:order]) || {}
      end

      def extract_and_sanitize_filters
        filters = params[:filters]&.to_unsafe_h || params[:filter]&.to_unsafe_h || {}
        filters = filters.except(:source, :high_freshness, :strict_filters, :filter_out_no_emails, :reveal_emails, :filter_out_no_phones, :reveal_phones, :filter_out_no_phones_or_emails)
        filters.is_a?(String) ? parse_json_param(filters) : filters
      end

      def build_calculated_remunerations(remunerations)
        sub_total = 0.0

        calculated = remunerations.each_with_object([]) do |remuneration, list|
          next sub_total += add_salary_entries(remuneration, list) if remuneration.remuneration_id == 1

          list << build_generic_remuneration(remuneration)
          sub_total += list.last[:value].to_f
        end

        [ calculated, sub_total ]
      end

      def add_salary_entries(remuneration, list)
        basic_salary = remuneration.value.to_f
        annual_salary = basic_salary * 13.33

        list << {
          name: "Salário",
          value: basic_salary,
          amount: remuneration.amount,
          currency: remuneration.currency,
          type: "salary"
        }

        list << {
          name: "Salário Anual",
          value: annual_salary,
          amount: remuneration.amount,
          currency: remuneration.currency,
          type: "annual_salary"
        }

        annual_salary
      end

      def build_generic_remuneration(remuneration)
        amount = remuneration.amount.to_i
        value = remuneration.value.to_f
        value = value * amount if amount > 1
        remuneration_name = Remuneration::REMUNERATION_TYPES_CANDIDATE.find { |r| r[:id] == remuneration.remuneration_id }[:name]

        {
          name: remuneration_name,
          value: value,
          amount: amount,
          currency: remuneration.currency
        }
      end

      def candidate_params
        permitted = params.require(:candidate).permit(
          :name, :email, :secondary_email, :mobile_phone, :phone, :secondary_phone, :linkedin, :github,
          :portfolio, :current_company, :role_name, :position_level, :self_introduction, :curriculum_text, :date_birth,
          :gender, :nationality, :marital_status, :cpf, :street, :number, :district, :zip, :city, :state, :country, :complement,
          :clt_expectation, :pj_expectation, :freelance_expectation, :current_salary, :desired_salary, :currency, :remote_work,
          :mobility, :interests, :comments, :source, :curriculum_pdf_url, :completed_register, :account_id, :accept_terms, :avatar,
          :pin, :confidential, :favorite, :hide, :external_id, :external_provider, :availability, :work_model,
          :pcd, :ethnicity, :lgbtqia, :neurodivergent, :is_hidden, :lgpd_expires_at, :is_twin, :twin_source_id
        )

        permitted[:data_raw] = params[:candidate][:data_raw] if params[:candidate][:data_raw].present?
        permitted[:external_profile_data] = params[:candidate][:external_profile_data] if params[:candidate][:external_profile_data].present?

        permitted
      end
    end
  end
end
