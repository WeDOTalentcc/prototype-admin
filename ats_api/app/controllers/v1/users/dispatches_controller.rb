# frozen_string_literal: true

module V1
  module Users
    class DispatchesController < ApplicationController
      before_action :set_dispatch, only: %i[show]

      def index
        scope = Dispatch.where(account_id: @current_user.account_id)
                        .includes(:dispatch_messages)
                        .order(created_at: :desc)

        scope = scope.where(channel_type: params[:channel_type]) if params[:channel_type].present?
        scope = scope.where(status: params[:status]) if params[:status].present?

        if params[:candidate_id].present?
          dispatch_ids = DispatchMessage.where(recipient_type: "Candidate", recipient_id: params[:candidate_id])
                                       .select(:dispatch_id)
          scope = scope.where(id: dispatch_ids)
        end

        if params[:job_id].present?
          scope = scope.where(reference_type: "Job", reference_id: params[:job_id])
        end

        page = (params[:page] || 1).to_i
        per_page = [ (params[:per_page] || 30).to_i, 30 ].min
        total = scope.count
        records = scope.offset((page - 1) * per_page).limit(per_page)

        render json: DispatchSerializer.new(
          records,
          meta: { total: total, page: page, per_page: per_page }
        ).serializable_hash, status: :ok
      end

      def show
        render json: DispatchSerializer.new(@dispatch).serializable_hash, status: :ok
      end

      def create
        service = Dispatches::CreateService.new(
          user: @current_user,
          account: @current_user.account,
          params: dispatch_params
        )

        return render json: success_payload(service), status: :accepted if service.call

        render json: { errors: service.dispatch.errors.full_messages }, status: :unprocessable_entity
      end

      def tracking_summary
        dispatch = Dispatch.includes(:dispatch_messages)
                           .where(account_id: @current_user.account_id)
                           .find_by(id: params[:id])
        return render_not_found("Dispatch") unless dispatch

        messages = dispatch.dispatch_messages
        total = messages.count
        sent = messages.where(status: [ :sent, :delivered, :opened ]).count
        delivered = messages.where(status: [ :delivered, :opened ]).count
        opened = messages.where.not(opened_at: nil).count
        clicked = messages.where.not(clicked_at: nil).count
        bounced = messages.where(status: :failed).count
        pending = messages.where(status: [ :pending, :processing ]).count

        opened_candidates = messages.where.not(opened_at: nil)
                                     .joins("INNER JOIN candidates ON candidates.id = dispatch_messages.recipient_id AND dispatch_messages.recipient_type = 'Candidate'")
                                     .pluck("candidates.id", "candidates.name", "candidates.email", "dispatch_messages.opened_at")
                                     .map { |id, name, email, opened_at| { id: id, name: name, email: email, opened_at: opened_at&.iso8601 } }

        unopened_candidates = messages.where(opened_at: nil)
                                      .where.not(status: :failed)
                                      .joins("INNER JOIN candidates ON candidates.id = dispatch_messages.recipient_id AND dispatch_messages.recipient_type = 'Candidate'")
                                      .pluck("candidates.id", "candidates.name", "candidates.email")
                                      .map { |id, name, email| { id: id, name: name, email: email } }

        render json: {
          data: {
            dispatch_id: dispatch.id,
            subject: dispatch.subject,
            created_at: dispatch.created_at&.iso8601,
            totals: {
              total: total,
              sent: sent,
              delivered: delivered,
              opened: opened,
              clicked: clicked,
              bounced: bounced,
              pending: pending,
              open_rate: total.positive? ? (opened.to_f / total * 100).round(1) : 0,
              click_rate: opened.positive? ? (clicked.to_f / opened * 100).round(1) : 0
            },
            opened_candidates: opened_candidates,
            unopened_candidates: unopened_candidates
          }
        }, status: :ok
      end

      def tracking_by_job
        job = Job.find_by(id: params[:job_id], account_id: @current_user.account_id)
        return render_not_found("Job") unless job

        dispatches = Dispatch.where(account_id: @current_user.account_id, reference: job)
                             .includes(:dispatch_messages)
                             .order(created_at: :desc)
                             .limit(20)

        summaries = dispatches.map do |dispatch|
          messages = dispatch.dispatch_messages
          total = messages.count
          opened = messages.where.not(opened_at: nil).count
          clicked = messages.where.not(clicked_at: nil).count

          {
            dispatch_id: dispatch.id,
            subject: dispatch.subject,
            created_at: dispatch.created_at&.iso8601,
            total: total,
            opened: opened,
            clicked: clicked,
            open_rate: total.positive? ? (opened.to_f / total * 100).round(1) : 0
          }
        end

        render json: { data: summaries }, status: :ok
      end

      private

      def set_dispatch
        @dispatch = Dispatch.includes(:dispatch_messages)
                            .where(account_id: @current_user.account_id)
                            .find_by(id: params[:id])
        render_not_found("Dispatch") unless @dispatch
      end

      def dispatch_params
        params.require(:dispatch).permit(
          :name,
          :channel_type,
          :reference_type,
          :reference_id,
          :scheduled_for,
          :status,
          :target_type,
          :subject,
          :body,
          :is_followup,
          candidate_ids: [],
          user_ids: [],
          target_payload: {}
        )
      end

      def success_payload(service)
        {
          dispatch: {
            id: service.dispatch.id,
            status: service.dispatch.status,
            channel_type: service.dispatch.channel_type
          }
        }
      end
    end
  end
end
