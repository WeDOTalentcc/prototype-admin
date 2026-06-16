module V1
  module Users
    module SourcedProfiles
      class ContactEnrichmentController < ApplicationController
        before_action :set_sourced_profile

        def enrich_emails
          result = ::Pearch::ContactEnrichmentService.new(
            sourced_profile: @sourced_profile,
            user: @current_user,
            enrich_emails: true,
            enrich_phones: false,
            require_phones_or_emails: require_phones_or_emails_param
          ).enrich!

          return render_enrichment_error(result) unless result[:success]

          render json: {
            success: true,
            emails: @sourced_profile.emails,
            emails_found: result[:emails_found],
            credits_used: result[:credits_used]
          }, status: :ok
        end

        def enrich_phones
          result = ::Pearch::ContactEnrichmentService.new(
            sourced_profile: @sourced_profile,
            user: @current_user,
            enrich_emails: false,
            enrich_phones: true,
            require_phones_or_emails: require_phones_or_emails_param
          ).enrich!

          return render_enrichment_error(result) unless result[:success]

          render json: {
            success: true,
            phones: @sourced_profile.phones,
            phones_found: result[:phones_found],
            credits_used: result[:credits_used]
          }, status: :ok
        end

        def enrich_both
          result = ::Pearch::ContactEnrichmentService.new(
            sourced_profile: @sourced_profile,
            user: @current_user,
            enrich_emails: true,
            enrich_phones: true,
            require_phones_or_emails: require_phones_or_emails_param
          ).enrich!

          return render_enrichment_error(result) unless result[:success]

          render json: {
            success: true,
            emails: @sourced_profile.emails,
            phones: @sourced_profile.phones,
            emails_found: result[:emails_found],
            phones_found: result[:phones_found],
            credits_used: result[:credits_used]
          }, status: :ok
        end

        private

        def set_sourced_profile
          @sourced_profile = @current_user.account.sourced_profiles.active.find(params[:id])
        end

        def require_phones_or_emails_param
          return true unless params.key?(:require_phones_or_emails)

          ActiveModel::Type::Boolean.new.cast(params[:require_phones_or_emails])
        end

        def render_enrichment_error(result)
          status = result[:error].include?("Insufficient credits") ? :payment_required : :unprocessable_entity

          render json: {
            success: false,
            error: result[:error],
            current_balance: @current_user.account.pearch_credits
          }, status: status
        end
      end
    end
  end
end
