# frozen_string_literal: true

module EntityColumnService
  class Structure
    SUPPORTED_ENTITIES = {
      "candidate" => EntityColumnService::Entities::Candidate,
      "candidate_match" => EntityColumnService::Entities::CandidateMatch,
      "job" => EntityColumnService::Entities::Job,
      "apply" => EntityColumnService::Entities::Apply,
      "education" => EntityColumnService::Entities::Education,
      "experience" => EntityColumnService::Entities::Experience,
      "skill_relationship" => EntityColumnService::Entities::SkillRelationship,
      "remuneration_relationship" => EntityColumnService::Entities::RemunerationRelationship,
      "selective_process" => EntityColumnService::Entities::SelectiveProcess,
      "feedback" => EntityColumnService::Entities::Feedback,
      "language_relationship" => EntityColumnService::Entities::LanguageRelationship,
      "evaluation" => EntityColumnService::Entities::Evaluation,
      "question" => EntityColumnService::Entities::Question,
      "data_file" => EntityColumnService::Entities::DataFile,
      "account" => EntityColumnService::Entities::Account,
      "user" => EntityColumnService::Entities::User,
      "role" => EntityColumnService::Entities::Role,
      "job_status" => EntityColumnService::Entities::JobStatus,
      "business" => EntityColumnService::Entities::Business,
      "address" => EntityColumnService::Entities::Address,
      "address_relationship" => EntityColumnService::Entities::AddressRelationship,
      "benefit" => EntityColumnService::Entities::Benefit,
      "benefit_relationship" => EntityColumnService::Entities::BenefitRelationship,
      "activity_log" => EntityColumnService::Entities::ActivityLog,
      "whatsapp_configuration" => EntityColumnService::Entities::WhatsappConfiguration,
      "job_user" => EntityColumnService::Entities::JobUser,
      "department" => EntityColumnService::Entities::Department,
      "organizational_position" => EntityColumnService::Entities::OrganizationalPosition,
      "team" => EntityColumnService::Entities::Team,
      "team_member" => EntityColumnService::Entities::TeamMember,
      "position_assignment" => EntityColumnService::Entities::PositionAssignment,
      "sourcing" => EntityColumnService::Entities::Sourcing,
      "sourced_profile" => EntityColumnService::Entities::SourcedProfile,
      "sourced_profile_sourcing" => EntityColumnService::Entities::SourcedProfileSourcing,
      "meeting" => EntityColumnService::Entities::Meeting,
      "background_agent" => EntityColumnService::Entities::BackgroundAgent
    }.freeze

    def self.supported_entity?(entity_name)
      SUPPORTED_ENTITIES.key?(entity_name.to_s.singularize.downcase)
    end

    def self.entity_columns(entity_string, requester = "default", only_active: false, entity_id: nil)
      entity_name = entity_string.to_s.singularize.downcase
      return [] unless supported_entity?(entity_name)

      entity_class = SUPPORTED_ENTITIES[entity_name]
      return [] unless entity_class

      if entity_name == "apply" && entity_class.respond_to?(requester) && entity_id.present?
        return entity_class.public_send(requester, entity_id) if only_active
        return entity_class.public_send(requester, entity_id)
      end

      return entity_class.structure(entity_id) if entity_name == "apply" && entity_class.respond_to?(:structure)
      return entity_class.structure unless entity_class.respond_to?(requester)
      return entity_class.public_send(requester) if only_active

      merge_requester_columns(entity_class, requester, entity_id)
    end

    def self.column_filter_type(response_type)
      filter_types = [
        "Text",        # 0
        "AnswersAgg",  # 1
        "AnswersAgg",  # 2
        "AnswersAgg",  # 3
        "Money",       # 4
        "AnswersAgg",  # 5
        "AnswersAgg",  # 6
        "Text"         # 7
      ]

      filter_types[response_type.to_i] || "Text"
    end

    private

    def self.merge_requester_columns(entity_class, requester, entity_id)
      base_columns = entity_class.structure.dup
      requester_columns = entity_class.public_send(requester)

      merged_columns = merge_column_configurations(base_columns, requester_columns)
      add_shortlist_columns(merged_columns, requester) if shortlist_requester?(requester)
      add_evaluation_columns(merged_columns, requester, entity_id) if evaluation_requester?(requester, entity_id)

      merged_columns
    end

    def self.merge_column_configurations(base_columns, requester_columns)
      base_columns.map do |base_column|
        requester_column = find_matching_column(requester_columns, base_column)
        requester_column || base_column
      end
    end

    def self.find_matching_column(requester_columns, base_column)
      requester_columns.find { |column| column[:value] == base_column[:value] }
    end

    def self.add_shortlist_columns(columns, requester)
      return unless %w[shortlists candidate_shortlists].include?(requester)

      Report.where(is_deleted: false).find_each do |report|
        columns << build_report_column(report)
      end
    end

    def self.add_evaluation_columns(columns, requester, entity_id)
      return unless requester == "job" && entity_id.present?

      evaluation_ids = Evaluation.where(job_id: entity_id).pluck(:id)
      question_data = Question.where(evaluation_id: evaluation_ids)
                             .group(:title, :response_type)
                             .pluck(:title, :response_type)

      question_data.each do |title, response_type|
        columns << build_question_column(title, response_type, entity_id)
      end
    end

    def self.build_report_column(report)
      {
        value: report.name.downcase.split(" ").join(""),
        text: report.name.capitalize,
        sortable: true,
        type: "ShortlistText",
        filter: "text"
      }
    end

    def self.build_question_column(title, response_type, entity_id)
      {
        value: "answers_cache",
        text: title,
        sortable: true,
        type: "AnswersCache",
        filter: column_filter_type(response_type),
        field_sub_filter: response_type,
        entity_id: entity_id
      }
    end

    def self.shortlist_requester?(requester)
      %w[shortlists candidate_shortlists].include?(requester)
    end

    def self.evaluation_requester?(requester, entity_id)
      requester == "job" && entity_id.present?
    end
  end
end
