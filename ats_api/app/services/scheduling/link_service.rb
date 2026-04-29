# frozen_string_literal: true

module Scheduling
  class LinkService
    Result = Struct.new(:success?, :data, :errors, keyword_init: true)

    def initialize(user:)
      @user = user
      @account = user.account
    end

    def create(params)
      link = SchedulingLink.new(
        account: account,
        created_by: user,
        duration_minutes: params[:duration_minutes] || user.scheduling_setting&.default_duration_minutes || 60,
        interview_type: params[:interview_type],
        platform: params[:platform],
        location: params[:location],
        subject: params[:subject],
        message: params[:message],
        expires_at: params[:expires_at],
        apply_id: params[:apply_id],
        candidate_id: params[:candidate_id],
        job_id: params[:job_id],
        channels: params[:channels].presence || []
      )

      return failure(link.errors.full_messages) unless link.save

      generate_slots(link, params[:slots]) if params[:slots].present?

      Scheduling::InviteNotificationWorker.perform_async(link.id, account.id) if link.candidate_id.present?

      success(link.reload)
    end

    def update(link, params)
      return failure([ "Link is not active" ]) unless link.active?

      updatable = params.slice(:subject, :message, :location, :expires_at, :duration_minutes, :interview_type, :platform, :channels)
      return failure(link.errors.full_messages) unless link.update(updatable)

      if params[:slots].present?
        link.scheduling_slots.destroy_all
        generate_slots(link, params[:slots])
      end

      success(link.reload)
    end

    def cancel(link)
      return failure([ "Link is already cancelled" ]) if link.status == "cancelled"
      return failure([ "Link is already booked" ]) if link.booked?

      link.update!(status: SchedulingLink::STATUSES[:cancelled])
      success(link)
    end

    def list(filters = {})
      scope = SchedulingLink.where(created_by: user)
      scope = scope.where(status: filters[:status]) if filters[:status].present?
      scope = scope.where(job_id: filters[:job_id]) if filters[:job_id].present?
      scope = scope.where(apply_id: filters[:apply_id]) if filters[:apply_id].present?
      scope.order(created_at: :desc)
    end

    private

    attr_reader :user, :account

    def generate_slots(link, slots_data)
      slots_data.each do |slot|
        link.scheduling_slots.create!(
          start_time: slot[:start_time],
          end_time: slot[:end_time],
          is_available: true
        )
      end
    end

    def success(data)
      Result.new(success?: true, data: data, errors: [])
    end

    def failure(errors)
      Result.new(success?: false, data: nil, errors: errors)
    end
  end
end
