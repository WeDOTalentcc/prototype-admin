# frozen_string_literal: true

module SourcedProfiles
  class AiEnrichmentService
    def initialize(sourced_profile_sourcing)
      @sps = sourced_profile_sourcing
      @sourced_profile = sourced_profile_sourcing.sourced_profile
      @account = @sourced_profile.account
      @analysis = safe_hash(sourced_profile_sourcing.analysis)
    end

    def enrich!
      return unless @analysis.present?

      Searchkick.callbacks(false) do
        ActiveRecord::Base.transaction do
          enrich_skills_data
          enrich_expertise
          enrich_profile_data
          enrich_basic_fields
          create_skill_relationships
          @sourced_profile.save!
        end
      end

      @sourced_profile
    rescue => e
      Rails.logger.error "[AiEnrichment] Failed for SourcedProfile ##{@sourced_profile.id}: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise
    end

    private

    def enrich_skills_data
      return if all_skill_names.empty?

      current_skills = safe_array(@sourced_profile.skills_data)
      existing_names = current_skills.filter_map { |s| extract_skill_name(s)&.downcase }

      new_skills = all_skill_names.reject { |name| existing_names.include?(name.downcase) }
      return if new_skills.empty?

      strong = strong_skill_names
      new_entries = new_skills.map do |name|
        {
          "name" => name,
          "level" => strong.include?(name.downcase) ? "strong" : "mentioned",
          "source" => "ai_analysis",
          "added_at" => Time.current.iso8601
        }
      end

      @sourced_profile.skills_data = current_skills + new_entries
    end

    def enrich_expertise
      current_expertise = safe_array(@sourced_profile.expertise)
      existing_values = current_expertise.map { |e| normalize_expertise_value(e) }.compact

      new_items = []

      all_skill_names.each do |name|
        next if existing_values.include?(name.downcase)

        new_items << name
        existing_values << name.downcase
      end

      return if new_items.empty?

      @sourced_profile.expertise = current_expertise + new_items
    end

    def enrich_profile_data
      current_data = safe_hash(@sourced_profile.profile_data)

      current_data["expertise"] = safe_array(@sourced_profile.expertise) if safe_array(current_data["expertise"]).empty?

      enrich_profile_highlights(current_data)
      enrich_profile_suggested_questions(current_data)
      enrich_profile_development_areas(current_data)
      enrich_profile_evaluation(current_data)

      current_data["enrichment"] = build_enrichment_metadata

      @sourced_profile.profile_data = current_data
    end

    def enrich_basic_fields
      one_liner = safe_string(@analysis, "one_liner")
      @sourced_profile.summary = one_liner if one_liner.present? && @sourced_profile.summary.blank?

      title_from_analysis = safe_string(@analysis, "sourcing_query")
      if title_from_analysis.present? && @sourced_profile.title.blank?
        @sourced_profile.title = @sourced_profile.current_title.presence || @sourced_profile.role_name
      end
    end

    def create_skill_relationships
      return if all_skill_names.empty?

      all_skill_names.each do |skill_name|
        skill = find_or_create_skill(skill_name)
        next unless skill

        create_skill_relationship_record(skill, skill_name)
      end
    end

    def all_skill_names
      @all_skill_names ||= begin
        assessment = safe_hash(@analysis["skills_assessment"])
        strong = safe_array(assessment["strong"])
        mentioned = safe_array(assessment["mentioned"])

        (strong + mentioned)
          .filter_map { |s| s.is_a?(String) ? s.strip : nil }
          .reject(&:blank?)
          .uniq
      end
    end

    def strong_skill_names
      @strong_skill_names ||= begin
        safe_array(safe_hash(@analysis["skills_assessment"])["strong"])
          .filter_map { |s| s.is_a?(String) ? s.strip.downcase : nil }
          .to_set
      end
    end

    def find_or_create_skill(skill_name)
      normalized = skill_name.downcase.strip

      Skill.find_by(
        "LOWER(name) = ? AND account_id = ? AND is_deleted = ?",
        normalized, @account.id, false
      ) || Skill.create!(name: skill_name, account_id: @account.id, is_deleted: false)
    rescue ActiveRecord::RecordInvalid
      nil
    end

    def create_skill_relationship_record(skill, original_name)
      level = strong_skill_names.include?(original_name.downcase) ? 3 : 2

      existing = SkillRelationship.find_by(
        skill_id: skill.id,
        reference_type: "SourcedProfile",
        reference_id: @sourced_profile.id,
        is_deleted: false
      )
      return if existing

      SkillRelationship.create!(
        skill_id: skill.id,
        reference_type: "SourcedProfile",
        reference_id: @sourced_profile.id,
        account_id: @account.id,
        level_skill: level,
        is_deleted: false
      )
    rescue ActiveRecord::RecordInvalid
      nil
    end

    def enrich_profile_highlights(data)
      highlights = safe_array(@analysis["highlights"])
      return if highlights.empty?

      existing = safe_array(data["highlights"])
      existing_descriptions = existing.map { |h| safe_string(h, "description")&.downcase }.compact

      new_highlights = highlights.filter_map do |h|
        desc = safe_string(h, "description")
        next if desc.blank? || existing_descriptions.include?(desc.downcase)

        { "type" => safe_string(h, "type"), "description" => desc }
      end

      data["highlights"] = existing + new_highlights unless new_highlights.empty?
    end

    def enrich_profile_suggested_questions(data)
      questions = safe_array(@analysis["suggested_questions"])
      return if questions.empty?

      existing = safe_array(data["suggested_questions"])
      new_questions = questions.select { |q| q.is_a?(String) && q.present? } - existing
      data["suggested_questions"] = (existing + new_questions).uniq unless new_questions.empty?
    end

    def enrich_profile_development_areas(data)
      areas = safe_array(@analysis["development_areas"])
      return if areas.empty?

      existing = safe_array(data["development_areas"])
      existing_descriptions = existing.map { |a| safe_string(a, "description")&.downcase }.compact

      new_areas = areas.filter_map do |area|
        desc = safe_string(area, "description")
        next if desc.blank? || existing_descriptions.include?(desc.downcase)

        { "type" => safe_string(area, "type"), "description" => desc, "requirement" => safe_string(area, "requirement") }
      end

      data["development_areas"] = existing + new_areas unless new_areas.empty?
    end

    def enrich_profile_evaluation(data)
      evaluation = safe_array(@analysis["evaluation"])
      return if evaluation.empty?

      return if safe_array(data["evaluation"]).any?

      data["evaluation"] = evaluation.filter_map do |eval_item|
        next unless eval_item.is_a?(Hash)

        {
          "requirement" => safe_string(eval_item, "requirement"),
          "match_level" => safe_string(eval_item, "match_level"),
          "priority" => safe_string(eval_item, "priority"),
          "points" => eval_item["points"],
          "rationale" => safe_string(eval_item, "rationale")
        }.compact
      end
    end

    def build_enrichment_metadata
      {
        "enriched_at" => Time.current.iso8601,
        "enrichment_source" => "ai_analysis",
        "sourcing_id" => @sps.sourcing_id,
        "ai_score" => @analysis["calculated_score"],
        "ai_confidence" => safe_string(@analysis, "score_confidence"),
        "skills_extracted" => all_skill_names.size,
        "highlights_added" => safe_array(@analysis["highlights"]).size
      }
    end

    def extract_skill_name(skill)
      return skill if skill.is_a?(String)
      return skill["name"] if skill.is_a?(Hash) && skill["name"].is_a?(String)

      nil
    end

    def normalize_expertise_value(item)
      return item.downcase if item.is_a?(String)
      return safe_string(item, "description")&.downcase if item.is_a?(Hash)

      nil
    end

    def safe_hash(value)
      value.is_a?(Hash) ? value : {}
    end

    def safe_array(value)
      value.is_a?(Array) ? value : []
    end

    def safe_string(hash, key)
      return nil unless hash.is_a?(Hash)

      value = hash[key]
      value.is_a?(String) ? value : nil
    end
  end
end
