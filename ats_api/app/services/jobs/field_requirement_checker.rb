# frozen_string_literal: true

module Jobs
  class FieldRequirementChecker
    attr_reader :job, :remuneration_data, :benefits_data, :skills_data, :language_count, :requirements, :confidential_user_ids

    SKILLS_CHECK = ->(ctx) { ctx.skills_data[:skills].blank? }

    CHECKS = {
      "salary_from" => ->(ctx) { ctx.remuneration_data[:salary_from].blank? },
      "salary_to" => ->(ctx) { ctx.remuneration_data[:salary_to].blank? },
      "remuneration_data" => ->(ctx) { ctx.remuneration_data[:remunerations].blank? },
      "benefits_data" => ->(ctx) { ctx.benefits_data[:benefits].blank? },
      "skills" => SKILLS_CHECK,
      "skills_a" => SKILLS_CHECK,
      "languages" => ->(ctx) { ctx.language_count.zero? },
      "location" => ->(ctx) { ctx.job.city.blank? && ctx.job.state.blank? && ctx.job.country.blank? },
      "user" => ->(ctx) { ctx.job.user_id.blank? }
    }.freeze

    def initialize(job)
      @job = job
      @requirements = Array(job.field_requirements)
      @remuneration_data = {}
      @benefits_data = {}
      @skills_data = {}
      @language_count = 0

      preload_relationship_data if requirements_present?
    end

    def missing_fields
      return [] unless requirements_present?

      @missing_fields ||= begin
        requirements.each_with_object([]) do |field_req, acc|
          field_name = field_req["field_name"].to_s
          next unless missing_field?(field_name)

          if field_req["is_required"] == false && field_req["checked"] == true
            next
          end

          acc << build_missing_field_entry(field_req, field_name)
        end.sort_by { |f| f[:priority] }
      end
    end

    def required_fields_count
      @required_fields_count ||= requirements.count { |req| req["is_required"] }
    end

    def requirements_present?
      requirements.any?
    end

    private

    def requirements
      @requirements
    end

    def preload_relationship_data
      @remuneration_data = job.remuneration_relationships_data
      @benefits_data = job.benefit_relationships_data
      @skills_data = job.skill_relationships_data
      @language_count = if job.instance_variable_defined?(:@preloaded_language_count)
        job.instance_variable_get(:@preloaded_language_count)
      else
        LanguageRelationship.where(reference_type: "Job", reference_id: job.id).count
      end
    end

    def missing_field?(field_name)
      handler = CHECKS[field_name]
      return handler.call(self) if handler

      attribute_missing?(field_name)
    end

    def attribute_missing?(field_name)
      return false unless job.respond_to?(field_name)

      value = job.public_send(field_name)
      value.blank? || (value.respond_to?(:empty?) && value.empty?)
    end

    def build_missing_field_entry(field_req, field_name)
      entry = {
        field: field_name,
        priority: field_req["priority"] || 10,
        category: field_req["category"] || "important",
        label: field_req["label"],
        job_journey_position: field_req["job_journey_position"]
      }

      if field_req["is_required"] == false
        entry[:checked] = field_req["checked"] || false
      end

      entry
    end
  end
end
