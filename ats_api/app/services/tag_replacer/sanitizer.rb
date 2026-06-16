# frozen_string_literal: true

module TagReplacer
  class Sanitizer
    ALLOWED_METHODS = %i[
      name first_name last_name email phone mobile_phone
      title description location occupation_name company_name
      cpf rg cnpj address city state zip
      linkedin logo_url corporate_name
      get_evaluation_candidate_url workplace_type_text
      tracking_pixel_url unsubscribe_url
    ].to_set.freeze

    ALLOWED_ENTITIES = %i[
      candidate recruiter job client_contact client_company user
      interview experience education business proposal evaluation_candidate account
      dispatch_message
    ].to_set.freeze

    def self.allowed_method?(method_name)
      ALLOWED_METHODS.include?(method_name.to_sym)
    end

    def self.allowed_entity?(entity_key)
      ALLOWED_ENTITIES.include?(entity_key.to_sym)
    end
  end
end
