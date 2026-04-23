# frozen_string_literal: true

module AppliesJob
  class AddAppliesFromListJob < ApplicationJob
    queue_as :default
    sidekiq_options retry: false

    def perform(list_id, job_id, selective_process_id, user_id, account_id)
      account = Account.find(account_id)
      Apartment::Tenant.switch!(account.tenant)

      list = List.find_by(id: list_id, account_id: account_id)
      return unless list

      job = Job.find_by(id: job_id, account_id: account_id)
      return unless job

      selective_process = SelectiveProcess.find_by(id: selective_process_id)
      selective_process_status = selective_process&.status

      list_relationships = ListRelationship.where(
        list_id: list_id,
        account_id: account_id,
        is_deleted: false
      )

      list_relationships.find_each do |list_relationship|
        process_list_relationship(
          list_relationship,
          job_id,
          selective_process_id,
          selective_process_status,
          user_id,
          account_id
        )
      end
    rescue => e
      Rails.logger.error("AddAppliesFromListJob failed: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
      raise
    end

    private

    def process_list_relationship(list_relationship, job_id, selective_process_id, selective_process_status, user_id, account_id)
      candidate_id = extract_candidate_id(list_relationship, account_id)
      return unless candidate_id

      Apply.find_or_create_apply(
        candidate_id: candidate_id,
        job_id: job_id,
        account_id: account_id,
        selective_process_id: selective_process_id,
        selective_process_status: selective_process_status,
        user_id: user_id
      )
    rescue => e
      Rails.logger.error("Failed to create apply for list_relationship #{list_relationship.id}: #{e.message}")
    end

    def extract_candidate_id(list_relationship, account_id)
      case list_relationship.reference_type
      when "Candidate"
        list_relationship.reference_id
      when "SourcedProfileSourcing"
        extract_candidate_from_sourced_profile_sourcing(list_relationship, account_id)
      else
        nil
      end
    end

    def extract_candidate_from_sourced_profile_sourcing(list_relationship, account_id)
      sourced_profile_sourcing = SourcedProfileSourcing.find_by(
        id: list_relationship.reference_id,
        account_id: account_id
      )
      return nil unless sourced_profile_sourcing

      sourced_profile = sourced_profile_sourcing.sourced_profile
      return nil unless sourced_profile

      if sourced_profile.candidate_id.blank?
        SourcedProfiles::ConvertToCandidateJob.perform_later(
          [ sourced_profile.id ],
          account_id
        )
        sourced_profile.reload
      end

      sourced_profile.candidate_id
    end
  end
end
