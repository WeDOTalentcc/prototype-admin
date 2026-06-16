# frozen_string_literal: true

class ChatNotification < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :user

  validates :user_id, presence: true
end
