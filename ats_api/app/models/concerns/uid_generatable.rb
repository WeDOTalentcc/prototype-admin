# frozen_string_literal: true

module UidGeneratable
  extend ActiveSupport::Concern

  included do
    before_create :generate_uid
    validates :uid, uniqueness: true, allow_nil: true
    index_uid if respond_to?(:index_uid)
  end

  private

  def generate_uid
    self.uid = generate_unique_uid
  end

  def generate_unique_uid
    loop do
      candidate = SecureRandom.uuid
      break candidate unless self.class.exists?(uid: candidate)
    end
  end
end
