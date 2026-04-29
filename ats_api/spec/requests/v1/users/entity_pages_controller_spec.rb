# frozen_string_literal: true

require "rails_helper"

RSpec.describe "V1::Users::EntityPages API", type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }

  describe "GET /v1/users/entity_pages" do
    context "when authenticated" do
      it "returns entity pages for the user" do
        create(:entity_page, user: user, account: account, entity: "candidates")
        create(:entity_page, user: user, account: account, entity: "jobs", link: "/jobs")

        Apartment::Tenant.switch!(account.tenant) do
          get "/v1/users/entity_pages", headers: auth_headers(user)
        end

        expect(response).to have_http_status(:ok)
        expect(json["data"].length).to eq(2)
      end
    end

    context "when unauthenticated" do
      it "returns unauthorized" do
        get "/v1/users/entity_pages", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe "POST /v1/users/entity_pages" do
    let(:valid_params) do
      {
        entity_page: {
          entity: "candidates",
          type_view: "table",
          pages: { link: "/candidates", data: { current_page: 1 }, query: { search: "test" } }
        }
      }
    end

    it "creates an entity page" do
      Apartment::Tenant.switch!(account.tenant) do
        expect {
          post "/v1/users/entity_pages", params: valid_params.to_json, headers: auth_headers(user)
        }.to change(EntityPage, :count).by(1)
      end

      expect(response).to have_http_status(:ok)
    end

    it "upserts when same combination exists" do
      Apartment::Tenant.switch!(account.tenant) do
        post "/v1/users/entity_pages", params: valid_params.to_json, headers: auth_headers(user)

        updated_params = valid_params.deep_dup
        updated_params[:entity_page][:pages][:data][:current_page] = 5

        expect {
          post "/v1/users/entity_pages", params: updated_params.to_json, headers: auth_headers(user)
        }.not_to change(EntityPage, :count)
      end
    end

    context "with missing required params" do
      let(:invalid_params) do
        { entity_page: { type_view: "table", pages: { link: "/test" } } }
      end

      it "returns error when entity is missing" do
        Apartment::Tenant.switch!(account.tenant) do
          post "/v1/users/entity_pages", params: invalid_params.to_json, headers: auth_headers(user)
        end

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe "GET /v1/users/entity_pages/:id" do
    it "returns the entity page" do
      page = create(:entity_page, user: user, account: account)

      Apartment::Tenant.switch!(account.tenant) do
        get "/v1/users/entity_pages/#{page.id}", headers: auth_headers(user)
      end

      expect(response).to have_http_status(:ok)
      expect(json["data"]["id"].to_i).to eq(page.id)
    end
  end

  describe "PUT /v1/users/entity_pages/:id" do
    it "updates the entity page" do
      page = create(:entity_page, user: user, account: account, entity: "candidates")

      Apartment::Tenant.switch!(account.tenant) do
        put "/v1/users/entity_pages/#{page.id}",
            params: { entity_page: { entity: "jobs" } }.to_json,
            headers: auth_headers(user)
      end

      expect(response).to have_http_status(:ok)
      expect(page.reload.entity).to eq("jobs")
    end
  end

  describe "DELETE /v1/users/entity_pages/:id" do
    it "destroys a specific entity page" do
      page = create(:entity_page, user: user, account: account)

      Apartment::Tenant.switch!(account.tenant) do
        delete "/v1/users/entity_pages/#{page.id}", headers: auth_headers(user)
      end

      expect(response).to have_http_status(:no_content)
      expect(EntityPage.find_by(id: page.id)).to be_nil
    end
  end

  describe "DELETE /v1/users/entity_pages/destroy_all" do
    it "destroys all entity pages for the user" do
      create(:entity_page, user: user, account: account, entity: "candidates")
      create(:entity_page, user: user, account: account, entity: "jobs", link: "/jobs")

      Apartment::Tenant.switch!(account.tenant) do
        delete "/v1/users/entity_pages/destroy_all", headers: auth_headers(user)
      end

      expect(response).to have_http_status(:no_content)
      expect(EntityPage.where(user_id: user.id).count).to eq(0)
    end
  end

  describe "IDOR protection" do
    let(:other_user) { create(:user) }
    let!(:other_page) { create(:entity_page, user: other_user, account: other_user.account) }

    it "cannot show another user's entity page" do
      Apartment::Tenant.switch!(account.tenant) do
        get "/v1/users/entity_pages/#{other_page.id}", headers: auth_headers(user)
      end

      expect(response).to have_http_status(:not_found)
    end

    it "cannot destroy another user's entity page" do
      Apartment::Tenant.switch!(account.tenant) do
        delete "/v1/users/entity_pages/#{other_page.id}", headers: auth_headers(user)
      end

      expect(response).to have_http_status(:not_found)
      expect(EntityPage.find_by(id: other_page.id)).to be_present
    end

    it "cannot update another user's entity page" do
      Apartment::Tenant.switch!(account.tenant) do
        put "/v1/users/entity_pages/#{other_page.id}",
            params: { entity_page: { entity: "hacked" } }.to_json,
            headers: auth_headers(user)
      end

      expect(response).to have_http_status(:not_found)
      expect(other_page.reload.entity).not_to eq("hacked")
    end

    it "index only returns own entity pages" do
      create(:entity_page, user: user, account: account, entity: "jobs", link: "/jobs")

      Apartment::Tenant.switch!(account.tenant) do
        get "/v1/users/entity_pages", headers: auth_headers(user)
      end

      expect(response).to have_http_status(:ok)
      ids = json["data"].map { |d| d["id"].to_i }
      expect(ids).not_to include(other_page.id)
    end
  end
end
