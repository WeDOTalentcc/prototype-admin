# frozen_string_literal: true

module V1
  module Users
    module Applies
      class EmailTrackingController < ApplicationController
        before_action :set_apply

        def followup_status
          followup = EmailFollowupStatus.find_by(
            candidate_id: @apply.candidate_id,
            dispatch_id: Dispatch.where(reference: @apply).select(:id)
          )

          unless followup
            return render json: { data: nil }, status: :ok
          end

          render json: {
            data: {
              id: followup.id,
              status: followup.status,
              attempt_count: followup.attempt_count,
              total_followups_sent: followup.attempt_count,
              last_followup_at: followup.last_attempt_at&.iso8601,
              first_sent_at: followup.created_at&.iso8601,
              next_attempt_at: followup.next_attempt_at&.iso8601,
              completed_at: followup.completed_at&.iso8601,
              stop_reason: followup.stop_reason
            }
          }, status: :ok
        end

        def tracking_events
          dispatch_ids = Dispatch.where(reference: @apply).select(:id)
          message_ids = DispatchMessage.where(dispatch_id: dispatch_ids, recipient_id: @apply.candidate_id)
                                       .select(:id)

          events = EmailTrackingEvent.where(dispatch_message_id: message_ids)
                                      .order(occurred_at: :desc)

          page = (params[:page] || 1).to_i
          per_page = [ (params[:per_page] || 50).to_i, 100 ].min
          total = events.count
          records = events.offset((page - 1) * per_page).limit(per_page)

          render json: {
            data: records.map { |e|
              {
                id: e.id,
                event_type: e.event_type,
                occurred_at: e.occurred_at&.iso8601,
                url_clicked: e.url_clicked,
                user_agent: e.user_agent
              }
            },
            meta: { total: total, page: page, per_page: per_page }
          }, status: :ok
        end

        private

        def set_apply
          @apply = Apply.find_by(id: params[:apply_id], account_id: @current_user.account_id)
          render_not_found("Apply") unless @apply
        end
      end
    end
  end
end
