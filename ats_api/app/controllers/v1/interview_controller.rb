# frozen_string_literal: true

module V1
  class InterviewController < V1::Users::ApplicationController
    skip_before_action :authorize_request
    before_action :switch_tenant
    before_action :set_session
    before_action :require_internal_auth, only: %i[complete result]

    def show
      return render json: { status: "expired" }, status: :ok if @session.expires_at <= Time.current
      return render json: { status: @session.status }, status: :ok unless @session.status.in?(%w[pending active])

      render json: {
        token: @session.token,
        status: @session.status,
        interview_type: @session.interview_type,
        duration_minutes: @session.duration_minutes,
        language: @session.language,
        recruiter_email: @session.created_by&.email,
        job: @session.job_context,
        candidate: build_candidate_context,
        questions: formatted_questions,
        evaluation: build_evaluation_context,
        notification_channels: Array(@session.evaluation_candidate&.notification_channels),
        company: {
          name: @account.name,
          interviewer_name: @session.created_by&.name || "Lia"
        }
      }, status: :ok
    end

    def start
      return render json: { error: "already started" }, status: :unprocessable_entity unless @session.status == "pending"

      @session.update!(status: "active", started_at: Time.current)
      render json: { status: "active" }, status: :ok
    end

    def submit_answer
      return render json: { error: "not active" }, status: :unprocessable_entity unless @session.status == "active"
      return render json: { error: "missing question_id" }, status: :unprocessable_entity if params[:question_id].blank?

      answers = @session.transcript || []
      answers << {
        question_id: params[:question_id].to_i,
        transcription: params[:transcription],
        audio_duration: params[:audio_duration],
        answered_at: Time.current.iso8601
      }
      @session.update!(transcript: answers)

      save_answer_record

      render json: { status: "ok", answers_count: answers.size }, status: :ok
    end

    def complete
      return render json: { error: "not active" }, status: :unprocessable_entity unless @session.status.in?(%w[active pending])

      @session.update!(
        status: "completed",
        completed_at: Time.current,
        transcript: params[:transcript] || @session.transcript,
        report: params[:report],
        score: params[:score],
        recommendation: params[:recommendation]
      )

      PostInterview::DispatchService.new(interview_session: @session).call
      finalize_evaluation_candidate

      render json: { status: "completed" }, status: :ok
    end

    def result
      return render json: { error: "not active" }, status: :unprocessable_entity unless @session.status.in?(%w[active completed pending])

      @session.update!(
        status: "scored",
        completed_at: @session.completed_at || Time.current,
        report: params[:report],
        score: params[:score],
        recommendation: params[:recommendation]
      )

      render json: { status: "scored" }, status: :ok
    end

    private

    def require_internal_auth
      token = request.headers["Authorization"]&.split(" ")&.last
      payload = token.present? ? JsonWebToken.decode(token) : nil
      role = payload&.dig(:role).to_s

      render json: { error: "Forbidden" }, status: :forbidden unless %w[service one_time_token].include?(role)
    end

    def switch_tenant
      @account = Account.find_by(uid: params[:account_uid])
      return render_not_found("Account") unless @account

      Apartment::Tenant.switch!(@account.tenant)
    end

    def set_session
      @session = InterviewSession.find_by(token: params[:token])
      render_not_found("InterviewSession") unless @session
    end

    def build_candidate_context
      ctx = @session.candidate_context || {}
      {
        name: ctx["name"],
        phone: ctx["mobile_phone"] || @session.candidate&.mobile_phone,
        current_company: ctx["current_company"],
        current_role: ctx["role_name"],
        experience_years: ctx["position_level"]
      }
    end

    def build_evaluation_context
      evaluation = @session.evaluation
      {
        id: evaluation.id,
        name: evaluation.name
      }
    end

    def formatted_questions
      @session.questions_snapshot.each_with_index.map do |q, index|
        {
          id: q["id"],
          title: q["title"],
          text: q["title"],
          description: q["description"],
          type: q["competence_type"] || q["response_type"] || "behavioral",
          competency: q["competence_type"],
          weight: q["validation_type_weight"] || 1.0,
          follow_up_limit: q["follow_up_limit"] || 2,
          parent_question_id: q["parent_question_id"],
          value_father: q["value_father"] || [],
          response_type: q["response_type"],
          order: index + 1
        }
      end
    end

    def save_answer_record
      PostInterview::SaveAnswerService.new(
        interview_session: @session,
        question_id: params[:question_id].to_i,
        transcription: params[:transcription],
        audio_content: params[:audio_data],
        audio_content_type: params[:audio_content_type],
        audio_duration: params[:audio_duration]
      ).call
    rescue StandardError => e
      Rails.logger.error "❌ [InterviewController] save_answer_record failed: #{e.message}"
    end

    def finalize_evaluation_candidate
      ec = @session.evaluation_candidate
      return unless ec

      ec.update!(completed: true) unless ec.completed?
      ::Evaluations::EvaluationAggregateService.call(evaluation_candidate: ec)
    rescue StandardError => e
      Rails.logger.error "❌ [InterviewController] finalize_evaluation_candidate failed: #{e.message}"
    end
  end
end
