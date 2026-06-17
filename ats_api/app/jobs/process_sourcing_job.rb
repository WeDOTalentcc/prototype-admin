class ProcessSourcingJob
  include Sidekiq::Job

  sidekiq_options queue: :sourcing_search, retry: 3

  LOG_INTERVAL = 10
  POOL_SIZE = 150
  POOL_TTL = 30.minutes

  def perform(account_id, user_id, query, result_json, params_json, sourcing_id = nil)
    account = Account.find(account_id)
    user = User.find(user_id)
    result = parse_json(result_json)
    params = parse_json(params_json)

    Apartment::Tenant.switch!(account.tenant)

    sourcing = sourcing_id ? Sourcing.find(sourcing_id) : create_sourcing(account, user, query, result, params)

    broadcast_global_search_processing(sourcing)
    broadcast_processing_started(sourcing)

    create_sourced_profiles(sourcing, result[:search_results] || [], account)
    sourcing.update!(status: "done")

    broadcast_profiles_created(sourcing)
    log_info("Finished processing sourcing #{sourcing.id}")
  rescue ActiveRecord::RecordNotFound => e
    log_error("Record not found: #{e.message}")
    raise
  rescue => e
    log_error("Failed to process sourcing: #{e.message}\n#{e.backtrace.join("\n")}")
    sourcing&.update(status: "failed") rescue nil
    broadcast_processing_failed(sourcing, e.message) if sourcing
    raise
  end

  private

  def parse_json(json_string)
    JSON.parse(json_string, symbolize_names: true)
  end

  def create_sourcing(account, user, query, result, params)
    account.sourcings.create!(
      user: user,
      uid: result[:uuid] || SecureRandom.uuid,
      provider: "pearch",
      external_id: result[:uuid],
      thread_id: result[:thread_id],
      query: query,
      parameters: params.except(:query),
      status: result[:status]&.downcase || "done",
      duration: result[:duration],
      total_estimate: result[:total_estimate],
      total_estimate_is_lower_bound: result[:total_estimate_is_lower_bound] || false,
      results_count: (result[:search_results] || []).size,
      credits_used: result[:credits_used],
      searched_at: Time.current
    )
  end

  def create_sourced_profiles(sourcing, search_results, account)
    total = search_results.size
    log_info("📊 Starting to process #{total} profiles for sourcing #{sourcing.id}")

    sourcing.update!(global_results_count: total)
    broadcast_sourcing_profiles_found(sourcing, total, "global")

    batch_size = Sourcings::FirstBatchPageSize.for_sourcing(sourcing)
    cache_search_pool(sourcing, search_results, batch_size)

    first_batch = search_results.first(batch_size)

    processed_count = 0
    first_batch.each_with_index do |result, index|
      log_info("🔄 Processing profile #{index + 1}/#{total}: #{result[:docid]}")
      profile = create_sourced_profile(sourcing, result, account)
      if profile
        processed_count += 1
        broadcast_profile_processed(sourcing, profile.id, processed_count, first_batch.size)
      end
      log_progress(index, total)
    rescue => e
      log_error("Failed to create profile #{index + 1}: #{e.message}")
      log_error(e.backtrace.first(5).join("\n"))
    end

    sourcing.update!(
      processed_count: processed_count,
      results_count: processed_count
    )
    Rails.cache.write("sourcing_pool_page:#{sourcing.id}", 1, expires_in: POOL_TTL)
    broadcast_profiles_processing_completed(sourcing, processed_count)

    log_info("✅ Processed first #{processed_count} profiles. Remaining #{total - processed_count} cached for load_more")
  end

  def cache_search_pool(sourcing, search_results, page_size)
    Rails.cache.write(
      pool_cache_key(sourcing),
      {
        search_results: search_results,
        total: search_results.size,
        page_size: page_size,
        created_at: Time.current.iso8601,
        expires_at: POOL_TTL.from_now.iso8601
      },
      expires_in: POOL_TTL
    )
  end

  def pool_cache_key(sourcing)
    "sourcing_pool:#{sourcing.id}:global"
  end

  def broadcast_profiles_processing_completed(sourcing, processed_count)
    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "profiles_processing_completed",
        sourcing_id: sourcing.id,
        processed_count: processed_count,
        source: "global",
        phase: "processing_completed",
        timestamp: Time.current.iso8601
      }
    )
  end

  def create_sourced_profile(sourcing, result, account)
    profile_data = result[:profile] || {}

    all_emails = extract_all_emails(profile_data)
    primary_email = all_emails.first

    all_phones = extract_all_phones(profile_data)
    primary_phone = all_phones.first

    cpf = profile_data[:cpf]
    linkedin_url = profile_data[:linkedin_url]

    log_info("🔍 Checking for duplicate profile: #{profile_data[:name]}")

    matcher = SourcedProfiles::ProfileMatchingService.new(account_id: account.id)
    existing_profile = matcher.find_duplicate(
      email: primary_email,
      phone: primary_phone,
      cpf: cpf,
      linkedin_url: linkedin_url,
      external_id: result[:docid]
    )

    if existing_profile
      log_info("♻️  Duplicate found (ID: #{existing_profile.id}, provider: #{existing_profile.provider}), merging data from Pearch")
      merge_profile_data(existing_profile, profile_data, primary_email, all_emails, primary_phone, all_phones, result)
      create_or_update_sourced_profile_sourcing(existing_profile, sourcing, result)
      log_info("⏳ Profile #{existing_profile.id} will be analyzed by AI, broadcast will happen after analysis")
      return existing_profile
    end

    log_info("🆕 Creating new profile for external_id: #{result[:docid]}")
    profile = create_new_profile(account, result, profile_data, primary_email, all_emails, primary_phone, all_phones)
    log_info("✅ Profile created with ID: #{profile.id}")

    log_info("🔗 Linking profile #{profile.id} to sourcing #{sourcing.id}")
    create_or_update_sourced_profile_sourcing(profile, sourcing, result)

    log_info("⏳ Profile #{profile.id} will be analyzed by AI, broadcast will happen after analysis")

    profile
  end

  def merge_profile_data(profile, profile_data, primary_email, all_emails, primary_phone, all_phones, result)
    curriculum_text = build_curriculum_text(profile_data, result)
    current_company = extract_current_company(profile_data)
    current_title = extract_current_title(profile_data)

    updates = {
      email: primary_email.presence || profile.email,
      emails: all_emails.any? ? all_emails : profile.emails,
      phone: primary_phone.presence || profile.phone,
      phones: all_phones.any? ? all_phones : profile.phones,
      picture_url: profile_data[:picture_url].presence || profile.picture_url,
      summary: profile_data[:summary].presence || profile.summary,
      curriculum_text: curriculum_text.presence || profile.curriculum_text,
      title: profile_data[:title].presence || profile.title,
      location: profile_data[:location].presence || profile.location,
      city: profile_data[:city].presence || profile.city,
      state: profile_data[:state].presence || profile.state,
      country: profile_data[:country].presence || profile.country,
      cpf: profile_data[:cpf].presence || profile.cpf,
      date_birth: parse_date(profile_data[:date_birth]) || profile.date_birth,
      linkedin_url: profile_data[:linkedin_url].presence || profile.linkedin_url,
      linkedin_slug: profile_data[:linkedin_slug].presence || profile.linkedin_slug,
      first_name: profile_data[:first_name].presence || profile.first_name,
      last_name: profile_data[:last_name].presence || profile.last_name,
      estimated_age: profile_data[:estimated_age] || profile.estimated_age,
      total_experience_years: profile_data[:total_experience_years] || profile.total_experience_years,
      is_decision_maker: profile_data[:is_decision_maker] || profile.is_decision_maker,
      is_top_universities: profile_data[:is_top_universities] || profile.is_top_universities,
      followers_count: profile_data[:followers_count] || profile.followers_count,
      connections_count: profile_data[:connections_count] || profile.connections_count,
      has_emails: (primary_email.presence || profile.email).present?,
      has_phone_numbers: (primary_phone.presence || profile.phone).present?,
      current_company: current_company.presence || profile.current_company,
      current_title: current_title.presence || profile.current_title,
      role_name: profile_data[:role_name].presence || profile_data[:title].presence || current_title.presence || profile.role_name,
      position_level: profile_data[:position_level].presence || profile.position_level,
      remote_work: profile_data[:remote_work].presence || profile.remote_work,
      mobility: profile_data[:mobility].nil? ? profile.mobility : profile_data[:mobility],
      profile_updated_at: Time.current
    }

    updates[:expertise] = merge_arrays(profile.expertise, profile_data[:expertise])
    updates[:languages_data] = profile_data[:languages].presence || profile.languages_data
    updates[:skills_data] = merge_arrays(profile.skills_data, profile_data[:skills])
    updates[:experiences_data] = profile_data[:experiences].presence || profile.experiences_data
    updates[:educations_data] = profile_data[:educations].presence || profile.educations_data
    updates[:certifications_data] = profile_data[:certifications].presence || profile.certifications_data
    updates[:awards_data] = profile_data[:awards].presence || profile.awards_data

    if profile.provider == "local" && profile_data.present?
      updates[:provider] = "hybrid"
      updates[:external_id] = result[:docid] if profile.external_id&.start_with?("internal_")
    end

    profile.update!(updates)
    log_info("✅ Profile #{profile.id} updated with Pearch data (provider now: #{profile.provider})")
  rescue => e
    log_error("Failed to merge profile #{profile.id}: #{e.message}")
  end

  def merge_arrays(arr1, arr2)
    return arr2 if arr1.blank?
    return arr1 if arr2.blank?
    (arr1 + arr2).uniq
  end

  def create_new_profile(account, result, profile_data, primary_email, all_emails, primary_phone, all_phones)
    curriculum_text = build_curriculum_text(profile_data, result)
    SourcedProfile.create!(
      account: account,
      sourcing_id: nil,
      uid: SecureRandom.uuid,
      provider: "pearch",
      external_id: result[:docid],
      linkedin_slug: profile_data[:linkedin_slug],
      linkedin_url: profile_data[:linkedin_url],
      name: profile_data[:name],
      first_name: profile_data[:first_name],
      middle_name: profile_data[:middle_name],
      last_name: profile_data[:last_name],
      email: primary_email,
      emails: all_emails,
      phone: primary_phone,
      phones: all_phones,
      date_birth: parse_date(profile_data[:date_birth]),
      title: profile_data[:title],
      role_name: profile_data[:role_name].presence || profile_data[:title],
      summary: profile_data[:summary],
      curriculum_text: curriculum_text,
      picture_url: profile_data[:picture_url],
      estimated_age: profile_data[:estimated_age],
      location: profile_data[:location],
      city: profile_data[:city],
      state: profile_data[:state],
      country: profile_data[:country],
      remote_work: profile_data[:remote_work],
      mobility: profile_data[:mobility],
      current_company: extract_current_company(profile_data),
      current_title: extract_current_title(profile_data),
      position_level: profile_data[:position_level],
      total_experience_years: profile_data[:total_experience_years],
      is_decision_maker: profile_data[:is_decision_maker] || false,
      is_top_universities: profile_data[:is_top_universities] || false,
      expertise: profile_data[:expertise] || [],
      languages_data: profile_data[:languages] || [],
      skills_data: profile_data[:skills] || [],
      has_emails: primary_email.present?,
      has_phone_numbers: primary_phone.present?,
      followers_count: profile_data[:followers_count],
      connections_count: profile_data[:connections_count],
      profile_data: profile_data,
      experiences_data: profile_data[:experiences] || [],
      educations_data: profile_data[:educations] || [],
      certifications_data: profile_data[:certifications] || [],
      awards_data: profile_data[:awards] || [],
      status: "new",
      profile_updated_at: Time.current
    )
  end

  def create_or_update_sourced_profile_sourcing(profile, sourcing, result)
    sourced_profile_sourcing = SourcedProfileSourcing.find_or_initialize_by(
      sourced_profile_id: profile.id,
      sourcing_id: sourcing.id,
      account_id: sourcing.account_id,
      user_id: sourcing.user_id
    )

    sourced_profile_sourcing.is_deleted = false
    sourced_profile_sourcing.save!
    sourced_profile_sourcing
  rescue => e
    log_error("Failed to link profile #{profile.id} to sourcing #{sourcing.id}: #{e.message}")
    nil
  end

  def extract_contact(profile_data, field)
    contacts = profile_data.dig(:contact_info, field)
    contacts.is_a?(Array) && contacts.any? ? contacts.first : nil
  end

  def extract_all_emails(profile_data)
    business_emails = Array(profile_data[:business_emails]).compact
    personal_emails = Array(profile_data[:personal_emails]).compact

    all_emails = business_emails + personal_emails
    all_emails.uniq.reject(&:blank?)
  end

  def extract_all_phones(profile_data)
    phone_numbers = Array(profile_data[:phone_numbers]).compact
    phone_numbers.uniq.reject(&:blank?)
  end

  def extract_current_company(profile_data)
    find_current_experience(profile_data)&.dig(:company_info, :name)
  end

  def extract_current_title(profile_data)
    find_current_role(profile_data)&.dig(:title)
  end

  def build_curriculum_text(profile_data, result)
    SourcedProfiles::CurriculumTextBuilder.build(profile_data: profile_data, result: result)
  end

  def find_current_experience(profile_data)
    (profile_data[:experiences] || []).find do |exp|
      has_current_role?(exp)
    end
  end

  def find_current_role(profile_data)
    (profile_data[:experiences] || []).each do |exp|
      role = (exp[:company_roles] || []).find { |r| r[:is_current_experience] }
      return role if role
    end
    nil
  end

  def has_current_role?(experience)
    (experience[:company_roles] || []).any? { |role| role[:is_current_experience] }
  end

  def parse_date(date_string)
    return nil if date_string.blank?
    Date.parse(date_string)
  rescue StandardError
    nil
  end

  def log_progress(index, total)
    return unless ((index + 1) % LOG_INTERVAL).zero?
    log_info("Created #{index + 1}/#{total} profiles")
  end

  def log_info(message)
    Rails.logger.info("[ProcessSourcingJob] #{message}")
  end

  def log_error(message)
    Rails.logger.error("[ProcessSourcingJob] #{message}")
  end

  def broadcast_processing_started(sourcing)
    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "profiles_processing_started",
        sourcing_id: sourcing.id,
        total_profiles: sourcing.results_count
      }
    )
  end

  def broadcast_profiles_created(sourcing)
    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "profiles_created",
        sourcing_id: sourcing.id,
        total_profiles: sourcing.sourced_profiles.count,
        phase: "profiles_saved",
        message: "Perfis criados. Iniciando análise IA..."
      }
    )
  end

  def broadcast_processing_failed(sourcing, error_message)
    serialized = SourcingSerializer.new(sourcing).serializable_hash[:data][:attributes]

    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "sourcing_failed",
        sourcing: serialized,
        error: error_message
      }
    )
  end

  def broadcast_sourcing_profiles_found(sourcing, count, source)
    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "sourcing_profiles_found",
        sourcing_id: sourcing.id,
        count: count,
        source: source,
        total_expected: sourcing.local_results_count.to_i + sourcing.global_results_count.to_i
      }
    )
  end

  def broadcast_profile_processed(sourcing, profile_id, _current, _total)
    sps = SourcedProfileSourcing.find_by(
      sourcing_id: sourcing.id,
      sourced_profile_id: profile_id,
      is_deleted: false
    )
    return unless sps

    Sourcings::ProfileAnalyzedBroadcast.call(sourcing: sourcing, sourced_profile_sourcing: sps)
  rescue => e
    Rails.logger.error("[ProcessSourcingJob] Failed to broadcast profile processed: #{e.message}")
  end

  def broadcast_global_search_processing(sourcing)
    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "global_search_processing",
        sourcing_id: sourcing.id,
        search_type: "global",
        timestamp: Time.current.iso8601,
        message: "Aguardando resultados globais..."
      }
    )
  rescue => e
    Rails.logger.error("[ProcessSourcingJob] Failed to broadcast global_search_processing: #{e.message}")
  end

  def broadcast_global_search_completed(sourcing, count)
    sleep(0.3)
    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "global_profiles_created",
        sourcing_id: sourcing.id,
        profiles_count: count,
        source: "global",
        phase: "creation_completed",
        timestamp: Time.current.iso8601
      }
    )
    log_info("✅ Global search completed - #{count} profiles created")

    # Indicar que os perfis globais entrarão na fila de análise IA
    sleep(0.2)
    SourcingChannel.broadcast_to(
      "#{sourcing.user_id}_sourcing_#{sourcing.id}",
      {
        type: "profiles_processing_started",
        sourcing_id: sourcing.id,
        total_profiles: count,
        source: "global",
        phase: "ai_analysis_queue"
      }
    )
  end
end
