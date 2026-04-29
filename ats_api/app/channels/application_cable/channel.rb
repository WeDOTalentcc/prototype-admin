module ApplicationCable
  class Channel < ActionCable::Channel::Base
    include ApplicationCable::Authenticatable

    def subscribed
      return unless authenticate_user!

      after_authentication
    end

    def unsubscribed
      stop_all_streams
    end

    private

    def after_authentication; end
  end
end
