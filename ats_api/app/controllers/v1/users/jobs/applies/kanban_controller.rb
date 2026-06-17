module V1
  module Users
    module Jobs
      module Applies
        class KanbanController < ApplicationController
          before_action :set_job

          def show
            columns = @job.selective_processes.order(:position)

            columns = columns.where(id: params[:selective_process_id]) if params[:selective_process_id].present?

            kanban_data = columns.map do |process_stage|
              search_where = build_kanban_search_where(process_stage.id)
              search_result = Apply.search_default(params[:term] || "*", {
                where: search_where,
                per_page: Apply::PER_PAGE_KANBAN,
                page: params[:page] || 1
              }, 1, false, nil, false)

              sourcing_applies_count = 0
              web_response_applies_count = 0

              applies = search_result[:records]
              ActiveRecord::Associations::Preloader.new(records: applies, associations: [:candidate]).call

              applies_with_summaries = applies.map do |apply|
                apply_attributes = apply.attributes
                apply_attributes["evaluation_candidate_summaries"] = apply.evaluation_candidate_summaries
                apply_attributes["candidate_name"] = apply.candidate&.name
                apply_attributes["candidate_email"] = apply.candidate&.email
                apply_attributes["candidate_phone"] = apply.candidate&.mobile_phone
                apply_attributes["candidate_role"] = apply.candidate&.role_name
                apply_attributes["candidate_company"] = apply.candidate&.current_company
                apply_attributes["candidate_avatar"] = apply.candidate&.avatar_public_url
                sourcing_applies_count += 1 if apply.source == "sourcing"
                web_response_applies_count += 1 if apply.source == "web_response"
                apply_attributes
              end

              {
                selective_process_id: process_stage.id,
                selective_process_title: process_stage.name,
                approved_process_id: process_stage.approved_process_id,
                rejected_process_id: process_stage.rejected_process_id,
                action_behavior: process_stage.action_behavior,
                sub_status_options: process_stage.sub_status_options,
                sourcing_applies_count: sourcing_applies_count,
                web_response_applies_count: web_response_applies_count,
                applies: {
                  records: applies_with_summaries,
                  total_count: search_result[:total_count]
                }
              }
            end

            render json: {
              data: {
                job_id: @job.id,
                job_title: @job.title,
                columns: kanban_data
              }
            }, status: :ok
          end

          private

          def set_job
            @job = Job.find(params[:job_id])
          end

          def build_kanban_search_where(selective_process_id)
            base_where = {
              job_id: @job.id,
              selective_process_id: selective_process_id,
              is_deleted: [ false, nil ]
            }
            request_filters = where_params(base_where)
            filters = request_filters.except(:job_id, :selective_process_id)
            return base_where if filters.blank?

            filters = normalize_range_filters(filters)
            filters = normalize_in_filters(filters)
            base_where.merge(filters)
          end

          def normalize_in_filters(filters)
            filters.transform_values do |value|
              next value unless value.is_a?(Hash) && (value.key?(:in) || value.key?("in"))

              arr = Array(value[:in] || value["in"]).compact
              next value if arr.empty?

              normalized = arr.map { |v| v.to_s.match?(/\A\d+\z/) ? v.to_i : v }
              normalized.one? ? normalized.first : normalized
            end
          end

          def normalize_range_filters(filters)
            filters.transform_values do |value|
              next value unless value.is_a?(Hash)

              value.to_h.transform_values do |v|
                next v unless v.is_a?(String) && v.match?(/\A-?\d+\.?\d*\z/)

                v.include?(".") ? v.to_f : v.to_i
              end
            end
          end
        end
      end
    end
  end
end
