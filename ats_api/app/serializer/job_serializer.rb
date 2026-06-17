class JobSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :uid,
    :slug,
    :is_published,
    :title,
    :description,
    :user_id,
    :account_id,
    :job_status_id,
    :created_at,
    :updated_at,
    :provider,
    :provider_job_id,
    :company_id,
    :published_date,
    :application_deadline,
    :is_remote,
    :city,
    :state,
    :country,
    :job_url,
    :career_page_id,
    :career_page_name,
    :career_page_url,
    :career_page_logo,
    :friendly_badge,
    :disabilities,
    :workplace_type,
    :external_id,
    :is_urgent,
    :screening_deadline,
    :shortlist_deadline,
    :closing_deadline,
    :is_active,
    :is_archived,
    :reason_for_pause,
    :is_screening_active,
    :sector,
    :segment,
    :target_audience,
    :has_linkedin_post,
    :has_website_post,
    :has_indeed_post,
    :confidential_type,
    :confidential_company_name,
    :use_whatsapp_channel,
    :use_webchat_channel,
    :use_voice_channel,
    :use_call_channel,
    :notification_channels,
    :minimum_screening_score,
    :screening_timeout,
    :screening_max_attempts,
    :screening_approve_limit,
    :interview_minimum_score,
    :has_automatic_interview,
    :interview_calendar_type,
    :interview_hours_range,
    :interview_duration,
    :responsibilities,
    :web_saturation_amount,
    :sourcing_saturation_amount,
    :saturation_amount_increase,
    :saturation_release_hours,
    :allowed_screenings_limit_date,
    :agent_search_criteria,
    :wsi_suggested_seniority_key
  )

  attribute :salary_from do |object|
    object.try(:[], :salary_from) || object.salary_from rescue nil
  end

  attribute :salary_to do |object|
    object.try(:[], :salary_to) || object.salary_to rescue nil
  end

  attribute :salary_currency do |object|
    object.try(:[], :salary_currency) || object.salary_currency rescue nil
  end

  attribute :salary_period do |object|
    period = object.try(:[], :salary_period) || object.salary_period rescue nil
    next unless period

    RemunerationRelationship.period_label(period)
  end

  attribute :salary_contract_type do |object|
    contract = object.try(:[], :salary_contract_type) || object.salary_contract_type rescue nil
    next unless contract

    RemunerationRelationship.normalize_contract_type(contract) || contract
  end

  attribute :commission_from do |object|
    object.try(:[], :commission_from) || object.commission_from rescue nil
  end

  attribute :commission_to do |object|
    object.try(:[], :commission_to) || object.commission_to rescue nil
  end

  attribute :commission_currency do |object|
    object.try(:[], :commission_currency) || object.commission_currency rescue nil
  end

  attribute :commission_period do |object|
    period = object.try(:[], :commission_period) || object.commission_period rescue nil
    next unless period

    RemunerationRelationship.period_label(period)
  end

  attribute :bonus_from do |object|
    object.try(:[], :bonus_from) || object.bonus_from rescue nil
  end

  attribute :bonus_to do |object|
    object.try(:[], :bonus_to) || object.bonus_to rescue nil
  end

  attribute :bonus_currency do |object|
    object.try(:[], :bonus_currency) || object.bonus_currency rescue nil
  end

  attribute :bonus_period do |object|
    period = object.try(:[], :bonus_period) || object.bonus_period rescue nil
    next unless period

    RemunerationRelationship.period_label(period)
  end

  attribute :applies_count do |job|
    job.total_applies_count
  end

  attribute :job_status do |object|
    if object.respond_to?(:job_status)
      object[:job_status]
    else
      nil
    end
  end

  attribute :job_status_color do |object|
    if object.respond_to?(:job_status_color)
      object[:job_status_color]
    else
      nil
    end
  end

  attribute :user_name do |object|
    if object.respond_to?(:user_name)
      object[:user_name] || object.user.name
    else
      object.user.name
    end
  end

  attribute :user_email do |object|
    if object.respond_to?(:user_email)
      object[:user_email].presence || object.user&.email
    else
      object.user&.email
    end
  end

  attribute :user_whatsapp do |object|
    if object.respond_to?(:user_whatsapp)
      object[:user_whatsapp] || object.user.whatsapp
    else
      object.user.whatsapp
    end
  end

  attribute :url do |object|
    "/user/jobs/" + object.id.to_s
  end

  attribute :pin do |job, params|
    next false unless params[:current_user]
    job.pin_user_ids&.include?(params[:current_user].id) || false
  end

  attribute :confidential do |job, params|
    next false unless params[:current_user]
    job.confidential_user_ids&.include?(params[:current_user].id) || false
  end

  attributes :applies_by_status_count do |job|
    if job.respond_to?(:applies_by_status_count)
      job.applies_by_status_count[:applies_by_status_count]
    else
      nil
    end
  end

  attributes :in_process do |job|
    if job.respond_to?(:applies_by_status_count)
      job.applies_by_status_count[:in_process]
    else
      nil
    end
  end

  attribute :selection_process_summary do |job|
    job.selection_process_summary
  end

  attribute :company do |job|
    next unless job.company_id

    {
      id: job.company_id,
      name: job[:company_name] || job.company&.name
    }
  end

  attribute :missing_fields do |job|
    job.missing_fields || []
  end

  attribute :wsi_jd_big_five_profile do |job|
    job.wsi_jd_big_five_profile.presence || {}
  end

  attribute :wsi_jd_trait_ranking do |job|
    job.wsi_jd_trait_ranking.presence || {}
  end

  attribute :completeness_percentage do |job|
    job.completeness_percentage
  end

  attribute :is_ready_for_publication do |job|
    job.is_ready_for_publication?
  end

  attribute :selective_processes, if: Proc.new { |record, params|
    params && params[:include_selective_processes]
  } do |job|
    # Busca selective_processes com contagem de applies
    processes_with_counts = job.selective_processes
      .left_joins(:applies)
      .where(applies: { is_deleted: [ false, nil ] })
      .group("selective_processes.id", "selective_processes.color", "selective_processes.name",
             "selective_processes.position", "selective_processes.status", "selective_processes.external_id",
             "selective_processes.sub_status", "selective_processes.childrens")
      .order(:position)
      .select(
        "selective_processes.*",
        "COUNT(applies.id) as applies_count"
      )

    processes_with_counts.map do |sp|
      {
        id: sp.id,
        name: sp.name,
        position: sp.position,
        status: sp.status,
        status_code: sp.status,
        external_id: sp.external_id,
        color: sp.color,
        sub_status: sp.sub_status,
        childrens: sp.childrens,
        count: sp.applies_count.to_i,  # Contagem de applies
        created_at: sp.created_at,
        updated_at: sp.updated_at
      }
    end
  end

  attribute :organizational_structure do |job|
    job.organizational_structure
  end

  attribute :is_confidential do |job|
    if job.respond_to?(:is_confidential)
      job.is_confidential
    else
      nil
    end
  end

  attribute :remunerations, if: proc { |_record, params|
    params[:includes]&.include?("remunerations")
  } do |object, _params|
    object.remunerations
  end

  attribute :benefits, if: proc { |_record, params|
    params[:includes]&.include?("benefits")
  } do |object, _params|
    object.benefits
  end

  attribute :skills, if: proc { |_record, params|
    params[:includes]&.include?("skills")
  } do |object, _params|
    object.skills
  end

  attribute :languages, if: proc { |_record, params|
    params[:includes]&.include?("languages")
  } do |object, _params|
    object.languages
  end

  attribute :behavioral_skills, if: proc { |_record, params|
    params[:includes]&.include?("behavioral_skills")
  } do |object, _params|
    object.behavioral_skills
  end

  attribute :priority do |object|
    object.priority
  end

  attribute :urgency_level do |object|
    object.urgency_level
  end

  attribute :priority_text do |object|
    Job::PRIORITY.find { |p| p["id"] == object.priority }&.dig("name") || "Não informado"
  end

  attribute :urgency_level_text do |object|
    Job::URGENCY_LEVEL.find { |u| u["id"] == object.urgency_level }&.dig("name") || "Não informado"
  end

  attribute :workplace_type_text do |object|
    Job::WORKPLACE_TYPES.find { |w| w["id"].to_s == object.workplace_type.to_s || w["name"] == object.workplace_type }&.dig("name") || "Não informado"
  end

  attribute :employment_type do |object|
    object.employment_type
  end

  attribute :employment_type_text do |object|
    idx = object.employment_type
    idx.nil? ? "Não informado" : (Job::EMPLOYMENT_TYPES[idx] || "Não informado")
  end

  attribute :seniority do |object|
    object.seniority
  end

  attribute :seniority_text do |object|
    idx = object.seniority
    idx.nil? ? "Não informado" : (Job::SENIORITY[idx] || "Não informado")
  end

  attribute :main_pcd_category do |object|
    object.main_pcd_category
  end

  attribute :main_pcd_category_text do |object|
    Job::PCD_CATEGORIES.find { |c| c["id"] == object.main_pcd_category }&.dig("name") || "Não informado"
  end

  attribute :secondary_pcd_category do |object|
    object.secondary_pcd_category
  end

  attribute :secondary_pcd_category_text do |object|
    Job::PCD_CATEGORIES.find { |c| c["id"] == object.secondary_pcd_category }&.dig("name") || "Não informado"
  end

  attribute :pcd_description do |object|
    object.pcd_description
  end

  attribute :pcd_files_description do |object|
    object.pcd_files_description
  end

  attribute :required_pcd_files do |object|
    object.required_pcd_files
  end

  attribute :confidential_type_text do |object|
    Job::CONFIDENTIAL_TYPES.find { |c| c["id"] == object.confidential_type }&.dig("name") || "Não informado"
  end

  attribute :department_id do |object|
    object.department_id
  end

  attribute :department_name do |object|
    if object.respond_to?(:department_name)
      object[:department_name]
    else
      object.department&.name || nil
    end
  end

  attribute :confidential_type_text do |object|
    Job::CONFIDENTIAL_TYPES.find { |c| c["id"] == object.confidential_type }&.dig("name") || "Não informado"
  end

  attribute :hiring_manager_id do |object|
    object.hiring_manager_id
  end

  attribute :hiring_manager_name do |object|
    object[:hiring_manager_name] || object.hiring_manager&.name
  end

  attribute :hiring_manager_email do |object|
    object[:hiring_manager_email] || object.hiring_manager&.email
  end

  attribute :share_url do |object|
    next nil unless object.is_published

    account_slug = object.try(:[], :account_slug) || object.account&.slug
    next nil if account_slug.blank?

    domain = ENV["FRONT_URL"] || "localhost:3000"
    "#{domain}/vagas/#{object.slug}/#{account_slug}"
  end

  attribute :jd_quality_score do |object|
    object.jd_quality_score.presence || {}
  end

  attribute :lia_job_description do |object|
    lia = object.lia_job_description.presence || {}
    next nil if lia.blank?

    {
      status:          lia["status"],
      enriched_at:     lia["enriched_at"],
      approved_at:     lia["approved_at"],
      approved_by:     lia["approved_by"],
      method_version:  lia["method_version"],
      description:     lia["description"],
      quality_report:  lia["quality_report"],
      enriched_jd:     lia["enriched_jd"]
    }
  end
end
