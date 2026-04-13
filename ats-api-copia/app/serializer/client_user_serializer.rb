# frozen_string_literal: true

class ClientUserSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :company_id,
    :user_id,
    :email,
    :name,
    :role,
    :permissions,
    :status,
    :invitation_token,
    :invitation_expires_at,
    :invited_at,
    :accepted_at,
    :last_login_at,
    :is_deleted,
    :deleted_at,
    :deleted_by,
    :created_at,
    :updated_at
  )
end
