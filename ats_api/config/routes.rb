# frozen_string_literal: true

require "sidekiq/web"
# opcional, se usar sidekiq-cron:
# require "sidekiq/cron/web"

# Sessão própria da UI (necessária mesmo em API-only)
Sidekiq::Web.use Rack::Session::Cookie, secret: Rails.application.secret_key_base

# Proteção (recomendo em produção)
if Rails.env.production?
  Sidekiq::Web.use Rack::Auth::Basic do |user, pass|
    ActiveSupport::SecurityUtils.secure_compare(user, ENV.fetch("SIDEKIQ_WEB_USER")) &
      ActiveSupport::SecurityUtils.secure_compare(pass, ENV.fetch("SIDEKIQ_WEB_PASSWORD"))
  end
end


Rails.application.routes.draw do
  mount Sidekiq::Web => "/sidekiq"
  mount ActionCable.server => "/cable"

  get "/healthz", to: proc { [ 200, { "Content-Type"=>"text/plain" }, [ "ok" ] ] }
  get "up" => "rails/health#show", as: :rails_health_check

  get "/.well-known/appspecific/com.chrome.devtools.json", to: proc { [ 204, {}, [] ] }

  namespace :v1 do
    # Agent token exchange: trade one-time token (OTT) for short-lived service token
    post "agent_tokens/exchange", to: "agent_tokens#exchange"
    post "agent_tokens/refresh", to: "agent_tokens#refresh"
    # OAuth2-like token endpoint for service-to-service auth
    post "oauth/token", to: "oauth#create"
    post "sessions", to: "sessions#create"
    post "sessions/verify_mfa", to: "sessions#verify_mfa"
    post "sessions/resend_mfa", to: "sessions#resend_mfa"
    post "logout", to: "sessions#logout"

    # Alias top-level /v1/me — FastAPI lia-agent-system resolve Rails user via esse endpoint.
    # A rota canônica (namespace :users) é /v1/users/me (sessions#me).
    get "me", to: "sessions#me"

    get    "notifications",              to: "notifications#index"
    get    "notifications/unread-count", to: "notifications#unread_count"
    post   "notifications/read-all",     to: "notifications#read_all"
    get    "notifications/:id",          to: "notifications#show"
    post   "notifications/:id/read",     to: "notifications#read"
    put    "notifications/:id/read",     to: "notifications#read"
    post   "notifications/:id/dismiss",  to: "notifications#dismiss"
    delete "notifications/:id",          to: "notifications#dismiss"

    namespace :webhooks do
      resource :meta_whatsapp, only: [ :show, :create ], controller: "meta_whatsapp/meta_whatsapp"
      post "teams_chat", to: "microsoft_teams/teams_webhook#create"
      post "mailgun/tracking", to: "mailgun#tracking"
    end


    get "tracking/pixel/:token.gif", to: "tracking#pixel", as: :tracking_pixel
    get "tracking/click/:token", to: "tracking#click", as: :tracking_click
    get "email/opt-out/:token", to: "email_opt_outs#show", as: :email_opt_out
    post "email/opt-out/:token", to: "email_opt_outs#create"

    post "password_resets/", to: "password_reset_tokens#create"
    get "password_resets/:token", to: "password_reset_tokens#show"
    post "password_resets/:token/complete", to: "password_reset_tokens#complete"

    namespace :setups do
      get "/:setup_token", to: "setups#show"

      post "/:setup_token/create_user", to: "setups#create_user"

      post "/:setup_token/complete", to: "setups#complete"

      scope "/:setup_token" do
        resource :accounts, only: [ :show, :update ], controller: "accounts"
        resource :businesses, only: [ :show, :update, :create ], controller: "businesses"

        resource :workflow_templates, only: [ :show, :update ], controller: "workflow_templates", as: "workflow_template" do
          resources :selective_processes, controller: "workflow_templates/selective_processes", except: [ :new, :edit ]
        end
      end
    end

    get "auth/microsoft_graph_auth/callback", to: "users/microsoft_auths#callback"

    # WorkOS routes
    get "workos/login_url", to: "workos#login_url"
    get "workos/callback", to: "workos#callback"
    post "workos/webhook", to: "workos#webhook"
    get "workos/sso_options", to: "workos#sso_options"

    namespace :users do
        get "me", to: "/v1/sessions#me"
        post "me/mark_welcomed", to: "/v1/sessions#mark_welcomed"
        post "telemetry", to: "telemetry#create"

        get "microsoft_graph_auth/url", to: "microsoft_auths#url"
        get "microsoft_graph_auth/login_url", to: "microsoft_auths#login_url"
        get "microsoft_graph_auth/status", to: "microsoft_auths#status"
        namespace :integrations do
          namespace :microsoft do
            get "me", to: "profiles#show"
            post "email", to: "emails#create"
            post "email/bulk", to: "bulk_emails#create"
            post "teams/message", to: "teams#message"
          end
        end

        get "aggregators/:entity", to: "aggregators#index", as: "entity_aggregators"
        post "aggregators/:entity", to: "aggregators#index"

        resources :jobs do
          get "kanban", to: "jobs/applies/kanban#show", as: "kanban"
          member do
            get "analytics", to: "jobs/analytics#show", as: "analytics"
            get "context_for_ai", to: "jobs/context_for_ai#show", as: "context_for_ai"
            get "matching_candidates", to: "jobs/matching_candidates#index", as: "matching_candidates"
            post "add_candidates_from_list", to: "jobs#add_candidates_from_list", as: "add_candidates_from_list"
            post "suggestion/questions", to: "jobs/suggestions#evaluation_questions", as: "suggestion_questions"
            post "wsi_jd_big_five_extract", to: "jobs#wsi_jd_big_five_extract", as: "wsi_jd_big_five_extract"
            post "applies/approve_collection", to: "jobs/applies/applies#approve_collection", as: "approve_applies_collection"
            post "applies/reject_collection", to: "jobs/applies/applies#reject_collection", as: "reject_applies_collection"
            post "gate1/approve", to: "jobs/applies/applies#gate1_approve", as: "gate1_approve"
            post "gate1/reject", to: "jobs/applies/applies#gate1_reject", as: "gate1_reject"
            post "gate2/approve", to: "jobs/applies/applies#gate2_approve", as: "gate2_approve"
            post "gate2/reject", to: "jobs/applies/applies#gate2_reject", as: "gate2_reject"
            post "applies/send_reject_feedback", to: "jobs/applies/applies#send_reject_feedback", as: "send_reject_feedback_applies_collection"
            post "change_status", to: "jobs#change_status", as: "change_status"
            post "publish", to: "jobs#publish", as: "publish"
            post "unpublish", to: "jobs#unpublish", as: "unpublish"
            post "duplicate_selective_processes", to: "jobs#duplicate_selective_processes", as: "duplicate_selective_processes"
            get "activity_log", to: "jobs/activity_logs#index", as: "activity_log"
            get "evaluations", to: "jobs/evaluations#index", as: "evaluations"
            get "export", to: "jobs#export", as: "export"
            post "auto_source", to: "jobs/auto_source#create", as: "auto_source"
            post "wsi_jd_enrich", to: "jobs/wsi_jd_enrich#create", as: "wsi_jd_enrich"
            get "wsi_ranking", to: "jobs#wsi_ranking", as: "wsi_ranking"
          end
          resource :suggestion, only: [ :create ], controller: "jobs/suggestions"
          resource :organizational_structure, only: [ :show, :create, :update ], controller: "jobs/organizational_structures"
          resource :search_criteria, only: [ :update ], controller: "jobs/search_criteria" do
            post :generate, on: :member
          end
          collection do
            post "generate_query_from_job", to: "jobs/suggestions#generate_query_from_job"
            post "boolean_search", to: "jobs#boolean_search", as: "boolean_search"
            post "archive", to: "jobs#archive_collection", as: "archive"
            post "unarchive", to: "jobs#unarchive_collection", as: "unarchive"
            post "activate", to: "jobs#activate_collection", as: "activate"
            post "pause", to: "jobs#pause_collection", as: "pause"
            post "bulk_update", to: "jobs#bulk_update", as: "bulk_update"
            get "matches/candidates", to: "jobs/matches#candidates", as: "candidate_matches"
            get "data_for_description", to: "jobs#get_data_for_description"
            get "stats", to: "jobs#stats", as: "stats"
            get "alerts", to: "jobs#alerts", as: "alerts"
            get "priorities", to: "jobs#priorities", as: "priorities"
            get "urgency_levels", to: "jobs#urgency_levels", as: "urgency_levels"
            get "workplace_types", to: "jobs#workplace_types", as: "workplace_types"
            get "employment_types", to: "jobs#employment_types", as: "employment_types"
            get "seniorities", to: "jobs#seniorities", as: "seniorities"
            get "pcd_categories", to: "jobs#pcd_categories", as: "pcd_categories"
            get "confidential_types", to: "jobs#confidential_types", as: "confidential_types"
            post "bulk_analytics", to: "jobs/bulk_analytics#create", as: "bulk_analytics"
            get "pipeline_health", to: "jobs/pipeline_health#index", as: "pipeline_health"
          end
        end

        resources :llm_usages, only: %i[index show create] do
          collection do
            get :stats
            get :by_model
            get :by_operation
            get :by_service
            get :daily_trend
            get :failures
            get :recent
            get :top_consumers
          end
        end

        resource :llm_quotas, only: [] do
          collection do
            get :current
            patch :update_current
          end
        end

        resource :llm_configurations, only: %i[show create update destroy] do
          collection do
            get :providers
            get :status
            post :retry_sync
          end
        end

        get "applies/stats", to: "applies#stats"
        get "applies/aging", to: "applies#aging"

        get "dashboard/briefing", to: "dashboard#briefing"

        resource :notification_preferences, only: %i[show update]

        resources :notifications, only: %i[index show] do
          member do
            put :read
          end
          collection do
            post :mark_all_read
            get :unread_count
            post :send_push
          end
        end

        get "me/productivity", to: "productivity#show"

        get "applies", to: "applies#index"
        get "applies/:apply_id/email_followup_status", to: "applies/email_tracking#followup_status"
        get "applies/:apply_id/email_tracking_events", to: "applies/email_tracking#tracking_events"
        get "applies/:id/timeline", to: "applies#timeline"
        get "applies/:id", to: "applies#show"
        post "applies", to: "applies#create"
        post "applies/create_collection", to: "applies#create_collection"
        put "applies/update_collection", to: "applies#update_collection"
        delete "applies/delete_collection", to: "applies#delete_collection"
        put "applies/:id", to: "applies#update"
        delete "applies/:id", to: "applies#destroy"

        resources :apply_statuses, only: [ :index, :show, :create, :update, :destroy ]

        get "jobs", to: "jobs#index"
        get "jobs/:id", to: "jobs#show"
        post "jobs", to: "jobs#create"
        put "jobs/:id", to: "jobs#update"
        post "jobs/:id/copy", to: "jobs#copy", as: "copy_job"
        post "jobs/:id/copy_job_by_amount", to: "jobs#copy_job_by_amount", as: "copy_job_by_amount"
        delete "jobs/:id", to: "jobs#destroy"

        get "selective_processes", to: "selective_processes#index"
        get "selective_processes/:id", to: "selective_processes#show"
        post "selective_processes", to: "selective_processes#create"
        post "selective_processes/order", to: "selective_processes#order_position"
        put "selective_processes/:id", to: "selective_processes#update"
        delete "selective_processes/:id", to: "selective_processes#destroy"

        get "candidates/stats", to: "candidates#stats"
        get "candidates/search_hints", to: "candidates#search_hints"
        get "candidates", to: "candidates#index"
        get "candidates/suggestions", to: "candidates#get_suggestions"
        get "candidates/prompt_search", to: "candidates#prompt_search"
        post "candidates/generate_query", to: "candidates#generate_query"
        get "candidates/generate_query", to: "candidates#generate_query"
        post "candidates/upload_resume", to: "candidates#upload_resume"
        post "candidates/match_by_text", to: "candidate_matches#search"
        get "candidates/:id/communications", to: "candidates#communications"
        get "candidates/:id", to: "candidates#show"
        get "candidates/:id/calculate_remunerations", to: "candidates#get_calculated_remunerations"
        get "candidates/:id/calculate_benefits", to: "candidates#get_calculated_benefits"
        post "candidates", to: "candidates#create"
        put "candidates/:id", to: "candidates#update"
        delete "candidates/:id", to: "candidates#destroy"

        get "role_names", to: "role_names#index"
        get "role_names/suggestions", to: "role_names#suggestions"
        get "position_levels", to: "position_levels#index"

        resource :account, only: [ :show ]

        resources :workspaces

        resources :candidate_imports_preview, only: [ :create ]
        resources :candidate_imports, only: [ :create ]
        resources :linkedin_imports, only: [ :create ]

        resources :countries, only: %i[index show]
        resources :states, only: %i[index show create update destroy]

        resources :genders, only: %i[index]
        resources :marital_statuses, only: %i[index]

        resources :departments do
          member do
            get :ancestors
            get :descendants
            get :organization_chart
          end
          collection do
            get :tree
            post :reorder
            post :import
          end
        end

        resources :department_relationships

        resources :approvers do
          collection do
            post :reorder
            get :by_type
            get :approval_types
          end
        end

        resources :approval_requests, only: %i[index show create] do
          member do
            post :approve
            post :reject
            post :cancel
          end
          collection do
            get :pending
            get :my_requests
            get :by_reference
            post :create_chain
          end
        end

        resources :email_templates, only: %i[index show create update destroy] do
          member do
            post :duplicate
          end
          collection do
            get :categories
            get :tags
            post :generate_suggestion
            post "render", to: "email_templates#render_preview"
            post "render_for_candidate", to: "email_templates#render_for_candidate"
            post "send", to: "email_templates#send_email"
          end
        end

        resources :organizational_positions do
          member do
            get :reporting_chain
            get :direct_reports
          end
        end

        resources :teams do
          resources :team_members, only: %i[index create destroy]
          member do
            get :composition
          end
        end

        resources :position_assignments

        resources :replace_tags, only: %i[index]

        resources :meetings, only: %i[index show create update destroy] do
          collection do
            get :stats
          end
        end

        resources :calendar_events, only: %i[index show create update destroy] do
          member do
            post :sync
          end
          collection do
            post :suggest_schedule
            get :daily_agenda
            get :missing_feedback
          end
        end

        namespace :scheduling do
          resource :settings, only: %i[show update]
          resources :availability, only: %i[index], controller: "availability"
          resources :links, only: %i[index show create update destroy]
        end

        resources :interview_sessions, only: %i[index show create]

        resources :phone_call_interviews, only: %i[create]

        resources :addresses, only: %i[index show create update destroy] do
          collection do
            get "/:entity/:id", to: "addresses#relationships"
          end
        end
        resources :address_relationships, only: %i[index show create update destroy]

        get "messages", to: "messages#index"
        get "messages/:id", to: "messages#show"
        post "messages", to: "messages#create"
        put "messages/:id", to: "messages#update"
        delete "messages/:id", to: "messages#destroy"


        resources :audio_messages, only: [ :create, :show ] do
          member do
            get :audio
          end
        end

        resources :data_files, only: [ :index, :show, :create, :update, :destroy ]

        resources :shared_searches, only: %i[index show create update destroy] do
          member do
            post :resend
          end
        end

        resources :opinions, only: %i[index create destroy] do
          collection do
            get "candidate/:candidate_id/summary", to: "opinions#candidate_summary", as: :candidate_summary
            get "candidate/:candidate_id/history", to: "opinions#candidate_history", as: :candidate_history
          end
        end

        namespace :lia do
          get "profile_analyses/candidate/:candidate_id", to: "profile_analyses#by_candidate"
        end
        resources :businesses, only: [ :index, :show, :create, :update, :destroy ] do
          member do
            post :generate_big_five
          end
        end

        resources :feedbacks, only: [ :index, :show, :create, :update, :destroy ]

        resources :activity_logs, only: [ :index, :show, :create, :update, :destroy ] do
          member do
            post "rollback"
          end
        end
        resources :workflow_templates, only: [ :index, :show, :create, :update, :destroy ]

        resources :search_archetypes, param: :uid do
          collection do
            get :defaults
            get :enums
          end

          member do
            post :search
            post :duplicate
          end
        end

        resources :sourcings, only: [ :index, :show, :create, :update ] do
          member do
            get :stats
            get :context_for_ai
            post :recalculate_stats
            post :refine
            post :load_more
            post :move_to_job
            post :create_job
            post :add_candidate
          end
          collection do
            get :history
            get :credits
            get :transactions
            post :search_profiles
            post :find_similar_candidates
            post :bulk_stats, to: "sourcings_bulk_stats#create"
          end

          resources :refinements, only: [ :create ]
        end

        resources :sourced_profiles, only: [ :index, :show, :update ] do
          member do
            post :import
            get :similar
            post "enrich_emails", to: "sourced_profiles/contact_enrichment#enrich_emails"
            post "enrich_phones", to: "sourced_profiles/contact_enrichment#enrich_phones"
            post "enrich_contacts", to: "sourced_profiles/contact_enrichment#enrich_both"
            post "analyze", to: "sourced_profiles/analysis#create"
          end
          collection do
            post :convert_to_candidates
            get :stats
          end
        end

        resources :sourced_profile_sourcings, only: [ :index, :show, :create, :update, :destroy ] do
          member do
            get :similar_candidates
          end
          collection do
            post :load_more
          end
        end

        resources :talent_searches, only: [ :create ] do
          collection do
            get :credits
            get :search_profiles
            get :transactions
          end
        end

        resources :candidate_feedbacks, only: [ :index, :create, :destroy ] do
          collection do
            delete "/", action: :destroy
          end
        end

        resources :skills, only: [ :index, :show, :create, :update, :destroy ]
        resources :skill_categories, only: [ :index, :show, :create, :update, :destroy ]
        resources :skill_relationships, only: [ :index, :show, :create, :update, :destroy ] do
          collection do
            get "/experience_times", to: "skill_relationships#get_experience_times"
            get "/skill_levels", to: "skill_relationships#get_skill_levels"
          end
        end

        resources :behavioral_skills, only: [ :index, :show, :create, :update, :destroy ]
        resources :behavioral_skill_relationships, only: [ :index, :show, :create, :update, :destroy ] do
          collection do
            get "/experience_times", to: "behavioral_skill_relationships#get_experience_times"
            get "/skill_levels", to: "behavioral_skill_relationships#get_skill_levels"
          end
        end

        resources :remunerations, only: [ :index, :show, :create, :update, :destroy ]
        resources :remuneration_relationships, only: [ :index, :show, :create, :update, :destroy ] do
          collection do
            get "/currencies", to: "remuneration_relationships#get_currencies"
            get "/contract_types", to: "remuneration_relationships#get_contract_types"
            post "/bulk_upsert", to: "remuneration_relationships#bulk_upsert"
          end
        end

        resources :job_journeys, only: [ :index, :show, :create, :update, :destroy ] do
          collection do
            put "update_positions"
          end
        end

        resources :experiences, only: %i[index show create update destroy]
        resources :educations, only: %i[index show create update destroy]

        resources :companies, only: %i[index show create update destroy]
        resources :occupations, only: %i[index show create update destroy]
        resources :institutions, only: %i[index show create update destroy]
        resources :study_areas, only: %i[index show create update destroy]

        resources :languages, only: %i[index show create update destroy]
        resources :language_relationships, only: %i[index show create update destroy] do
          collection do
            get :levels, to: "language_relationships#levels", as: :levels
          end
        end
        resources :benefits, only: %i[index show create update destroy] do
          collection do
            get :grouped_by_category
          end
        end
        resources :benefit_relationships, only: %i[index show create update destroy] do
          collection do
            post "/create_collection", to: "benefit_relationships#create_collection"
            post "/bulk_upsert", to: "benefit_relationships#bulk_upsert"
          end
        end

        resources :dispatches, only: %i[index show create] do
          member do
            get "tracking_summary", to: "dispatches#tracking_summary"
          end
          collection do
            get "tracking_by_job", to: "dispatches#tracking_by_job"
          end
        end
        resources :answers, except: %i[new edit]

        resources :cities, only: %i[index]

        resources :entity_pages, only: %i[index show create update destroy] do
          collection do
            delete :destroy_all
          end
        end

        resources :entity_columns, only: [ :index, :show, :destroy ] do
          collection do
            get ":entity/structure", to: "entity_columns#show_structure", as: :structure
            post ":entity/save", to: "entity_columns#create", as: :create
            delete ":entity/delete", to: "entity_columns#destroy_by_entity", as: :destroy_by_entity
            post "views", to: "entity_columns#create_view", as: :create_view
            put ":entity/update_view", to: "entity_columns#update_view", as: :update_view
          end
          member do
            delete "view", to: "entity_columns#delete_view", as: :delete_view
          end
        end

        resources :job_field_templates, only: %i[index show create update destroy] do
          collection do
            get :default_fields
          end
        end

        resources :sectors, only: %i[index show create update destroy] do
          collection do
            get :tree
            get :autocomplete
          end
        end

        resources :sector_relationships, only: %i[index show create update destroy]

        resources :background_agents do
          collection do
            get :runnable, controller: "background_agents/status"
          end
          member do
            post :pause, controller: "background_agents/status"
            post :resume, controller: "background_agents/status"
            post :stop, controller: "background_agents/status"
            get :search_context, controller: "background_agents/status"
            patch :update_preferences, controller: "background_agents/status"
            patch :update_status, controller: "background_agents/status", action: :update_status
            post :deliver_cycle, controller: "background_agents/cycles", action: :deliver
            get :steps, controller: "background_agents/cycles"
            post :reset_cycles, controller: "background_agents/cycles", action: :reset
            post :log_search_iteration, controller: "background_agents/progress"
            post :report_progress, controller: "background_agents/progress", action: :report
            post :pearch_search, controller: "background_agents/searches", action: :pearch
            post :linkedin_search, controller: "background_agents/searches", action: :linkedin
            post :semantic_search, controller: "background_agents/searches", action: :semantic
          end
          resources :cycles, controller: "agent_cycles", only: %i[index show]
          resources :feedbacks, controller: "agent_feedbacks", only: %i[create] do
            collection do
              post :bulk
            end
          end
        end

        resources :sourcing_filters, only: %i[index create destroy]

        resources :lists, only: %i[index show create update destroy] do
          scope module: :lists do
            get "relationships/:reference_type", to: "list_relationships#index", as: :relationships
            get "relationships_by_reference/:reference_type", to: "list_relationships#index_by_reference", as: :relationships_by_reference

            resources :list_relationships, path: "relationships", param: :relationship_id do
              collection do
                post :sort
                post :collection
                delete :delete_collection
              end
            end
          end
        end

        namespace :evaluations do
          resources :evaluations, path: "", except: [ :new, :edit ] do
            member do
              get :dashboard_stats
            end
            post ":job_id/generate_report", to: "evaluations#generate_report", as: "generate_report"
            resources :questions, except: [ :new, :edit ]
            collection do
              get :bulk_stats, to: "evaluations_bulk_stats#index"
              get :response_rates, to: "response_rates#index"
            end
          end
          post "process_ai_response", to: "evaluations#process_ai_response"
        end

        resources :evaluation_candidates, only: [ :index, :show, :create, :update, :destroy ] do
          collection do
            post "create_collection", to: "evaluation_candidates#create_collection"
            get :stats
            get ":uid/wsi_decision", action: :wsi_decision, constraints: { uid: /[0-9a-f-]{36}/i }
            get ":uid/wsi_report", action: :wsi_report, constraints: { uid: /[0-9a-f-]{36}/i }
          end
        end

        resources :issues, only: %i[index show create update destroy]

        namespace :reports do
          post :executive_summary, to: "executive_summary#create"
        end

        namespace :admin do
          resources :accounts, only: %i[index show create update destroy]
          resources :roles, only: %i[index show create update destroy]
          resources :permissions, only: %i[index show]
          resources :users, only: %i[index show create update destroy]

          resources :llm_costs, only: [] do
            collection do
              get :overview
            end
          end

          resources :search_credits, only: [] do
            collection do
              get :list_accounts
            end
            member do
              post :add
              post :remove
              get :show
              get :transactions
            end
          end

          resources :llm_quotas, only: %i[index show update] do
            member do
              post :grant_extra
              post :reset_usage
            end
          end

          resources :job_field_templates, only: %i[index show create update destroy] do
            collection do
              get :default_fields
            end
          end

          resources :whatsapp_configurations, only: %i[index show create update destroy] do
            member do
              post :restore
            end
            collection do
              post :quick_update_url
            end
          end
        end

        resources :job_statuses, only: %i[index show create update destroy]
        resources :job_users, only: %i[index show create update destroy]

        # namespace :candidate_bulk_imports do
        #   post '/', to: 'candidate_bulk_imports#create'
        #   resource :preview, only: [:create], controller: 'previews'
        # end

        namespace :bulk_imports do
          post ":entity_type", to: "bulk_imports#create"
          post ":entity_type/preview", to: "previews#create", as: :preview
        end
      end



      resources :users, only: %i[index show create update destroy] do
        collection do
          get :search
        end
        member do
          post :send_invite
        end
      end

      namespace :evaluations do
        scope "/:account_uid/:evaluation_candidate_uid" do
          get "", to: "evaluation_candidates#show"
          post "decline", to: "evaluation_candidates#decline"
          get "status", to: "evaluation_candidates#status"
          post "reconnect", to: "evaluation_candidates#reconnect"
          get "questions", to: "questions#index"
          get "messages", to: "messages#index"
          post "messages", to: "messages#create"
          resources :answers, only: %i[index show create update destroy], controller: "answers"
        end
      end

      get "vagas/:slug/:account_slug", to: "public/jobs#show", as: "public_job_by_slug"
      post "vagas/:slug/:account_slug/applications", to: "public/applies#create", as: "public_apply_by_slug"

      scope "interview/:account_uid" do
        get ":token", to: "interview#show"
        post ":token/start", to: "interview#start"
        post ":token/answer", to: "interview#submit_answer"
        post ":token/complete", to: "interview#complete"
        post ":token/result", to: "interview#result"
      end

      scope "/:account_uid" do
        get "scheduling/:token", to: "scheduling#show", as: "scheduling_show"
        post "scheduling/:token/book", to: "scheduling#book", as: "scheduling_book"
        get "interview/:token", to: "interview#show", as: "interview_show"
      end
    end

  scope "api" do
    namespace :v1 do
      get    "notifications",              to: "notifications#index"
      get    "notifications/unread-count", to: "notifications#unread_count"
      post   "notifications/read-all",     to: "notifications#read_all"
      get    "notifications/:id",          to: "notifications#show"
      post   "notifications/:id/read",     to: "notifications#read"
      put    "notifications/:id/read",     to: "notifications#read"
      post   "notifications/:id/dismiss",  to: "notifications#dismiss"
      delete "notifications/:id",          to: "notifications#dismiss"
    end
  end
end
