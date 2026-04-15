# frozen_string_literal: true

module V1
  module Users
    class ApplicationController < ActionController::Base
      include TenantScoped
      include SearchRenderer
      include Authorizable
      protect_from_forgery with: :null_session

      before_action :authorize_request

      rescue_from ActiveRecord::RecordInvalid, with: :record_errors
      rescue_from ActiveRecord::RecordNotSaved, with: :record_errors

      include TranslatedErrors

      def record_not_found
        class_name = self.class.name.split("::").last
        class_name = class_name.remove("Controller")
        class_name = class_name.singularize
        render json: { error: "#{class_name} not found" }, status: 404
      end

      def record_errors(invalid)
        render json: { error: invalid.record.errors }, status: :unprocessable_entity
      end

      def authorize_request
        header = request.headers["Authorization"]
        token = header.split(" ").last if header
        decoded = jwt_decode(token)
        if decoded
          if JwtBlacklist.revoked?(decoded)
            return render json: { error: "Token revogado" }, status: :unauthorized
          end

          @current_user = User.find_by(id: decoded[:user_id])
          Current.user = @current_user
          if @current_user
            return
          end

          return render json: { error: "Invalid token" }, status: :unauthorized unless @current_user
        end

        render json: { error: "Token missing or invalid" }, status: :unauthorized
      end

      def jwt_encode(payload, exp = 24.hours.from_now)
        payload[:exp] = exp.to_i
        JWT.encode(payload, Rails.application.secret_key_base)
      end

      def jwt_decode(token)
        decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
        HashWithIndifferentAccess.new decoded
      rescue JWT::DecodeError => e
        Rails.logger.error "JWT Decode Error: #{e.message}"
        nil
      end

      def only_admin
        require_admin!
      end

      def order_params
        order = {}
        if params[:order]&.present?
          order = JSON.parse(params[:order]) || {}
        end
        order[:created_at] = "desc" if params[:search] == "*" && order == {}
        order
      end

      def default_response
        head :ok, content_type: "text/html"
      end

      def search_response(search, class_name = "default", per_page = 30)
        {
          "#{class_name}": search[:records],
          "total_#{class_name}": search[:total_count],
          page_count: search[:total_count].zero? ? 1 : (search[:total_count] / per_page.to_f).ceil,
          aggregators: search[:aggs]
        }
      end

      def model_class_from_string(model_name)
        class_name = model_name.singularize.camelize

        klass = class_name.safe_constantize
        return klass if klass && klass < ActiveRecord::Base

        nil
      end

      def where_params(base = false)
        where = base || {}
        where.merge!(JSON.parse(params[:where])) if params[:where]

        filter = JSON.parse(params[:filter]) if params[:filter]

        filter&.to_a&.each do |field|
          if field[1].is_a?(Array) || field[1].is_a?(Integer) || field[1].is_a?(Hash)
            where[field[0].to_s] = field[1]
            next
          end
          where[field[0].to_s] = { like: "%#{field[1]&.downcase}%" } if field[1].present?
        end

        model = model_class_from_string(controller_name)

        where.deep_symbolize_keys
      end

      def custom_params
        {
          where: where_params,
          order: order_params,
          extra_params: params[:extra_params],
          entity_column_id: params[:entity_column_id]
        }
      end

      def identify_type_params
        {
          "Hash" => ->(field) { field[1] },
          "Integer" => ->(field) { field[1] },
          "Array" => ->(field) { { all: field[1] } },
          "String" => ->(field) { identify_string_params(field[1]) },
          "NilClass" => ->(field) { field[1] }
        }
      end

      def identify_string_params(field)
        boolean_search = false
        [ " or ", " and " ].each do |op|
          field.downcase.include?(op) ? boolean_search = true : next
        end

        return field if boolean_search

        { like: "%#{field.downcase}%" }
      end

      def limit_params
        return 30 unless params[:limit]

        params[:limit]
      end

      def search_params
        params[:search] = "*" unless params[:search]
        params[:search] = params[:search].downcase
        params[:search]
      end

      def global_search_params
        @search_params = {}
        @search_params = @search_params.merge({ where: where_params })
                                       .merge({ order: order_params })
                                       .merge({ page: params[:page] || 1 })
                                       .merge({ limit: limit_params })
      end

      def inject_pin_and_confidential(params_entity, object_current)
        params_entity = inject_array_ids(params_entity, object_current, :pin_recruiter_ids) if params_entity[:pin]
        if params_entity[:pin] == false
          params_entity = remove_array_ids(params_entity, object_current,
                                           :pin_recruiter_ids)
        end

        if params_entity[:confidential]
          params_entity = inject_array_ids(params_entity, object_current, :confidential_recruiter_ids)
        end

        if params_entity[:confidential] == false
          params_entity = remove_array_ids(params_entity, object_current, :confidential_recruiter_ids)
        end
        params_entity.except(:pin, :confidential)
      end

      def inject_array_ids(params_entity, object_current, field)
        params_entity[field] = object_current[field]
        params_entity[field] << @current_user.id
        params_entity[field].uniq!
        params_entity[field]
        params_entity
      end

      def remove_array_ids(params_entity, object_current, field)
        params_entity[field] = object_current[field]
        params_entity[field].delete @current_user.id if params_entity[field].present?
        params_entity[field].uniq! if params_entity[field].present?
        params_entity[field] if params_entity[field].present?
        params_entity
      end

      def search_with_pin
        params_new = custom_params
        params_new[:order] = { _score: "desc" }.merge(order_params)
        params_new[:boost_where] = { "pin_recruiter_ids" => @current_user.id }

        if params[:boost_where]
          params_new[:boost_where] = params_new[:boost_where].merge(JSON.parse(params[:boost_where]))
        end

        params_new
      end

      def save_search_history
        build = {
          operator: "and",
          page: custom_params[:page].nil? ? 1 : page,
          per_page: 30,
          smart_aggs: true,
          body_options: { track_total_hits: true },
          aggs: controller_name.classify.constantize.agg_search_array
        }
        current_class = controller_name.classify

        build_params = build.merge(custom_params).merge(build_where: params[:term] ? false : true)

        if params[:term] ? false : true
          text_search = SearchService.build_text_search(params[:term] || search_params, build_params,
                                                        params[:term] ? false : true)
        end
        final_params = SearchService.build_agg(build_params, text_search)
        SearchHistory.save_history(final_params, current_class, custom_params[:where], @current_user,
                                   params[:term] || search_params)
      end

      def save_activity_log
        current_class = controller_name.classify
        object = instance_variable_get("@#{current_class.underscore}")
        updated_changes = []
        previous_changes = []

        object.previous_changes.each do |keys, _values|
          updated_changes.push({ field: keys, value: object.previous_changes[keys][1] })
          previous_changes.push({ field: keys, value: object.previous_changes[keys][0] })
        end

        ActivityLogService.save_logs(
          updated_changes,
          previous_changes,
          current_class,
          object.id,
          @current_user.id
        )
      end

      def delete_collection
        CollectionJob::DeleteJob.perform_later(
          params[:select_all_params] ? select_all_params : nil,
          params[:entity_collection] ?  entity_collection_params : nil,
          controller_name.classify.constantize,
          @current_user
        )

        render json: { status: true }
      end

      def select_all_params
        params.required(:select_all_params)&.permit!
      end

      def entity_collection_params
        params.required(:entity_collection)&.permit(
          collections: %i[
            reference_type reference_id
          ]
        )
      end

      def class_valid?
        class_name = params[:class_name]
        class_name = class_name.singularize
        class_name = class_name.capitalize
        @class = class_name.constantize
      rescue StandardError
        render json: { message: "Class #{params[:class_name].constantize} does not exist" },
               status: :not_found
      end

      def data_applies_days(job_id)
        {
          applies: Apply.where("created_at >= ?", Time.now - 30.days)
                        .where(registered_candidate: true)
                        .where(job_id:)
                        .group_by_day(
                          :created_at, last: 30, reverse: true
                        ).count,

          candidate_interests: CandidateInterest.where("updated_at >= ?", Time.now - 30.days)
                                                .where(job_id:)
                                                .group_by_day(:updated_at, last: 30, reverse: true).count
        }
      end

      def data_applies_weeks(job_id)
        {
          applies: Apply.where("created_at >= ?", Time.now - 2.months)
                        .where(registered_candidate: true)
                        .where(job_id:)
                        .group_by_week(:created_at, last: 12, reverse: true).count,

          candidate_interests: CandidateInterest.where("updated_at >= ?", Time.now - 2.months)
                                                .where(job_id:)
                                                .group_by_day(:updated_at, last: 12, reverse: true).count
        }
      end

      def data_applies_months(job_id)
        {
          applies: Apply.where("created_at >= ?", Time.now - 12.months)
                        .where(job_id:)
                        .where(registered_candidate: true).group_by_month(
                          :created_at, last: 12, reverse: true
                        ).count,

          candidate_interests: CandidateInterest.where("updated_at >= ?", Time.now - 12.months)
                                                .where(job_id:)
                                                .group_by_day(:updated_at, last: 12, reverse: true).count
        }
      end

      def render_success(resource, status: :ok, serializer: nil, meta: nil)
        options = {}
        options[:serializer] = serializer if serializer
        options[:meta] = meta if meta
        render json: resource, status: status, **options
      end

      def render_error(resource, status: :unprocessable_entity)
        render json: { errors: resource.errors.full_messages }, status: status
      end

      def render_simple_error(message, status: :bad_request)
        render json: { error: message }, status: status
      end

      def render_not_found(entity = "Recurso")
        render_simple_error("#{entity} não encontrado", status: :not_found)
      end

      def render_no_content
        head :no_content
      end
    end
  end
end
