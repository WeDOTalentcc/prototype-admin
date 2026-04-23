# frozen_string_literal: true

module CollectionJob
  module AppliesJob
    class CreateCollectionJob < ApplicationJob
      include AtsSyncable

      queue_as :critical
      sidekiq_options retry: false

      def perform(select_all_params, user_id, apply_collection_params)
        account = User.find(user_id).account
        Apartment::Tenant.switch!(account.tenant)

        @user_id = user_id
        @job_id = apply_collection_params[:job_id]
        @selective_process_id = apply_collection_params[:selective_process_id]

        page = 1
        first_record = CollectionService.call(select_all_params, page)
        total_page = (first_record[:total_count] / 30) + 1
        total_records = first_record[:total_count]
        created = 0
        skipped = 0
        created_applies = []

        broadcast_apply_collection_event("started", {
          total: total_records,
          job_id: @job_id,
          selective_process_id: @selective_process_id
        })

        while page <= total_page
          CollectionService.call(select_all_params, page)[:records].each do |record|
            next if record.is_deleted

            candidate_id = resolve_candidate_id(record, select_all_params, account)

            if candidate_id.blank?
              skipped += 1
              next
            end

            apply = Apply.find_or_create_apply(
              candidate_id: candidate_id,
              job_id: apply_collection_params[:job_id],
              account_id: account.id,
              selective_process_id: apply_collection_params[:selective_process_id],
              selective_process_status: apply_collection_params[:selective_process_status],
              user_id: user_id
            )

            apply.update(
              selective_process_id: apply_collection_params[:selective_process_id],
              selective_process_status: apply_collection_params[:selective_process_status]
            )
            apply.save!

            sync_apply_to_ats(apply)
            created += 1
            created_applies << apply

            broadcast_apply_collection_event("item_completed", {
              current: created + skipped,
              total: total_records,
              created: created,
              skipped: skipped,
              percent: (((created + skipped) * 100.0) / [ total_records, 1 ].max).round,
              apply_id: apply.id,
              candidate_id: candidate_id,
              apply: serialize_apply(apply)
            })
          end

          CollectionChannel.broadcast_to("#{user_id}_collection", {
            status: "loading",
            percent: page * 100 / total_page
          })

          page += 1
        end

        broadcast_apply_collection_event("completed", {
          total: total_records,
          created: created,
          skipped: skipped,
          percent: 100,
          applies: created_applies.map { |a| serialize_apply(a) }
        })

        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "completed",
          percent: 100
        })
      end

      private

      def resolve_candidate_id(record, select_all_params, account)
        reference_type = select_all_params[:reference_type].to_s
        sourced_type = reference_type.casecmp("SourcedProfileSourcing").zero? ||
                       reference_type.downcase == "sourced_profile_sourcings"

        return resolve_sourced_candidate(record, account) if sourced_type

        reference_type == "applies" ? record.candidate_id : record.id
      end

      def resolve_sourced_candidate(record, account)
        sourced_profile = record.respond_to?(:sourced_profile) ? record.sourced_profile : nil
        return nil unless sourced_profile

        return sourced_profile.candidate_id if sourced_profile.candidate_id.present?

        Rails.logger.info "[CreateCollectionJob] Converting SourcedProfile##{sourced_profile.id} to Candidate"

        begin
          SourcedProfiles::ConvertToCandidateJob.perform_now([ sourced_profile.id ], account.id)
          sourced_profile.reload

          if sourced_profile.candidate_id.present?
            candidate = Candidate.find_by(id: sourced_profile.candidate_id)
            sync_candidate_to_ats(candidate) if candidate.present?
            Rails.logger.info "[CreateCollectionJob] Conversion successful - Candidate##{sourced_profile.candidate_id}"
            return sourced_profile.candidate_id
          end

          Rails.logger.warn "[CreateCollectionJob] ConvertToCandidateJob did not create candidate for SourcedProfile##{sourced_profile.id}"
        rescue StandardError => e
          Rails.logger.error "[CreateCollectionJob] ConvertToCandidateJob failed: #{e.message}"
        end

        nil
      end

      def broadcast_apply_collection_event(event_type, data = {})
        ApplyCollectionChannel.broadcast_to(
          apply_collection_stream_id,
          { type: event_type, timestamp: Time.current.iso8601 }.merge(data)
        )
      end

      def apply_collection_stream_id
        parts = [ @user_id, "apply_collection", @job_id ]
        parts << @selective_process_id if @selective_process_id.present?
        parts.join("_")
      end

      def serialize_apply(apply)
        ApplySerializer.new(apply).serializable_hash.dig(:data, :attributes)
      end
    end
  end
end
