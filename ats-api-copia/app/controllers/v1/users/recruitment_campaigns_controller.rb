# frozen_string_literal: true

module V1
  module Users
    class RecruitmentCampaignsController < ApplicationController
      before_action :set_campaign, only: %i[show update advance_stage complete_stage add_checkpoint]

      # GET /v1/users/recruitment_campaigns
      def index
        campaigns = scope_to_tenant(RecruitmentCampaign)
                    .includes(:campaign_stage_events)
                    .order(created_at: :desc)

        campaigns = campaigns.where(status: params[:status]) if params[:status].present?
        campaigns = campaigns.where(job_id: params[:job_id]) if params[:job_id].present?

        render json: RecruitmentCampaignSerializer.new(campaigns).serializable_hash, status: :ok
      end

      # GET /v1/users/recruitment_campaigns/:id
      def show
        render json: RecruitmentCampaignSerializer.new(@campaign).serializable_hash, status: :ok
      end

      # POST /v1/users/recruitment_campaigns
      def create
        campaign = RecruitmentCampaign.new(campaign_params)
        campaign.account_id = @current_account_id
        campaign.created_by_user = @current_user

        if campaign.save
          campaign.campaign_stage_events.create!(
            stage: "definition",
            event_type: "started",
            triggered_by: @current_user.id.to_s
          )
          campaign.broadcast_update!
          render json: RecruitmentCampaignSerializer.new(campaign).serializable_hash, status: :created
        else
          render_error(campaign)
        end
      end

      # PATCH /v1/users/recruitment_campaigns/:id
      def update
        if @campaign.update(campaign_params)
          @campaign.broadcast_update!
          render json: RecruitmentCampaignSerializer.new(@campaign).serializable_hash, status: :ok
        else
          render_error(@campaign)
        end
      end

      # POST /v1/users/recruitment_campaigns/:id/advance_stage
      def advance_stage
        if @campaign.advance_stage!
          render json: RecruitmentCampaignSerializer.new(@campaign.reload).serializable_hash, status: :ok
        else
          render_simple_error("Não é possível avançar — já na última etapa", status: :unprocessable_entity)
        end
      end

      # POST /v1/users/recruitment_campaigns/:id/complete_stage
      def complete_stage
        @campaign.complete_current_stage!(
          candidates_count: params[:candidates_count]&.to_i || 0,
          triggered_by: @current_user.id.to_s
        )
        render json: RecruitmentCampaignSerializer.new(@campaign.reload).serializable_hash, status: :ok
      end

      # POST /v1/users/recruitment_campaigns/:id/add_checkpoint
      def add_checkpoint
        message = params.require(:message)
        @campaign.add_checkpoint!(
          message,
          candidates_count: params[:candidates_count]&.to_i || 0
        )
        render json: { status: "checkpoint_added" }, status: :ok
      end

      private

      def set_campaign
        @campaign = scope_to_tenant(RecruitmentCampaign).find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Campanha")
      end

      def campaign_params
        params.require(:recruitment_campaign).permit(
          :name, :job_id, :talent_pool_id, :automation_level, :status,
          stages_config: {}, metadata: {}
        )
      end
    end
  end
end
