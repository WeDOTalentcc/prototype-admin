# frozen_string_literal: true

module TagReplacer
  class Registry
    TagDefinition = Data.define(:tag, :entity, :attribute, :resolver_type, :description, :extra)

    TAGS = [
      # === Candidate ===
      TagDefinition.new(tag: "{{candidate_name}}", entity: :candidate, attribute: :name, resolver_type: :attribute, description: "Full candidate name", extra: {}),
      TagDefinition.new(tag: "{{candidate_first_name}}", entity: :candidate, attribute: :first_name, resolver_type: :attribute, description: "Candidate first name", extra: {}),
      TagDefinition.new(tag: "{{candidate_email}}", entity: :candidate, attribute: :email, resolver_type: :attribute, description: "Candidate email", extra: {}),
      TagDefinition.new(tag: "{{candidate_phone}}", entity: :candidate, attribute: :phone, resolver_type: :attribute, description: "Candidate phone", extra: {}),
      TagDefinition.new(tag: "{{candidate_mobile_phone}}", entity: :candidate, attribute: :mobile_phone, resolver_type: :attribute, description: "Candidate mobile phone", extra: {}),

      # Legacy Portuguese tags (deprecated but supported)
      TagDefinition.new(tag: "{{nome_do_candidato}}", entity: :candidate, attribute: :name, resolver_type: :attribute, description: "Nome completo do candidato", extra: {}),
      TagDefinition.new(tag: "{{email_do_candidato}}", entity: :candidate, attribute: :email, resolver_type: :attribute, description: "E-mail do candidato", extra: {}),

      # === User/Recruiter ===
      TagDefinition.new(tag: "{{user_name}}", entity: :user, attribute: :name, resolver_type: :attribute, description: "User full name", extra: {}),
      TagDefinition.new(tag: "{{user_email}}", entity: :user, attribute: :email, resolver_type: :attribute, description: "User email", extra: {}),
      TagDefinition.new(tag: "{{nome_do_usuario}}", entity: :user, attribute: :name, resolver_type: :attribute, description: "Nome do usuário", extra: {}),
      TagDefinition.new(tag: "{{email_do_usuario}}", entity: :user, attribute: :email, resolver_type: :attribute, description: "E-mail do usuário", extra: {}),

      TagDefinition.new(tag: "{{recruiter_name}}", entity: :recruiter, attribute: :name, resolver_type: :attribute, description: "Recruiter name", extra: {}),
      TagDefinition.new(tag: "{{recruiter_email}}", entity: :recruiter, attribute: :email, resolver_type: :attribute, description: "Recruiter email", extra: {}),
      TagDefinition.new(tag: "{{recruiter_phone}}", entity: :recruiter, attribute: :phone, resolver_type: :attribute, description: "Recruiter phone", extra: {}),

      # === Job ===
      TagDefinition.new(tag: "{{job_title}}", entity: :job, attribute: :title, resolver_type: :attribute, description: "Job title", extra: {}),
      TagDefinition.new(tag: "{{job_description}}", entity: :job, attribute: :description, resolver_type: :attribute, description: "Job description", extra: {}),
      TagDefinition.new(tag: "{{job_location}}", entity: :job, attribute: :location, resolver_type: :attribute, description: "Job location", extra: {}),
      TagDefinition.new(tag: "{{job_workplace_type}}", entity: :job, attribute: nil, resolver_type: :method, description: "Job workplace type (Remoto, Híbrido, Presencial)", extra: { method_name: :workplace_type_text }),
      TagDefinition.new(tag: "{{job_salary_from}}", entity: :job, attribute: :salary_from, resolver_type: :attribute, description: "Job salary from", extra: {}),
      TagDefinition.new(tag: "{{job_salary_to}}", entity: :job, attribute: :salary_to, resolver_type: :attribute, description: "Job salary to", extra: {}),

      # === Account ===
      TagDefinition.new(tag: "{{account_name}}", entity: :account, attribute: :name, resolver_type: :attribute, description: "Account name", extra: {}),

      # === Client Contact ===
      TagDefinition.new(tag: "{{client_contact_name}}", entity: :client_contact, attribute: :name, resolver_type: :attribute, description: "Client contact name", extra: {}),
      TagDefinition.new(tag: "{{client_contact_email}}", entity: :client_contact, attribute: :email, resolver_type: :attribute, description: "Client contact email", extra: {}),

      # === Client Company ===
      TagDefinition.new(tag: "{{client_company_name}}", entity: :client_company, attribute: :name, resolver_type: :attribute, description: "Client company name", extra: {}),
      TagDefinition.new(tag: "{{client_company_corporate_name}}", entity: :client_company, attribute: :corporate_name, resolver_type: :attribute, description: "Client company corporate name", extra: {}),

      # === Dates ===
      TagDefinition.new(tag: "{{date_today}}", entity: nil, attribute: nil, resolver_type: :date, description: "Current date (EN format)", extra: { format: :en }),
      TagDefinition.new(tag: "{{date_br_today}}", entity: nil, attribute: nil, resolver_type: :date, description: "Current date (BR format)", extra: { format: :br }),

      # === URLs ===
      TagDefinition.new(tag: "{{candidate_access_url}}", entity: :candidate, attribute: nil, resolver_type: :url, description: "Candidate access URL", extra: { url_type: :candidate_access }),
      TagDefinition.new(tag: "{{evaluation_candidate_url}}", entity: :evaluation_candidate, attribute: nil, resolver_type: :method, description: "Evaluation candidate URL", extra: { method_name: :get_evaluation_candidate_url }),

      # === Interview ===
      TagDefinition.new(tag: "{{interview_date}}", entity: :interview, attribute: :formatted_date, resolver_type: :attribute, description: "Interview date (formatted)", extra: {}),
      TagDefinition.new(tag: "{{response_deadline}}", entity: :interview, attribute: :formatted_deadline, resolver_type: :attribute, description: "Response deadline (humanized)", extra: {}),

      # === Email Tracking ===
      TagDefinition.new(tag: "{{tracking_pixel}}", entity: :dispatch_message, attribute: nil, resolver_type: :method, description: "Email tracking pixel (1x1 GIF)", extra: { method_name: :tracking_pixel_url }),
      TagDefinition.new(tag: "{{unsubscribe_url}}", entity: :dispatch_message, attribute: nil, resolver_type: :method, description: "Email unsubscribe/opt-out URL", extra: { method_name: :unsubscribe_url })
    ].freeze

    def self.tags_in(message)
      return [] if message.blank?
      TAGS.select { |tag_def| message.include?(tag_def.tag) }
    end

    def self.all(entities: nil)
      return TAGS if entities.nil?
      TAGS.select { |t| entities.include?(t.entity) }
    end

    def self.available_tags(entities: nil)
      all(entities: entities).map do |t|
        { tag: t.tag, entity: t.entity, description: t.description }
      end
    end
  end
end
