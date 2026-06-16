Rails.configuration.active_storage.paths_for_service = lambda { |key, _service|
  if Apartment::Tenant.current.present?
    "#{Apartment::Tenant.current}/#{key}"
  else
    key
  end
}
