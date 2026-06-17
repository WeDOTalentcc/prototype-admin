module V1
  module Users
    module Jobs
      class SuggestionsController < ApplicationController
        before_action :set_job, only: [ :evaluation_questions ]

        def create
          job_data = build_job_data_for_suggestion

          if job_data.blank?
            return render json: { error: "Dados da vaga não encontrados" }, status: :unprocessable_entity
          end

          result = JobSuggestionService.call(
            job_data: job_data,
            type: suggestion_params[:type]
          )

          if result.success?
            return render json: { suggestion: result.suggestion }, status: :ok
          end
          render json: { error: result.error }, status: :unprocessable_entity
        end

        def evaluation_questions
          Rails.logger.info "SuggestionsController#evaluation_questions: Gerando questions para Job ##{@job.id}"

          wsi_type = evaluation_questions_params[:type]
          evaluation_id = evaluation_questions_params[:evaluation_id]

          unless %w[wsi_compact wsi_compact_plus query].include?(wsi_type)
            return render json: { error: "Tipo inválido. Use 'wsi_compact', 'wsi_compact_plus' ou 'query'" }, status: :bad_request
          end

          if %w[wsi_compact wsi_compact_plus].include?(wsi_type)
            lia = @job.lia_job_description.presence || {}
            unless lia["status"] == "approved"
              return render json: { error: "wsi_jd_not_approved" }, status: :unprocessable_entity
            end
          end

          if evaluation_id.present?
            @evaluation = Evaluation.find_by(id: evaluation_id, account_id: @current_user.account_id)
            unless @evaluation
              return render json: { error: "Avaliação não encontrada ou sem permissão" }, status: :not_found
            end
          end

          result = JobSuggestionService.generate_evaluation_questions(
            @job,
            wsi_type: wsi_type,
            query: evaluation_questions_params[:query]
          )

          if result.success?
            Rails.logger.info "SuggestionsController#evaluation_questions: Questions geradas com sucesso (tipo: #{wsi_type})"
            enriched_suggestion = enrich_suggestion_with_defaults(result.suggestion, wsi_type)

            if evaluation_id.present? && @evaluation
              created_questions = create_questions_from_suggestion(enriched_suggestion, @evaluation, wsi_type, job: @job)
              return render json: {
                questions: enriched_suggestion,
                created_questions: created_questions.map { |q| { id: q.id, title: q.title } }
              }, status: :ok
            end

            return render json: { questions: enriched_suggestion }, status: :ok
          end

          error_message = result.error || "Falha ao gerar perguntas de avaliação"
          Rails.logger.error "SuggestionsController#evaluation_questions: #{error_message}"
          render json: { error: error_message }, status: :unprocessable_entity
        end

        def generate_query_from_job
          jobs = get_last_3_jobs

          if jobs.empty?
            return render json: { error: "Nenhuma vaga encontrada" }, status: :not_found
          end

          queries = generate_queries_for_jobs(jobs)

          render json: queries, status: :ok
        end

        private

        def set_job
          @job = Job.find_by(id: params[:id], account_id: @current_user.account_id, is_deleted: false)
          render json: { error: "Vaga não encontrada" }, status: :not_found unless @job
        end

        def evaluation_questions_params
          params.permit(:type, :evaluation_id, :query)
        end

        def enrich_suggestion_with_defaults(suggestion_data, wsi_type = nil)
          data = suggestion_data.to_h
          questions = data[:questions] || data["questions"] || []
          return data if questions.empty?

          enriched = questions.map do |q|
            q = q.to_h.with_indifferent_access
            normalized_fw = normalize_framework_weights(q[:framework_weights], q[:competence_type])
            normalized_vtw = normalize_validation_type_weight(q[:validation_type_weight], q[:response_type])
            normalized_category = normalize_category(q[:category], q[:competence_type], q[:response_type], wsi_type)
            normalized_framework = normalize_framework(q[:framework], normalized_fw)
            q.merge(
              framework_weights: normalized_fw,
              validation_type_weight: normalized_vtw,
              category: normalized_category,
              framework: normalized_framework
            )
          end

          data.merge(questions: enriched)
        end

        def create_questions_from_suggestion(suggestion_data, evaluation, wsi_type = nil, job: nil)
          questions_data = suggestion_data[:questions] || []

          return [] if questions_data.empty?

          created_questions = []

          questions_data.each_with_index do |question_data, index|
            normalized_fw = normalize_framework_weights(question_data[:framework_weights], question_data[:competence_type])
            ocean_trait_storage = Wsi::OceanTraitCanonical.to_storage(question_data[:ocean_trait])
            extra_params = merge_question_extra_params(question_data, job: job, ocean_trait_storage: ocean_trait_storage)
            question_attrs = {
              evaluation_id: evaluation.id,
              title: question_data[:title],
              description: question_data[:description],
              response_type: normalize_response_type(question_data[:response_type]),
              competence_type: question_data[:competence_type],
              bloom_level: question_data[:bloom_level],
              dreyfus_target: normalize_integer(question_data[:dreyfus_target]),
              ocean_trait: ocean_trait_storage,
              framework_weights: normalized_fw,
              framework: normalize_framework(question_data[:framework], normalized_fw),
              validation_type_weight: normalize_validation_type_weight(question_data[:validation_type_weight], question_data[:response_type]),
              time: normalize_time_minutes(question_data[:time]),
              category: normalize_category(question_data[:category], question_data[:competence_type], question_data[:response_type], wsi_type),
              position: index + 1,
              is_required: true,
              wsi_reviewed: false,
              wsi_metadata: {
                reviewed_by_recruiter: false,
                needs_manual_review: false,
                generation_attempts: 0
              }
            }
            question_attrs[:extra_params] = extra_params if extra_params.present?

            question_attrs.compact!

            question = Question.create(question_attrs)

            if question.persisted?
              created_questions << question
            else
              Rails.logger.error "Erro ao criar question: #{question.errors.full_messages.join(', ')}"
              Rails.logger.error "Dados: #{question_attrs.inspect}"
            end
          end

          Rails.logger.info "SuggestionsController: Criadas #{created_questions.length} questions para Evaluation ##{evaluation.id}"
          created_questions
        end

        def merge_question_extra_params(question_data, job:, ocean_trait_storage:)
          raw = question_data[:extra_params].presence || question_data["extra_params"]
          base = raw.is_a?(Hash) ? raw.stringify_keys : {}
          return base if question_data[:competence_type].to_s.downcase != "behavioral"
          return base if ocean_trait_storage.blank?

          base.merge("trait_weight" => Wsi::TraitRankingService.trait_weight_for(job: job, ocean_trait: ocean_trait_storage))
        end

        def normalize_response_type(response_type)
          return "text" if response_type.blank?

          case response_type.to_s.downcase
          when "autodeclaration", "autodeclaracao"
            "autodeclaration"
          when "contextual"
            "contextual"
          when "microcase"
            "microcase"
          when "situational", "situacional"
            "situational"
          when "theoretical", "teorica"
            "theoretical"
          else
            "text"
          end
        end

        def normalize_integer(value)
          return nil if value.blank?
          value.to_i if value.respond_to?(:to_i)
        end

        VALID_FRAMEWORK_KEYS = %w[bloom dreyfus big_five cbi_star].freeze
        VALID_FRAMEWORK_VALUES = %w[cbi bloom dreyfus big_five].freeze

        FRAMEWORK_WEIGHT_TO_FRAMEWORK = { "cbi_star" => "cbi" }.freeze

        DEFAULT_FRAMEWORK_WEIGHTS = {
          technical: { "bloom" => 0.25, "dreyfus" => 0.35, "big_five" => 0.1, "cbi_star" => 0.3 },
          behavioral: { "bloom" => 0.15, "dreyfus" => 0.25, "big_five" => 0.3, "cbi_star" => 0.3 }
        }.freeze

        DEFAULT_VALIDATION_TYPE_WEIGHTS = {
          "autodeclaration" => 0.60,
          "contextual" => 0.60,
          "microcase" => 0.20,
          "situational" => 0.15,
          "theoretical" => 0.05,
          "text" => 0.60
        }.freeze

        def normalize_framework_weights(value, competence_type)
          if value.present? && value.is_a?(Hash)
            result = value.transform_keys(&:to_s)
                         .slice(*VALID_FRAMEWORK_KEYS)
                         .transform_values { |v| v.to_f }
                         .compact
            return result if result.any?
          end
          type = competence_type.to_s.downcase == "behavioral" ? :behavioral : :technical
          DEFAULT_FRAMEWORK_WEIGHTS[type]
        end

        def normalize_framework(value, framework_weights)
          normalized = value.to_s.downcase.strip
          return normalized if VALID_FRAMEWORK_VALUES.include?(normalized)

          return nil if framework_weights.blank? || !framework_weights.is_a?(Hash)

          max_key = framework_weights.max_by { |_, w| w.to_f }&.first
          return nil if max_key.blank?

          FRAMEWORK_WEIGHT_TO_FRAMEWORK.fetch(max_key, max_key)
        end

        def normalize_validation_type_weight(value, response_type)
          if value.present? && value.to_s.match?(/\A[\d.]+\z/)
            weight = value.to_f
            return weight if weight.between?(0, 1)
          end
          type = normalize_response_type(response_type)
          DEFAULT_VALIDATION_TYPE_WEIGHTS[type]
        end

        def normalize_time_minutes(value)
          return nil if value.blank?
          minutes = value.to_f
          return nil unless minutes.positive?
          (minutes * 60).to_i
        end

        QUESTION_CATEGORIES = %w[padrao avaliacao situacional].freeze

        def normalize_category(value, competence_type, response_type, wsi_type)
          return nil unless %w[wsi_compact wsi_compact_plus].include?(wsi_type)
          return value.to_s if value.present? && QUESTION_CATEGORIES.include?(value.to_s.downcase)
          return "avaliacao" if competence_type.to_s.downcase == "technical"
          return "situacional" if competence_type.to_s.downcase == "behavioral"
          "avaliacao"
        end

        def get_last_3_jobs
          Job.where(account_id: @current_user.account_id, is_deleted: false)
             .includes(:skills, :company)
             .order(created_at: :desc)
             .limit(3)
        end

        def generate_queries_for_jobs(jobs)
          jobs.map do |job|
            Candidates::SuggestionService.generate_concise_query_from_job(job)
          end
        end

        def suggestion_params
          params.require(:suggestion).permit(
            :type,
            job: [
              :id, :title, :description, :is_remote, :city, :state, :country,
              :workplace_type, :contract_type, :seniority_level, :company_id,
              responsibilities: [], skills: [], behavioral_skills: []
            ]
          )
        end

        def job_params
          params.permit(job: [
            :id, :title, :description, :is_remote, :city, :state, :country,
            :workplace_type, :contract_type, :seniority_level, :company_id,
            responsibilities: [], skills: [], behavioral_skills: []
          ]).fetch(:job, {})
        end

        def build_job_data_for_suggestion
          request_job = suggestion_params[:job].presence || job_params.presence

          if request_job.present?
            request_job.to_h.symbolize_keys
          elsif params[:job_id].present?
            job = Job.find_by(id: params[:job_id], account_id: @current_user.account_id, is_deleted: false)
            return {} unless job

            job_to_hash_for_suggestion(job)
          else
            {}
          end
        end

        def job_to_hash_for_suggestion(job)
          skills = job.skill_relationships
                     .includes(:skill)
                     .where(is_deleted: false)
                     .map { |sr| sr.skill&.name }
                     .compact

          behavioral_skills = job.behavioral_skill_relationships
                                .includes(:behavioral_skill)
                                .where(is_deleted: false)
                                .map { |bsr| bsr.behavioral_skill&.name }
                                .compact

          {
            title: job.title,
            description: job.description,
            is_remote: job.is_remote,
            city: job.city,
            state: job.state,
            country: job.country,
            workplace_type: job.workplace_type,
            contract_type: job.employment_type.present? ? Job::EMPLOYMENT_TYPES[job.employment_type] : nil,
            seniority_level: job.seniority.present? ? Job::SENIORITY[job.seniority] : nil,
            responsibilities: job.responsibilities.to_a,
            skills: skills.presence,
            behavioral_skills: behavioral_skills.presence
          }.compact
        end
      end
    end
  end
end
