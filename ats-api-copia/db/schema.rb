# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.1].define(version: 2025_07_14_142059) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"

  create_table "accounts", force: :cascade do |t|
    t.string "name"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "tenant"
    t.string "staging_tenant"
    t.index ["staging_tenant"], name: "index_accounts_on_staging_tenant"
    t.index ["tenant"], name: "index_accounts_on_tenant"
  end

  create_table "applies", force: :cascade do |t|
    t.bigint "candidate_id", null: false
    t.bigint "job_id", null: false
    t.bigint "selective_process_id", null: false
    t.boolean "is_deleted", default: false, null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["candidate_id"], name: "index_applies_on_candidate_id"
    t.index ["job_id"], name: "index_applies_on_job_id"
    t.index ["selective_process_id"], name: "index_applies_on_selective_process_id"
  end

  create_table "candidates", force: :cascade do |t|
    t.string "uid"
    t.string "name"
    t.string "surname"
    t.string "email", default: ""
    t.string "secondary_email"
    t.string "mobile_phone"
    t.string "phone"
    t.string "secondary_phone"
    t.string "linkedin"
    t.string "github"
    t.string "portfolio"
    t.string "current_company"
    t.string "role_name"
    t.string "position_level"
    t.text "self_introduction"
    t.text "curriculum_text"
    t.date "date_birth"
    t.integer "gender"
    t.string "nationality"
    t.integer "marital_status"
    t.string "cpf"
    t.string "street"
    t.integer "number"
    t.string "district"
    t.string "zip"
    t.string "city"
    t.string "state"
    t.string "country"
    t.string "complement"
    t.float "clt_expectation", default: 0.0
    t.float "pj_expectation", default: 0.0
    t.float "freelance_expectation", default: 0.0
    t.float "current_salary", default: 0.0
    t.float "desired_salary"
    t.string "currency", default: "BRL"
    t.boolean "remote_work"
    t.boolean "mobility", default: true
    t.string "interests"
    t.text "comments"
    t.string "source"
    t.string "avatar_url"
    t.string "curriculum_pdf_url"
    t.boolean "completed_register", default: false
    t.boolean "accept_terms", default: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["email"], name: "index_candidates_on_email"
    t.index ["linkedin"], name: "index_candidates_on_linkedin"
    t.index ["uid"], name: "index_candidates_on_uid"
  end

  create_table "jobs", force: :cascade do |t|
    t.string "title"
    t.text "description"
    t.bigint "user_id", null: false
    t.bigint "account_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "provider", default: "", null: false
    t.string "provider_job_id", default: "", null: false
    t.bigint "company_id"
    t.datetime "published_date"
    t.datetime "application_deadline"
    t.boolean "is_remote"
    t.string "city"
    t.string "state"
    t.string "country"
    t.string "job_url"
    t.bigint "career_page_id"
    t.string "career_page_name"
    t.string "career_page_url"
    t.string "career_page_logo"
    t.boolean "friendly_badge"
    t.boolean "disabilities"
    t.string "workplace_type"
    t.index ["account_id"], name: "index_jobs_on_account_id"
    t.index ["provider", "provider_job_id"], name: "index_jobs_on_provider_and_job_id", unique: true
    t.index ["user_id"], name: "index_jobs_on_user_id"
  end

  create_table "messages", force: :cascade do |t|
    t.text "content"
    t.integer "entity", default: 0, null: false
    t.boolean "is_deleted", default: false
    t.integer "status", default: 0, null: false
    t.bigint "parent_message_id"
    t.string "reference_type", null: false
    t.bigint "reference_id", null: false
    t.bigint "account_id"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.jsonb "metadata", default: {}
    t.index ["account_id"], name: "index_messages_on_account_id"
    t.index ["parent_message_id"], name: "index_messages_on_parent_message_id"
    t.index ["reference_type", "reference_id"], name: "index_messages_on_reference"
  end

  create_table "permissions", force: :cascade do |t|
    t.string "name", null: false
    t.text "description"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["name"], name: "index_permissions_on_name", unique: true
  end

  create_table "role_permissions", force: :cascade do |t|
    t.bigint "role_id", null: false
    t.bigint "permission_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["permission_id"], name: "index_role_permissions_on_permission_id"
    t.index ["role_id", "permission_id"], name: "index_role_permissions_on_role_id_and_permission_id", unique: true
    t.index ["role_id"], name: "index_role_permissions_on_role_id"
  end

  create_table "roles", force: :cascade do |t|
    t.string "name", null: false
    t.text "description"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["name"], name: "index_roles_on_name", unique: true
  end

  create_table "selective_processes", force: :cascade do |t|
    t.string "name"
    t.integer "position"
    t.integer "status"
    t.bigint "job_id"
    t.string "uid"
    t.jsonb "sub_status", default: []
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["job_id"], name: "index_selective_processes_on_job_id"
    t.index ["uid"], name: "index_selective_processes_on_uid"
  end

  create_table "user_permissions", force: :cascade do |t|
    t.bigint "user_id", null: false
    t.bigint "permission_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["permission_id"], name: "index_user_permissions_on_permission_id"
    t.index ["user_id", "permission_id"], name: "index_user_permissions_on_user_id_and_permission_id", unique: true
    t.index ["user_id"], name: "index_user_permissions_on_user_id"
  end

  create_table "user_roles", force: :cascade do |t|
    t.bigint "user_id", null: false
    t.bigint "role_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["role_id"], name: "index_user_roles_on_role_id"
    t.index ["user_id", "role_id"], name: "index_user_roles_on_user_id_and_role_id", unique: true
    t.index ["user_id"], name: "index_user_roles_on_user_id"
  end

  create_table "users", force: :cascade do |t|
    t.string "email"
    t.string "password_digest"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.bigint "account_id"
    t.index ["account_id"], name: "index_users_on_account_id"
  end

  add_foreign_key "applies", "candidates"
  add_foreign_key "applies", "jobs"
  add_foreign_key "applies", "selective_processes"
  add_foreign_key "messages", "accounts"
  add_foreign_key "role_permissions", "permissions"
  add_foreign_key "role_permissions", "roles"
  add_foreign_key "selective_processes", "jobs"
  add_foreign_key "user_permissions", "permissions"
  add_foreign_key "user_permissions", "users"
  add_foreign_key "user_roles", "roles"
  add_foreign_key "user_roles", "users"
  add_foreign_key "users", "accounts"
end
