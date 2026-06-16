# frozen_string_literal: true

module V1
  module Users
    class SourcedProfilesController < ApplicationController
      include ResourceLoader
      include Pinnable

      before_action :set_resource, only: %i[show update]

      def index
        params[:where] = parse_json_param(params[:where])
        params[:where] ||= {}
        params[:where]["is_deleted"] = false if params[:where]["is_deleted"].nil?

        perform_search(
          model: SourcedProfile,
          serializer: SourcedProfileSerializer,
          search_with_pin: search_with_pin,
          compact: params[:compact]&.split(",") || []
        )
      end

      def stats
        start_date = params[:start_date]&.to_date || 30.days.ago.to_date
        end_date = params[:end_date]&.to_date || Date.current

        cache_key = "sourced_profiles_stats:#{@current_user.account_id}:#{start_date}:#{end_date}"
        data = Rails.cache.fetch(cache_key, expires_in: 10.minutes) do
          SourcedProfiles::StatsService.new(start_date: start_date, end_date: end_date).call
        end

        render json: data, status: :ok
      end

      def show
        @sourced_profile.mark_as_viewed!
        render_success(@sourced_profile, serializer: SourcedProfileSerializer)
      end

      def update
        params_to_update = inject_pin_and_confidential(sourced_profile_params, @sourced_profile)

        return render_error(@sourced_profile) unless @sourced_profile.update(params_to_update)

        render_success(@sourced_profile, serializer: SourcedProfileSerializer)
      end

      def import
        candidate = @current_user.account.candidates.find_by(
          external_id: @sourced_profile.external_id,
          external_provider: @sourced_profile.provider
        )

        created = candidate.nil?
        candidate = created ? create_candidate_from_profile : update_candidate_from_profile(candidate)

        @sourced_profile.update(candidate_id: candidate.id)

        render_success({
          message: created ? "Candidato importado" : "Candidato atualizado",
          candidate: CandidateSerializer.new(candidate).serializable_hash,
          created: created
        })
      end

      def similar
        profiles = @sourced_profile.similar_profiles(params[:limit] || 5)
        render_success(
          profiles.map { |p| SourcedProfileSerializer.new(p).serializable_hash }
        )
      end

      def convert_to_candidates
        if params[:select_all_params].present?
          CollectionJob::SourcedProfilesJob::ConvertToCandidatesCollectionJob.perform_later(
            select_all_params.to_h,
            @current_user.id
          )

          return render_success({
            status: "processing",
            message: "Conversão em lote iniciada em background"
          }, status: :accepted)
        end

        permitted_params = params.permit(sourced_profile_ids: [])
        sourced_profile_ids = Array(permitted_params[:sourced_profile_ids]).flatten.compact

        return render_simple_error("sourced_profile_ids ou select_all_params é obrigatório", status: :unprocessable_entity) if sourced_profile_ids.empty?

        ::SourcedProfiles::ConvertToCandidateJob.perform_later(
          sourced_profile_ids,
          @current_user.account_id
        )

        render_success({
          message: "Conversão iniciada em background",
          sourced_profile_ids: sourced_profile_ids,
          total: sourced_profile_ids.size
        }, status: :accepted)
      end

      private

      def set_resource
        @sourced_profile = @current_user.account.sourced_profiles.active.find(params[:id])
      end

      def resource_class
        SourcedProfile
      end

      def sourced_profile_params
        params.require(:sourced_profile).permit(
          :status, :rating, :internal_notes,
          :remote_work, :mobility,
          :clt_expectation, :pj_expectation, :freelance_expectation,
          tags: []
        )
      end

      def select_all_params
        params.require(:select_all_params).permit!
      end

      def create_candidate_from_profile
        @current_user.account.candidates.create!(
          name: @sourced_profile.full_name,
          email: @sourced_profile.email,
          phone: @sourced_profile.phone,
          cpf: @sourced_profile.cpf,
          date_birth: @sourced_profile.date_birth,
          gender: @sourced_profile.gender,
          marital_status: @sourced_profile.marital_status,
          city: @sourced_profile.city,
          state: @sourced_profile.state,
          external_id: @sourced_profile.external_id,
          external_provider: @sourced_profile.provider,
          linkedin_slug: @sourced_profile.linkedin_slug,
          external_profile_data: @sourced_profile.profile_data,
          source: "sourcing",
          pin_user_ids: @sourced_profile.pin_user_ids || [],
          confidential_user_ids: @sourced_profile.confidential_user_ids || []
        )
      end

      def update_candidate_from_profile(candidate)
        candidate.update!(
          name: @sourced_profile.full_name || candidate.name,
          email: @sourced_profile.email || candidate.email,
          phone: @sourced_profile.phone || candidate.phone,
          city: @sourced_profile.city || candidate.city,
          state: @sourced_profile.state || candidate.state,
          external_profile_data: @sourced_profile.profile_data
        )
        candidate
      end
    end
  end
end
