# frozen_string_literal: true

module CollectionJob
  module AppliesJob
    class CreateCollectionFromListJob < ApplicationJob
      queue_as :critical
      sidekiq_options retry: 2, concurrency: 3

      def perform(collections_data, user_id, apply_data)
        collections_data = collections_data.with_indifferent_access if collections_data.respond_to?(:with_indifferent_access)
        apply_data = apply_data.with_indifferent_access if apply_data.respond_to?(:with_indifferent_access)

        account = User.find(user_id).account
        Apartment::Tenant.switch!(account.tenant)

        @user_id = user_id
        @job_id = apply_data[:job_id]
        @selective_process_id = apply_data[:selective_process_id]
        @selective_process = SelectiveProcess.find_by(id: @selective_process_id)
        @selective_process_name = @selective_process&.name
        @selective_process_status = apply_data[:selective_process_status]

        collections = collections_data[:collections] || []
        total = collections.size
        created = 0
        skipped = 0
        failed = 0
        created_applies = []

        Rails.logger.info "[CreateCollectionFromListJob] Starting processing #{total} items for SP##{@selective_process_id} (#{@selective_process_name})"

        broadcast_apply_collection_event("started", {
          total: total,
          message: "Iniciando processamento de #{total} candidatos"
        })

        collections.each_with_index do |collection_item, index|
          begin
            collection_item = collection_item.with_indifferent_access if collection_item.respond_to?(:with_indifferent_access)

            reference_type = collection_item[:reference_type]
            reference_id = collection_item[:reference_id]

            Rails.logger.info "[CreateCollectionFromListJob] Processing #{index + 1}/#{total}: #{reference_type}##{reference_id}"

            broadcast_apply_collection_event("processing_item", {
              current: index + 1,
              total: total,
              percent: ((index + 1) * 100.0 / total).round,
              reference_type: reference_type,
              reference_id: reference_id,
              message: "Processando item #{index + 1} de #{total}..."
            })

            candidate_id = extract_candidate_id_from_collection(collection_item, account.id)

            unless candidate_id
              Rails.logger.warn "[CreateCollectionFromListJob] Skipped #{reference_type}##{reference_id}: No candidate_id found"
              skipped += 1
            broadcast_apply_collection_event("item_skipped", {
              current: index + 1,
              total: total,
              created: created,
              skipped: skipped,
              percent: ((index + 1) * 100.0 / total).round,
              reason: "no_candidate",
              message: "Item ignorado: candidato não encontrado"
            })
            next
            end

          apply = Apply.find_or_create_apply(
            candidate_id: candidate_id,
            job_id: apply_data[:job_id],
            account_id: account.id,
            selective_process_id: apply_data[:selective_process_id],
            selective_process_status: apply_data[:selective_process_status],
            user_id: user_id
          )

          unless apply
            Rails.logger.warn "[CreateCollectionFromListJob] Failed to create apply for Candidate##{candidate_id}"
            failed += 1
            next
          end

          Rails.logger.info "[CreateCollectionFromListJob] Created/Found Apply##{apply.id} for Candidate##{candidate_id}"

          created += 1
          created_applies << apply

          candidate_name = apply.candidate&.name || apply.name

          broadcast_apply_collection_event("item_completed", {
            current: index + 1,
            total: total,
            created: created,
            skipped: skipped,
            percent: ((index + 1) * 100.0 / total).round,
            apply_id: apply.id,
            candidate_id: candidate_id,
            candidate_name: candidate_name,
            message: "Candidato #{candidate_name} adicionado",
            apply: serialize_apply(apply)
          })
        rescue StandardError => e
          Rails.logger.error "[CreateCollectionFromListJob] Error processing item #{index + 1}: #{e.message}"
          Rails.logger.error e.backtrace.first(5).join("\n")
          failed += 1
        end
        end

        Rails.logger.info "[CreateCollectionFromListJob] Completed: created=#{created}, skipped=#{skipped}, failed=#{failed}"

        broadcast_apply_collection_event("completed", {
          total: total,
          created: created,
          skipped: skipped,
          failed: failed,
          percent: 100,
          message: "Processamento concluído: #{created} candidatos adicionados",
          applies: created_applies.map { |a| serialize_apply(a) }
        })

        broadcast_progress(user_id, "completed", 100, created, total, skipped)
      rescue StandardError => e
        Rails.logger.error "[CreateCollectionFromListJob] Fatal error: #{e.message}"
        Rails.logger.error e.backtrace.first(10).join("\n")
        broadcast_apply_collection_event("error", { message: e.message })
        broadcast_error(user_id, e.message)
      end

      private

      def extract_candidate_id_from_collection(collection_item, account_id)
        candidate_id = collection_item[:candidate_id] || collection_item["candidate_id"]
        return candidate_id if candidate_id.present?

        reference_type = collection_item[:reference_type] || collection_item["reference_type"]
        reference_id = collection_item[:reference_id] || collection_item["reference_id"]

        return nil unless reference_type.present? && reference_id.present?

        case reference_type
        when "SourcedProfileSourcing"
          extract_from_sourced_profile_sourcing(reference_id, account_id)
        when "SourcedProfile"
          extract_from_sourced_profile(reference_id, account_id)
        when "Candidate"
          reference_id
        when "Apply"
          extract_from_apply(reference_id)
        else
          Rails.logger.warn "[CreateCollectionFromListJob] Unknown reference_type: #{reference_type}"
          nil
        end
      end

      def extract_from_sourced_profile_sourcing(reference_id, account_id)
        sourced_profile_sourcing = SourcedProfileSourcing.find_by(id: reference_id)
        return nil unless sourced_profile_sourcing

        sourced_profile = sourced_profile_sourcing.sourced_profile
        return nil unless sourced_profile

        ensure_candidate_exists(sourced_profile, account_id)
      end

      def extract_from_sourced_profile(reference_id, account_id)
        sourced_profile = SourcedProfile.find_by(id: reference_id)
        return nil unless sourced_profile

        ensure_candidate_exists(sourced_profile, account_id)
      end

      def extract_from_apply(reference_id)
        apply = Apply.find_by(id: reference_id)
        apply&.candidate_id
      end

      def ensure_candidate_exists(sourced_profile, account_id)
        return sourced_profile.candidate_id if sourced_profile.candidate_id.present?

        Rails.logger.info "[CreateCollectionFromListJob] Converting SourcedProfile##{sourced_profile.id} to Candidate"

        begin
          SourcedProfiles::ConvertToCandidateJob.perform_now([ sourced_profile.id ], account_id)
          sourced_profile.reload

          if sourced_profile.candidate_id.present?
            Rails.logger.info "[CreateCollectionFromListJob] Conversion successful - Candidate##{sourced_profile.candidate_id}"
            return sourced_profile.candidate_id
          end

          Rails.logger.warn "[CreateCollectionFromListJob] ConvertToCandidateJob did not create candidate, trying fallback"
          create_candidate_fallback(sourced_profile, account_id)
        rescue StandardError => e
          Rails.logger.error "[CreateCollectionFromListJob] ConvertToCandidateJob failed: #{e.message}"
          create_candidate_fallback(sourced_profile, account_id)
        end
      end

      def create_candidate_fallback(sourced_profile, account_id)
        email = extract_profile_email(sourced_profile)
        linkedin = sourced_profile.linkedin_url || sourced_profile.linkedin

        if email.blank? && linkedin.blank?
          Rails.logger.warn "[CreateCollectionFromListJob] Cannot create candidate without email or linkedin for SourcedProfile##{sourced_profile.id}"
          return nil
        end

        candidate = find_existing_candidate_by_identifiers(sourced_profile, account_id, email, linkedin)
        candidate ||= create_new_candidate(sourced_profile, account_id, email)

        return nil unless candidate&.persisted?

        sourced_profile.update(candidate_id: candidate.id)
        Rails.logger.info "[CreateCollectionFromListJob] Fallback created/found Candidate##{candidate.id} for SourcedProfile##{sourced_profile.id}"
        candidate.id
      rescue StandardError => e
        Rails.logger.error "[CreateCollectionFromListJob] Fallback failed for SourcedProfile##{sourced_profile.id}: #{e.message}"
        nil
      end

      def extract_profile_email(sourced_profile)
        return sourced_profile.email if sourced_profile.email.present?

        emails = sourced_profile.emails
        return nil unless emails.is_a?(Array) && emails.any?

        emails.first
      end

      def find_existing_candidate_by_identifiers(sourced_profile, account_id, email, linkedin)
        if email.present?
          found = Candidate.find_by(email: email, account_id: account_id)
          return found if found
        end

        return nil if linkedin.blank?

        Candidate.where(account_id: account_id)
                 .where("linkedin ILIKE ?", "%#{linkedin.split('/').last}%")
                 .first
      end

      def create_new_candidate(sourced_profile, account_id, email)
        Candidate.create!(
          account_id: account_id,
          name: sourced_profile.name || sourced_profile.full_name,
          email: email,
          phone: sourced_profile.phone,
          mobile_phone: sourced_profile.mobile_phone,
          linkedin: sourced_profile.linkedin_url || sourced_profile.linkedin,
          city: sourced_profile.city,
          state: sourced_profile.state,
          country: sourced_profile.country,
          current_company: sourced_profile.current_company,
          role_name: sourced_profile.current_title || sourced_profile.title,
          curriculum_text: sourced_profile.curriculum_text,
          self_introduction: sourced_profile.summary
        )
      rescue ActiveRecord::RecordInvalid => e
        Rails.logger.error "[CreateCollectionFromListJob] Failed to create candidate: #{e.message}"
        nil
      end

      def broadcast_progress(user_id, status, percent, created, total, skipped = 0)
        CollectionChannel.broadcast_to(
          "#{user_id}_collection",
          {
            status: status,
            percent: percent,
            created: created,
            skipped: skipped,
            total: total
          }
        )
      end

      def broadcast_error(user_id, message)
        CollectionChannel.broadcast_to(
          "#{user_id}_collection",
          {
            status: "error",
            message: message
          }
        )
      end

      def broadcast_apply_collection_event(event_type, data = {})
        base_data = {
          type: event_type,
          timestamp: Time.current.iso8601,
          job_id: @job_id,
          selective_process_id: @selective_process_id,
          selective_process_name: @selective_process_name,
          selective_process_status: @selective_process_status
        }

        payload = base_data.merge(data)

        stream_ids_for_broadcast.each do |stream_id|
          Rails.logger.info "[CreateCollectionFromListJob] Broadcasting #{event_type} to stream: #{stream_id}"
          ApplyCollectionChannel.broadcast_to(stream_id, payload)
        end
      end

      def stream_ids_for_broadcast
        base_stream = "#{@user_id}_apply_collection_#{@job_id}"
        streams = [ base_stream ]
        streams << "#{base_stream}_#{@selective_process_id}" if @selective_process_id.present?
        streams
      end

      def serialize_apply(apply)
        ApplySerializer.new(apply).serializable_hash.dig(:data, :attributes)
      end
    end
  end
end
