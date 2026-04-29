# frozen_string_literal: true

require "rails_helper"

RSpec.describe EntityPage, type: :model do
  describe "validations" do
    it { is_expected.to validate_presence_of(:entity) }
    it { is_expected.to validate_presence_of(:type_view) }

    describe "uniqueness" do
      subject { create(:entity_page) }

      it { is_expected.to validate_uniqueness_of(:entity).scoped_to(%i[user_id type_view link custom_entity]) }
    end

    describe "#pages_size_limit" do
      let(:user) { create(:user) }

      it "rejects pages larger than 512KB" do
        page = build(:entity_page, user: user, account: user.account, pages: { query: "x" * 600_000 })
        expect(page).not_to be_valid
        expect(page.errors[:pages]).to include("is too large (max 512KB)")
      end

      it "accepts pages within 512KB" do
        page = build(:entity_page, user: user, account: user.account, pages: { query: "ok" })
        expect(page).to be_valid
      end
    end

    describe "#max_pages_per_user" do
      let(:user) { create(:user) }

      it "rejects when user has 100+ entity pages" do
        EntityPage::MAX_PAGES_PER_USER.times do |i|
          create(:entity_page, user: user, account: user.account, entity: "entity_#{i}", link: "/e/#{i}")
        end

        page = build(:entity_page, user: user, account: user.account, entity: "overflow", link: "/overflow")
        expect(page).not_to be_valid
        expect(page.errors[:base]).to include("maximum entity pages reached")
      end
    end
  end

  describe "associations" do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to belong_to(:account).optional }
  end

  describe "#strip_heavy_keys_from_pages" do
    let(:user) { create(:user) }

    it "strips data key from pages before validation" do
      page = create(:entity_page, user: user, account: user.account, pages: {
        link: "/candidates", query: "test", data: { items: Array.new(500) { { id: _1, name: "n" } } }
      })

      expect(page.pages).not_to have_key("data")
      expect(page.pages["link"]).to eq("/candidates")
      expect(page.pages["query"]).to eq("test")
    end

    it "preserves pages when data key is absent" do
      page = create(:entity_page, user: user, account: user.account, pages: {
        link: "/jobs", query: "ruby", where: { is_active: true }
      })

      expect(page.pages["link"]).to eq("/jobs")
      expect(page.pages["query"]).to eq("ruby")
      expect(page.pages["where"]).to eq({ "is_active" => true })
    end

    it "does nothing when pages is blank" do
      page = build(:entity_page, user: user, account: user.account, pages: nil)
      page.valid?
      expect(page.pages).to be_nil
    end
  end

  describe ".upsert_page" do
    let(:user) { create(:user) }

    let(:params) do
      {
        entity: "candidates",
        type_view: "table",
        custom_entity: nil,
        pages: { link: "/candidates", data: { current_page: 1 }, query: { search: "test" } }
      }
    end

    it "creates a new entity_page" do
      result = described_class.upsert_page(user, params)

      expect(result).to be_persisted
      expect(result.entity).to eq("candidates")
      expect(result.link).to eq("/candidates")
    end

    it "updates existing entity_page when same combination exists" do
      described_class.upsert_page(user, params)

      updated_params = params.deep_dup
      updated_params[:pages][:query][:search] = "updated"

      result = described_class.upsert_page(user, updated_params)

      expect(described_class.for_user(user.id).count).to eq(1)
      expect(result.pages["query"]["search"]).to eq("updated")
    end

    it "creates separate records for different entities" do
      described_class.upsert_page(user, params)

      job_params = params.deep_dup.merge(entity: "jobs")
      job_params[:pages][:link] = "/jobs"
      described_class.upsert_page(user, job_params)

      expect(described_class.for_user(user.id).count).to eq(2)
    end

    it "retries on RecordNotUnique and limits retries" do
      allow(described_class).to receive(:find_by).and_return(nil)
      allow(described_class).to receive(:create).and_raise(ActiveRecord::RecordNotUnique)

      expect { described_class.upsert_page(user, params) }.to raise_error(ActiveRecord::RecordNotUnique)
    end
  end

  describe ".for_user" do
    let(:user) { create(:user) }

    it "returns only records for the given user ordered by id" do
      page1 = create(:entity_page, user: user, account: user.account, entity: "candidates")
      page2 = create(:entity_page, user: user, account: user.account, entity: "jobs", link: "/jobs")
      other_user = create(:user)
      create(:entity_page, user: other_user, account: other_user.account, entity: "candidates")

      result = described_class.for_user(user.id)

      expect(result).to eq([page1, page2])
    end
  end
end
