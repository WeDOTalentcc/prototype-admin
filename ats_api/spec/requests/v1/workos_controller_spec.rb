# frozen_string_literal: true

require 'rails_helper'

RSpec.describe "V1::Workos API", type: :request do
  let(:headers) { { "Content-Type" => "application/json" } }

  describe "GET /v1/workos/sso_options" do
    context "when password login is disabled" do
      let(:account) do
        create(:account,
          workos_enabled: true,
          workos_organization_id: "org_123",
          workos_connection_id: "conn_123",
          domain: "example.com",
          sso_providers: [ "microsoft_entra_id" ],
          auth_config: {
            "password_login_enabled" => false,
            "microsoft_sso_enabled" => true
          })
      end
      let(:user) { create(:user, account: account, email: "user@example.com") }

      it "returns login_traditional_enabled as false" do
        get "/v1/workos/sso_options", params: { email: user.email }, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["login_traditional_enabled"]).to eq(false)
      end
    end

    context "when password login is enabled" do
      let(:account) do
        create(:account,
          workos_enabled: true,
          workos_organization_id: "org_123",
          workos_connection_id: "conn_123",
          domain: "example.com",
          sso_providers: [ "microsoft_entra_id" ],
          auth_config: {
            "password_login_enabled" => true,
            "microsoft_sso_enabled" => true
          })
      end
      let(:user) { create(:user, account: account, email: "user@example.com") }

      it "returns login_traditional_enabled as true" do
        get "/v1/workos/sso_options", params: { email: user.email }, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["login_traditional_enabled"]).to eq(true)
      end
    end

    context "when sso is enforced and password is enabled" do
      let(:account) do
        create(:account,
          workos_enabled: true,
          workos_organization_id: "org_123",
          workos_connection_id: "conn_123",
          domain: "example.com",
          sso_enforced: true,
          sso_providers: [ "microsoft_entra_id" ],
          auth_config: {
            "password_login_enabled" => true,
            "microsoft_sso_enabled" => true
          })
      end
      let(:user) { create(:user, account: account, email: "user@example.com") }

      it "returns login_traditional_enabled as false because sso is enforced" do
        get "/v1/workos/sso_options", params: { email: user.email }, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["login_traditional_enabled"]).to eq(false)
      end
    end

    context "when account has no auth config" do
      let(:account) { create(:account, domain: "example.com") }
      let(:user) { create(:user, account: account, email: "user@example.com") }

      it "returns login_traditional_enabled as true by default" do
        get "/v1/workos/sso_options", params: { email: user.email }, headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["login_traditional_enabled"]).to eq(true)
      end
    end
  end
end
