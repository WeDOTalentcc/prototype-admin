# frozen_string_literal: true

module Dispatches
  class CreateService
    attr_reader :dispatch

    VALID_TARGETS = %w[ids reference search].freeze

    def initialize(user:, account:, params:)
      @user    = user
      @account = account
      @params  = params.deep_dup
      @dispatch = nil
    end


    def call
      Apartment::Tenant.switch!(@account.tenant)
      ActiveRecord::Base.transaction do
        build_dispatch
        return fail_with(:base, "Canal inválido") unless channel_type_present?
        return fail_with(:base, "target_type inválido") unless VALID_TARGETS.include?(@dispatch.target_type)
        target_validators.fetch(@dispatch.target_type).call
        @dispatch.account_id = @account.id
        @dispatch.save!
      rescue ActiveRecord::RecordInvalid => e
        @dispatch ||= Dispatch.new
        @dispatch.errors.add(:base, e.message)
        return false
      end
      enqueue_orchestrator
    end

    private

   def build_dispatch
      @dispatch = @user.dispatches.new(dispatch_attributes)
      @dispatch.status = :pending
      @dispatch.target_type ||= "ids"
      @dispatch.target_payload ||= {}
    end

    def dispatch_attributes
      attrs = @params.fetch(:dispatch, @params)
      attrs.except(:candidate_ids, :user_ids)
    end

    def candidate_ids
      attrs = @params.fetch(:dispatch, @params)

      @candidate_ids ||= Array(attrs[:candidate_ids])
                              .select { |id| id.is_a?(Integer) || id.to_s =~ /\A\d+\z/ }
                              .map(&:to_i).uniq
    end

    def user_ids
      attrs = @params.fetch(:dispatch, @params)

      @user_ids ||= Array(attrs[:user_ids])
                         .select { |id| id.is_a?(Integer) || id.to_s =~ /\A\d+\z/ }
                         .map(&:to_i).uniq
    end

    def channel_type_present?
      @dispatch.channel_type.present?
    end

    def valid_candidate_ids?
      return true if candidate_ids.empty?

      @account.candidates.where(id: candidate_ids).count == candidate_ids.size
    end

    def valid_user_ids?
      return true if user_ids.empty?

      @account.users.where(id: user_ids).count == user_ids.size
    end

    def reference_candidates?
      ref = @dispatch.reference
      ref.respond_to?(:candidates) && ref.candidates.exists?
    end

    def reference_users?
      ref = @dispatch.reference
      ref.respond_to?(:users) && ref.users.exists?
    end

    def valid_search_payload?
      p = @dispatch.target_payload || {}
      has_searchkick_candidate = defined?(Searchkick) && Candidate.respond_to?(:search)
      has_searchkick_user = defined?(Searchkick) && User.respond_to?(:search)
      has_searchkick = has_searchkick_candidate || has_searchkick_user
      has_searchkick && (p["query"].present? || (p["where"].is_a?(Hash) && p["where"].any?))
    end

    def enqueue_orchestrator
      opts = build_enqueue_options
      schedule_time = @dispatch.scheduled_for

      if schedule_time && schedule_time > Time.current
        return DispatchOrchestratorJob.set(wait_until: schedule_time).perform_later(@dispatch.id, opts, account_id: @account.id)
      end
      DispatchOrchestratorJob.perform_later(@dispatch.id, opts, account_id: @account.id)
    end

    def build_enqueue_options
      opts = {}
      opts["candidate_ids"] = candidate_ids if @dispatch.target_type == "ids" && candidate_ids.any?
      opts["user_ids"] = user_ids if @dispatch.target_type == "ids" && user_ids.any?
      opts["search"] = @dispatch.target_payload if @dispatch.target_type == "search"
      opts
    end

    def target_validators
      @target_validators ||= {
        "ids" => -> {
          has_candidates = candidate_ids.any?
          has_users = user_ids.any?

          fail_with(:base, "Sem candidatos ou usuários informados") unless has_candidates || has_users
          fail_with(:base, "Candidatos inválidos para a conta") if has_candidates && !valid_candidate_ids?
          fail_with(:base, "Usuários inválidos para a conta") if has_users && !valid_user_ids?
        },
        "reference" => -> {
          has_candidates = reference_candidates?
          has_users = reference_users?
          fail_with(:base, "Referência sem candidatos ou usuários") unless has_candidates || has_users
        },
        "search" => -> { fail_with(:base, "Payload de busca inválido") unless valid_search_payload? }
      }
    end

    def fail_with(attr, message)
      @dispatch.errors.add(attr, message)
      raise ActiveRecord::RecordInvalid.new(@dispatch)
    end
  end
end
