# frozen_string_literal: true

Rails.application.routes.draw do
  mount ActionCable.server => "/cable"
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Render dynamic PWA files from app/views/pwa/*
  get "service-worker" => "rails/pwa#service_worker", as: :pwa_service_worker
  get "manifest" => "rails/pwa#manifest", as: :pwa_manifest

  namespace :v1 do
    post "sessions", to: "sessions#create"
    get "me", to: "sessions#me"
    post "logout", to: "sessions#logout"

    namespace :auth do
      get "magic-link/verify", to: "magic_links#verify"
    end

    # Onboarding routes — controller is V1::Users::OnboardingController
    # but routes live at /v1/onboarding/* per API contract
    scope :onboarding, controller: "users/onboarding" do
      get "status", action: :status
      patch "progress", action: :progress
      get "settings", action: :settings
      patch "settings", action: :settings, as: :update_onboarding_settings
      post "consent", action: :consent
    end

    namespace :users do
      post "invite", to: "onboarding#invite"

      get "applies", to: "applies#index"
      get "applies/:id", to: "applies#show"
      post "applies", to: "applies#create"
      put "applies/:id", to: "applies#update"
      delete "applies/:id", to: "applies#destroy"

      get "jobs", to: "jobs#index"
      get "jobs/:id", to: "jobs#show"
      post "jobs", to: "jobs#create"
      put "jobs/:id", to: "jobs#update"
      delete "jobs/:id", to: "jobs#destroy"

      get "selective_processes", to: "selective_processes#index"
      get "selective_processes/:id", to: "selective_processes#show"
      post "selective_processes", to: "selective_processes#create"
      put "selective_processes/:id", to: "selective_processes#update"
      delete "selective_processes/:id", to: "selective_processes#destroy"

      get "candidates", to: "candidates#index"
      get "candidates/:id", to: "candidates#show"
      post "candidates", to: "candidates#create"
      put "candidates/:id", to: "candidates#update"
      delete "candidates/:id", to: "candidates#destroy"

      get "search", to: "users#index"
      get "search/:id", to: "users#show"
      post "create", to: "users#create"
      put "edit/:id", to: "users#update"
      delete "delete/:id", to: "users#destroy"

      get "messages", to: "messages#index"
      get "messages/:id", to: "messages#show"
      post "messages", to: "messages#create"
      put "messages/:id", to: "messages#update"
      delete "messages/:id", to: "messages#destroy"

      resources :client_accounts
      resources :client_users
      resources :company_profiles
      resources :departments
      resources :email_templates
      resources :interviews
      resources :notifications

      resources :talent_pools do
        member do
          get :candidates
          post :add_candidates
          post :move_to_job
          post :create_job_from_pool
        end
      end

      resources :recruitment_campaigns do
        member do
          post :advance_stage
          post :complete_stage
          post :add_checkpoint
        end
      end
    end
  end
  # Defines the root path route ("/")
  # root "posts#index"
end
