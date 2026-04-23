module V1
  module Users
    class EvaluationCandidatesController < ApplicationController
      before_action :set_evaluation_candidate, only: %i[show update destroy]
      before_action :reject_if_wsi_questions_pending_review, only: [ :create ]

      def index
        perform_search(
          model: EvaluationCandidate,
          serializer: EvaluationCandidateSerializer,
        )
      end

      def wsi_decision
        ec = EvaluationCandidate.find_by(uid: params[:uid], account_id: @current_user.account_id, is_deleted: false)
        return render_error({ error: "Evaluation candidate not found" }, status: :not_found) if ec.blank?

        render json: {
          data: {
            wsi_decision: ec.wsi_decision,
            wsi_red_flags: ec.wsi_red_flags
          }
        }, status: :ok
      end

      def wsi_report
        ec = EvaluationCandidate.find_by(uid: params[:uid], account_id: @current_user.account_id, is_deleted: false)
        return render_error({ error: "Evaluation candidate not found" }, status: :not_found) if ec.blank?

        if ec.f11_report_json.blank? && ec.completed? && ec.wsi_decision.is_a?(Hash) && ec.wsi_decision["result"].present?
          Wsi::ReportGenerationJob.perform_async(ec.id, ec.account_id)
          return render json: {
            data: { report: nil, f11_report_stale: true, status: "generation_enqueued" }
          }, status: :accepted
        end

        render json: {
          data: {
            report: ec.f11_report_json,
            f11_report_stale: ec.respond_to?(:f11_report_stale) ? ec.f11_report_stale : nil,
            report_generated_at: ec.respond_to?(:report_generated_at) ? ec.report_generated_at&.iso8601 : nil
          }
        }, status: :ok
      end

      def stats
        start_date = params[:start_date]&.to_date || 30.days.ago.to_date
        end_date = params[:end_date]&.to_date || Date.current

        cache_key = "evaluation_candidates_stats:#{@current_user.account_id}:#{start_date}:#{end_date}"
        data = Rails.cache.fetch(cache_key, expires_in: 10.minutes) do
          EvaluationCandidates::StatsService.new(start_date: start_date, end_date: end_date).call
        end

        render json: data, status: :ok
      end

      def show
        render_success(@evaluation_candidate, serializer: EvaluationCandidateSerializer)
      end

      def create
        @evaluation_candidate = EvaluationCandidate.new(evaluation_candidate_params)
        @evaluation_candidate.user = @current_user
        @evaluation_candidate.account = @current_user.account

        if @evaluation_candidate.save
          render_success(@evaluation_candidate, serializer: EvaluationCandidateSerializer)
        else
          render_error(@evaluation_candidate)
        end
      end

      def update
        if @evaluation_candidate.update(evaluation_candidate_params)
          render_success(@evaluation_candidate, serializer: EvaluationCandidateSerializer)
        else
          render_error(@evaluation_candidate)
        end
      end

      def destroy
        @evaluation_candidate.update(is_deleted: true)
        render_success(@evaluation_candidate, serializer: EvaluationCandidateSerializer)
      end

      def create_collection
        CollectionJob::EvaluationCandidatesJob::CreateCollectionJob.perform_later(select_all_params, @current_user.id, set_evaluation_candidate_params)
        render_success({ message: "Avaliações enviadas com sucesso!" })
      end

      private

      def reject_if_wsi_questions_pending_review
        ec_params = params[:evaluation_candidate] || {}
        eval_id = ec_params[:evaluation_id]
        return if eval_id.blank?

        evaluation = Evaluation.find_by(id: eval_id, account_id: @current_user.account_id)
        return if evaluation.blank?

        return unless evaluation.questions.where(is_deleted: false).where(wsi_reviewed: false).exists?

        render json: { error: "questions_pending_review" }, status: :unprocessable_entity
      end

      def set_evaluation_candidate
        @evaluation_candidate = EvaluationCandidate.find(params[:id])
        return if @evaluation_candidate
        render_error({ error: "EvaluationCandidate not found" }, status: :not_found)
      end

      def set_evaluation_candidate_params
        params_to_set = evaluation_candidate_params
        candidate = Candidate.find(id: params_to_set[:candidate_id]) if params_to_set[:candidate_id].present?
        params_to_set[:candidate_uid] = candidate.uid if candidate
        params_to_set[:uid] = SecureRandom.uuid if params_to_set[:uid].blank?
        params_to_set
      end

      def evaluation_candidate_params
        params.require(:evaluation_candidate).permit(:candidate_id, :evaluation_id, :apply_id, :job_id, :date_expiration, :date_view, :completed, :ai_feedback, :is_screening, notification_channels: [])
      end

      def select_all_params
        params.require(:select_all_params).permit!
      end
    end
  end
end
