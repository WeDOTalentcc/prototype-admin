# frozen_string_literal: true

# ADD to config/routes.rb inside the v1 namespace:
#
# namespace :v1 do
#   # ... existing routes ...
#
#   # Auth: Magic link
#   namespace :auth do
#     get "magic-link/verify", to: "magic_links#verify"
#   end
#
#   # Onboarding
#   namespace :users do
#     post "invite", to: "onboarding#invite"
#   end
#
#   scope :onboarding do
#     get "status", to: "users/onboarding#status"
#     patch "progress", to: "users/onboarding#progress"
#     post "consent", to: "users/onboarding#consent"
#     get "settings", to: "users/onboarding#settings"
#     patch "settings", to: "users/onboarding#settings"
#   end
# end
