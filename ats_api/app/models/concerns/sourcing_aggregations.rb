# frozen_string_literal: true

module SourcingAggregations
  extend ActiveSupport::Concern

  def calculate_aggregated_stats
    profiles = sourced_profile_sourcings.where(is_deleted: false).includes(:sourced_profile)
    sourced_profiles = profiles.map(&:sourced_profile).compact

    {
      profile_stats: calculate_profile_stats(sourced_profiles, profiles),
      counts: calculate_counts(profiles, sourced_profiles),
      score_stats: calculate_score_stats(profiles),
      experience_stats: calculate_experience_stats(sourced_profiles),
      salary_stats: calculate_salary_stats(sourced_profiles),
      location_distribution: calculate_location_distribution(sourced_profiles),
      skills_distribution: calculate_skills_distribution(sourced_profiles),
      languages_distribution: calculate_languages_distribution(sourced_profiles),
      education_stats: calculate_education_stats(sourced_profiles),
      remote_work_stats: calculate_remote_work_stats(sourced_profiles),
      work_model_stats: calculate_work_model_stats(sourced_profiles),
      diversity_stats: calculate_diversity_stats(sourced_profiles),
      companies_distribution: calculate_companies_distribution(sourced_profiles),
      contact_stats: calculate_contact_stats(sourced_profiles),
      age_stats: calculate_age_stats(sourced_profiles),
      top_candidates_summary: calculate_top_candidates_summary(profiles),
      common_strengths: calculate_common_strengths(sourced_profiles),
      skill_gaps: calculate_skill_gaps(sourced_profiles),
      calculated_at: Time.current.iso8601
    }
  end

  def refresh_aggregated_stats!
    stats = calculate_aggregated_stats
    total = stats.dig(:profile_stats, :total) || 0
    computed_cost = total.zero? || credits_used.nil? ? 0 : (credits_used.to_f / total).round(2)

    update_columns(aggregated_stats: stats, cost_per_profile: computed_cost)
    stats
  end

  private

  def calculate_profile_stats(sourced_profiles, profiles)
    status_counts = sourced_profiles.group_by(&:status).transform_values(&:count)
    scores = profiles.filter_map(&:score)

    {
      total: sourced_profiles.size,
      new: status_counts["new"] || 0,
      viewed: status_counts["viewed"] || 0,
      interested: status_counts["interested"] || 0,
      contacted: status_counts["contacted"] || 0,
      rejected: status_counts["rejected"] || 0,
      hired: status_counts["hired"] || 0,
      imported: sourced_profiles.count { |p| p.candidate_id.present? },
      avg_score: scores.any? ? (scores.sum / scores.size.to_f).round(2) : nil,
      avg_experience: calculate_avg_experience(sourced_profiles),
      with_email: sourced_profiles.count { |p| p.has_emails },
      with_phone: sourced_profiles.count { |p| p.has_phone_numbers }
    }
  end

  def calculate_avg_experience(sourced_profiles)
    years = sourced_profiles.filter_map(&:total_experience_years)
    return nil if years.empty?

    (years.sum / years.size.to_f).round(1)
  end

  def calculate_counts(profiles, sourced_profiles)
    {
      total: profiles.count,
      with_score: profiles.where.not(score: nil).count,
      without_score: profiles.where(score: nil).count,
      from_linkedin: sourced_profiles.count { |p| p.provider == "pearch" },
      from_local: sourced_profiles.count { |p| p.provider == "local" },
      with_curriculum: sourced_profiles.count { |p| p.curriculum_text.present? },
      already_candidates: sourced_profiles.count { |p| p.candidate_id.present? }
    }
  end

  def calculate_score_stats(profiles)
    scores = profiles.pluck(:score).compact
    return empty_score_stats if scores.empty?

    {
      average: (scores.sum / scores.count.to_f).round(1),
      median: calculate_median(scores),
      min: scores.min,
      max: scores.max,
      std_deviation: calculate_std_deviation(scores).round(2),
      distribution: {
        excellent: scores.count { |s| s >= 90 },
        good: scores.count { |s| s >= 70 && s < 90 },
        regular: scores.count { |s| s >= 50 && s < 70 },
        low: scores.count { |s| s < 50 }
      },
      above_90: scores.count { |s| s >= 90 },
      above_80: scores.count { |s| s >= 80 },
      above_70: scores.count { |s| s >= 70 },
      above_60: scores.count { |s| s >= 60 },
      above_50: scores.count { |s| s >= 50 }
    }
  end

  def calculate_experience_stats(sourced_profiles)
    years = sourced_profiles.map(&:total_experience_years).compact
    return empty_numeric_stats if years.empty?

    {
      average: (years.sum / years.count.to_f).round(1),
      median: calculate_median(years),
      min: years.min,
      max: years.max,
      distribution: {
        junior: years.count { |y| y <= 2 },
        pleno: years.count { |y| y > 2 && y <= 5 },
        senior: years.count { |y| y > 5 && y <= 10 },
        specialist: years.count { |y| y > 10 }
      },
      with_data: years.count,
      without_data: sourced_profiles.count - years.count
    }
  end

  def calculate_salary_stats(sourced_profiles)
    clt_values = sourced_profiles.map(&:clt_expectation).compact.map(&:to_f).reject(&:zero?)
    pj_values = sourced_profiles.map(&:pj_expectation).compact.map(&:to_f).reject(&:zero?)

    {
      clt: salary_stats_for(clt_values),
      pj: salary_stats_for(pj_values),
      with_clt_expectation: clt_values.count,
      with_pj_expectation: pj_values.count,
      without_salary_info: sourced_profiles.count { |p| p.clt_expectation.blank? && p.pj_expectation.blank? }
    }
  end

  def salary_stats_for(values)
    return { average: nil, median: nil, min: nil, max: nil, distribution: {} } if values.empty?

    {
      average: (values.sum / values.count.to_f).round(2),
      median: calculate_median(values),
      min: values.min,
      max: values.max,
      distribution: {
        "ate_5k" => values.count { |v| v <= 5000 },
        "5k_8k" => values.count { |v| v > 5000 && v <= 8000 },
        "8k_12k" => values.count { |v| v > 8000 && v <= 12000 },
        "12k_15k" => values.count { |v| v > 12000 && v <= 15000 },
        "15k_20k" => values.count { |v| v > 15000 && v <= 20000 },
        "acima_20k" => values.count { |v| v > 20000 }
      }
    }
  end

  def calculate_location_distribution(sourced_profiles)
    cities = sourced_profiles.map(&:city).compact.map { |c| c.to_s.downcase.strip }
    states = sourced_profiles.map(&:state).compact.map { |s| s.to_s.downcase.strip }
    countries = sourced_profiles.map(&:country).compact.map { |c| c.to_s.downcase.strip }

    {
      by_city: count_and_sort(cities, limit: 15),
      by_state: count_and_sort(states, limit: 10),
      by_country: count_and_sort(countries, limit: 10),
      with_location: sourced_profiles.count { |p| p.city.present? || p.state.present? },
      without_location: sourced_profiles.count { |p| p.city.blank? && p.state.blank? }
    }
  end

  def calculate_skills_distribution(sourced_profiles)
    all_skills = []

    sourced_profiles.each do |profile|
      skills = profile.skills_data || []
      skills.each do |skill|
        skill_name = skill.is_a?(Hash) ? skill["name"] : skill
        all_skills << skill_name.to_s.downcase.strip if skill_name.present?
      end

      (profile.expertise || []).each do |exp|
        all_skills << exp.to_s.downcase.strip if exp.present?
      end
    end

    {
      top_skills: count_and_sort(all_skills, limit: 30),
      unique_count: all_skills.uniq.count,
      total_mentions: all_skills.count,
      profiles_with_skills: sourced_profiles.count { |p| (p.skills_data || []).any? || (p.expertise || []).any? }
    }
  end

  def calculate_languages_distribution(sourced_profiles)
    all_languages = []
    language_levels = []

    sourced_profiles.each do |profile|
      (profile.languages_data || []).each do |lang|
        if lang.is_a?(Hash)
          lang_name = lang["language"] || lang["name"]
          level = lang["level"] || lang["proficiency"]
          all_languages << lang_name.to_s.downcase.strip if lang_name.present?
          language_levels << "#{lang_name}_#{level}".downcase if lang_name.present? && level.present?
        else
          all_languages << lang.to_s.downcase.strip if lang.present?
        end
      end
    end

    english_levels = language_levels.select { |l| l.start_with?("english") || l.start_with?("inglês") }

    {
      by_language: count_and_sort(all_languages, limit: 15),
      by_language_level: count_and_sort(language_levels, limit: 30),
      english_distribution: count_and_sort(english_levels, limit: 10),
      profiles_with_languages: sourced_profiles.count { |p| (p.languages_data || []).any? },
      profiles_without_languages: sourced_profiles.count { |p| (p.languages_data || []).empty? }
    }
  end

  def calculate_education_stats(sourced_profiles)
    institutions = []
    degrees = []
    areas = []

    sourced_profiles.each do |profile|
      (profile.educations_data || []).each do |edu|
        institutions << (edu["campus"] || edu["institution"]).to_s.downcase.strip if edu["campus"] || edu["institution"]
        degrees << (edu["degree"] || edu["education_level"]).to_s.downcase.strip if edu["degree"] || edu["education_level"]
        areas << (edu["major"] || edu["study_area"]).to_s.downcase.strip if edu["major"] || edu["study_area"]
      end
    end

    {
      top_institutions: count_and_sort(institutions, limit: 15),
      by_degree: count_and_sort(degrees, limit: 10),
      by_area: count_and_sort(areas, limit: 15),
      from_top_universities: sourced_profiles.count { |p| p.is_top_universities },
      with_education_data: sourced_profiles.count { |p| (p.educations_data || []).any? },
      without_education_data: sourced_profiles.count { |p| (p.educations_data || []).empty? }
    }
  end

  def calculate_remote_work_stats(sourced_profiles)
    remote_values = sourced_profiles.map(&:remote_work)
    mobility_values = sourced_profiles.map(&:mobility)

    {
      accepts_remote: remote_values.count(true),
      prefers_onsite: remote_values.count(false),
      remote_not_specified: remote_values.count(nil),
      has_mobility: mobility_values.count(true),
      no_mobility: mobility_values.count(false),
      mobility_not_specified: mobility_values.count(nil),
      remote_with_mobility: sourced_profiles.count { |p| p.remote_work == true && p.mobility == true },
      onsite_only: sourced_profiles.count { |p| p.remote_work == false && p.mobility == false }
    }
  end

  def calculate_work_model_stats(sourced_profiles)
    total = sourced_profiles.count
    accepts_remote = sourced_profiles.count { |p| p.remote_work == true }
    accepts_onsite = sourced_profiles.count { |p| p.remote_work == false || p.mobility == true }
    accepts_hybrid = sourced_profiles.count { |p| p.remote_work == true && p.mobility == true }
    only_remote = sourced_profiles.count { |p| p.remote_work == true && p.mobility == false }
    only_onsite = sourced_profiles.count { |p| p.remote_work == false && p.mobility == false }
    flexible = sourced_profiles.count { |p| p.remote_work == true && p.mobility == true }
    not_specified = sourced_profiles.count { |p| p.remote_work.nil? && p.mobility.nil? }

    {
      total: total,
      accepts_remote: accepts_remote,
      accepts_remote_percent: total.zero? ? 0 : ((accepts_remote.to_f / total) * 100).round(1),
      accepts_onsite: accepts_onsite,
      accepts_onsite_percent: total.zero? ? 0 : ((accepts_onsite.to_f / total) * 100).round(1),
      accepts_hybrid: accepts_hybrid,
      accepts_hybrid_percent: total.zero? ? 0 : ((accepts_hybrid.to_f / total) * 100).round(1),
      only_remote: only_remote,
      only_remote_percent: total.zero? ? 0 : ((only_remote.to_f / total) * 100).round(1),
      only_onsite: only_onsite,
      only_onsite_percent: total.zero? ? 0 : ((only_onsite.to_f / total) * 100).round(1),
      flexible: flexible,
      flexible_percent: total.zero? ? 0 : ((flexible.to_f / total) * 100).round(1),
      not_specified: not_specified,
      summary: {
        remoto: only_remote,
        hibrido: accepts_hybrid,
        presencial: only_onsite,
        flexivel: flexible,
        nao_informado: not_specified
      }
    }
  end

  def calculate_diversity_stats(sourced_profiles)
    genders = sourced_profiles.map(&:gender).compact
    total = sourced_profiles.count

    gender_labels = {
      0 => "nao_informado",
      1 => "masculino",
      2 => "feminino",
      3 => "outro",
      4 => "prefiro_nao_dizer",
      5 => "homem_transgenero",
      6 => "mulher_transgenero"
    }

    gender_distribution = genders.group_by { |g| gender_labels[g] || "nao_mapeado" }.transform_values(&:count)

    gender_text_distribution = sourced_profiles.map { |p| p.gender_text&.downcase&.strip }.compact.tally

    masculino = (gender_distribution["masculino"] || 0) + (gender_text_distribution["homem cisgânero"] || 0) + (gender_text_distribution["homem cisgenero"] || 0)
    feminino = (gender_distribution["feminino"] || 0) + (gender_text_distribution["mulher cisgânero"] || 0) + (gender_text_distribution["mulher cisgenero"] || 0)
    outros = total - masculino - feminino - (gender_distribution["nao_informado"] || 0)

    {
      by_gender: gender_distribution,
      by_gender_text: gender_text_distribution,
      gender_informed: genders.count,
      gender_not_informed: sourced_profiles.count - genders.count,
      summary: {
        masculino: masculino,
        masculino_percent: total.zero? ? 0 : ((masculino.to_f / total) * 100).round(1),
        feminino: feminino,
        feminino_percent: total.zero? ? 0 : ((feminino.to_f / total) * 100).round(1),
        outros: [ outros, 0 ].max,
        outros_percent: total.zero? ? 0 : (([ outros, 0 ].max.to_f / total) * 100).round(1),
        nao_informado: gender_distribution["nao_informado"] || 0
      }
    }
  end

  def calculate_companies_distribution(sourced_profiles)
    current_companies = sourced_profiles.map(&:current_company).compact.map { |c| c.to_s.downcase.strip }

    all_companies = []
    sourced_profiles.each do |profile|
      (profile.experiences_data || []).each do |exp|
        next unless exp.is_a?(Hash)

        company = exp.dig("company_info", "name") || exp["company"]
        all_companies << company.to_s.downcase.strip if company.present?

        (exp["company_roles"] || []).each do |role|
          company = role["company"]
          all_companies << company.to_s.downcase.strip if company.present?
        end
      end
    end

    {
      current_companies: count_and_sort(current_companies, limit: 20),
      all_companies_history: count_and_sort(all_companies, limit: 30),
      currently_employed: sourced_profiles.count { |p| p.current_company.present? },
      is_decision_maker: sourced_profiles.count { |p| p.is_decision_maker }
    }
  end

  def calculate_contact_stats(sourced_profiles)
    {
      with_email: sourced_profiles.count { |p| p.email.present? || p.has_emails },
      with_phone: sourced_profiles.count { |p| p.phone.present? || p.has_phone_numbers },
      with_linkedin: sourced_profiles.count { |p| p.linkedin_url.present? || p.linkedin_slug.present? },
      with_github: sourced_profiles.count { |p| p.github.present? },
      contactable: sourced_profiles.count { |p| p.email.present? || p.has_emails || p.phone.present? || p.has_phone_numbers },
      not_contactable: sourced_profiles.count { |p| p.email.blank? && !p.has_emails && p.phone.blank? && !p.has_phone_numbers }
    }
  end

  def count_and_sort(array, limit: 10)
    array.tally.sort_by { |_, count| -count }.first(limit).to_h
  end

  def calculate_median(array)
    return nil if array.empty?

    sorted = array.sort
    mid = sorted.length / 2
    sorted.length.odd? ? sorted[mid] : ((sorted[mid - 1] + sorted[mid]) / 2.0).round(1)
  end

  def calculate_std_deviation(array)
    return 0 if array.length < 2

    mean = array.sum / array.length.to_f
    variance = array.map { |x| (x - mean)**2 }.sum / array.length
    Math.sqrt(variance)
  end

  def empty_score_stats
    {
      average: nil,
      median: nil,
      min: nil,
      max: nil,
      std_deviation: nil,
      distribution: { excellent: 0, good: 0, regular: 0, low: 0 },
      above_90: 0,
      above_80: 0,
      above_70: 0,
      above_60: 0,
      above_50: 0
    }
  end

  def empty_numeric_stats
    {
      average: nil,
      median: nil,
      min: nil,
      max: nil,
      distribution: {},
      with_data: 0,
      without_data: 0
    }
  end

  def calculate_age_stats(sourced_profiles)
    ages = sourced_profiles.map(&:estimated_age).compact
    return empty_age_stats if ages.empty?

    total = sourced_profiles.count
    {
      average: (ages.sum / ages.count.to_f).round(1),
      median: calculate_median(ages),
      min: ages.min,
      max: ages.max,
      with_data: ages.count,
      without_data: total - ages.count,
      distribution: {
        "18_25" => ages.count { |a| a >= 18 && a <= 25 },
        "26_30" => ages.count { |a| a >= 26 && a <= 30 },
        "31_35" => ages.count { |a| a >= 31 && a <= 35 },
        "36_40" => ages.count { |a| a >= 36 && a <= 40 },
        "41_50" => ages.count { |a| a >= 41 && a <= 50 },
        "51_plus" => ages.count { |a| a > 50 }
      },
      summary: {
        jovens: ages.count { |a| a <= 30 },
        plenos: ages.count { |a| a > 30 && a <= 40 },
        seniors: ages.count { |a| a > 40 }
      }
    }
  end

  def empty_age_stats
    {
      average: nil, median: nil, min: nil, max: nil,
      with_data: 0, without_data: 0,
      distribution: {}, summary: { jovens: 0, plenos: 0, seniors: 0 }
    }
  end

  def calculate_top_candidates_summary(profiles)
    top_10 = profiles.where.not(score: nil).order(score: :desc).limit(10)
    top_profiles = top_10.map(&:sourced_profile).compact

    return empty_top_candidates if top_profiles.empty?

    skills_freq = top_profiles.flat_map { |p| (p.skills_data || []).map { |s| s.is_a?(Hash) ? s["name"] : s }.compact }.tally
    companies_freq = top_profiles.map(&:current_company).compact.tally
    locations_freq = top_profiles.map(&:city).compact.tally
    experience_years = top_profiles.map(&:total_experience_years).compact

    {
      count: top_profiles.count,
      avg_score: top_10.average(:score)&.round(1),
      avg_experience_years: experience_years.any? ? (experience_years.sum / experience_years.count.to_f).round(1) : nil,
      common_skills: skills_freq.sort_by { |_, v| -v }.first(10).to_h,
      common_companies: companies_freq.sort_by { |_, v| -v }.first(5).to_h,
      common_locations: locations_freq.sort_by { |_, v| -v }.first(5).to_h,
      profiles: top_profiles.map do |p|
        sps = top_10.find { |t| t.sourced_profile_id == p.id }
        {
          id: p.id,
          name: p.name,
          score: sps&.score,
          title: p.current_title || p.title,
          company: p.current_company,
          experience_years: p.total_experience_years,
          location: p.city
        }
      end
    }
  end

  def empty_top_candidates
    { count: 0, avg_score: nil, avg_experience_years: nil, common_skills: {}, common_companies: {}, common_locations: {}, profiles: [] }
  end

  def calculate_common_strengths(sourced_profiles)
    all_skills = sourced_profiles.flat_map do |p|
      extract_string_values(p.skills_data, "name")
    end

    all_expertise = sourced_profiles.flat_map do |p|
      extract_expertise_values(p.expertise)
    end

    combined = all_skills + all_expertise

    skill_counts = combined.tally
    total_profiles = sourced_profiles.count

    common_skills = skill_counts.select { |_, count| count >= (total_profiles * 0.2) }.sort_by { |_, v| -v }

    {
      most_common: common_skills.first(15).to_h,
      shared_by_majority: common_skills.select { |_, count| count >= (total_profiles * 0.5) }.to_h,
      unique_skills_count: skill_counts.count,
      avg_skills_per_profile: total_profiles.zero? ? 0 : (combined.count.to_f / total_profiles).round(1)
    }
  end

  def calculate_skill_gaps(sourced_profiles)
    all_skills = sourced_profiles.flat_map { |p| extract_string_values(p.skills_data, "name") }
    skill_counts = all_skills.tally
    total_profiles = sourced_profiles.count

    rare_skills = skill_counts.select { |_, count| count == 1 }.keys
    uncommon_skills = skill_counts.select { |_, count| count <= (total_profiles * 0.1) && count > 1 }.sort_by { |_, v| v }

    profiles_with_few_skills = sourced_profiles.count { |p| (p.skills_data || []).count < 3 }
    profiles_without_skills = sourced_profiles.count { |p| (p.skills_data || []).empty? && (p.expertise || []).empty? }

    {
      rare_skills: rare_skills.first(20),
      uncommon_skills: uncommon_skills.first(15).to_h,
      profiles_with_few_skills: profiles_with_few_skills,
      profiles_without_skills: profiles_without_skills,
      skill_coverage: total_profiles.zero? ? 0 : (((total_profiles - profiles_without_skills).to_f / total_profiles) * 100).round(1)
    }
  end

  def extract_string_values(data, key)
    (data || []).filter_map do |item|
      value = item.is_a?(Hash) ? item[key] : item
      value.is_a?(String) ? value.downcase : nil
    end
  end

  def extract_expertise_values(data)
    (data || []).filter_map do |item|
      value = item.is_a?(Hash) ? (item["description"] || item["type"]) : item
      value.is_a?(String) ? value.downcase : nil
    end
  end
end
