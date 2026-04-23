# frozen_string_literal: true

module Pearch
  class SearchProfilesBuilder
    PROFILES = {
      fast: -> {
        {
          type: "fast",
          insights: false,
          profile_scoring: false,
          high_freshness: false,
          limit: 10
        }
      },
      balanced: -> {
        {
          type: "fast",
          insights: false,
          profile_scoring: false,
          high_freshness: false,
          limit: 10
        }
      },
      premium: -> {
        {
          type: "pro",
          insights: true,
          profile_scoring: false,
          high_freshness: false,
          limit: 10
        }
      }
    }.freeze

    DEFAULT_PROFILE = :balanced

    def self.build(params)
      new(params).build
    end

    def initialize(params)
      @params = params
    end

    def build
      base_options = custom_mode? ? custom_options : profile_options

      final_options = merge_optional_params(base_options)


      final_options
    end

    private

    attr_reader :params

    def custom_mode?
      params[:type].present?
    end

    def profile_options
      profile_name = (params[:search_profile]&.to_sym || DEFAULT_PROFILE)
      profile_lambda = PROFILES[profile_name] || PROFILES[DEFAULT_PROFILE]

      profile_lambda.call.merge(common_options)
    end

    def custom_options
      {
        type: params[:type] || "fast",
        insights: parse_boolean(:insights, false),
        profile_scoring: parse_boolean(:profile_scoring, false),
        high_freshness: parse_boolean(:high_freshness, false),
        limit: calculate_limit,
        offset: params[:offset]&.to_i || 0
      }.merge(common_options)
    end

    def common_options
      {
        strict_filters: parse_boolean(:strict_filters, false)
      }
    end

    def merge_optional_params(options)
      options.tap do |opts|
        opts[:thread_id] = params[:thread_id] if params[:thread_id].present?
        opts[:custom_filters] = build_custom_filters
        opts[:docid_blacklist] = params[:docid_blacklist] if params[:docid_blacklist].present?
        opts[:limit] = calculate_limit if params[:limit].present?
        opts[:offset] = params[:offset].to_i if params[:offset].present?

        opts[:reveal_emails] = parse_boolean(:show_emails, false) || parse_boolean(:reveal_emails, false)
        opts[:reveal_phones] = parse_boolean(:show_phone_numbers, false) || parse_boolean(:reveal_phones, false)

        if parse_boolean(:has_email, false)
          opts[:filter_out_no_emails] = true
        else
          opts[:filter_out_no_emails] = parse_boolean(:filter_out_no_emails, false) ||
                                         parse_boolean(:require_emails, false)
        end

        if parse_boolean(:has_phone, false)
          opts[:filter_out_no_phones] = true
        else
          opts[:filter_out_no_phones] = parse_boolean(:filter_out_no_phones, false) ||
                                         parse_boolean(:require_phone_numbers, false)
        end

        if parse_boolean(:has_email_or_phone, false)
          opts[:filter_out_no_phones_or_emails] = true
        else
          opts[:filter_out_no_phones_or_emails] = parse_boolean(:filter_out_no_phones_or_emails, false) ||
                                                   parse_boolean(:require_phones_or_emails, false)
        end
      end
    end

    def calculate_limit
      requested_limit = params[:limit]&.to_i
      pool_size = 150
      min_limit = 5
      default_limit = 10

      return default_limit if requested_limit.nil? || requested_limit <= 0

      requested_limit.clamp(min_limit, pool_size)
    end

    def parse_boolean(key, default)
      value = params[key]
      return default if value.nil?
      ActiveModel::Type::Boolean.new.cast(value)
    end

    def build_custom_filters
      base_filters = parse_custom_filters
      auto_filters = extract_automatic_filters

      merged = merge_filters(base_filters, auto_filters)

      merged
    end

    def extract_automatic_filters
      filters = {}

      current_job_titles = find_current_job_titles

      if current_job_titles.present?
        filters[:titles] = Array(current_job_titles).map(&:to_s)

        scope = find_current_job_title_scope
      end

      companies = find_companies
      if companies.present?
        filters[:companies] = Array(companies).map(&:to_s)
      end

      excluded_companies = find_excluded_companies
      if excluded_companies.present?
        filters[:excluded_companies] = Array(excluded_companies).map(&:to_s)
      end

      company_sectors = find_company_sectors
      if company_sectors.present?
        filters[:industries] = Array(company_sectors).map(&:to_s)
      end

      universities = find_universities
      if universities.present?
        filters[:universities] = Array(universities).map(&:to_s)
      end

      study_areas = find_study_areas
      if study_areas.present?
        filters[:keywords] ||= []
        filters[:keywords] += Array(study_areas).map(&:to_s)
      end

      academic_degrees = find_academic_degrees
      if academic_degrees.present?
        filters[:degrees] = Array(academic_degrees).map(&:to_s)
      end

      skills_and_categories = find_skills_and_categories
      if skills_and_categories.present?
        filters[:keywords] ||= []
        filters[:keywords] += Array(skills_and_categories).map(&:to_s)
      end

      languages = find_languages
      if languages.present?
        filters[:languages] = Array(languages).map(&:to_s)
      end

      filters
    end

    def find_current_job_titles
      params[:current_job_titles] ||
      params.dig(:where, :current_job_titles) ||
      params.dig(:where, "current_job_titles") ||
      params.dig("where", :current_job_titles) ||
      params.dig("where", "current_job_titles")
    end

    def find_current_job_title_scope
      params[:current_job_title_scope] ||
      params.dig(:where, :current_job_title_scope) ||
      params.dig(:where, "current_job_title_scope") ||
      params.dig("where", :current_job_title_scope) ||
      params.dig("where", "current_job_title_scope") ||
      "current_and_history" # default
    end

    def find_companies
      companies_param = params[:companies] ||
                       params.dig(:where, :companies) ||
                       params.dig(:where, "companies") ||
                       params.dig("where", :companies) ||
                       params.dig("where", "companies")

      return nil if companies_param.blank?

      if companies_param.is_a?(Hash)
        companies_param[:values] || companies_param["values"]
      else
        companies_param
      end
    end

    def find_excluded_companies
      excluded_param = params[:excluded_companies] ||
                      params.dig(:where, :excluded_companies) ||
                      params.dig(:where, "excluded_companies") ||
                      params.dig("where", :excluded_companies) ||
                      params.dig("where", "excluded_companies")

      return nil if excluded_param.blank?

      if excluded_param.is_a?(Hash)
        excluded_param[:values] || excluded_param["values"]
      else
        excluded_param
      end
    end

    def find_company_sectors
      sectors_param = params[:company_sectors] ||
                     params.dig(:where, :company_sectors) ||
                     params.dig(:where, "company_sectors") ||
                     params.dig("where", :company_sectors) ||
                     params.dig("where", "company_sectors")

      return nil if sectors_param.blank?

      if sectors_param.is_a?(Hash)
        sectors_param[:values] || sectors_param["values"]
      else
        sectors_param
      end
    end

    def find_universities
      universities_param = params[:universities] ||
                          params.dig(:where, :universities) ||
                          params.dig(:where, "universities") ||
                          params.dig("where", :universities) ||
                          params.dig("where", "universities")

      return nil if universities_param.blank?

      Array(universities_param)
    end

    def find_study_areas
      study_areas_param = params[:study_areas] ||
                         params.dig(:where, :study_areas) ||
                         params.dig(:where, "study_areas") ||
                         params.dig("where", :study_areas) ||
                         params.dig("where", "study_areas")

      return nil if study_areas_param.blank?

      if study_areas_param.is_a?(Hash)
        study_areas_param[:values] || study_areas_param["values"]
      else
        Array(study_areas_param)
      end
    end

    def find_academic_degrees
      degree_param = params[:academic_degree] ||
                    params.dig(:where, :academic_degree) ||
                    params.dig(:where, "academic_degree") ||
                    params.dig("where", :academic_degree) ||
                    params.dig("where", "academic_degree")

      return nil if degree_param.blank?

      if degree_param.is_a?(Hash)
        scope = degree_param[:scope] || degree_param["scope"] || "min"
        value = degree_param[:value] || degree_param["value"]

        if value.present?
          normalized_value = normalize_degree_value_for_search(value)

          if scope == "min"
            hierarchy = {
              "high school" => 1,
              "technical" => 2,
              "online course" => 3,
              "bachelors" => 4,
              "postgraduate" => 5,
              "masters" => 6,
              "doctorate" => 7,
              "phd" => 8
            }

            min_level = hierarchy[normalized_value]

            if min_level
              internal_levels = hierarchy.select { |_, level| level >= min_level }.keys
              internal_levels.map { |level| normalize_degree_for_pearch(level) }.compact.uniq
            else
              [ normalize_degree_for_pearch(normalized_value) ].compact
            end
          else
            [ normalize_degree_for_pearch(normalized_value) ].compact
          end
        else
          nil
        end
      else
        Array(degree_param).map { |d| normalize_degree_for_pearch(d.to_s) }.compact.uniq
      end
    end

    def normalize_degree_value_for_search(value)
      normalized = value.to_s.strip.downcase

      portuguese_mapping = {
        "ensino médio" => "high school",
        "ensino medio" => "high school",
        "curso técnico" => "technical",
        "curso tecnico" => "technical",
        "técnico" => "technical",
        "tecnico" => "technical",
        "curso online" => "online course",
        "graduação" => "bachelors",
        "graduacao" => "bachelors",
        "pós-graduação" => "postgraduate",
        "pos-graduacao" => "postgraduate",
        "pós graduação" => "postgraduate",
        "pos graduacao" => "postgraduate",
        "mestrado" => "masters",
        "doutorado" => "doctorate",
        "phd" => "phd",
        "outros" => "other"
      }

      portuguese_mapping[normalized] || normalized
    end

    def normalize_degree_for_pearch(internal_level)
      case internal_level.to_s.downcase
      when "bachelors", "bachelor"
        "bachelor"
      when "masters", "master"
        "master"
      when "postgraduate", "postgrad", "mba"
        "postdoc"
      when "doctorate", "doctor"
        "doctor"
      when "phd"
        "doctor"
      when "high school", "technical", "online course", "other"
        nil
      else
        nil
      end
    end

    def find_skills_and_categories
      keywords = []

      skills_param = params[:skills] ||
                    params.dig(:where, :skills) ||
                    params.dig(:where, "skills") ||
                    params.dig("where", :skills) ||
                    params.dig("where", "skills")

      if skills_param.present? && skills_param.is_a?(Array)
        skills_param.each do |skill|
          if skill.is_a?(Hash)
            name = skill[:name] || skill["name"]
            is_mandatory = skill[:isMandatory] || skill["isMandatory"] || false

            keywords << name.to_s if name.present?
          else
            keywords << skill.to_s if skill.present?
          end
        end
      end

      categories_param = params[:skill_categories] ||
                        params.dig(:where, :skill_categories) ||
                        params.dig(:where, "skill_categories") ||
                        params.dig("where", :skill_categories) ||
                        params.dig("where", "skill_categories")

      if categories_param.present? && categories_param.is_a?(Array)
        categories_param.each do |category|
          if category.is_a?(Hash)
            name = category[:name] || category["name"]
            keywords << name.to_s if name.present?
          else
            keywords << category.to_s if category.present?
          end
        end
      end

      keywords.uniq
    end

    def find_languages
      languages_param = params[:languages] ||
                       params.dig(:where, :languages) ||
                       params.dig(:where, "languages") ||
                       params.dig("where", :languages) ||
                       params.dig("where", "languages")

      return nil if languages_param.blank?

      language_names = []

      if languages_param.is_a?(Array)
        languages_param.each do |lang|
          if lang.is_a?(Hash)
            name = lang[:name] || lang["name"]
            language_names << name.to_s if name.present?
          else
            language_names << lang.to_s if lang.present?
          end
        end
      end

      language_names.uniq
    end

    def merge_filters(base, auto)
      result = base.dup

      auto.each do |key, value|
        if result[key].is_a?(Array) && value.is_a?(Array)
          result[key] = (result[key] + value).uniq
        else
          result[key] = value
        end
      end

      result
    end

    def parse_custom_filters
      return {} unless params[:custom_filters].present?

      if params[:custom_filters].is_a?(String)
        JSON.parse(params[:custom_filters])
      elsif params[:custom_filters].respond_to?(:to_unsafe_h)
        params[:custom_filters].to_unsafe_h
      else
        params[:custom_filters].is_a?(Hash) ? params[:custom_filters] : {}
      end
    rescue JSON::ParserError
      {}
    end
  end
end
