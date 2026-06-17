# frozen_string_literal: true

module Candidates
  class CurriculumTextGenerator
    attr_reader :candidate

    FORMATION_TYPES = {
      1 => "Elementary School",
      2 => "High School",
      3 => "Technical Degree",
      4 => "Associate Degree",
      5 => "Bachelor's Degree",
      6 => "Teaching Degree",
      7 => "Postgraduate"
    }.freeze

    def initialize(candidate)
      @candidate = candidate
    end

    def generate
      [
        header_section,
        about_section,
        experience_section,
        education_section,
        skills_section,
        languages_section,
        additional_section
      ].compact.join("\n\n")
    end

    private

    def header_section
      [
        candidate.name&.upcase,
        build_contact_line,
        build_location,
        build_current_role
      ].compact.join("\n")
    end

    def build_contact_line
      contact_parts = [ candidate.email, candidate.mobile_phone, candidate.linkedin ].compact
      return nil if contact_parts.empty?

      contact_parts.join(" | ")
    end

    def build_current_role
      return nil unless candidate.role_name.present?

      role = candidate.role_name
      role += " at #{candidate.current_company}" if candidate.current_company.present?
      role
    end

    def about_section
      return nil unless candidate.self_introduction.present?

      build_section("ABOUT", candidate.self_introduction)
    end

    def experience_section
      experiences = safe_load_experiences
      return nil if experiences.empty?

      content = experiences.map { |exp| format_experience(exp) }.join("\n\n")
      build_section("PROFESSIONAL EXPERIENCE", content)
    rescue => e
      Rails.logger.error "[CurriculumTextGenerator] Error building experience section: #{e.message}"
      nil
    end

    def format_experience(exp)
      [
        build_experience_title(exp),
        build_experience_dates(exp),
        build_experience_description(exp)
      ].compact.join("\n")
    rescue => e
      Rails.logger.error "[CurriculumTextGenerator] Error formatting experience: #{e.message}"
      safe_attribute(exp, :company, :name) || safe_attribute(exp, :occupation, :name) || "Experience Entry"
    end

    def build_experience_title(exp)
      occupation = safe_attribute(exp, :occupation, :name)
      company = safe_attribute(exp, :company, :name)

      return "#{occupation} at #{company}" if occupation && company
      return occupation if occupation
      company
    end

    def build_experience_dates(exp)
      build_date_range(
        safe_attribute(exp, :start_date),
        safe_attribute(exp, :end_date),
        safe_attribute(exp, :work_here)
      )
    end

    def build_experience_description(exp)
      description = safe_attribute(exp, :description)
      return nil unless description.present?

      "\n#{description.strip}"
    end

    def education_section
      educations = safe_load_educations
      return nil if educations.empty?

      content = educations.map { |edu| format_education(edu) }.join("\n\n")
      build_section("EDUCATION", content)
    rescue => e
      Rails.logger.error "[CurriculumTextGenerator] Error building education section: #{e.message}"
      nil
    end

    def format_education(edu)
      [
        build_education_title(edu),
        build_education_dates(edu)
      ].compact.join("\n")
    rescue => e
      Rails.logger.error "[CurriculumTextGenerator] Error formatting education: #{e.message}"
      safe_attribute(edu, :institution, :name) || "Education Entry"
    end

    def build_education_title(edu)
      institution = safe_attribute(edu, :institution, :name)
      study_area = safe_attribute(edu, :study_area, :name)
      formation = map_formation_type_name(safe_attribute(edu, :formation_type))

      degree_parts = []
      degree_parts << formation if formation != "Other"
      degree_parts << "in #{study_area}" if study_area.present?

      return "#{degree_parts.join(' ')} - #{institution}" if degree_parts.any? && institution.present?
      return institution if institution.present?
      return degree_parts.join(" ") if degree_parts.any?
      nil
    end

    def build_education_dates(edu)
      build_date_range(
        safe_attribute(edu, :start_date),
        safe_attribute(edu, :end_date),
        safe_attribute(edu, :study_here)
      )
    end

    def skills_section
      skills = candidate.skills.pluck(:name)
      return nil if skills.empty?

      build_section("SKILLS", skills.join(", "))
    end

    def languages_section
      languages = candidate.languages.includes(:language_relationships)
      return nil if languages.empty?

      content = languages.map { |lang| format_language(lang) }.join(", ")
      build_section("LANGUAGES", content)
    end

    def format_language(lang)
      lang_rel = candidate.language_relationships.find_by(language_id: lang.id)
      return lang.name unless lang_rel&.proficiency.present?

      "#{lang.name} (#{lang_rel.proficiency})"
    end

    def additional_section
      parts = [
        build_work_preferences,
        build_interests,
        build_portfolio_links
      ].compact

      return nil if parts.empty?

      build_section("ADDITIONAL INFORMATION", parts.join("\n"))
    end

    def build_work_preferences
      prefs = []
      prefs << "Remote Work: Yes" if candidate.remote_work == true
      prefs << "Mobility: Yes" if candidate.mobility == true
      return nil if prefs.empty?

      prefs.join(" | ")
    end

    def build_interests
      return nil unless candidate.interests.present?

      "Interests: #{candidate.interests}"
    end

    def build_portfolio_links
      links = []
      links << "GitHub: #{candidate.github}" if candidate.github.present?
      links << "Portfolio: #{candidate.portfolio}" if candidate.portfolio.present?
      return nil if links.empty?

      links.join(" | ")
    end

    def build_section(title, content)
      return nil unless content.present?

      "#{title}\n\n#{content}"
    end

    def build_location
      [ candidate.city, candidate.state, candidate.country ].compact.join(", ")
    end

    def build_date_range(start_date, end_date, is_current)
      return nil unless start_date

      start_str = format_date(start_date)
      return "#{start_str} - Present" if is_current
      return "#{start_str} - #{format_date(end_date)}" if end_date

      start_str
    end

    def format_date(date)
      return nil unless date
      date.strftime("%b %Y")
    end

    def map_formation_type_name(type)
      return "Other" unless type

      FORMATION_TYPES.fetch(type.to_i, "Other")
    rescue
      "Other"
    end

    def safe_attribute(object, *methods)
      return nil unless object

      methods.reduce(object) do |obj, method|
        break nil unless obj
        obj.respond_to?(method) ? obj.send(method) : nil
      end
    rescue
      nil
    end

    def safe_load_experiences
      candidate.experiences.includes(:occupation, :company).order(start_date: :desc)
    rescue => e
      Rails.logger.error "[CurriculumTextGenerator] Error loading experiences: #{e.message}"
      []
    end

    def safe_load_educations
      candidate.educations.includes(:institution, :study_area).order(start_date: :desc)
    rescue => e
      Rails.logger.error "[CurriculumTextGenerator] Error loading educations: #{e.message}"
      []
    end
  end
end
