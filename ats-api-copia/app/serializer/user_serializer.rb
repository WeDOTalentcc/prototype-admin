class UserSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :email,
    :name,
    :role,
    :permissions,
    :workos_user_id,
    :avatar_url,
    :last_login_at,
    :status,
    :fork_uuid
  )
end
  