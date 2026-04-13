# frozen_string_literal: true

module V1
  module Users
    class TalentPoolsController < ApplicationController
      before_action :set_talent_pool, only: %i[show update destroy candidates add_candidates
                                               move_to_job create_job_from_pool]

      # GET /v1/users/talent_pools
      def index
        pools = scope_to_tenant(TalentPool).order(created_at: :desc)
        pools = pools.where(status: params[:status]) if params[:status].present?
        render json: TalentPoolSerializer.new(pools).serializable_hash, status: :ok
      end

      # GET /v1/users/talent_pools/:id
      def show
        render json: TalentPoolSerializer.new(@talent_pool).serializable_hash, status: :ok
      end

      # POST /v1/users/talent_pools
      def create
        pool = TalentPool.new(talent_pool_params)
        pool.account_id = @current_account_id
        pool.created_by_user = @current_user

        if pool.save
          render json: TalentPoolSerializer.new(pool).serializable_hash, status: :created
        else
          render_error(pool)
        end
      end

      # PATCH /v1/users/talent_pools/:id
      def update
        if @talent_pool.update(talent_pool_params)
          render json: TalentPoolSerializer.new(@talent_pool).serializable_hash, status: :ok
        else
          render_error(@talent_pool)
        end
      end

      # DELETE /v1/users/talent_pools/:id
      def destroy
        @talent_pool.update!(status: "archived")
        render_no_content
      end

      # GET /v1/users/talent_pools/:id/candidates
      def candidates
        tpcs = @talent_pool.talent_pool_candidates
                           .includes(:candidate)
                           .order(created_at: :desc)

        tpcs = tpcs.by_stage(params[:stage]) if params[:stage].present?
        tpcs = tpcs.not_moved if params[:exclude_moved] == "true"

        render json: TalentPoolCandidateSerializer.new(tpcs).serializable_hash, status: :ok
      end

      # POST /v1/users/talent_pools/:id/candidates
      def add_candidates
        candidate_ids = params.require(:candidate_ids)
        origin = params[:origin] || "manual"

        added = []
        candidate_ids.each do |cid|
          tpc = @talent_pool.talent_pool_candidates.find_or_initialize_by(candidate_id: cid)
          next unless tpc.new_record?

          tpc.origin = origin
          tpc.stage = "discovered"
          tpc.save!
          added << tpc
        end

        @talent_pool.update_counters!
        render json: { added_count: added.size, total: @talent_pool.candidates_count }, status: :ok
      end

      # POST /v1/users/talent_pools/:id/move_to_job
      def move_to_job
        job_id = params.require(:job_id)
        target_stage = params.require(:target_stage)
        candidate_ids = params.require(:candidate_ids)

        job = scope_to_tenant(Job).find(job_id)

        moved = []
        candidate_ids.each do |cid|
          tpc = @talent_pool.talent_pool_candidates.find_by(candidate_id: cid)
          next unless tpc && !tpc.moved?

          tpc.move_to_job!(job.id, target_stage)

          # Create apply in the job pipeline at the target stage
          # Map target_stage to SelectiveProcess status enum
          stage_map = { "screening" => :screening, "interview" => :interview, "hired" => :hired }
          sp_status = stage_map[target_stage]
          selective_process = sp_status ? job.selective_processes.find_by(status: sp_status) : job.selective_processes.find_by(name: target_stage)
          if selective_process
            Apply.find_or_create_by!(
              candidate_id: cid,
              job_id: job.id,
              selective_process_id: selective_process.id
            )
          end

          moved << cid
        end

        @talent_pool.update_counters!
        render json: { moved_count: moved.size, job_id: job.id, target_stage: target_stage }, status: :ok
      end

      # POST /v1/users/talent_pools/:id/create_job_from_pool
      def create_job_from_pool
        profile = @talent_pool.ideal_profile
        render_simple_error("Pool sem arquétipo vinculado", status: :unprocessable_entity) and return unless profile

        job = Job.new(
          title: profile.name,
          description: profile.description,
          account_id: @current_account_id,
          user_id: @current_user.id,
          status: "draft",
          seniority_level: profile.seniority_level,
          technical_requirements: profile.technical_requirements,
          behavioral_competencies: profile.behavioral_requirements,
          screening_questions: @talent_pool.screening_questions
        )

        if job.save
          render json: { job_id: job.id, title: job.title, status: "draft" }, status: :created
        else
          render_error(job)
        end
      end

      private

      def set_talent_pool
        @talent_pool = scope_to_tenant(TalentPool).find(params[:id])
      rescue ActiveRecord::RecordNotFound
        render_not_found("Banco de Talentos")
      end

      def talent_pool_params
        params.require(:talent_pool).permit(
          :name, :description, :status, :ideal_profile_id,
          :agent_sourcing_enabled, :screening_approved,
          screening_questions: [:question, :ideal_answer, :weight, :competency],
          screening_config: {},
          agent_config: {}
        )
      end
    end
  end
end
