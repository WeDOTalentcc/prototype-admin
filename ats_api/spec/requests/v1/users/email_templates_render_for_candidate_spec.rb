# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::EmailTemplates#render_for_candidate", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe "POST /v1/users/email_templates/render_for_candidate" do
    context "when authenticated" do
      let!(:candidate) { create(:candidate, account: account, name: "Maria Silva") }
      let!(:job) { create(:job, account: account, user: user, title: "Developer") }
      let!(:template) do
        create(:email_template,
               account: account,
               user: user,
               subject: "Process update - {{vaga}}",
               content: "Hello {{candidato_nome}}, your application to {{vaga}} has an update.")
      end

      it "returns rendered template with variables resolved" do
        post "/v1/users/email_templates/render_for_candidate", headers: headers, params: {
          template_id: template.id,
          candidate_id: candidate.id,
          job_id: job.id
        }

        expect(response).to have_http_status(:ok)
        body = json

        expect(body).to have_key("subject")
        expect(body).to have_key("body")
        expect(body).to have_key("body_text")
        expect(body).to have_key("variables_used")
        expect(body).to have_key("variables_missing")
        expect(body["variables_missing"]).to be_an(Array)
      end

      it "applies extra_variables substitutions" do
        template.update!(content: "Hello {{candidato_nome}}, custom: {{custom_field}}")

        post "/v1/users/email_templates/render_for_candidate", headers: headers, params: {
          template_id: template.id,
          candidate_id: candidate.id,
          extra_variables: { custom_field: "custom_value" }
        }

        expect(response).to have_http_status(:ok)
        body = json
        expect(body["body"]).to include("custom_value")
      end

      it "returns not found for invalid template_id" do
        post "/v1/users/email_templates/render_for_candidate", headers: headers, params: {
          template_id: 0,
          candidate_id: candidate.id
        }

        expect(response).to have_http_status(:not_found)
      end

      it "returns not found for invalid candidate_id" do
        post "/v1/users/email_templates/render_for_candidate", headers: headers, params: {
          template_id: template.id,
          candidate_id: 0
        }

        expect(response).to have_http_status(:not_found)
      end
    end

    context "when not authenticated" do
      it "returns unauthorized" do
        post "/v1/users/email_templates/render_for_candidate"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
