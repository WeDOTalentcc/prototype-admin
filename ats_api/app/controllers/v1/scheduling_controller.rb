# frozen_string_literal: true

module V1
  class SchedulingController < V1::Users::ApplicationController
    skip_before_action :authorize_request
    before_action :switch_tenant

    PLATFORM_LABELS = {
      "teams" => "Microsoft Teams",
      "microsoft_teams" => "Microsoft Teams",
      "google_meet" => "Google Meet",
      "zoom" => "Zoom"
    }.freeze

    def show
      link = SchedulingLink.find_by(token: params[:token])
      return render_not_found("SchedulingLink") unless link

      effective_status = link.expired? ? "expired" : link.status
      unless effective_status == "active"
        return render json: { status: effective_status }, status: :ok
      end

      slots = link.scheduling_slots.available.future.ordered

      render json: {
        token: link.token,
        status: effective_status,
        subject: link.subject,
        message: link.message,
        interview_type: link.interview_type,
        platform: link.platform,
        platform_label: PLATFORM_LABELS[link.platform] || link.platform,
        duration_minutes: link.duration_minutes,
        location: link.location,
        expires_at: link.expires_at&.iso8601,
        recruiter_name: link.created_by&.name,
        company_name: @account.name,
        job_title: link.job&.title,
        candidate_name: link.candidate&.name,
        slots: slots.map { |s| format_slot(s) }
      }, status: :ok
    end

    def book
      link = SchedulingLink.find_by(token: params[:token])
      return render_not_found("SchedulingLink") unless link
      return render_simple_error("Link is no longer available", status: :gone) unless link.bookable?

      service = ::Scheduling::BookingService.new(link: link)
      result = service.book(slot_id: params[:slot_id])

      if result.success?
        slot = result.data[:slot]
        render json: {
          status: "booked",
          subject: link.subject,
          start_time: slot.start_time.iso8601,
          end_time: slot.end_time.iso8601,
          join_url: result.data[:meeting]&.try(:join_url),
          platform: link.platform,
          recruiter_name: link.created_by&.name,
          company_name: @account.name
        }, status: :ok
      else
        render json: { success: false, errors: result.errors }, status: :unprocessable_entity
      end
    end

    private

    def switch_tenant
      @account = Account.find_by(uid: params[:account_uid])
      return render_not_found("Account") unless @account

      Apartment::Tenant.switch!(@account.tenant)
    end

    def format_slot(slot)
      local = slot.start_time.in_time_zone(Time.zone || "UTC")
      local_end = slot.end_time.in_time_zone(Time.zone || "UTC")

      {
        id: slot.id,
        start_time: slot.start_time.iso8601,
        end_time: slot.end_time.iso8601,
        date: local.strftime("%Y-%m-%d"),
        day_of_week: I18n.l(local, format: "%A"),
        start_hour: local.strftime("%H:%M"),
        end_hour: local_end.strftime("%H:%M")
      }
    end
  end
end
