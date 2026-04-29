module V1
  module Evaluations
    class EvaluationCandidatesController < ApplicationController
      def show
        render json: { finished: true, declined: @evaluation_candidate.declined? }, status: :ok and return if @evaluation_candidate.completed
        render json: { finished: true, declined: true }, status: :ok and return if @evaluation_candidate.declined?

        account = @evaluation_candidate.user&.account
        job = @evaluation_candidate.job
        business = account&.business

        logo_url = nil
        if business&.logo&.attached?
          logo_url = Rails.application.routes.url_helpers.rails_blob_url(
            business.logo,
            only_path: true
          )
          api_prefix = ENV.fetch("API_URL", "http://localhost:8080")
          logo_url = "#{api_prefix}#{logo_url}"
        end

        questions = Question.where(evaluation_id: @evaluation.id, is_deleted: false)
                             .order(position: :asc)
                             .select(:id, :title, :description, :position)

        render json: {
          evaluation: @evaluation.as_json(except: [ :account_id ]),
          evaluation_candidate: @evaluation_candidate.as_json(except: [ :account_id ]),
          user: @evaluation_candidate.user.as_json(except: [ :account_id, :password_digest, :is_deleted, :created_at, :updated_at ]),
          candidate: @evaluation_candidate.candidate.as_json(only: [ :name ]),
          finished: @evaluation_candidate.completed,
          declined: @evaluation_candidate.declined?,
          company: {
            name: account&.name,
            logo_url: logo_url
          },
          job: {
            title: job&.title
          },
          questions: questions.as_json(only: [ :id, :title, :description, :position ]),
          interview_sessions: build_interview_sessions_payload
        }, status: :ok
      end

      private

      def build_interview_sessions_payload
        sessions = InterviewSession.accessible.where(
          evaluation_candidate: @evaluation_candidate,
          account_id: @account.id
        )

        sessions.map do |session|
          {
            interview_type: session.interview_type,
            token: session.token,
            url: "/interviews/#{@account.uid}/#{session.token}",
            status: session.status,
            expires_at: session.expires_at
          }
        end
      end

      public

      def status
        questions = @evaluation.questions.where(is_deleted: false)
        total = questions.count
        answered = Answer.where(evaluation_id: @evaluation.id, candidate_id: @evaluation_candidate.candidate_id).count

        render json: {
          session_status: @evaluation_candidate.session_status,
          current_question: answered,
          total_questions: total,
          progress: total.positive? ? (answered.to_f / total * 100).round(1) : 0,
          completed: @evaluation_candidate.completed?,
          declined: @evaluation_candidate.declined?
        }, status: :ok
      end

      def reconnect
        can_resume = !@evaluation_candidate.completed? &&
                     !@evaluation_candidate.declined? &&
                     @evaluation_candidate.session_status.in?(%w[active pending])

        render json: {
          evaluation_candidate_uid: @evaluation_candidate.uid,
          session_status: @evaluation_candidate.session_status,
          can_resume: can_resume,
          websocket_url: "/cable",
          channel: "EvaluationChannel",
          params: {
            account_uid: @account.uid,
            evaluation_candidate_uid: @evaluation_candidate.uid
          }
        }, status: :ok
      end

      def decline
        if @evaluation_candidate.declined? || @evaluation_candidate.completed?
          return render json: {
            success: false,
            message: "Avaliação já foi finalizada ou recusada anteriormente"
          }, status: :unprocessable_entity
        end

        reason = params[:reason].presence

        if @evaluation_candidate.decline!(reason)
          render json: {
            success: true,
            message: "Você recusou a avaliação. Obrigado pelo retorno!"
          }, status: :ok
        else
          render json: {
            success: false,
            message: "Não foi possível processar sua recusa. Tente novamente mais tarde."
          }, status: :unprocessable_entity
        end
      end
    end
  end
end
