# Be sure to restart your server when you modify this file.

# Configure parameters to be partially matched (e.g. passw matches password) and filtered from the log file.
# Use this to limit dissemination of sensitive information.
# See the ActiveSupport::ParameterFilter documentation for supported notations and behaviors.
Rails.application.config.filter_parameters += [
  :passw, :email, :secret, :token, :_key, :crypt, :salt, :certificate, :otp, :ssn,
  :name, :phone, :mobile_phone, :cpf, :linkedin, :github, :portfolio,
  :self_introduction, :resume, :curriculum, :text_response, :search_text,
  :candidate_name, :recruiter_name, :file_name, :filename
]
