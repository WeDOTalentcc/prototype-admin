# frozen_string_literal: true

module V1
  module Users
    module BackgroundAgents
      class SearchesController < BaseController
        before_action :require_service_token
        before_action :set_background_agent

        def pearch
          query = params[:query]
          return render_simple_error("query is required", status: :unprocessable_entity) if query.blank?

          account = @background_agent.account
          user = @background_agent.user
          limit = [params[:limit]&.to_i || 10, 30].min

          unless account.pearch_credits.positive?
            return render json: {
              success: false, error: "insufficient_credits",
              current_balance: account.pearch_credits
            }, status: :payment_required
          end

          search_params = {
            search_profile: "fast",
            limit: limit,
            parse_query: params.fetch(:parse_query, "true"),
            show_emails: true,
          }

          if params[:custom_filters].present?
            params[:custom_filters].each do |key, value|
              search_params[key.to_sym] = value
            end
          end

          if params[:docid_blacklist].present?
            search_params[:docid_blacklist] = Array(params[:docid_blacklist])
          end

          result = Pearch::TalentSearchExecutorService.new(
            user: user,
            query: query,
            params: search_params.with_indifferent_access
          ).call

          render json: result
        rescue StandardError => e
          Rails.logger.error("[BackgroundAgent:#{@background_agent.id}] Pearch search failed: #{e.message}")
          render json: { success: false, error: e.message }, status: :internal_server_error
        end

        def linkedin
          query = params[:query]
          return render_simple_error("query is required", status: :unprocessable_entity) if query.blank?

          account = @background_agent.account
          user = @background_agent.user

          sourcing = account.sourcings.create!(
            user: user,
            uid: SecureRandom.uuid,
            provider: "linkedin",
            query: query,
            status: "processing",
            searched_at: Time.current
          )

          search_params = build_linkedin_search_params(query)

          result = Apify::LinkedinSearchExecutorService.new(
            user: user,
            sourcing: sourcing,
            params: search_params
          ).call

          unless result[:success]
            return render json: result, status: :unprocessable_entity
          end

          profiles = sourcing.sourced_profile_sourcings
            .includes(:sourced_profile)
            .map { |sps| serialize_linkedin_profile(sps.sourced_profile) }

          render json: {
            success: true,
            sourcing_id: sourcing.id,
            profiles_count: profiles.size,
            total_found: result[:total_found],
            profiles: profiles
          }
        rescue StandardError => e
          Rails.logger.error("[BackgroundAgent:#{@background_agent.id}] LinkedIn search failed: #{e.message}")
          render json: { success: false, error: e.message }, status: :internal_server_error
        end

        def semantic
          ideal_cv_text = params[:ideal_cv_text]
          return render_simple_error("ideal_cv_text is required", status: :unprocessable_entity) if ideal_cv_text.blank?

          limit = [params[:limit]&.to_i || 50, 100].min
          exclude_ids = Array(params[:exclude_candidate_ids]).map(&:to_i)

          query_vector = Embeddings::Encoder.call(ideal_cv_text)

          results = Embedding
            .for_candidates
            .nearest_neighbors(:embedding, query_vector, distance: "cosine")
            .limit(limit + exclude_ids.size)

          candidate_distances = results.map { |e| [e.reference_id, e.neighbor_distance] }.to_h
          candidate_ids = candidate_distances.keys - exclude_ids
          candidate_ids = candidate_ids.first(limit)

          candidates = Candidate
            .where(id: candidate_ids, is_deleted: false)
            .includes(:skills)

          profiles = candidates.map do |c|
            {
              id: c.id,
              name: c.name,
              title: c.role_name,
              company: c.current_company,
              city: c.city,
              state: c.state,
              country: c.country,
              skills: c.skills.map(&:name),
              linkedin: c.linkedin,
              bio: c.self_introduction&.truncate(500),
              position_level: c.position_level,
              total_experience_years: c.total_experience_years,
              remote_work: c.remote_work,
              similarity_score: (1.0 - candidate_distances[c.id]).round(4),
              source_provider: "semantic",
            }
          end

          profiles.sort_by! { |p| -p[:similarity_score] }

          render json: {
            success: true,
            total_found: profiles.size,
            profiles: profiles,
          }
        rescue StandardError => e
          Rails.logger.error("[BackgroundAgent:#{@background_agent.id}] Semantic search failed: #{e.class} #{e.message}")
          render json: { success: false, error: "Semantic search failed" }, status: :internal_server_error
        end

        private

        def build_linkedin_search_params(query)
          search_params = {
            query: query,
            locations: Array(params[:locations].presence || ["Brazil"]),
            mode: params.fetch(:mode, "full_with_email").to_s,
            take_pages: [params.fetch(:take_pages, 1).to_i, 4].min,
            max_items: [params.fetch(:limit, 25).to_i, 50].min
          }

          %i[current_job_titles past_job_titles industries years_of_experience
             exclude_current_companies exclude_locations exclude_current_job_titles].each do |key|
            search_params[key] = Array(params[key]) if params[key].present?
          end

          %i[seniority_levels functions].each do |key|
            search_params[key] = Array(params[key]).map(&:to_s) if params[key].present?
          end

          search_params[:profile_languages] = Array(params[:profile_languages]) if params[:profile_languages].present?
          search_params[:recently_changed_jobs] = params[:recently_changed_jobs] if params.key?(:recently_changed_jobs)

          search_params
        end

        def serialize_linkedin_profile(sp)
          {
            id: sp.id,
            external_id: sp.external_id,
            name: sp.name,
            first_name: sp.first_name,
            last_name: sp.last_name,
            title: sp.title,
            current_company: sp.current_company,
            current_title: sp.current_title,
            linkedin_url: sp.linkedin_url,
            linkedin_slug: sp.linkedin_slug,
            city: sp.city,
            state: sp.state,
            country: sp.country,
            location: sp.location,
            total_experience_years: sp.total_experience_years,
            skills_data: sp.skills_data,
            languages_data: sp.languages_data,
            summary: sp.summary,
            followers_count: sp.followers_count,
            connections_count: sp.connections_count,
            picture_url: sp.picture_url,
            experiences_data: sp.experiences_data,
            educations_data: sp.educations_data,
            certifications_data: sp.certifications_data,
            profile_data: sp.profile_data
          }
        end
      end
    end
  end
end
