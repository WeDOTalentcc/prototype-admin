# config/initializers/active_storage_custom_types.rb

# Se quiser servir 'audio/ogg' inline no navegador
Rails.application.config.active_storage.content_types_to_serve_as_binary.delete("audio/ogg")
Rails.application.config.active_storage.content_types_allowed_inline << "audio/ogg"
