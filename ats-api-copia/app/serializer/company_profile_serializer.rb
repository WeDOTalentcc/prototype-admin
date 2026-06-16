# frozen_string_literal: true

class CompanyProfileSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :client_account_id,
    :name,
    :trading_name,
    :website,
    :logo_url,
    :cnpj,
    :industry,
    :sector,
    :company_size,
    :founded_year,
    :description,
    :short_description,
    :headquarters_city,
    :headquarters_state,
    :headquarters_country,
    :address,
    :main_phone,
    :hr_phone,
    :main_email,
    :hr_email,
    :linkedin_url,
    :glassdoor_url,
    :employee_count,
    :revenue_range,
    :is_active,
    :is_default,
    :culture_analyzed,
    :culture_analysis_date,
    :culture_insights,
    :ats_history_analyzed,
    :ats_analysis_date,
    :ats_insights,
    :additional_data,
    :created_by,
    :created_at,
    :updated_at
  )
end
