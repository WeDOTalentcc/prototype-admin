# frozen_string_literal: true

require "terminal-table"

module V1
  module Users
    class JobsController < ApplicationController
      include Pinnable

      before_action :set_job, only: %i[show update destroy add_candidates_from_list change_status publish unpublish duplicate_selective_processes export wsi_jd_big_five_extract wsi_ranking]
      # before_action :ensure_owner, only: %i[update destroy]

      def index
        new_params = search_with_pin_and_confidential
        new_params[:where][:is_deleted] = false unless new_params[:where].key?(:is_deleted)
        new_params[:where][:id] = params[:id].to_i if params[:id].present?

        perform_search(
          model: Job,
          serializer: JobSerializer,
          search_with_pin: new_params,
          compact: params[:compact]&.split(",") || ([])
        )
      end

      def show
        render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user })
      end

      def create
        benefits_data = params[:job][:benefits] if params[:job][:benefits].present?
        skills_data = params[:job][:skills] if params[:job][:skills].present?

        selective_processes_data = params[:job][:selective_processes_attributes]
        job_params_without_sp = job_params.except(:selective_processes_attributes)

        @job = @current_user.jobs.build(job_params_without_sp.merge(account_id: @current_user.account_id))

        if @job.save
          sync_selective_processes(selective_processes_data) if selective_processes_data.present?

          @job.create_default_selective_processes if @job.selective_processes.empty?
          @job.sync_benefits_from_array(benefits_data) if benefits_data.present?
          @job.sync_skills_from_data(skills_data) if skills_data.present?

          return render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user, include_selective_processes: true }, status: :created)
        end
        render_error(@job, status: :unprocessable_entity)
      end

      def update
        benefits_data = params[:job][:benefits] if params[:job][:benefits].present?
        skills_data = params[:job][:skills] if params[:job][:skills].present?
        languages_data = params[:job][:languages] unless params[:job][:languages].nil?
        selective_processes_data = params[:job][:selective_processes_attributes]

        params_to_update = inject_pin_and_confidential(job_params, @job)

        department_name = params_to_update[:department]
        department_name = department_name.is_a?(String) ? department_name : department_name&.name

        params_to_update = params_to_update.except(:department, :languages)

        @job.sync_languages_from_data(languages_data) unless languages_data.nil?

        if selective_processes_data.present?
          params_to_update = params_to_update.except(:selective_processes_attributes)
        end

        Rails.logger.info "Job ##{@job.id} update attempt with params: #{params_to_update.except(:description).inspect}"

        if @job.update(params_to_update)
          Rails.logger.info "Job ##{@job.id} updated successfully"

          sync_selective_processes(selective_processes_data) if selective_processes_data.present?
          @job.sync_benefits_from_array(benefits_data) if benefits_data.present?
          @job.sync_skills_from_data(skills_data) if skills_data.present?

          @job.sync_department_from_name(department_name, @job.account_id) if department_name.present?

          render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user })
        else
          Rails.logger.error "Job ##{@job.id} update FAILED - Errors: #{@job.errors.full_messages.join(', ')}"
          Rails.logger.error "Job ##{@job.id} validation details: #{@job.errors.details.inspect}"
          render_error(@job)
        end
      end

      def destroy
        @job.destroy
        render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user })
      end

      def copy
        copy_params = copy_job_params

        result = ::Jobs::CopyService.new(
          job_id: params[:id],
          user_id: copy_params[:user_id] || @current_user.id,
          entities: copy_params[:entities] || []
        ).call

        return render_error({ error: result[:error] }, status: :unprocessable_entity) unless result[:success]

        render_success(result[:job], serializer: JobSerializer)
      end

      def copy_job_by_amount
        amount = params[:amount]&.to_i
        return render_error({ error: "Amount cannot be zero" }, status: :unprocessable_entity) if amount.nil? || amount.zero?
        return render_error({ error: "Amount must be less than 100" }, status: :unprocessable_entity) if amount >= 100

        job = Job.find_by(id: params[:id], is_deleted: false)
        return render_error({ error: "Job not found" }, status: :not_found) unless job

        copy_params = copy_job_params
        user_id = copy_params[:user_id] || @current_user.id
        entities = copy_params[:entities] || []

        Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        Rails.logger.info("📋 [JobsController] Copy job by amount")
        Rails.logger.info("   Job ID: #{job.id}, Amount: #{amount}, User: #{user_id}")
        Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        if amount == 1
          ::Jobs::CopyByAmountJob.perform_now(amount, job.id, user_id, entities)
        else
          ::Jobs::CopyByAmountJob.perform_later(amount, job.id, user_id, entities)
        end

        render_success({ message: "Job duplication in progress", amount: amount, job_id: job.id })
      end

      def boolean_search
        @job = Job.find(params[:job_id])

        message = Message.where(
          reference_type: "User",
          reference_id: @current_user.id,
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          is_deleted: false
        ).last

        skill_ids = SkillRelationship.where(
          reference_type: "Job",
          reference_id: @job.id,
          is_deleted: false
        ).pluck(:skill_id)

        skills = Skill.where(id: skill_ids).pluck(:name).join(", ")

        content = "Gere uma busca booleana para encontrar candidatos no linkedin através do google com as seguintes habilidades: #{skills}; e que possam se encaixar na vaga #{@job.title}."

        MessageService::EventPublisher.publish(
          message_id: message.id,
          reference_type: "User",
          reference_id: @current_user.id,
          content: content,
          user_name: @current_user.name,
          user_id: @current_user.id,
          account_id: @current_user.account_id,
          status: 0,
          entity: 0,
          created_at: Time.current.iso8601
        )
      end

      def get_data_for_description
        @job = Job.find(params[:job_id])

        includes = [ "remunerations", "benefits", "skills", "languages" ]

        render_success(@job, serializer: JobSerializer, serializer_params: { current_user: @current_user, includes: includes })
      end

      def priorities
        render json: {
          data: Job::PRIORITY.each_with_index.map { |priority, index|
            { id: index.to_s, attributes: { name: priority["name"], id: priority["id"] } }
          }
        }, status: :ok
      end

      def urgency_levels
        render json: {
          data: Job::URGENCY_LEVEL.each_with_index.map { |urgency_level, index|
            { id: index.to_s, attributes: { name: urgency_level["name"], id: urgency_level["id"] } }
          }
        }, status: :ok
      end

      def workplace_types
        render json: {
          data: Job::WORKPLACE_TYPES.each_with_index.map { |workplace_type, index|
            { id: index.to_s, attributes: { name: workplace_type["name"], id: workplace_type["id"] } }
          }
        }, status: :ok
      end

      def employment_types
        render json: {
          data: Job::EMPLOYMENT_TYPES.each_with_index.map { |employment_type, index|
            { id: index.to_s, attributes: { name: employment_type, id: index } }
          }
        }, status: :ok
      end

      def seniorities
        render json: {
          data: Job::SENIORITY.each_with_index.map { |seniority, index|
            { id: index.to_s, attributes: { name: seniority, id: index } }
          }
        }, status: :ok
      end

      def pcd_categories
        render json: {
          data: Job::PCD_CATEGORIES.each_with_index.map { |category, index|
            { id: index.to_s, attributes: { name: category["name"], id: category["id"] } }
          }
        }, status: :ok
      end

      def confidential_types
        render json: {
          data: Job::CONFIDENTIAL_TYPES.each_with_index.map { |category, index|
            { id: index.to_s, attributes: { name: category["name"], id: category["id"] } }
          }
        }, status: :ok
      end

      def add_candidates_from_list
        return render_simple_error("list_id is required", status: :bad_request) unless params[:list_id].present?
        return render_simple_error("selective_process_id is required", status: :bad_request) unless params[:selective_process_id].present?

        list = List.find_by(id: params[:list_id], account_id: @current_user.account_id)
        return render_simple_error("List not found", status: :not_found) unless list

        AppliesJob::AddAppliesFromListJob.perform_later(
          list.id,
          @job.id,
          params[:selective_process_id],
          @current_user.id,
          @current_user.account_id
        )

        render_success({ message: "Processamento iniciado. Os candidatos da lista serão adicionados à vaga." })
      end

      def archive_collection
        return render_simple_error("select_all_params is required", status: :bad_request) unless params[:select_all_params].present?

        is_archived = params[:is_archived].nil? ? true : params[:is_archived]

        CollectionJob::JobsJob::ArchiveCollectionJob.perform_later(
          select_all_params.to_h,
          @current_user.id,
          is_archived: is_archived
        )

        action_text = is_archived ? "arquivadas" : "desarquivadas"
        render_success({
          status: "processing",
          message: "As vagas estão sendo #{action_text}"
        })
      end

      def unarchive_collection
        return render_simple_error("select_all_params is required", status: :bad_request) unless params[:select_all_params].present?

        CollectionJob::JobsJob::ArchiveCollectionJob.perform_later(
          select_all_params.to_h,
          @current_user.id,
          is_archived: false
        )

        render_success({
          status: "processing",
          message: "As vagas estão sendo desarquivadas"
        })
      end

      def activate_collection
        return render_simple_error("select_all_params is required", status: :bad_request) unless params[:select_all_params].present?

        job_params = {
          is_active: true
        }
        reason = params[:reason] || params[:reason_for_pause]
        job_params[:reason_for_pause] = reason if reason.present?

        CollectionJob::JobsJob::ActivateCollectionJob.perform_later(
          select_all_params.to_h,
          @current_user.id,
          **job_params
        )

        render_success({
          status: "processing",
          message: "As vagas estão sendo ativadas"
        })
      end

      def pause_collection
        return render_simple_error("select_all_params is required", status: :bad_request) unless params[:select_all_params].present?

        job_params = {
          is_active: false
        }
        reason = params[:reason] || params[:reason_for_pause]
        job_params[:reason_for_pause] = reason if reason.present?

        CollectionJob::JobsJob::ActivateCollectionJob.perform_later(
          select_all_params.to_h,
          @current_user.id,
          **job_params
        )

        render_success({
          status: "processing",
          message: "As vagas estão sendo paralisadas"
        })
      end

      def change_status
        return render_simple_error("job_status_id is required", status: :bad_request) unless params[:job_status_id].present?

        result = ::Jobs::ChangeStatusService.new(
          job: @job,
          target_status_id: params[:job_status_id],
          reason: params[:reason]
        ).call

        if result[:success]
          render_success(@job.reload, serializer: JobSerializer, serializer_params: { current_user: @current_user })
        else
          payload = { errors: [ result[:error] ] }
          payload[:allowed_transitions] = result[:allowed_transitions] if result[:allowed_transitions]
          render json: payload, status: :unprocessable_entity
        end
      end

      def publish
        result = ::Jobs::PublishService.new(job: @job).publish

        if result[:success]
          render_success(@job.reload, serializer: JobSerializer, serializer_params: { current_user: @current_user })
        else
          payload = { errors: [ result[:error] ] }
          payload[:missing_fields] = result[:missing_fields] if result[:missing_fields]
          render json: payload, status: :unprocessable_entity
        end
      end

      def unpublish
        result = ::Jobs::PublishService.new(job: @job).unpublish

        if result[:success]
          render_success(@job.reload, serializer: JobSerializer, serializer_params: { current_user: @current_user })
        else
          render_simple_error(result[:error], status: :unprocessable_entity)
        end
      end

      def wsi_jd_big_five_extract
        unless @job.account_id == @current_user.account_id
          render_not_found("Job")
          return
        end

        result = Wsi::JdBigFiveExtractionService.call(job: @job)
        if result[:success]
          render_success(@job.reload, serializer: JobSerializer, serializer_params: { current_user: @current_user })
        else
          render json: { errors: [ result[:error] ], code: result[:code] }, status: :unprocessable_entity
        end
      end

      def duplicate_selective_processes
        return render_simple_error("source_job_id is required", status: :bad_request) unless params[:source_job_id].present?

        result = ::Jobs::DuplicateSelectiveProcessesService.new(
          target_job: @job,
          source_job_id: params[:source_job_id],
          replace: ActiveModel::Type::Boolean.new.cast(params[:replace])
        ).call

        if result[:success]
          render_success(@job.reload, serializer: JobSerializer, serializer_params: { current_user: @current_user, include_selective_processes: true })
        else
          render_simple_error(result[:error], status: :unprocessable_entity)
        end
      end

      def bulk_update
        return render_simple_error("job_ids is required", status: :bad_request) unless params[:job_ids].present?
        return render_simple_error("fields is required", status: :bad_request) unless params[:fields].present?

        job_ids = Array(params[:job_ids]).map(&:to_i)
        fields = params[:fields].to_unsafe_h

        if job_ids.size > 100
          CollectionJob::JobsJob::BulkUpdateCollectionJob.perform_later(job_ids, fields, @current_user.id)
          render_success({ status: "processing", message: "Atualização em lote iniciada" })
        else
          result = ::Jobs::BulkUpdateService.new(
            job_ids: job_ids,
            fields: fields,
            user: @current_user
          ).call

          if result[:success]
            render json: { success: true, data: result.except(:success) }, status: :ok
          else
            render_simple_error(result[:error], status: :unprocessable_entity)
          end
        end
      end

      def export
        result = ::Jobs::ExportService.new(
          job: @job,
          format: params[:format] || "csv"
        ).call

        if result[:success]
          send_data result[:content],
                    filename: result[:filename],
                    type: result[:content_type],
                    disposition: "attachment"
        else
          render_simple_error(result[:error], status: :unprocessable_entity)
        end
      end

      def stats
        result = ::Jobs::StatsService.new(
          account_id: @current_user.account_id,
          start_date: params[:start_date],
          end_date: params[:end_date]
        ).call

        render json: { success: true, data: result }, status: :ok
      end

      def alerts
        result = ::Jobs::AlertsService.new(account_id: @current_user.account_id).call

        render json: { success: true, data: result }, status: :ok
      end

      def wsi_ranking
        rows = EvaluationCandidate
          .includes(:candidate)
          .where(
            job_id: @job.id,
            account_id: @current_user.account_id,
            is_deleted: false,
            completed: true
          )
          .where("jsonb_typeof(wsi_decision) = 'object' AND wsi_decision ? 'result'")
          .order(score: :desc)

        data = rows.map do |ec|
          {
            uid: ec.uid,
            name: ec.candidate&.name,
            wsi_final: ec.score.to_f,
            decision: ec.wsi_decision["result"],
            red_flags_count: ec.wsi_red_flags.is_a?(Array) ? ec.wsi_red_flags.size : 0
          }
        end

        render json: { data: data }, status: :ok
      end

      private

      def select_all_params
        params.require(:select_all_params).permit!
      end

      def set_job
        @job = Job.include_base.where(is_deleted: false).find_by(id: params[:id])
        render_not_found("Job") unless @job
      end

      def ensure_owner
        return if @job.user_id == @current_user.id
        render_simple_error("Não autorizado a realizar esta ação neste job", status: :forbidden)
      end

      def job_params
        scope = params.require(:job)
        permitted = scope.permit(
                                    :title, :description, :user_id, :account_id, :job_status_id,
                                    :published_date, :application_deadline, :is_remote, :company_id,
                                    :friendly_badge, :disabilities, :workplace_type, :city, :state,
                                    :pin, :confidential, :provider, :provider_job_id, :external_id,
                                    :job_url, :department, :employment_type,
                                    :salary_from, :salary_to, :salary_currency, :salary_period, :salary_contract_type,
                                    :commission_from, :commission_to, :commission_currency, :commission_period,
                                    :bonus_from, :bonus_to, :bonus_currency, :bonus_period, :seniority,
                                    :is_urgent, :is_deleted, :is_active, :is_published, :reason_for_pause,
                                    :screening_deadline, :shortlist_deadline, :closing_deadline,
                                    :priority, :urgency_level, :is_screening_active, :department_id, :required_pcd_files,
                                    :main_pcd_category, :secondary_pcd_category, :pcd_description, :pcd_files_description,
                                    :sector, :segment, :target_audience, :has_linkedin_post, :has_website_post, :has_indeed_post,
                                    :confidential_type, :confidential_company_name,
                                    :hiring_manager_id, :hiring_manager_name, :hiring_manager_email,
                                    :use_whatsapp_channel, :use_webchat_channel, :use_voice_channel, :use_call_channel,
                                    :minimum_screening_score, :screening_timeout, :screening_max_attempts,
                                    :screening_approve_limit, :interview_minimum_score, :has_automatic_interview,
                                    :interview_calendar_type, :interview_hours_range, :interview_duration,
                                    :web_saturation_amount, :sourcing_saturation_amount,
                                    :saturation_amount_increase, :saturation_release_hours,
                                    :allowed_screenings_limit_date,
                                    responsibilities: [],
                                    notification_channels: [],
                                    selective_processes_attributes: [
                                      :id, :name, :status, :position, :external_id, :color,
                                      :position_x, :position_y, :_destroy,
                                      sub_status: [], childrens: []
                                    ]
                                  )
        merge_wsi_job_jsonb_from_scope(scope, permitted)
      end

      def merge_wsi_job_jsonb_from_scope(scope, permitted)
        extras = {}
        if scope.key?(:jd_quality_score)
          extras[:jd_quality_score] = permitted_jd_quality_score(scope[:jd_quality_score])
        end
        if scope.key?(:lia_job_description)
          val = scope[:lia_job_description]
          extras[:lia_job_description] = val.is_a?(ActionController::Parameters) ? val.to_unsafe_h : val
        end
        permitted.merge(extras)
      end

      def permitted_jd_quality_score(val)
        return nil if val.nil?

        p = val.is_a?(ActionController::Parameters) ? val : ActionController::Parameters.new(val)
        p.permit(
          :score, :status, :evaluated_at,
          dimensions: %i[score status finding dimension max_score]
        )
      end

      def copy_job_params
        return {} unless params[:job].present?

        params.require(:job).permit(:user_id, entities: [])
      end

      def sync_selective_processes(selective_processes_data)
        return unless selective_processes_data.is_a?(Array)

        external_ids = selective_processes_data.map { |sp| sp[:external_id].presence || sp["external_id"].presence }.compact.uniq
        return if external_ids.empty?

        existing_map = SelectiveProcess
          .where(external_id: external_ids, account_id: @job.account_id, job_id: @job.id)
          .index_by(&:external_id)

        selective_processes_data.each do |sp_data|
          ext_id = sp_data[:external_id].presence || sp_data["external_id"].presence
          next unless ext_id.present?

          begin
            existing_sp = existing_map[ext_id]

            if existing_sp
              Rails.logger.info "Job ##{@job.id}: Updating existing SelectiveProcess ##{existing_sp.id} (external_id: #{ext_id})"
              existing_sp.update(
                name: sp_data[:name] || sp_data["name"],
                status: sp_data[:status] || sp_data["status"],
                position: sp_data[:position] || sp_data["position"],
                color: sp_data[:color] || sp_data["color"],
                sub_status: sp_data[:sub_status] || sp_data["sub_status"],
                is_deleted: false
              )
            else
              Rails.logger.info "Job ##{@job.id}: Creating new SelectiveProcess (external_id: #{ext_id})"
              @job.selective_processes.create!(
                external_id: ext_id,
                name: sp_data[:name] || sp_data["name"],
                status: sp_data[:status] || sp_data["status"],
                position: sp_data[:position] || sp_data["position"],
                color: sp_data[:color] || sp_data["color"],
                sub_status: sp_data[:sub_status] || sp_data["sub_status"],
                account_id: @job.account_id
              )
            end
          rescue ActiveRecord::RecordInvalid => e
            Rails.logger.error "Job ##{@job.id}: Failed to sync SelectiveProcess (external_id: #{ext_id}): #{e.message}"
          rescue => e
            Rails.logger.error "Job ##{@job.id}: Unexpected error syncing SelectiveProcess (external_id: #{ext_id}): #{e.message}"
          end
        end
      end

      def map_selective_process_external_ids!(params_hash, account_id)
        return unless params_hash.is_a?(Hash)

        sps = params_hash[:selective_processes_attributes] || params_hash["selective_processes_attributes"]
        return unless sps.is_a?(Array)

        external_ids = sps.map { |sp| sp[:external_id].presence || sp["external_id"].presence }.compact.uniq
        return if external_ids.empty?

        existing_map = SelectiveProcess
          .where(external_id: external_ids, account_id: account_id, job_id: @job.id)
          .index_by(&:external_id)

        sps.each do |sp|
          next if sp[:id].present? || sp["id"].present?

          ext = sp[:external_id].presence || sp["external_id"].presence
          next unless ext.present?

          existing = existing_map[ext]
          if existing
            sp[:id] = existing.id
            sp["id"] = existing.id
          end
        end
      end
    end
  end
end
