class ListRelationshipJob < ApplicationJob
  queue_as :default

  def perform(search_params, list_id, user_id, account_id, action = "create", collections = nil)
    @list = List.find_by(id: list_id, account_id: account_id)
    @account_id = account_id
    return unless @list

    if collections.present?
      if action == "create"
        process_collections(collections)
      elsif action == "delete"
        delete_collections(collections)
      end
      @list.count_relationships
      return
    end

    return unless search_params

    reference_type = search_params["reference_type"]
    return unless reference_type

    if action == "create"
      results = execute_search(search_params, reference_type, account_id)
      add_to_list(results, reference_type)
    elsif action == "delete"
      # Para delete, buscamos diretamente os ListRelationship
      results = execute_list_relationship_search(search_params, account_id)
      remove_from_list_relationships(results)
    end

    @list.count_relationships
  rescue StandardError => e
    Rails.logger.error("ListRelationshipJob error: #{e.message}")
    Rails.logger.error(e.backtrace.join("\n"))
  end

  private

  def add_to_list(results, reference_type)
    results.each do |result|
      final_reference_type = reference_type
      final_reference_id = result.id

      if reference_type == "Apply"
        final_reference_type = "Candidate"
        apply = Apply.find_by(id: result.id)
        next unless apply
        final_reference_id = apply.candidate_id
        next unless final_reference_id
      end

      if reference_type == "SourcedProfileSourcing"
        candidate_id = get_or_create_candidate_from_sourced_profile_sourcing(result.id)
        next unless candidate_id
        final_reference_type = "Candidate"
        final_reference_id = candidate_id
      end

      ListRelationship.find_or_create_by(
        list_id: @list.id,
        reference_type: final_reference_type,
        reference_id: final_reference_id,
        account_id: @account_id
      )
    rescue StandardError => e
      Rails.logger.error("Error adding #{result.id} to list: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
    end
  end

  def remove_from_list(results, reference_type)
    result_ids = results.map(&:id)

    if reference_type == "Apply"
      applies = Apply.where(id: result_ids)
      result_ids = applies.pluck(:candidate_id).compact
      reference_type = "Candidate"
    end

    if reference_type == "SourcedProfileSourcing"
      sourced_profile_sourcings = SourcedProfileSourcing.where(id: result_ids).includes(:sourced_profile)
      candidate_ids = []

      sourced_profile_sourcings.each do |sps|
        candidate_id = sps.candidate_id || get_or_create_candidate_from_sourced_profile_sourcing(sps.id)
        candidate_ids << candidate_id if candidate_id
      end

      result_ids = candidate_ids
      reference_type = "Candidate"
    end

    return if result_ids.empty?

    ListRelationship.where(
      list_id: @list.id,
      reference_type: reference_type,
      reference_id: result_ids,
      account_id: @account_id,
      is_deleted: false
    ).update_all(is_deleted: true)
  end

  def remove_from_list_relationships(list_relationships)
    return if list_relationships.empty?

    relationship_ids = list_relationships.map(&:id)

    ListRelationship.where(
      id: relationship_ids,
      list_id: @list.id,
      account_id: @account_id
    ).update(is_deleted: true)
  end

  def execute_search(search_params, reference_type, account_id)
    model = reference_type.constantize

    where_params = (search_params["where"] || {}).merge({ account_id: account_id })

    except_ids = normalize_except_ids(search_params["except_ids"])

    results = model.search(
      search_params["term"] || "*",
      where: where_params,
      page: search_params["page"] || 1,
      per_page: 1000,
      load: true
    )

    if except_ids.present?
      results = results.reject { |result| except_ids.include?(result.id) }
    end

    results
  rescue StandardError => e
    Rails.logger.error("Search error: #{e.message}")
    []
  end

  def execute_list_relationship_search(search_params, account_id)
    where_params = (search_params["where"] || {}).dup
    where_params["list_id"] = @list.id
    where_params["account_id"] = account_id
    where_params["is_deleted"] = false

    if search_params["reference_type"].present?
      where_params["reference_type"] = search_params["reference_type"]
    end

    except_ids = normalize_except_ids(search_params["except_ids"])

    results = ListRelationship.search(
      search_params["term"] || "*",
      where: where_params,
      page: search_params["page"] || 1,
      per_page: 1000,
      load: true
    )

    if except_ids.present?
      results = results.reject { |result| except_ids.include?(result.id) }
    end

    results
  rescue StandardError => e
    Rails.logger.error("ListRelationship search error: #{e.message}")
    Rails.logger.error(e.backtrace.join("\n"))
    []
  end

  def normalize_except_ids(except_ids)
    return [] unless except_ids.present?
    return [] unless except_ids.is_a?(Array)

    except_ids.map { |id| id.is_a?(String) && id.match?(/^\d+$/) ? id.to_i : id }
  end

  def process_collections(collections)
    collections.each do |reference|
      reference_type = reference[:reference_type] || reference["reference_type"]
      reference_id = reference[:reference_id] || reference["reference_id"]
      general_comments = reference[:general_comments] || reference["general_comments"]

      if reference_type == "Apply"
        reference_type = "Candidate"
        apply = Apply.find_by(id: reference_id)
        next unless apply
        reference_id = apply.candidate_id
      end

      if reference_type == "SourcedProfileSourcing"
        candidate_id = get_or_create_candidate_from_sourced_profile_sourcing(reference_id)
        next unless candidate_id
        reference_type = "Candidate"
        reference_id = candidate_id
      end

      next unless reference_type && reference_id

      ListRelationship.find_or_create_by(
        reference_type: reference_type,
        reference_id: reference_id,
        list_id: @list.id,
        account_id: @account_id
      ) do |rel|
        rel.general_comments = general_comments if general_comments
      end
    rescue StandardError => e
      Rails.logger.error("Error processing collection item: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
    end
  end

  def delete_collections(collections)
    collections.each do |reference|
      reference_type = reference[:reference_type] || reference["reference_type"]
      reference_id = reference[:reference_id] || reference["reference_id"]

      if reference_type == "Apply"
        reference_type = "Candidate"
        apply = Apply.find_by(id: reference_id)
        next unless apply
        reference_id = apply.candidate_id
      end

      if reference_type == "SourcedProfileSourcing"
        sourced_profile_sourcing = SourcedProfileSourcing.find_by(id: reference_id)
        next unless sourced_profile_sourcing
        candidate_id = sourced_profile_sourcing.candidate_id || get_or_create_candidate_from_sourced_profile_sourcing(reference_id)
        next unless candidate_id
        reference_type = "Candidate"
        reference_id = candidate_id
      end

      next unless reference_type && reference_id

      results = ListRelationship.where(
        id: reference_id,
        list_id: @list.id,
        account_id: @account_id
      )
      results.update(is_deleted: true)
    rescue StandardError => e
      Rails.logger.error("Error deleting collection item: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
    end
  end

  def get_or_create_candidate_from_sourced_profile_sourcing(sourced_profile_sourcing_id)
    sourced_profile_sourcing = SourcedProfileSourcing.find_by(id: sourced_profile_sourcing_id)
    return nil unless sourced_profile_sourcing

    sourced_profile = sourced_profile_sourcing.sourced_profile
    return nil unless sourced_profile

    candidate_id = sourced_profile.candidate_id
    return candidate_id if candidate_id.present?

    ::SourcedProfiles::ConvertToCandidateJob.perform_now(
      [ sourced_profile.id ],
      @account_id
    )
    sourced_profile.reload

    sourced_profile.candidate_id
  end
end
